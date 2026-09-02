# Next steps

The build is complete and all four eval suites are measured, see
[EVAL_REPORT.md](EVAL_REPORT.md). What follows is what is left, ordered by value.

Item 1 is a real correctness gap in the product. Items 2–4 are things only you can do,
because they need your judgement or your accounts.

---

## 1. The verifier does not check that the evidence fits the *pattern*

**The one genuine product bug still open.** A live end-to-end run submitted an O(n²)
brute-force two-sum and got back:

- pattern: `complexity.list_membership_scan`, *"Tested membership against a list instead
  of a hash set"*
- confidence: **0.15**
- verifier: **passed**

The code never tests membership against a list; it does a nested-loop pair scan. The
explanation described the nested loop correctly, so the prose and the pattern label
disagree, and the verifier waved it through at 15% confidence.

That points at a specific gap: the verifier's first check confirms the evidence spans are
grounded in real lines of the submission, but nothing confirms those lines actually
demonstrate the *named pattern*. Two things worth doing:

1. Add a fifth verifier check: does the evidence demonstrate this specific pattern, given
   its `signals` from the taxonomy? The signals exist precisely to make that checkable.
2. Decide what a 0.15-confidence diagnosis should do. Serving it unqualified is probably
   wrong; either surface the uncertainty in the UI or treat a low-confidence result as a
   verifier rejection and escalate.

This may also be depressing Suite A's 75% top-1, some of those misses are likely the same
failure, so fixing it and re-running Suite A is the natural way to measure the impact.

---

## 2. Expand Suite C beyond 23 patterns

Suite C covers 23 of 50 patterns (46%). Every retrieval conclusion in the README rests on
that sample, and at n=23 a 0.03 precision@3 margin is worth under one case.

This already bit once: a weight sweep picked `k=10`, and it did not survive being re-run
against deterministic measurements, the conventional `k=60` won instead. The arm
weighting held up, but the episode is a fair warning about how much this set can carry.

Labelling the remaining 27 patterns is the single highest-value eval investment. Fixtures
live in `api/evals/fixtures/`.

---

## 3. Review the fixtures: they are my labels, not yours

The spec asks for *you* to write these specifically so they cannot drift toward what the
model would say. I wrote all of them.

- `suite_a_*.py`, 124 diagnosis labels. Suite A's 75.0% is only as meaningful as these.
- `suite_b_judge.py`, 60 human ratings. **Suite B's κ = 0.258 is uninterpretable until
  these are independently written.** Right now it measures how well the model reproduces
  one person's judgement, not calibration against a ground truth.

You do not need to rewrite them all. Correcting the ones you disagree with is enough to
make the numbers defensible.

---

## 4. Ship it

**Open the PR.** `gh` is not installed here, so I could not create it. The branch is
pushed:

https://github.com/maazin/Weak_Spot/pull/new/fix/transient-400-and-eval-observability

Or `brew install gh && gh auth login` and I can do it next session.

**Confirm CI is green.** I fixed the `api` job (it never seeded, so DB-backed tests
failed) and reproduced the full sequence locally, but `gh` is missing so I never watched a
real run. Check <https://github.com/maazin/Weak_Spot/actions>.

**GitHub OAuth.** The only way in today is the dev bypass, which refuses to run in
production, so a deployed instance currently has no working sign-in.
<https://github.com/settings/developers> → New OAuth App, callback
`https://<your-api-host>/api/v1/auth/github/callback`.

**Deploy.** Configs are written and the image is verified. You need a Postgres with
pgvector (Neon) and a Redis (Upstash).

```bash
fly launch --no-deploy -c deploy/fly.api.toml
fly secrets set ANTHROPIC_API_KEY=... VOYAGE_API_KEY=... SESSION_SECRET=... \
  DATABASE_URL=... REDIS_URL=... GITHUB_CLIENT_ID=... GITHUB_CLIENT_SECRET=... \
  GITHUB_CALLBACK_URL=...
fly deploy -c deploy/fly.api.toml
```

Or point a Render Blueprint at `deploy/render.yaml`. The entrypoint runs
`alembic upgrade head` before serving. Seed once after deploying, then check `/healthz`
reports `"schema_current": true`.

Once it is live, paste the URL into <https://www.opengraph.xyz> to confirm the social card
,  that needs a real domain, so it could not be checked locally.

**Measure latency.** The README's p95 < 6s is a target, not a result; `/metrics` only
fills in under real traffic. The one measured run was 26.8 s, but it included a verifier
rejection and an Opus escalation, so it is a worst case.

---

## 5. Optional

**Pair curation.** 13 of ~200 decided. `--review` exports candidates,
`taxonomy/pair_overrides.yaml` holds decisions, `--apply-review` folds them in. Directly
improves the recommendations users see.

**Langfuse tracing.** Free tier at <https://cloud.langfuse.com>; add the two keys to
`.env`. Without them tracing is a no-op. Worth it for per-node latency and token
attribution to point at in an interview.

---

## Known state

| Thing | Status |
|---|---|
| Tests | **127 passing**, verified from an empty database |
| Lint | ruff + eslint clean |
| Migrations | up / `alembic check` / downgrade all verified |
| MCP | real protocol, verified with the `mcp` client library |
| End-to-end | verified live: real submission → diagnosis → 3 recommendations → review queue |
| Suite D, injection | **PASS**, 40/40 valid, 0 followed |
| Suite A, accuracy | 0.750 top-1, 0.823 top-2, macro F1 0.738, 124/124 |
| Suite C, retrieval | hybrid 0.522 / 0.739, beats both baselines |
| Suite B, judge | κ 0.258, weak, and **not trustworthy until fixtures are yours** |
| Cost per diagnosis | **$0.00343** |
| Latency percentiles | **unmeasured**, needs real traffic |
| CI | fixed and reproduced locally; **not observed green on GitHub** |
| Fixtures | written by me, not reviewed by you |
| Deploy / OAuth | configured, not executed |

## One deliberate deviation from the spec

The spec lists LangChain as the LLM client. The code uses the Anthropic SDK directly and
keeps LangGraph for orchestration, driven by three other spec requirements: exact
`cache_control` placement, reading real `cache_read_input_tokens` for cost, and forced
`tool_choice` schema enforcement. It is isolated in `api/weakspot/llm.py`, so reverting is
a single-file change. Stated in the README too, so it reads as a decision rather than an
oversight.
