"""`diagnoser` — LLM node with a closed-set, schema-enforced output."""

from __future__ import annotations

from ..config import get_settings
from ..llm import call_structured
from ..prompts import diagnoser as prompt
from ..taxonomy import get_taxonomy
from .state import GraphState


class DiagnosisRejected(ValueError):
    """The model emitted something outside the taxonomy — a bug, not a user error."""


def diagnoser_node(state: GraphState) -> GraphState:
    settings = get_settings()
    taxonomy = get_taxonomy()

    # Escalate only on a retry, and only once — spec section 2.
    tier = state.get("model_tier") or settings.model_tier_cheap
    retry_count = state.get("retry_count", 0)

    retry_reason = None
    if retry_count:
        failures = state.get("verifier_failures", [])
        retry_reason = "\n".join(f"- {f['check']}: {f['detail']}" for f in failures)

    result = call_structured(
        model=tier,
        cached_system=prompt.build_system_prompt(taxonomy),
        user_content=prompt.build_user_content(
            problem_slug=state["problem_slug"],
            problem_title=state.get("problem_title", ""),
            difficulty=state.get("problem_difficulty", "unknown"),
            tags=state.get("problem_tags", []),
            language=state["language"],
            failure_type=state["failure_type"],
            structural_signals=state.get("structural_signals", []),
            vaulted_code=state["vaulted_code"],
            retry_reason=retry_reason,
        ),
        tool_name=prompt.TOOL_NAME,
        tool_description=prompt.TOOL_DESCRIPTION,
        input_schema=prompt.build_tool_schema(taxonomy),
        max_tokens=8192,
        effort="high" if tier == settings.model_tier_strong else None,
    )

    payload = result.tool_input
    pattern_id = payload.get("pattern_id", "")

    # Belt and braces: the enum should make this unreachable, but a free-text category
    # reaching the database would corrupt every weak-pattern statistic downstream.
    if pattern_id not in taxonomy:
        raise DiagnosisRejected(f"{pattern_id!r} is not in the taxonomy")

    alternate = payload.get("alternate_pattern_id")
    if alternate is not None and alternate not in taxonomy:
        alternate = None

    spans = [
        {
            "start_line": int(s["start_line"]),
            "end_line": int(s["end_line"]),
            "why": str(s["why"]),
        }
        for s in payload.get("evidence_spans", [])
    ]

    return {
        **state,
        "pattern_id": pattern_id,
        "alternate_pattern_id": alternate,
        "confidence": max(0.0, min(1.0, float(payload.get("confidence", 0.0)))),
        "evidence_spans": spans,
        "explanation": str(payload.get("explanation", "")).strip(),
        "model_tier": result.model,
        "cost_usd": state.get("cost_usd", 0.0) + result.cost_usd,
        "latency_ms": state.get("latency_ms", 0) + result.latency_ms,
    }
