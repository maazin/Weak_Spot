"""Taxonomy loader and validator.

The taxonomy is a closed set. The diagnoser may only emit ids that appear here, and
`allowed_ids()` is what enforces that at the schema boundary — not a prompt instruction,
which a model is free to ignore.
"""

from __future__ import annotations

import functools
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from .config import get_settings

FAMILIES = ("pattern_selection", "implementation", "complexity", "comprehension")


class PatternEntry(BaseModel):
    id: str
    family: str
    name: str
    signals: list[str] = Field(min_length=1)
    correct_approach: str
    related_patterns: list[str] = Field(default_factory=list)
    practice_tags: list[str] = Field(min_length=1)

    @field_validator("family")
    @classmethod
    def _known_family(cls, v: str) -> str:
        if v not in FAMILIES:
            raise ValueError(f"unknown family {v!r}; expected one of {FAMILIES}")
        return v

    @field_validator("id")
    @classmethod
    def _id_shape(cls, v: str) -> str:
        if v.count(".") != 1:
            raise ValueError(f"id {v!r} must be exactly '<family>.<slug>'")
        return v

    @field_validator("correct_approach")
    @classmethod
    def _approach_is_prose(cls, v: str) -> str:
        text = v.strip()
        if len(text) < 120:
            raise ValueError("correct_approach must be a substantive description")
        # The spec forbids handing over solutions. Prose only, never code.
        if "```" in text or "def " in text or "for (" in text:
            raise ValueError("correct_approach must not contain code")
        return text

    def model_post_init(self, _ctx) -> None:
        prefix = self.id.split(".", 1)[0]
        if prefix != self.family:
            raise ValueError(f"id prefix {prefix!r} does not match family {self.family!r}")


class Taxonomy:
    def __init__(self, entries: list[PatternEntry]) -> None:
        self.entries = entries
        self.by_id = {e.id: e for e in entries}

    def __len__(self) -> int:
        return len(self.entries)

    def __contains__(self, pattern_id: object) -> bool:
        return pattern_id in self.by_id

    def get(self, pattern_id: str) -> PatternEntry | None:
        return self.by_id.get(pattern_id)

    def allowed_ids(self) -> list[str]:
        return [e.id for e in self.entries]

    def by_family(self, family: str) -> list[PatternEntry]:
        return [e for e in self.entries if e.family == family]

    def family_of(self, pattern_id: str) -> str | None:
        entry = self.by_id.get(pattern_id)
        return entry.family if entry else None

    def as_prompt_block(self) -> str:
        """The constant block that leads the diagnoser prompt and carries the cache marker.

        Kept deterministic — any instability here silently destroys the prompt cache hit
        rate, which is the largest single cost lever in the system.
        """
        lines: list[str] = []
        for family in FAMILIES:
            lines.append(f"## FAMILY: {family}")
            for e in self.by_family(family):
                lines.append(f"### {e.id}")
                lines.append(f"name: {e.name}")
                lines.append("signals:")
                lines.extend(f"  - {s}" for s in e.signals)
                lines.append(f"gap: {' '.join(e.correct_approach.split())}")
                lines.append("")
        return "\n".join(lines)


def load_taxonomy(path: Path | str | None = None) -> Taxonomy:
    p = Path(path or get_settings().taxonomy_path)
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError(f"{p} must contain a non-empty list of pattern entries")

    entries = [PatternEntry.model_validate(item) for item in raw]

    seen: set[str] = set()
    for e in entries:
        if e.id in seen:
            raise ValueError(f"duplicate pattern id {e.id!r}")
        seen.add(e.id)

    for e in entries:
        for rel in e.related_patterns:
            if rel not in seen:
                raise ValueError(f"{e.id} references unknown related pattern {rel!r}")
            if rel == e.id:
                raise ValueError(f"{e.id} lists itself as a related pattern")

    return Taxonomy(entries)


@functools.lru_cache(maxsize=1)
def get_taxonomy() -> Taxonomy:
    return load_taxonomy()
