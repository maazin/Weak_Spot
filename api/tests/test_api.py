"""API integration tests against a real Postgres.

Skipped automatically when no database is reachable, so `pytest` still works on a
laptop with nothing running. CI always has one, so these always run there.

The diagnosis graph is stubbed: these tests are about the HTTP contract, quota
accounting, cache behaviour, and ownership checks. Model quality is Suites A-D's job.
"""

from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("fastapi")

os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://weakspot:weakspot@localhost:5433/weakspot"
)
os.environ.setdefault("DEV_AUTH_BYPASS", "true")
os.environ.setdefault("ENV", "test")

from fastapi.testclient import TestClient  # noqa: E402

from weakspot.db import ping  # noqa: E402

pytestmark = pytest.mark.skipif(not ping(), reason="no database available")

from weakspot.graph import build as graph_build  # noqa: E402
from weakspot.main import app  # noqa: E402
from weakspot.models import Diagnosis, Submission  # noqa: E402


@pytest.fixture
def client():
    with TestClient(app) as c:
        c.post("/api/v1/auth/dev-login")
        yield c


@pytest.fixture(autouse=True)
def clean_user_data():
    """Each test starts from an empty history and a fresh daily quota.

    Without the quota reset the suite exhausts the 10/day limit partway through and
    later tests see 429s — which is the rate limiter behaving correctly, not a bug.
    """
    from weakspot.db import session_scope
    from weakspot.models import ReviewItem, User
    from weakspot.ratelimit import _quota_key, get_redis

    with session_scope() as db:
        user = db.query(User).filter(User.github_id == "dev-local").one_or_none()
        if user:
            redis_client = get_redis()
            if redis_client is not None:
                redis_client.delete(_quota_key(user.id))
            db.query(Diagnosis).filter(
                Diagnosis.submission_id.in_(
                    db.query(Submission.id).filter(Submission.user_id == user.id)
                )
            ).delete(synchronize_session=False)
            db.query(Submission).filter(Submission.user_id == user.id).delete()
            db.query(ReviewItem).filter(ReviewItem.user_id == user.id).delete()
    yield


@pytest.fixture
def stub_graph(monkeypatch):
    """Deterministic diagnosis so the HTTP layer can be tested without a model."""

    def fake_run(db, initial):
        from weakspot.graph.intake import intake_node
        from weakspot.graph.retriever import retriever_node
        from weakspot.graph.scheduler import scheduler_node

        state = intake_node(initial)
        state = {
            **state,
            "pattern_id": "complexity.missing_memoization",
            "alternate_pattern_id": None,
            "confidence": 0.82,
            "evidence_spans": [
                {"start_line": 1, "end_line": 2, "why": "recursion without a cache"}
            ],
            "explanation": "Your recursion recomputes the same arguments across branches.",
            "model_tier": "claude-haiku-4-5",
            "verifier_passed": True,
            "verifier_failures": [],
            "retry_count": 0,
            "cost_usd": 0.0004,
            "latency_ms": 900,
        }
        state = retriever_node(state, db)
        return scheduler_node(state, db)

    monkeypatch.setattr(graph_build, "run_diagnosis", fake_run)
    import weakspot.routers.submissions as submissions_module

    monkeypatch.setattr(submissions_module, "run_diagnosis", fake_run)


# ------------------------------------------------------------------ ops + auth


def test_healthz_reports_dependencies():
    with TestClient(app) as c:
        body = c.get("/healthz").json()
    assert body["database"] is True
    assert body["taxonomy_entries"] >= 40


def test_metrics_is_prometheus_text():
    with TestClient(app) as c:
        response = c.get("/metrics")
    assert response.status_code == 200
    assert "weakspot_diagnoses_total" in response.text


def test_routes_require_authentication():
    with TestClient(app) as c:
        for path in ("/api/v1/submissions", "/api/v1/reviews/due", "/api/v1/me/weak-patterns"):
            assert c.get(path).status_code == 401, path


def test_dev_login_issues_a_session(client):
    assert client.get("/api/v1/auth/me").json()["handle"] == "dev"


# ------------------------------------------------------------------ submissions


def test_submission_rejects_unknown_problem(client, stub_graph):
    response = client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "not-a-real-problem",
            "code": "def f():\n    return 1\n",
            "language": "python",
            "failure_type": "wrong_answer",
        },
    )
    assert response.status_code == 404


def test_submission_accepts_a_url_in_place_of_a_slug(client, stub_graph):
    response = client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "https://leetcode.com/problems/fibonacci-number/",
            "code": "def fib(n):\n    return fib(n-1) + fib(n-2)\n",
            "language": "python",
            "failure_type": "tle",
        },
    )
    assert response.status_code == 201, response.text


