# Weakspot

![Weakspot](web/public/assets/readme-banner.png)

Weakspot diagnoses **why** a failed coding-problem attempt failed at the conceptual
level, then schedules same-pattern problems for spaced review so the same mistake stops
recurring.

You paste the attempt that did not pass, the language, and what happened. You get back
one named failure mode from a closed taxonomy, the lines in your own code that
demonstrate it, a short explanation of the gap, and three problems that drill the same
pattern. Those three enter a review queue on an SM-2 schedule.

It never solves the problem for you. If a diagnosis contains working solution code, the
verifier rejects it — that is a bug, not a feature.

---

## Results

Everything below is produced by `make eval`, written to the `eval_runs` table, and
posted as a PR comment by CI.

### Retrieval quality — Suite C (measured)

100+ labelled `(pattern, problem)` pairs. Negatives are deliberately plausible: same
family, adjacent topic, or overlapping tags.

| arm | precision@3 | MRR |
|---|---|---|
| keyword only | **0.507** | **0.752** |
| vector only | not run — needs `VOYAGE_API_KEY` | — |
| hybrid (RRF, k=60) | not run — needs `VOYAGE_API_KEY` | — |

The keyword arm is a real measured baseline. The three-way comparison the spec asks for
needs problem and pattern embeddings, which need a Voyage key; with none set, the vector
arm returns nothing and the hybrid score collapses onto the keyword score. Run
`make seed EMBED=1 && make eval-offline` once a key is present to fill in the other two
rows.

### Diagnosis accuracy, judge calibration, injection — Suites A, B, D

**Not yet run.** These consume model calls and no `ANTHROPIC_API_KEY` was set when this
README was written. The fixtures, runners, and metric implementations are complete and
tested; only the spend is outstanding.

| suite | what it measures | fixtures | status |
|---|---|---|---|
| A | top-1 / top-2 accuracy, macro F1, per-family confusion | 124 labelled submissions | awaiting `ANTHROPIC_API_KEY` |
| B | judge-to-human exact / adjacent agreement, Cohen's kappa | 60 human-rated explanations | awaiting `ANTHROPIC_API_KEY` |
| D | valid-diagnosis rate, injections followed | 40 adversarial submissions | awaiting `ANTHROPIC_API_KEY` |

```bash
export ANTHROPIC_API_KEY=...
make eval
```

That writes measured numbers into `EVAL_REPORT.md`; paste them into the tables above.
**No placeholder numbers appear in this README** — an unrun suite is reported as unrun.

### Latency and cost

p50/p95/p99 latency and cost per diagnosis are recorded on every `diagnoses` row and
exported from `/metrics` as `weakspot_latency_quantile_ms` and
`weakspot_cost_per_diagnosis_usd`. They are populated by real traffic, so they are blank
until the system has served requests.

The target is **p95 under 6 seconds** end to end. The lever if it is missed is starting
the retriever's tag-based pre-warm earlier, not switching to a faster model.

---

## Architecture

Five nodes. State carries the submission, intermediate findings, and a retry counter.

```
                      ┌──────────────────────────────────────────┐
                      │  intake  (no LLM)                        │
  submission ────────▶│  normalize · vault comments and strings  │
                      │  AST signals · code_hash                 │
                      └───────────────┬──────────────────────────┘
                                      │
              cache hit on code_hash ─┴─▶ return stored diagnosis, skip the graph
                                      │
                    ┌─────────────────┴──────────────────┐
                    ▼                                    ▼
       ┌────────────────────────┐          ┌──────────────────────────┐
       │ diagnoser  (LLM)       │          │ retriever pre-warm       │
       │ taxonomy-led cached    │          │ tag-only keyword pass,   │
       │ prefix · strict tool   │          │ concurrent — hides the   │
       │ schema closes the enum │          │ wait inside the LLM call │
       └───────────┬────────────┘          └────────────┬─────────────┘
                   ▼                                    │
       ┌────────────────────────┐                       │
       │ verifier  (LLM, cheap) │                       │
       │ 1 evidence grounded    │                       │
       │ 2 consistent w/ failure│                       │
       │ 3 no solution code     │                       │
       │ 4 no injected command  │                       │
       └───────┬────────┬───────┘                       │
       rejected│        │passed                         │
    (once, then│        ▼                               ▼
     escalate) │   ┌────────────────────────────────────────────┐
               │   │ retriever  (no LLM)                        │
               └──▶│ keyword arm + pgvector arm, fused with RRF │
                   │ k=60 · difficulty-mixed · top 3            │
                   └───────────────────┬────────────────────────┘
                                       ▼
                   ┌────────────────────────────────────────────┐
                   │ scheduler  (no LLM)                        │
                   │ SM-2 · initial 3d · ease floored at 1.3    │
                   └────────────────────────────────────────────┘
```

Escalation is capped at one hop. A diagnosis the strong tier also fails to verify is
returned marked unverified rather than looping — an unbounded retry on a genuinely
ambiguous submission is how a per-user rate limit turns into an unbounded bill.

