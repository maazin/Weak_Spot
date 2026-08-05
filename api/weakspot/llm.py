"""Anthropic client, model tiering, prompt caching, and cost accounting.

Three things the spec demands live here:

1.  **Prompt caching on the taxonomy block.** The taxonomy is ~11k tokens and constant
    across every diagnosis, so it leads the system prompt and carries the sole
    `cache_control` breakpoint. Everything volatile (the submission) goes in the user
    turn, after the breakpoint. Cache reads bill at ~0.1x input, writes at ~1.25x, so
    this is the single biggest cost lever in the system. `cache_hit` on every call
    result exists so a regression here is visible in `/metrics` rather than silent.

2.  **Structured output.** Enforced with a strict tool schema plus a forced
    `tool_choice` — a prompt instruction to "return JSON" is not enforcement.

3.  **Cost.** Computed per call from the four usage counters, at each tier's real rates.

Tier notes that are easy to get wrong:
  - Haiku 4.5 rejects `output_config.effort` — never send it there.
  - Opus 5 runs adaptive thinking by default, so it needs `max_tokens` headroom for
    thinking plus the tool call, not just the tool call.
  - Haiku 4.5's minimum cacheable prefix is 4096 tokens. The taxonomy block clears it;
    a much smaller taxonomy would silently stop caching, which `test_taxonomy_block_
    exceeds_cache_minimum` guards.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import anthropic

from .config import get_settings

# USD per million tokens, per tier.
PRICING: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-opus-5": (5.00, 25.00),
}

CACHE_WRITE_MULTIPLIER = 1.25  # 5-minute TTL
CACHE_READ_MULTIPLIER = 0.10

# Below this, a prefix silently will not cache on Haiku 4.5.
HAIKU_CACHE_MINIMUM_TOKENS = 4096


class ModelTierError(RuntimeError):
    pass


@dataclass
class LLMResult:
    tool_input: dict[str, Any]
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    stop_reason: str | None = None
    raw_text: str = ""

    @property
    def cache_hit(self) -> bool:
        return self.cache_read_input_tokens > 0


@dataclass
class _Client:
    _client: anthropic.Anthropic | None = field(default=None, repr=False)

    def get(self) -> anthropic.Anthropic:
        if self._client is None:
            settings = get_settings()
            if not settings.anthropic_api_key:
                raise ModelTierError("ANTHROPIC_API_KEY is not set; the diagnosis graph cannot run")
            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        return self._client


_shared = _Client()


def compute_cost_usd(model: str, usage: Any) -> float:
    """Price a call from its four usage counters.

    `input_tokens` is the uncached remainder only — the cached span is reported
    separately, so summing all four is what actually reflects the prompt.
    """
    rates = PRICING.get(model)
    if rates is None:
        return 0.0
    in_rate, out_rate = rates

    uncached = getattr(usage, "input_tokens", 0) or 0
    written = getattr(usage, "cache_creation_input_tokens", 0) or 0
    read = getattr(usage, "cache_read_input_tokens", 0) or 0
    output = getattr(usage, "output_tokens", 0) or 0

    dollars = (
        uncached * in_rate
        + written * in_rate * CACHE_WRITE_MULTIPLIER
        + read * in_rate * CACHE_READ_MULTIPLIER
        + output * out_rate
    ) / 1_000_000
    return round(dollars, 8)


def call_structured(
    *,
    model: str,
    cached_system: str,
    volatile_system: str = "",
    user_content: str,
    tool_name: str,
    tool_description: str,
    input_schema: dict[str, Any],
    max_tokens: int = 4096,
    effort: str | None = None,
) -> LLMResult:
    """One structured call, with the constant prefix cached.

    `cached_system` must be byte-identical across calls — it carries the cache
    breakpoint, and any drift (a timestamp, a reordered dict) silently costs a full
    uncached prefix on every request. `volatile_system` sits after the breakpoint for
    the rare per-call system text (the verifier's rejection reason on a retry).
    """
    client = _shared.get()

    system_blocks: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": cached_system,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    if volatile_system:
        system_blocks.append({"type": "text", "text": volatile_system})

    request: dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_blocks,
        "messages": [{"role": "user", "content": user_content}],
        "tools": [
            {
                "name": tool_name,
                "description": tool_description,
                "strict": True,
                "input_schema": input_schema,
            }
        ],
        # Forcing the tool is what makes the schema a contract rather than a suggestion.
        "tool_choice": {"type": "tool", "name": tool_name},
    }

    # `effort` is rejected outright by Haiku 4.5, so it is opt-in per call site.
    if effort and model != "claude-haiku-4-5":
        request["output_config"] = {"effort": effort}

    started = time.perf_counter()
    response = client.messages.create(**request)
    latency_ms = int((time.perf_counter() - started) * 1000)

    tool_input: dict[str, Any] = {}
    text_parts: list[str] = []
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            tool_input = dict(block.input)
        elif block.type == "text":
            text_parts.append(block.text)

    if not tool_input:
        raise ModelTierError(
            f"{model} returned no {tool_name!r} tool call (stop_reason={response.stop_reason})"
        )

    usage = response.usage
    return LLMResult(
        tool_input=tool_input,
        model=response.model,
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
        cache_creation_input_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
        cache_read_input_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        cost_usd=compute_cost_usd(response.model, usage),
        latency_ms=latency_ms,
        stop_reason=response.stop_reason,
        raw_text="\n".join(text_parts),
    )


def escalate(model: str) -> str:
    """The one permitted escalation, per spec: cheap -> strong, once."""
    settings = get_settings()
    if model == settings.model_tier_cheap:
        return settings.model_tier_strong
    return model
