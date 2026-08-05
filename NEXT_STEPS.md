# Next steps — things only you can do

Everything in this file is blocked on your accounts, your keys, or your judgement.
The code is done and verified; these are the gaps between "built" and "finished".

Ordered by value. Items 1 and 2 are what a reader of the repo will notice first.

---

## 1. Run the eval suites — the README's biggest hole

**Why it matters:** the Results section currently says "not yet run" for three of the
four suites. That is honest, but a reader looking for evidence the system works finds
IOUs. One command turns them into real numbers.

**What you need:** an Anthropic API key. A Voyage key too, if you want the retrieval
comparison completed.

```bash
cd /Users/maazinshaikh/Claude_Working_Folder/Make_Here/Weak_Spot
cp .env.example .env      # if you have not already
# put ANTHROPIC_API_KEY=... and VOYAGE_API_KEY=... in .env
make up
make seed EMBED=1         # only needed if you added a Voyage key
make eval
```

That writes `EVAL_REPORT.md` and inserts a row per suite into the `eval_runs` table.

**Then edit README.md:** replace the three "awaiting `ANTHROPIC_API_KEY`" rows in the
Suites A/B/D table with the measured numbers, and fill the two blank rows in the
retrieval table. The keyword-only row (p@3 **0.507**, MRR **0.752**) is already real and
should not change.

**Cost:** roughly 224 diagnoses plus 60 judge calls on Haiku 4.5, most of them hitting
the cached taxonomy prefix. Small, but not zero — check `cost_usd` in the report.

**If Suite D fails, stop and read it.** It is the prompt-injection gate; a failure means
a payload got through, and that is a real finding, not a flaky test.

---

## 2. Confirm CI is actually green

**Why it matters:** I found that the `api` job had been failing since the tests were
written — several tests assert against the seeded problem index, and the workflow never
seeded. I added the seed step and reproduced the full CI sequence locally against an
empty database (migrate → seed → 116 passing), but **I could not watch a real run** —
the `gh` CLI is not installed on this machine, so I never saw GitHub's own result.

Open <https://github.com/maazin/Weak_Spot/actions> and confirm the latest run is green.
If the `api` job still fails, the log will say which test and why.

---

## 3. Review the Suite A fixtures

**Why it matters:** the spec asks for *you* to write these labels specifically so they
cannot drift toward what the model would say. I wrote all 124 of them. They are
internally consistent and the fixture tests pass, but they are my judgement, not yours —
and Suite A's accuracy number is only meaningful if the labels are.

Files: `api/evals/fixtures/suite_a_*.py` (one per family).

Skim for cases where you would have picked a different pattern. You do not need to
rewrite them all; even correcting the ones you disagree with makes the number defensible.
Do this **before** quoting Suite A accuracy anywhere.

Same applies, less urgently, to `suite_b_judge.py` — those human ratings are also mine.

---

## 4. Finish the pattern-problem curation

Ten pairs confirmed and five rejected so far, out of the top 200. The mechanism works;
the remaining ~185 are un-reviewed.

```bash
cd api
python -m weakspot.ingest.seed --review       # writes pair_candidates.yaml
# read it; move entries into taxonomy/pair_overrides.yaml under confirmed: / rejected:
python -m weakspot.ingest.seed --apply-review
```

`pair_candidates.yaml` is gitignored — it is scratch. Only `pair_overrides.yaml` is
tracked, and it is re-applied on every seed, so decisions are permanent.

This directly improves the recommendations users see, and it is the kind of unglamorous
data work that separates a demo from a product.

---

## 5. Set up GitHub OAuth

Right now the only way in is the dev bypass, which refuses to run in production — so a
deployed instance currently has no working sign-in.

1. <https://github.com/settings/developers> → New OAuth App
2. Homepage: your deployed web URL. Callback: `https://<your-api-host>/api/v1/auth/github/callback`
3. Put the client ID and secret in `.env` locally, and in the host's secret store for deploy.

---

## 6. Deploy

Both configs are written and the image is verified — I built it and ran it in production
mode against a fresh database (migrations ran, taxonomy loaded, `/healthz` returned ok).
What is left needs your accounts.

You need a Postgres with **pgvector** (Neon works) and a Redis (Upstash works).

**Fly** — run from the repo root, since the image needs both `api/` and `taxonomy/`:

```bash
fly launch --no-deploy -c deploy/fly.api.toml
fly secrets set ANTHROPIC_API_KEY=... VOYAGE_API_KEY=... SESSION_SECRET=... \
  DATABASE_URL=... REDIS_URL=... GITHUB_CLIENT_ID=... GITHUB_CLIENT_SECRET=... \
  GITHUB_CALLBACK_URL=...
fly deploy -c deploy/fly.api.toml
```

**Render** — point a Blueprint at `deploy/render.yaml`; it defines both services. Set
the `sync: false` secrets in the dashboard.

The entrypoint runs `alembic upgrade head` before serving, so the schema comes up on
first boot. After deploying, seed the index once:

```bash
fly ssh console -C "python -m weakspot.ingest.seed --no-embed"   # or with embeddings
```

Then check `/healthz` reports `"schema_current": true`.

**After it is live:** paste the URL into <https://www.opengraph.xyz> to confirm the
social card renders. That check needs a real domain, so it could not be done locally.

---

## 7. Optional: Langfuse tracing

Free tier at <https://cloud.langfuse.com>. Add `LANGFUSE_PUBLIC_KEY` and
`LANGFUSE_SECRET_KEY` to `.env`. Without them tracing degrades to a no-op — nothing
breaks, you just get no traces. Worth it if you want per-node latency and token
attribution to point at during an interview.

---

## Known state, for reference

| Thing | Status |
|---|---|
| Tests | 116 passing, verified from an empty database |
| Lint | ruff + eslint clean |
| Migrations | verified up, `alembic check` clean, downgrade round-trips |
| MCP | real protocol, verified with the `mcp` client library and in the built image |
| Docker image | builds from repo root, runs in production mode, migrates on boot |
| Suite C (keyword arm) | measured: p@3 0.507, MRR 0.752 |
| Suites A, B, D | **not run** — need `ANTHROPIC_API_KEY` |
| Vector / hybrid retrieval | **not measured** — need `VOYAGE_API_KEY` |
| Latency / cost percentiles | **empty** — populated by real traffic |
| CI | fixed and reproduced locally; **not observed green on GitHub** |
| Suite A/B fixtures | written by me, not reviewed by you |
| Pair curation | 15 of ~200 decided |

## One deliberate deviation from the spec

The spec lists LangChain as the LLM client. The code uses the Anthropic SDK directly and
keeps LangGraph for orchestration — driven by three other spec requirements (exact
`cache_control` placement, reading real `cache_read_input_tokens` for cost, and forced
`tool_choice` schema enforcement). It is isolated in `api/weakspot/llm.py`, so reverting
is a single-file change. This is stated in the README too, so it reads as a decision
rather than an oversight.
