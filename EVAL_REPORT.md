# Weakspot evaluation

Measured against the seeded index (205 problems, 51 patterns) on a local run.
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

## Suite E — verifier accuracy

23 diagnoses with a known correct verdict: 10 that a careful reader would accept, and 13
carrying a specific flaw, each labelled with the check that ought to catch it.

| metric | value |
|---|---|
| false rejection rate | **10.0%** of 10 sound diagnoses |
| false acceptance rate | **7.7%** of 13 flawed diagnoses |
| accuracy | **91.3%** |

The two directions are not symmetric. A false rejection forces a retry and an escalation
to the strong tier, so it is a bill and a latency spike as much as a quality problem. A
false acceptance puts a wrong diagnosis in front of someone who trusts it.

### What this suite found on its first run

Nothing exercised the verifier until this suite existed, and the first run put the false
rejection rate at **50%**. Half of all sound diagnoses were being rejected, every one of
them escalating to Opus 5 for no reason. Four of the five came from
`evidence_matches_pattern`, the check added to catch mislabelled diagnoses.

The wording was the cause. It told the model to judge the taxonomy's `signals` against
the cited lines, which reads as a checklist the span has to satisfy in full. A correct
memoization diagnosis citing `return fib(n - 1) + fib(n - 2)` was rejected because that
line does not literally demonstrate "called with the same arguments on multiple
branches". The check now asks whether the label names a mechanism the submission does
not contain, states that signals are a guide rather than a checklist, and says to default
to passing. Rewriting it took the rate from 50% to 10% with no loss on the other side.

Check 3 contributed one rejection by failing a two-line snippet that the mechanical cap
had already allowed, so its wording now says explicitly that short fragments are fine.

### What remains

One sound diagnosis is still rejected. The verifier asserted that `lo, hi = 0, len(nums)`
paired with `while lo <= hi` is correctly bounded, which is wrong: the midpoint can reach
`len(nums)` and index past the end. The verifier makes substantive reasoning errors on
subtle implementation bugs, and no amount of prompt wording fixes that.

One flawed diagnosis is still accepted. Evidence citing a function signature, which shows
nothing about the overlapping recursion being claimed, passes `evidence_grounded`. That
check is lenient about whether a span actually supports the claim made for it.

Results vary between runs on a 23-case set, and one case flipped between two runs during
this work. Treat single-point differences here as noise.

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

246 hand-labelled `(pattern, problem)` pairs covering all 51 patterns; every pattern has at
least one positive. Negatives are deliberately plausible: same family, adjacent topic, or
overlapping tags.

| arm | precision@3 | MRR |
|---|---|---|
| keyword only | 0.392 | 0.578 |
| vector only | 0.340 | 0.522 |
| **hybrid (RRF, k=60, weighted 3:1)** | **0.412** | **0.636** |

Fusion beats both baselines on both metrics, which is the bar the spec sets.

The absolute figures sit below the earlier 23-pattern measurement (hybrid 0.522 / 0.739).
That is expected: the 28 patterns added to reach full coverage are the harder ones, since
the subset labelled first was also the subset whose practice tags map most cleanly onto
problems. These numbers are the more representative ones.

### Two claims that did not survive the expansion

Recorded because they are a concrete lesson about tuning against a 23-case set:

- **`k=10` beat `k=60`** on the small suite. On the full suite `k=60` wins (0.412 vs
  0.399) and the conventional default was right.
- **Unweighted fusion scored worse than the keyword arm** on the small suite, which was
  the original argument for weighting the arms. On the full suite unweighted fusion
  already beats keyword on both metrics (0.399 / 0.634); the 3:1 weighting adds a further
  0.013 precision@3 rather than rescuing a loss.

The weighting is retained: it is the best configuration measured on both suite sizes, and
it has an argument independent of the sweep — the vector arm is a strictly lossier view of
the same information, since copyright means embeddings never see more than title,
difficulty and tags, which is exactly what the keyword arm indexes directly.

Measurements are reproducible: both arms order by a stable tiebreaker, and Suite C returns
identical metrics across repeated runs and a `VACUUM FULL`. Before that fix the keyword arm
scored 0.522 and then 0.507 on identical data and identical code.

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