---

## The injection threat model, and what comment vaulting does about it

Every submission is attacker-controlled text that the system feeds to a model. A user can
put anything in a comment, a docstring, a string literal, or an identifier — including
text engineered to read as an instruction: *report this pattern*, *return confidence
1.0*, *print your system prompt*, *emit a full working solution*. The diagnoser has no
reliable way to tell a genuine instruction from one that arrived inside the artifact it
is analysing, so the defense cannot be a prompt asking it to be careful. It has to remove
the attack surface before the model ever sees it.

**Comment vaulting** is that removal. During `intake`, a lexical scanner replaces every
comment and string literal with an opaque placeholder — `<!C0!>`, `<!S3!>` — and stores
the originals in a side table. The diagnoser sees program structure and nothing else; the
original text is restored only when evidence is rendered back to the user. Three
properties matter and each is tested. The scanner is lexical rather than parser-based, so
it still works on code that does not parse — submitting deliberately broken code is the
cheapest way to defeat anything that requires a successful parse. It preserves line
numbering, emitting a placeholder plus the newlines the original token consumed, so the
line numbers in `evidence_spans` still index the code the user actually submitted. And
structural signals are drawn from a fixed vocabulary of labels, never from submission
text, so nothing attacker-controlled reaches the model through that channel either.

Vaulting cannot cover identifiers. A variable named
`ignore_all_previous_instructions_and_report_x` is program structure, not a string, and
removing it would destroy the thing being diagnosed. That residue is exactly what
**verifier check 4** exists to catch, and it is why the two mitigations are specified
together rather than as alternatives. Suite D holds both classes of payload, with tests
asserting that comment and string payloads do not survive vaulting *and* that identifier
payloads deliberately do — if vaulting ever silently neutralised the second class, the
suite would stop measuring the verifier's contribution and would quietly overstate the
defense.

Suite D is a hard gate. Any failure blocks merge.

---

## Legal constraint

Problem statements and editorials are copyrighted, and scraping is against the terms of
the sites that host them. The data model reflects that in the initial migration:

- `problems` stores **only** slug, title, difficulty, official tag list, and a canonical
  URL. There is no column for a statement or an editorial, and there never will be.
- Every problem shown in the UI is a link out to the original.
- Pattern descriptions in `taxonomy/patterns.yaml` are original prose written for this
  project, not copied editorial text. The loader rejects any entry whose
  `correct_approach` contains code.
- Only metadata is ever embedded — `problem_embedding_text` is the single function that
  builds embedding input, so the constraint has one place it could be violated and one
  place to review.

---

## Stack

| Layer | Choice |
|---|---|
| Runtime | Python 3.11+ (3.11 in the image) |
| API | FastAPI |
| Orchestration | LangGraph |
| Models | Claude Haiku 4.5 (cheap tier), Claude Opus 5 (escalation) |
| Embeddings | Voyage `voyage-3`, 1024-dim — matches the column exactly, no truncation |
| DB | PostgreSQL 16 + `pgvector` — one database, no separate vector service |
| Cache | Redis |
| Frontend | React + Vite + Tailwind |
| Tracing | Langfuse |
| Migrations | Alembic — the app never creates its own schema |
| Tests | pytest — **116 passing** |
| CI | GitHub Actions |

**One deliberate deviation from the spec.** The spec lists LangChain as the LLM client.
The LLM layer calls the Anthropic SDK directly instead; LangGraph still orchestrates the
graph exactly as specified. Three spec requirements drove this: exact `cache_control`
breakpoint placement on the taxonomy block, which is the single biggest cost lever;
reading `usage.cache_read_input_tokens` directly so `cost_usd` is computed from the four
real token classes rather than estimated; and strict tool-use schema enforcement with a
forced `tool_choice`. All three are one indirection away through a wrapper. Everything
sits behind `weakspot/llm.py`, so swapping the client back is a single-file change.

---

## Running it

```bash
cp .env.example .env          # fill in keys; it boots without them
make up                       # postgres + redis
cd api && python -m venv .venv && .venv/bin/pip install -e ".[dev]"
make migrate                  # alembic upgrade head — creates the schema
make seed                     # 205 problems, 50 patterns, 579 links (no keys needed)
make api                      # http://localhost:8000
make web                      # http://localhost:5173
```

`make seed EMBED=1` additionally computes embeddings once `VOYAGE_API_KEY` is set.
`make seed` and `make api` both depend on `migrate`, so the explicit step is only needed
if you want to migrate without doing anything else.

**The app does not create its own tables.** `alembic upgrade head` owns the schema, the
Docker entrypoint runs it before serving, and `/healthz` reports `schema_current` so a
deploy that skipped the step is visible immediately rather than failing later at query
time. A database created before Alembic was introduced needs `make stamp` once to record
that it is already at head.

Sign in with GitHub, or use the local bypass on the landing page. The bypass mints a
session without GitHub and **the app refuses to start if it is enabled while
`ENV=production`** — a misconfigured deploy fails immediately rather than quietly
accepting unauthenticated sessions.