def test_full_diagnosis_round_trip(client, stub_graph):
    created = client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "fibonacci-number",
            "code": "def fib(n):\n    return fib(n-1) + fib(n-2)\n",
            "language": "python",
            "failure_type": "tle",
        },
    )
    assert created.status_code == 201, created.text
    submission_id = created.json()["submission_id"]

    detail = client.get(f"/api/v1/submissions/{submission_id}").json()
    assert detail["diagnosis"]["pattern"]["id"] == "complexity.missing_memoization"
    assert detail["diagnosis"]["pattern"]["family"] == "complexity"
    assert detail["diagnosis"]["evidence_spans"][0]["text"]
    # Recommendations enter the review queue on the spaced schedule.
    assert len(detail["recommendations"]) >= 1


def test_identical_resubmission_is_served_from_cache(client, stub_graph):
    payload = {
        "problem_slug": "fibonacci-number",
        "code": "def fib(n):\n    return fib(n-1) + fib(n-2)\n",
        "language": "python",
        "failure_type": "tle",
    }
    first = client.post("/api/v1/submissions", json=payload)
    second = client.post("/api/v1/submissions", json=payload)
    assert first.json()["status"] == "complete"
    assert second.json()["status"] == "cached"
    assert second.json()["diagnosis_id"] == first.json()["diagnosis_id"]


def test_oversized_code_is_rejected_by_validation(client):
    response = client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "two-sum",
            "code": "x = 1\n" * 900,
            "language": "python",
            "failure_type": "wrong_answer",
        },
    )
    assert response.status_code == 422


def test_unknown_language_rejected(client):
    response = client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "two-sum",
            "code": "print(1)",
            "language": "rust",
            "failure_type": "wrong_answer",
        },
    )
    assert response.status_code == 422


def test_unparseable_python_rejected_before_any_model_call(client, stub_graph):
    response = client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "two-sum",
            "code": "def broken(:\n    pass\n",
            "language": "python",
            "failure_type": "wrong_answer",
        },
    )
    assert response.status_code == 422


def test_daily_quota_is_enforced(client, stub_graph):
    """10 free diagnoses per user per day, enforced in Redis (spec section 7)."""
    from weakspot.config import get_settings
    from weakspot.ratelimit import get_redis

    if get_redis() is None:
        pytest.skip("redis unavailable; quota fails open by design")

    limit = get_settings().free_diagnoses_per_day
    statuses = []
    for i in range(limit + 2):
        response = client.post(
            "/api/v1/submissions",
            json={
                "problem_slug": "fibonacci-number",
                # Distinct code each time, or the cache would serve it for free.
                "code": f"def fib(n):\n    x = {i}\n    return fib(n-1) + fib(n-2)\n",
                "language": "python",
                "failure_type": "tle",
            },
        )
        statuses.append(response.status_code)

    assert statuses[:limit] == [201] * limit
    assert statuses[limit:] == [429, 429]


def test_cached_diagnoses_do_not_consume_quota(client, stub_graph):
    from weakspot.ratelimit import get_redis, remaining_quota

    if get_redis() is None:
        pytest.skip("redis unavailable")

    from weakspot.db import session_scope
    from weakspot.models import User

    payload = {
        "problem_slug": "fibonacci-number",
        "code": "def fib(n):\n    return fib(n-1) + fib(n-2)\n",
        "language": "python",
        "failure_type": "tle",
    }
    client.post("/api/v1/submissions", json=payload)

    with session_scope() as db:
        user_id = db.query(User).filter(User.github_id == "dev-local").one().id

    before = remaining_quota(user_id)
    client.post("/api/v1/submissions", json=payload)  # identical -> cached
    assert remaining_quota(user_id) == before


def test_submission_list_paginates(client, stub_graph):
    for slug in ("fibonacci-number", "climbing-stairs", "coin-change"):
        client.post(
            "/api/v1/submissions",
            json={
                "problem_slug": slug,
                "code": f"def f_{slug.replace('-', '_')}(n):\n    return f(n-1)\n",
                "language": "python",
                "failure_type": "tle",
            },
        )
    page = client.get("/api/v1/submissions?limit=2").json()
    assert len(page["items"]) == 2
    assert page["next_cursor"]
    nxt = client.get(f"/api/v1/submissions?limit=2&cursor={page['next_cursor']}").json()
    assert nxt["items"]


# ------------------------------------------------------------------ reviews


def test_review_queue_and_completion(client, stub_graph):
    client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "fibonacci-number",
            "code": "def fib(n):\n    return fib(n-1) + fib(n-2)\n",
            "language": "python",
            "failure_type": "tle",
        },
    )
    from weakspot.db import session_scope
    from weakspot.models import ReviewItem, User

    with session_scope() as db:
        user = db.query(User).filter(User.github_id == "dev-local").one()
        item = db.query(ReviewItem).filter(ReviewItem.user_id == user.id).first()
        assert item is not None
        item_id = item.id

    done = client.post(f"/api/v1/reviews/{item_id}/complete", json={"result": "solved"})
    assert done.status_code == 200
    assert done.json()["interval_days"] == pytest.approx(7.5)

    due = client.get("/api/v1/reviews/due").json()
    assert due["total_items"] >= 1


