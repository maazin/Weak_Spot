"""`intake` — no LLM. Normalize, vault, extract structural signals, hash.

The vaulting step is the system's primary defense against prompt injection, so it is
built to hold under adversarial input rather than to be elegant:

  * It is **lexical, not parser-based.** An attacker's submission is frequently invalid
    code — that is the cheapest way to defeat anything that needs a successful parse.
    This scanner never fails to produce output, so there is no input that slips through
    unvaulted because "the parser errored".
  * It **preserves line numbering.** A vaulted token spanning N lines emits its
    placeholder plus N-1 newlines, so `evidence_spans` line numbers returned by the
    model still index the code the user actually submitted.
  * Placeholders are opaque (`<!C0!>`, `<!S3!>`) and restored only when rendering
    evidence back to the user — never before the model sees the code.

What this cannot vault is identifiers: a variable literally named
`ignore_all_previous_instructions` is program structure, not a string. That residue is
what verifier check 4 exists to catch, which is why the two mitigations are specified
together.
"""

from __future__ import annotations

import ast
import hashlib
import re

from ..config import get_settings
from .state import GraphState

COMMENT_PLACEHOLDER = "<!C{}!>"
STRING_PLACEHOLDER = "<!S{}!>"

PLACEHOLDER_RE = re.compile(r"<!([CS])(\d+)!>")

# Per-language lexical rules: (line_comment_starts, block_comment_pairs, string_delims)
# Triple quotes precede single quotes so Python docstrings vault as one token.
_LANG_RULES: dict[str, tuple[tuple[str, ...], tuple[tuple[str, str], ...], tuple[str, ...]]] = {
    "python": (("#",), (), ('"""', "'''", '"', "'")),
    "java": (("//",), (("/*", "*/"),), ('"""', '"', "'")),
    "cpp": (("//",), (("/*", "*/"),), ('"', "'")),
    "javascript": (("//",), (("/*", "*/"),), ('"', "'", "`")),
    "go": (("//",), (("/*", "*/"),), ('"', "'", "`")),
}


class IntakeError(ValueError):
    """Raised before any LLM call — the spec requires rejecting unparseable input early."""


def normalize(code: str) -> str:
    text = code.replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip("\n")


def _blank_preserving(token: str, placeholder: str) -> str:
    """Placeholder padded with the newlines the original token consumed."""
    return placeholder + "\n" * token.count("\n")


def vault(code: str, language: str) -> tuple[str, dict[str, str]]:
    """Replace every comment and string literal with an opaque placeholder.

    Returns the vaulted source and a mapping from placeholder to original text.
    """
    line_comments, block_comments, string_delims = _LANG_RULES.get(
        language, _LANG_RULES["python"]
    )
    # Longest-first so `"""` wins over `"` and `/*` is not read as `/`.
    string_delims = tuple(sorted(string_delims, key=len, reverse=True))

    vault_map: dict[str, str] = {}
    out: list[str] = []
    i = 0
    n = len(code)
    c_index = 0
    s_index = 0

    while i < n:
        matched = False

        # --- line comments ---
        for marker in line_comments:
            if code.startswith(marker, i):
                end = code.find("\n", i)
                end = n if end == -1 else end
                token = code[i:end]
                key = COMMENT_PLACEHOLDER.format(c_index)
                vault_map[key] = token
                out.append(key)
                c_index += 1
                i = end
                matched = True
                break
        if matched:
            continue

        # --- block comments ---
        for opener, closer in block_comments:
            if code.startswith(opener, i):
                end = code.find(closer, i + len(opener))
                end = n if end == -1 else end + len(closer)
                token = code[i:end]
                key = COMMENT_PLACEHOLDER.format(c_index)
                vault_map[key] = token
                out.append(_blank_preserving(token, key))
                c_index += 1
                i = end
                matched = True
                break
        if matched:
            continue

        # --- string literals ---
        for delim in string_delims:
            if code.startswith(delim, i):
                j = i + len(delim)
                while j < n:
                    if code[j] == "\\":  # escaped char, skip the pair
                        j += 2
                        continue
                    if code.startswith(delim, j):
                        j += len(delim)
                        break
                    j += 1
                else:
                    j = n  # unterminated literal: vault to end of input
                token = code[i:j]
                key = STRING_PLACEHOLDER.format(s_index)
                vault_map[key] = token
                out.append(_blank_preserving(token, key))
                s_index += 1
                i = j
                matched = True
                break
        if matched:
            continue

        out.append(code[i])
        i += 1

    return "".join(out), vault_map


def restore(text: str, vault_map: dict[str, str]) -> str:
    """Put the originals back. Only ever called when rendering evidence to the user."""

    def _sub(match: re.Match[str]) -> str:
        return vault_map.get(match.group(0), match.group(0))

    return PLACEHOLDER_RE.sub(_sub, text)


