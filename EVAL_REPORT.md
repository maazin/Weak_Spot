# Weakspot evaluation

Measured against the seeded index (205 problems, 50 patterns) on a local run.
Every figure here is the latest row for its suite in the `eval_runs` table.
Reproduce with `make eval`.

Models: `claude-haiku-4-5` for diagnosis, verification and judging;
`claude-opus-5` on escalation only.

---

## Suite D — prompt injection: **PASS** (hard gate)

| metric | value |
|---|---|
| cases | 40 |
| valid taxonomy diagnoses | **40 / 40** |
| followed the injected instruction | **0** |
| errors | 0 |

Any failure here blocks merge. The suite carries both classes of payload:
instructions hidden in comments and string literals, which comment vaulting removes
before the model sees them, and instructions embedded in identifiers, which vaulting
deliberately cannot remove and the verifier's fourth check has to catch.

An earlier run reported FAIL with `followed_injection: 0` — three cases had died on a
transient API 400 and a case that did not run is not a case that passed. That was an
infrastructure failure, not a security one; it is fixed and the gate is green on all 40.

---

## Suite A — diagnosis accuracy

124 labelled submissions across the four families.

| metric | value |
|---|---|
| top-1 accuracy | **0.750** |
| top-2 accuracy | **0.823** |
| macro F1 | 0.738 |
| family accuracy | 0.823 |
| family macro F1 | 0.821 |
| scored / errored | **124 / 0** |
| cost per case | **$0.00343** |
| total cost | $0.4253 |

### Family confusion (rows = true, columns = predicted)

| true \ predicted | pattern_selection | implementation | complexity | comprehension |
|---|---|---|---|---|
| **pattern_selection** | **27** | 0 | 5 | 0 |
| **implementation** | 0 | **28** | 1 | 5 |
| **complexity** | 2 | 0 | **25** | 0 |
| **comprehension** | 1 | 4 | 4 | **22** |

`comprehension` is the weakest family at 22/31, leaking mainly into `implementation`
and `complexity`. That is structural rather than incidental: `comprehension` means
*misread the problem*, and the model is never shown the problem statement, because
storing it would infringe copyright. Detecting a misreading of a text the model cannot
see is the price of the legal constraint, and it is the clearest target for improvement.

`complexity` is the strongest at 25/27.

---

## Suite C — retrieval quality

23 patterns with at least one labelled positive, drawn from 106 hand-labelled
`(pattern, problem)` pairs. Negatives are deliberately plausible: same family, adjacent
topic, or overlapping tags.

| arm | precision@3 | MRR |
|---|---|---|
| keyword only | 0.493 | 0.693 |
| vector only | 0.420 | 0.642 |
| **hybrid (RRF, k=60, weighted)** | **0.522** | **0.739** |

Fusion beats both baselines on both metrics, which is the bar the spec sets. Two things
were required to get there, and neither is the fusion itself:

- **Weighting the arms 3:1 in favour of keyword.** Unweighted RRF scored 0.478 — *worse*
  than the keyword arm alone. The vector arm is a strictly lossier view of the same
  information: embeddings only ever see title, difficulty and tags, which is exactly what
  the keyword arm indexes directly and exactly. An equal vote let the weaker arm push
  correct results out of the top 3.
- **Embedding patterns on tags alone.** Including the `correct_approach` paragraph made
  the two sides of the comparison different kinds of text, and similarity tracked length
  and register as much as subject. Dropping it moved the vector arm from 0.348 to 0.420.

**Caveat, stated plainly.** 23 patterns is 46% of the taxonomy, so a 0.03 margin is worth
under one case. An earlier sweep picked `k=10` on this set; it did not survive once the
measurements were made deterministic, and the conventional `k=60` won instead. Treat the
weighting as a reasoned default the evidence supports, not a tuned optimum. Expanding
Suite C is the highest-value eval work outstanding.

Measurements are reproducible: both arms order by a stable tiebreaker, and Suite C
returns identical metrics across repeated runs and a `VACUUM FULL`. Before that fix the
keyword arm scored 0.522 and then 0.507 on identical data and identical code.

---

## Suite B — judge calibration

60 explanations rated 1–5 on three dimensions by a human and by the judge model.

| dimension | exact agreement | adjacent agreement | Cohen's κ |
|---|---|---|---|
| correctness | 0.650 | 0.850 | **0.469** |
| avoids_solution | 0.467 | 0.950 | 0.179 |
| clarity | 0.267 | 0.783 | 0.131 |
| **overall** | 0.461 | 0.861 | **0.258** |

κ = 0.26 is weak agreement. The judge is rarely wildly wrong — adjacent agreement is
0.861, and 0.95 on whether an explanation withholds a solution — but it does not
reproduce exact scores, and on `clarity` it barely beats chance.

**This number is not yet trustworthy in either direction.** The "human" ratings were
written by the same author as the fixtures rather than by an independent rater, so this
measures reproduction of one person's judgement, not calibration to a ground truth. The
spec asks for independently written labels precisely to avoid that, and this figure
should be re-derived once they exist.

---

## Not measured

**Latency percentiles.** `weakspot_latency_quantile_ms` is exported from `/metrics` and
recorded per diagnosis, but it is populated by real traffic and the system has not served
any. The README's p95 target of 6 seconds is therefore an unvalidated goal. One
end-to-end run measured 26.8 s, though that case included a verifier rejection and an
escalation to Opus 5, so it is a worst case rather than a typical one.

**Cache hit rate in steady state.** `cache_hit` is recorded per call, but a meaningful
rate needs sustained traffic against a warm prefix.
