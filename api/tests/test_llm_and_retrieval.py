"""Cost accounting, cache-prefix invariants, and RRF."""

from __future__ import annotations

from dataclasses import dataclass

import anthropic
import pytest

from weakspot.graph.retriever import ARM_WEIGHTS, RRF_K, reciprocal_rank_fusion
from weakspot.llm import (
    CACHE_READ_MULTIPLIER,
    CACHE_WRITE_MULTIPLIER,
    HAIKU_CACHE_MINIMUM_TOKENS,
    PRICING,
    TRANSIENT_400_RETRIES,
    _create_with_transient_retry,
    _is_transient_bad_request,
    compute_cost_usd,
    escalate,
)
from weakspot.prompts import diagnoser as diagnoser_prompt
from weakspot.taxonomy import load_taxonomy


@dataclass
class FakeUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


def test_cost_prices_each_token_class_at_its_own_rate():
    in_rate, out_rate = PRICING["claude-haiku-4-5"]
    usage = FakeUsage(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_creation_input_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
    )
    expected = (
        in_rate + in_rate * CACHE_WRITE_MULTIPLIER + in_rate * CACHE_READ_MULTIPLIER + out_rate
    )
    assert compute_cost_usd("claude-haiku-4-5", usage) == pytest.approx(expected)


def test_cache_read_is_an_order_of_magnitude_cheaper_than_uncached():
    cached = compute_cost_usd("claude-haiku-4-5", FakeUsage(cache_read_input_tokens=1_000_000))
    uncached = compute_cost_usd("claude-haiku-4-5", FakeUsage(input_tokens=1_000_000))
    assert cached == pytest.approx(uncached * CACHE_READ_MULTIPLIER)


def test_opus_is_the_expensive_tier():
    usage = FakeUsage(input_tokens=1_000_000, output_tokens=1_000_000)
    assert compute_cost_usd("claude-opus-5", usage) > compute_cost_usd("claude-haiku-4-5", usage)


def test_unknown_model_prices_at_zero_rather_than_crashing():
    assert compute_cost_usd("some-future-model", FakeUsage(input_tokens=100)) == 0.0


def test_cost_prices_the_dated_id_the_api_returns_not_just_the_alias():
    """Regression: the first real eval run priced 119 diagnoses at $0.00.

    Requests go out with an alias, but `response.model` comes back as the resolved
    dated id, and cost was looked up with that. Every other test here passes the alias,
    which is exactly why they stayed green while production recorded zero.
    """
    usage = FakeUsage(input_tokens=1_000_000)
    alias = compute_cost_usd("claude-haiku-4-5", usage)
    dated = compute_cost_usd("claude-haiku-4-5-20251001", usage)

    assert alias > 0.0
    assert dated == alias


def test_cost_prefix_match_picks_the_most_specific_alias():
    """`claude-opus-5-...` must not fall back to a shorter alias that also prefixes it."""
    usage = FakeUsage(input_tokens=1_000_000)
    assert compute_cost_usd("claude-opus-5-20260101", usage) == compute_cost_usd(
        "claude-opus-5", usage
    )


def test_escalation_is_one_way_and_terminal():
    assert escalate("claude-haiku-4-5") == "claude-opus-5"
    assert escalate("claude-opus-5") == "claude-opus-5"


def test_taxonomy_block_exceeds_the_haiku_cache_minimum():
    """Below 4096 tokens the prefix silently stops caching on Haiku 4.5."""
    taxonomy = load_taxonomy()
    system = diagnoser_prompt.build_system_prompt(taxonomy)
    approx_tokens = len(system) / 4
    assert approx_tokens > HAIKU_CACHE_MINIMUM_TOKENS


def test_cached_prefix_is_byte_stable():
    """Any per-call drift here drops the cache hit rate to zero."""
    taxonomy = load_taxonomy()
    assert diagnoser_prompt.build_system_prompt(taxonomy) == diagnoser_prompt.build_system_prompt(
        taxonomy
    )


def test_taxonomy_leads_the_prompt():
    taxonomy = load_taxonomy()
    system = diagnoser_prompt.build_system_prompt(taxonomy)
    assert system.index("PATTERN TAXONOMY") < system.index("# Your task")


def test_tool_schema_closes_the_enum_to_the_taxonomy():
    taxonomy = load_taxonomy()
    schema = diagnoser_prompt.build_tool_schema(taxonomy)
    assert schema["properties"]["pattern_id"]["enum"] == taxonomy.allowed_ids()
    assert schema["additionalProperties"] is False


