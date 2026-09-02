"""The five-node LangGraph, plus the retry-and-escalate path.

    intake ──▶ diagnoser ──▶ verifier ──┬─(passed)──▶ retriever ──▶ scheduler ──▶ END
                   ▲                    │
                   └────(rejected, once,─┘
                         escalate tier)

`intake` short-circuits to END on a `code_hash` cache hit, so a resubmitted identical
attempt costs nothing. The retriever pre-warm is launched from `intake` on a worker
thread using only the failed problem's own tags; `retriever` joins it. That is what keeps
the p95 latency target reachable without reaching for a faster model.

Escalation is deliberately capped at one hop: a diagnosis the strong tier also fails to
verify is returned with `verifier_passed=False` and surfaced as low-confidence, rather
than looping. An unbounded retry on a genuinely ambiguous submission is how a per-user
rate limit turns into an unbounded bill.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

from langgraph.graph import END, StateGraph
from sqlalchemy.orm import Session

from ..config import get_settings
from ..db import SessionLocal
from ..llm import escalate
from .diagnoser import diagnoser_node
from .intake import intake_node
from .retriever import prewarm, retriever_node
from .scheduler import scheduler_node
from .state import GraphState
from .verifier import verifier_node

logger = logging.getLogger(__name__)

_PREWARM_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="prewarm")
_PREWARM_KEY = "_prewarm_future"


def _prewarm_worker(tags: list[str], user_id: str) -> list[str]:
    """Runs off the request thread, so it needs its own session."""
    db: Session = SessionLocal()
    try:
        return prewarm(db, tags=tags, user_id=user_id)
    except Exception:
        logger.exception("retriever pre-warm failed; falling back to cold search")
        return []
    finally:
        db.close()


def _intake_with_prewarm(state: GraphState) -> dict[str, Any]:
    result = intake_node(state)
    future: Future[list[str]] = _PREWARM_POOL.submit(
        _prewarm_worker, list(state.get("problem_tags", [])), state["user_id"]
    )
    return {**result, _PREWARM_KEY: future}


def _retriever_with_prewarm(state: GraphState, db: Session) -> dict[str, Any]:
    future = state.get(_PREWARM_KEY)
    warmed: list[str] = []
    if isinstance(future, Future):
        try:
            warmed = future.result(timeout=2.0)
        except Exception:
            logger.warning("pre-warm did not finish in time; searching cold")

    enriched: GraphState = {**state, "prewarmed": [{"id": pid} for pid in warmed]}
    out = retriever_node(enriched, db)
    out.pop(_PREWARM_KEY, None)
    return out


# Escalating to the strong tier adds roughly fifteen seconds and forty times the cost.
# That is worth paying on a normal request and not worth paying on one that has already
# been slow, because the person is still waiting and the retry may stall too. Past this
# point the diagnosis is returned unverified rather than escalated.
ESCALATION_BUDGET_MS = 45_000


def _verifier_route(state: GraphState) -> str:
    settings = get_settings()
    if state.get("verifier_passed"):
        return "retriever"
    spent = state.get("latency_ms", 0)
    if spent > ESCALATION_BUDGET_MS:
        logger.warning(
            "skipping escalation: already spent %dms, over the %dms budget; "
            "returning unverified diagnosis submission=%s",
            spent,
            ESCALATION_BUDGET_MS,
            state.get("submission_id"),
        )
        return "retriever"
    if state.get("retry_count", 0) >= settings.max_retries:
        logger.warning(
            "verifier still rejecting after escalation; returning unverified "
            "diagnosis submission=%s",
            state.get("submission_id"),
        )
        return "retriever"
    return "retry"


def _retry_node(state: GraphState) -> dict[str, Any]:
    """Bump the counter and escalate the tier — the single permitted escalation."""
    settings = get_settings()
    current = state.get("model_tier") or settings.model_tier_cheap
    stronger = escalate(current)
    logger.info(
        "escalating diagnosis submission=%s %s -> %s",
        state.get("submission_id"),
        current,
        stronger,
    )
    return {
        **state,
        "retry_count": state.get("retry_count", 0) + 1,
        "model_tier": stronger,
    }


def build_graph(db: Session):
    """Compile the graph. `db` is bound into the two nodes that need it."""
    graph = StateGraph(GraphState)

    graph.add_node("intake", _intake_with_prewarm)
    graph.add_node("diagnoser", diagnoser_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("retry", _retry_node)
    graph.add_node("retriever", lambda s: _retriever_with_prewarm(s, db))
    graph.add_node("scheduler", lambda s: scheduler_node(s, db))

    graph.set_entry_point("intake")
    graph.add_edge("intake", "diagnoser")
    graph.add_edge("diagnoser", "verifier")
    graph.add_conditional_edges(
        "verifier",
        _verifier_route,
        {"retriever": "retriever", "retry": "retry"},
    )
    graph.add_edge("retry", "diagnoser")
    graph.add_edge("retriever", "scheduler")
    graph.add_edge("scheduler", END)

    return graph.compile()


def run_diagnosis(db: Session, initial: GraphState) -> GraphState:
    """Invoke the graph end to end and stamp total wall-clock latency."""
    started = time.perf_counter()
    compiled = build_graph(db)
    final: GraphState = compiled.invoke(
        {**initial, "retry_count": 0, "cost_usd": 0.0, "latency_ms": 0}
    )
    final["latency_ms"] = int((time.perf_counter() - started) * 1000)
    final.pop(_PREWARM_KEY, None)
    return final