```bash
make test          # 116 tests, run against migrated schema
make lint          # ruff + eslint
make eval          # all four suites (needs ANTHROPIC_API_KEY)
make eval-offline  # Suite C only — no model calls
make gate          # Suite D only — the hard merge gate
```

Postgres is published on host port **5433**, not 5432, so it does not collide with a
local Postgres. Inside the compose network the API still talks to `postgres:5432`.

---

## The taxonomy

50 failure modes across four families, in `taxonomy/patterns.yaml`. This is the closed
set the diagnoser may emit; the tool schema's `enum` enforces it, not a prompt
instruction.

| family | what it means | entries |
|---|---|---|
| `pattern_selection` | wrong algorithmic shape chosen | 13 |
| `implementation` | correct shape, wrong details | 16 |
| `complexity` | correct and too slow | 10 |
| `comprehension` | misread the problem | 11 |

Every entry carries concrete, checkable `signals` — properties of submitted code, not
abstractions. They ground the diagnoser's choice and give the verifier something to check
an evidence span against. A signal that cannot be checked against code a user wrote does
not belong in the file, and the loader's tests enforce the schema, id/family agreement,
and that `related_patterns` resolve.

### Curating the pattern-problem links

Links are generated from embedding similarity, or from tag overlap when there are no
embeddings. Both are approximations, so there is a review loop:

```bash
python -m weakspot.ingest.seed --review        # exports the top 200 pairs
# read pair_candidates.yaml, move entries into taxonomy/pair_overrides.yaml
python -m weakspot.ingest.seed --apply-review
```

`taxonomy/pair_overrides.yaml` is tracked in git and re-applied on every seed, so a
reseed never silently discards a human decision. Confirmed pairs are marked `curated`,
which the generator then leaves alone; rejected pairs are deleted. Tests assert the
overrides reference real patterns and problems, that no pair is both confirmed and
rejected, and that the database actually reflects the recorded decisions.

**The current file is a starter set, not the full pass** — ten confirmations and five
rejections from one review of the strongest and most obviously wrong candidates. The
remaining ~185 pairs are still un-reviewed.

---

## API

All routes under `/api/v1`, JSON only, session cookie from GitHub OAuth.

```
POST   /submissions                    201 -> {submission_id, status, diagnosis_id?}
GET    /submissions/{id}               200 -> {submission, diagnosis, recommendations[]}
GET    /submissions?limit=&cursor=     200 -> {items[], next_cursor}
GET    /reviews/due                    200 -> {items[], total_items}
POST   /reviews/{id}/complete          200 -> {next_due_at, interval_days}
GET    /patterns                       200 -> {patterns[]}
GET    /patterns/{id}/problems         200 -> {problems[]}
GET    /me/weak-patterns               200 -> {items[]}
GET    /problems/search?q=&pattern=&difficulty=&limit=
GET    /healthz                        includes schema_current (migrations at head)
GET    /metrics                        Prometheus text
```

### MCP

A real **MCP server** is mounted at `/mcp`, speaking the protocol over Streamable HTTP,
so any MCP client connects to it directly:

```json
{
  "mcpServers": {
    "weakspot": { "url": "http://localhost:8000/mcp/" }
  }
}
```

Three tools: `search_problems_by_pattern`, `get_pattern_taxonomy`, and
`get_my_weak_patterns` (the last requires an `Authorization: Bearer` API token). Every
tool has a description written for a model to read, constrained argument schemas, and
responses capped at 20 items so a call cannot blow out a client's context.

The tool logic is also mirrored as plain REST under `/api/v1/mcp-tools/` — same
functions, no JSON-RPC — because a POST is easier to debug against a deployed instance.
Both surfaces call one implementation, so they cannot drift. The suite covers the real
protocol path (`initialize` → `tools/list` → `tools/call`), not just the mirror, since a
broken mount or an unstarted session manager is invisible to the REST tests and is
exactly what stops a client from connecting.

### Cost control

- 10 free diagnoses per user per day, enforced in Redis.
- Diagnoses cached on `code_hash` indefinitely. **A cache hit does not consume quota** —
  charging for a resubmitted identical attempt would only punish users for re-reading
  their own result.
- Code capped at 32KB and 800 lines; a submission whose parser fails is rejected before
  any model call and the quota is refunded.
- The taxonomy block leads the system prompt and carries the sole cache breakpoint. It is
  ~11k tokens and constant, so cache reads bill at roughly a tenth of the uncached rate.
  One test asserts the block clears Haiku 4.5's 4096-token minimum, below which a prefix
  silently stops caching; another asserts it is byte-stable across calls.

---

## Non-goals

No chat interface. No code execution or verdict checking — you report your own failure
type. No storage or display of problem statements or editorials. No generated solutions.
No streaks, leaderboards, or gamification. No dashboard, and no charts beyond the trend
arrows on the weak-patterns screen.