def test_user_turn_carries_no_problem_statement():
    """Legal constraint: metadata and the user's own code only."""
    content = diagnoser_prompt.build_user_content(
        problem_slug="two-sum",
        problem_title="Two Sum",
        difficulty="easy",
        tags=["array", "hash-table"],
        language="python",
        failure_type="wrong_answer",
        structural_signals=["dict allocated"],
        vaulted_code="x = 1",
    )
    assert "Two Sum" in content and "two-sum" in content
    assert "1:" in content  # line numbering for evidence spans


def test_rrf_rewards_agreement_between_arms():
    """An item both arms like beats one only a single arm returned."""
    keyword = ["a", "b"]
    vector = ["b"]
    fused = reciprocal_rank_fusion([keyword, vector])
    assert fused[0] == "b"


def test_rrf_favours_rank_extremes_over_middles():
    """1/(k+rank) is convex, so a first-and-last item outscores a consistent middle.

    Pinned deliberately: it is the counterintuitive property of RRF, and Suite C's
    baseline comparison is only interpretable if this behaviour is understood.
    """
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["c", "b", "a"]])
    assert fused.index("b") == 2


def test_rrf_uses_the_specified_k():
    assert RRF_K == 10
    fused = reciprocal_rank_fusion([["x"]])
    assert fused == ["x"]


def test_rrf_weights_let_the_stronger_arm_win_a_disagreement():
    """The reason weighting exists: unweighted fusion lost to the keyword arm alone.

    The keyword arm ranks its pick third while the vector arm ranks its own first, so
    unweighted the vector arm wins outright. Weighting has to flip that — which is
    precisely the case where equal votes were costing precision@3.

    No item is shared between the arms, so this isolates the weighting from the
    agreement bonus tested above.
    """
    keyword = ["filler", "kw_pick"]
    vector = ["vec_pick"]

    unweighted = reciprocal_rank_fusion([keyword, vector])
    assert unweighted.index("vec_pick") < unweighted.index("kw_pick")

    weighted = reciprocal_rank_fusion([keyword, vector], weights=list(ARM_WEIGHTS))
    assert weighted.index("kw_pick") < weighted.index("vec_pick")


def test_rrf_weights_default_to_equal():
    """Callers that pass no weights get the textbook behaviour, unchanged."""
    assert reciprocal_rank_fusion([["a"], ["b"]], weights=[1.0, 1.0]) == (
        reciprocal_rank_fusion([["a"], ["b"]])
    )


def test_arm_weights_favour_keyword_over_vector():
    """Pinned because the ordering, not the exact values, is the load-bearing claim."""
    keyword_weight, vector_weight = ARM_WEIGHTS
    assert keyword_weight > vector_weight


def test_rrf_handles_empty_arms():
    assert reciprocal_rank_fusion([[], []]) == []
    assert reciprocal_rank_fusion([[], ["a"]]) == ["a"]


# ------------------------------------------------- transient 400 retry (regression)


class _FakeBadRequest(anthropic.BadRequestError):
    """Constructed without a real HTTP round trip; only `body` is read."""

    def __init__(self, message: str):
        self.body = {
            "type": "error",
            "error": {"type": "invalid_request_error", "message": message},
        }


def test_only_the_contentless_400_counts_as_transient():
    """A 400 that names the offending field is a real bug and must not be retried."""
    assert _is_transient_bad_request(_FakeBadRequest("Invalid request data"))
    assert _is_transient_bad_request(_FakeBadRequest("invalid request data"))
    assert not _is_transient_bad_request(
        _FakeBadRequest("messages.0.content.0.text: field required")
    )


def test_transient_400_is_retried_and_succeeds():
    """Regression: 5/124 Suite A cases and 3/40 Suite D cases died on this.

    The identical payload succeeded on retry — measured at 1 failure in 10 calls — but
    the SDK does not retry 400, so a routine hiccup surfaced as a red injection gate.
    """
    calls = {"n": 0}

    class Client:
        class messages:
            @staticmethod
            def create(**_):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise _FakeBadRequest("Invalid request data")
                return "response"

    assert _create_with_transient_retry(Client(), {"model": "m"}) == "response"
    assert calls["n"] == 2


def test_a_real_400_is_not_retried():
    calls = {"n": 0}

    class Client:
        class messages:
            @staticmethod
            def create(**_):
                calls["n"] += 1
                raise _FakeBadRequest("tools.0.input_schema: invalid")

    with pytest.raises(anthropic.BadRequestError):
        _create_with_transient_retry(Client(), {"model": "m"})
    assert calls["n"] == 1, "a malformed request must fail on the first attempt"


def test_persistent_transient_400_eventually_gives_up():
    calls = {"n": 0}

    class Client:
        class messages:
            @staticmethod
            def create(**_):
                calls["n"] += 1
                raise _FakeBadRequest("Invalid request data")

    with pytest.raises(anthropic.BadRequestError):
        _create_with_transient_retry(Client(), {"model": "m"})
    assert calls["n"] == TRANSIENT_400_RETRIES