def test_review_completion_rejects_unknown_result(client):
    response = client.post("/api/v1/reviews/does-not-exist/complete", json={"result": "nope"})
    assert response.status_code == 422


# ------------------------------------------------------------------ catalog + mcp


def test_patterns_endpoint_returns_the_whole_taxonomy(client):
    patterns = client.get("/api/v1/patterns").json()["patterns"]
    assert len(patterns) >= 40
    assert all("correct_approach" in p for p in patterns)


def test_pattern_problems_are_linked(client):
    results = client.get("/api/v1/patterns/complexity.missing_memoization/problems").json()[
        "results"
    ]
    assert results
    assert all(r["url"].startswith("https://") for r in results)


def test_problem_search_filters_by_difficulty(client):
    results = client.get("/api/v1/problems/search?q=sum&difficulty=easy").json()["results"]
    assert all(r["difficulty"] == "easy" for r in results)


def test_weak_patterns_reports_occurrences(client, stub_graph):
    client.post(
        "/api/v1/submissions",
        json={
            "problem_slug": "fibonacci-number",
            "code": "def fib(n):\n    return fib(n-1) + fib(n-2)\n",
            "language": "python",
            "failure_type": "tle",
        },
    )
    items = client.get("/api/v1/me/weak-patterns").json()["items"]
    assert items[0]["pattern"]["id"] == "complexity.missing_memoization"
    assert items[0]["occurrences"] >= 1
    assert items[0]["trend"] in {"up", "down", "flat"}


MCP_TOOLS = "/api/v1/mcp-tools/tools"


def test_mcp_tools_are_described_and_bounded():
    with TestClient(app) as c:
        tools = c.get(MCP_TOOLS).json()["tools"]
    assert {t["name"] for t in tools} == {
        "search_problems_by_pattern",
        "get_pattern_taxonomy",
        "get_my_weak_patterns",
    }
    for tool in tools:
        assert len(tool["description"]) > 80, tool["name"]
        assert tool["inputSchema"]["type"] == "object"


def test_mcp_search_caps_results():
    with TestClient(app) as c:
        body = c.post(
            f"{MCP_TOOLS}/search_problems_by_pattern",
            json={"pattern_id": "complexity.missing_memoization", "limit": 20},
        ).json()
    assert len(body["results"]) <= 20


def test_mcp_search_rejects_unknown_pattern():
    with TestClient(app) as c:
        response = c.post(f"{MCP_TOOLS}/search_problems_by_pattern", json={"pattern_id": "made.up"})
    assert response.status_code == 400


def test_mcp_weak_patterns_requires_a_token():
    with TestClient(app) as c:
        assert c.post(f"{MCP_TOOLS}/get_my_weak_patterns", json={}).status_code == 401


def _mcp_rpc(client: TestClient, method: str, params: dict | None = None, rid: int = 1):
    """One Streamable HTTP JSON-RPC call. The transport may answer as SSE or JSON."""
    response = client.post(
        "/mcp/",
        json={"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}},
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    assert response.status_code == 200, response.text
    body = response.text
    if "text/event-stream" in response.headers.get("content-type", ""):
        for line in body.splitlines():
            if line.startswith("data: "):
                return json.loads(line[6:])
        raise AssertionError(f"no data frame in SSE response: {body!r}")
    return response.json()


def test_mcp_endpoint_speaks_the_real_protocol():
    """The thing an MCP client actually does: initialize, then tools/list.

    The REST mirror above cannot catch a broken mount or an unstarted session manager,
    which is exactly what stops Claude Desktop and Cursor from connecting.
    """
    with TestClient(app) as c:
        init = _mcp_rpc(
            c,
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        )
        assert init["result"]["serverInfo"]["name"] == "weakspot"

        listed = _mcp_rpc(c, "tools/list", rid=2)
        names = {t["name"] for t in listed["result"]["tools"]}
    assert names == {
        "search_problems_by_pattern",
        "get_pattern_taxonomy",
        "get_my_weak_patterns",
    }


def test_mcp_tool_call_returns_taxonomy_over_the_protocol():
    with TestClient(app) as c:
        _mcp_rpc(
            c,
            "initialize",
            {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "pytest", "version": "0"},
            },
        )
        called = _mcp_rpc(
            c,
            "tools/call",
            {"name": "get_pattern_taxonomy", "arguments": {"family": "complexity"}},
            rid=3,
        )
    result = called["result"]
    assert not result.get("isError"), result
    patterns = result["structuredContent"]["patterns"]
    assert patterns and all(p["family"] == "complexity" for p in patterns)