def _python_signals(code: str) -> list[str]:
    """Real AST signals for Python — cheap structural facts, no semantics."""
    tree = ast.parse(code)
    signals: set[str] = set()
    max_loop_depth = 0

    def walk(node: ast.AST, loop_depth: int) -> None:
        nonlocal max_loop_depth
        for child in ast.iter_child_nodes(node):
            depth = loop_depth
            if isinstance(child, (ast.For, ast.While, ast.AsyncFor)):
                depth += 1
                max_loop_depth = max(max_loop_depth, depth)
            if isinstance(child, (ast.Dict, ast.DictComp)):
                signals.add("dict allocated")
            if isinstance(child, (ast.Set, ast.SetComp)):
                signals.add("set allocated")
            if isinstance(child, (ast.List, ast.ListComp)):
                signals.add("list allocated")
            if isinstance(child, ast.Call):
                fn = child.func
                name = getattr(fn, "id", None) or getattr(fn, "attr", None)
                if name in {"sort", "sorted"}:
                    signals.add("sorting called")
                if name in {"heappush", "heappop", "heapify", "nlargest", "nsmallest"}:
                    signals.add("heap used")
                if name in {"deque"}:
                    signals.add("deque used")
                if name in {"pop"} and child.args:
                    first = child.args[0]
                    if isinstance(first, ast.Constant) and first.value == 0:
                        signals.add("pop from front of list")
                if name in {"insert"} and child.args:
                    first = child.args[0]
                    if isinstance(first, ast.Constant) and first.value == 0:
                        signals.add("insert at front of list")
            if isinstance(child, ast.FunctionDef):
                for dec in child.decorator_list:
                    dec_name = getattr(dec, "id", None) or getattr(dec, "attr", None)
                    if dec_name in {"cache", "lru_cache", "memoize"}:
                        signals.add("memoization present")
            if isinstance(child, ast.Compare):
                for op in child.ops:
                    if isinstance(op, ast.In):
                        signals.add("membership test present")
            if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                signals.add("augmented addition in body")
            walk(child, depth)

    walk(tree, 0)

    # Recursion: any function that calls its own name.
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Call) and getattr(inner.func, "id", None) == node.name:
                    signals.add("recursion present")

    if max_loop_depth:
        signals.add(f"maximum loop nesting depth {max_loop_depth}")
    if "memoization present" not in signals and "recursion present" in signals:
        signals.add("recursion without memoization")
    return sorted(signals)


_GENERIC_PATTERNS: list[tuple[str, str]] = [
    (r"\bfor\b|\bwhile\b", "loop present"),
    (r"\bsort\s*\(|\.sort\b|Arrays\.sort|sort\.Slice", "sorting called"),
    (r"\bnew\s+HashMap|\bmap\[|\bunordered_map|\bnew Map\(|\{\}", "map or dict allocated"),
    (r"\bnew\s+HashSet|\bunordered_set|\bnew Set\(", "set allocated"),
    (r"PriorityQueue|priority_queue|heapq|container/heap", "heap used"),
    (r"\bmemo\b|\bcache\b|\bdp\b", "memoization or dp table present"),
    (r"\bmid\b|\(lo\s*\+\s*hi\)|\(left\s*\+\s*right\)", "binary search midpoint present"),
    (r"\bqueue\b|\bdeque\b|ArrayDeque|LinkedList", "queue used"),
    (r"\bvisited\b|\bseen\b", "visited set present"),
]


def _generic_signals(code: str) -> list[str]:
    signals: set[str] = set()
    for pattern, label in _GENERIC_PATTERNS:
        if re.search(pattern, code):
            signals.add(label)

    depth = 0
    max_depth = 0
    for line in code.split("\n"):
        if re.search(r"\b(for|while)\b", line):
            depth += 1
            max_depth = max(max_depth, depth)
        if line.strip() in {"}", "};"}:
            depth = max(0, depth - 1)
    if max_depth:
        signals.add(f"approximate loop nesting depth {max_depth}")
    return sorted(signals)


def extract_signals(code: str, language: str) -> list[str]:
    """Structural signals.

    Parsed from the *original* source, not the vaulted copy: placeholders like `<!S0!>`
    are not valid syntax in any supported language, so the vaulted text cannot be given
    to a parser. This is safe because every signal produced here is drawn from a fixed
    vocabulary of structural labels — no attacker-supplied text reaches the output, and
    `ast.parse` builds a tree without executing anything.
    """
    if language == "python":
        try:
            return _python_signals(code)
        except SyntaxError as exc:
            raise IntakeError(f"could not parse Python submission: {exc}") from exc
    return _generic_signals(code)


def compute_code_hash(problem_slug: str, normalized_code: str) -> str:
    return hashlib.sha256(f"{problem_slug}\n{normalized_code}".encode()).hexdigest()


def validate_size(code: str) -> None:
    settings = get_settings()
    encoded = code.encode("utf-8")
    if len(encoded) > settings.max_code_bytes:
        raise IntakeError(
            f"submission is {len(encoded)} bytes; the cap is {settings.max_code_bytes}"
        )
    line_count = code.count("\n") + 1
    if line_count > settings.max_code_lines:
        raise IntakeError(
            f"submission is {line_count} lines; the cap is {settings.max_code_lines}"
        )


def intake_node(state: GraphState) -> GraphState:
    code = state["code_text"]
    language = state["language"]

    validate_size(code)
    normalized = normalize(code)
    if not normalized.strip():
        raise IntakeError("submission is empty")

    # Signals from the original (parseable) source; the model only ever sees the vaulted
    # copy. See extract_signals for why these two inputs differ.
    signals = extract_signals(normalized, language)
    vaulted_code, vault_map = vault(normalized, language)

    return {
        **state,
        "normalized_code": normalized,
        "vaulted_code": vaulted_code,
        "vault": vault_map,
        "structural_signals": signals,
        "code_hash": compute_code_hash(state["problem_slug"], normalized),
    }
