# Weakspot evaluation

Measured against the seeded index (205 problems, 51 patterns) on a local run.
Every figure here is the latest row for its suite in the `eval_runs` table.
Reproduce with `make eval`.

Models: `claude-haiku-4-5` for diagnosis, verification and judging;
`claude-opus-5` on escalation only.

---

## Suite D, prompt injection: **PASS** (hard gate)

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

An earlier run reported FAIL with `followed_injection: 0`, three cases had died on a
transient API 400 and a case that did not run is not a case that passed. That was an
infrastructure failure, not a security one; it is fixed and the gate is green on all 40.

---

## Suite E, verifier accuracy

25 diagnoses with a known correct verdict: 12 a careful reader would accept, and 13
carrying a specific flaw, each labelled with the check that ought to catch it.

Measured over four consecutive runs, because a single run on a set this size is not a
number worth quoting.

| metric | min | max | mean |
|---|---|---|---|
| false rejection rate | 8.3% | 25.0% | **16.7%** |
| false acceptance rate | 0.0% | 0.0% | **0.0%** |

One rejection is 8.3 points on 12 sound cases, so the spread above is one or two cases
moving. Treat the mean as the figure and the range as the reason not to trust a single
run.

The two directions are not symmetric. A false rejection forces a retry and an escalation
to the strong tier, so it is a bill and a latency spike. A false acceptance puts a wrong
diagnosis in front of someone who trusts it.

### What the suite found

**Nothing exercised the verifier before this suite existed.** Suites A and D run intake
and the diagnoser only, so the checks that decide whether a diagnosis reaches a user were
measured by nothing at all. The first run put the false rejection rate at **50%**: half of
every sound diagnosis was being rejected and escalated to Opus for no reason, four of the
five from `evidence_matches_pattern`, the check meant to catch mislabelling.

The wording caused it. Telling the model to judge the taxonomy's `signals` against the
cited lines reads as a checklist the span has to satisfy in full, so a correct memoization
diagnosis citing `return fib(n - 1) + fib(n - 2)` was rejected for not literally
demonstrating "called with the same arguments on multiple branches". Rewriting the check
to ask whether the label names a mechanism the submission lacks, and to default to
passing, took it from 50% to roughly 10%.

**`evidence_grounded` was accepting evidence that supported nothing.** A span citing a
function signature passed a claim about overlapping recursion, because "plausibly
support" is a low bar and a signature is at least related to the function. Naming the
failure mode directly, that a span pointing at the `def` line rather than at the
recursive call fails, took false acceptance from 7.7% to **0.0% in every run since**.

**The suite caught a bad label of mine.** A fixture asserted that a nested loop summing
pairwise products should be diagnosed as `pairwise_scan_over_hashing`. The verifier
rejected it and was right: a hash map does not replace that loop, since nothing is being
searched for. The fixture was wrong, not the verifier.

**It also caught a taxonomy wording problem.** That pattern's fourth signal read "the
quantity being searched for can be derived from the current element", which describes why
the fix is available. The verifier read it as something the buggy code must already do,
concluded the code did not do it, and rejected a correct diagnosis. The signal now says
the value "is computable from the current element, so a lookup could stand in for the
inner loop".

### What remains, and why the tuning stopped

One case fails in every run. The verifier asserts that `lo, hi = 0, len(nums)` paired
with `while lo <= hi` is correctly bounded. It is not: the midpoint can reach `len(nums)`
and index past the end. This is a substantive reasoning error on a subtle implementation
bug, and no wording fixes it.

`evidence_grounded` is now the leading contributor to false rejection, firing six times
across four runs on sound diagnoses. One further attempt to rebalance it, telling the
model to pass whenever the mistake falls inside the cited range, made things worse: mean
false rejection went from 16.7% to 20.8% and the firings rose from six to nine. That
change was reverted.

**The tuning stopped there deliberately.** Several prompt revisions have now been made
against the same 25 cases, and the last one moved the number the wrong way by an amount
the run-to-run spread cannot distinguish from noise. Continuing would be fitting the
wording to this fixture set, which is the mistake already recorded under Suite C for the
RRF constants. The next real improvement is more cases, not more wording.

### What this suite does not measure

Every case grafts a diagnosis written by hand onto real intake output, which isolates the
checks from the diagnoser's run-to-run variation. That is the point, and it is also the
limit: these diagnoses are tidier than what the diagnoser actually produces. Live traffic
escalated on 2 of 8 submissions, above the false rejection rate measured here, so the two
are not interchangeable. This suite scores the checks. The escalation rate in the latency
section scores the diagnoser and verifier together, and that is the one that predicts the
bill.

---

## Suite A, diagnosis accuracy

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

## Suite C, retrieval quality

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
it has an argument independent of the sweep, the vector arm is a strictly lossier view of
the same information, since copyright means embeddings never see more than title,
difficulty and tags, which is exactly what the keyword arm indexes directly.

Measurements are reproducible: both arms order by a stable tiebreaker, and Suite C returns
identical metrics across repeated runs and a `VACUUM FULL`. Before that fix the keyword arm
scored 0.522 and then 0.507 on identical data and identical code.

---

## Suite B, judge calibration

60 explanations rated 1–5 on three dimensions by a human and by the judge model.

| dimension | exact agreement | adjacent agreement | Cohen's κ |
|---|---|---|---|
| correctness | 0.650 | 0.850 | **0.469** |
| avoids_solution | 0.467 | 0.950 | 0.179 |
| clarity | 0.267 | 0.783 | 0.131 |
| **overall** | 0.461 | 0.861 | **0.258** |

κ = 0.26 is weak agreement. The judge is rarely wildly wrong, adjacent agreement is
0.861, and 0.95 on whether an explanation withholds a solution, but it does not
reproduce exact scores, and on `clarity` it barely beats chance.

**This number is not yet trustworthy in either direction.** The "human" ratings were
written by the same author as the fixtures rather than by an independent rater, so this
measures reproduction of one person's judgement, not calibration to a ground truth. The
spec asks for independently written labels precisely to avoid that, and this figure
should be re-derived once they exist.

---

## Latency and cost, measured

Eight submissions through the running API, uncached, after the escalation path was
repaired. Small sample, and the escalation rate is the number least settled by it.

| path | n | p50 | mean cost |
|---|---|---|---|
| direct | 6 | **5.6 s** | **$0.0084** |
| escalated | 2 | **21.4 s** | **$0.0788** |

Escalation fired on 2 of 8. At that rate the blended figure is about **$0.026 per
diagnosis**, which is roughly eight times the $0.00343 Suite A reports.

### Why Suite A's cost figure is lower

Two reasons, both worth stating plainly rather than reconciling quietly.

Suite A runs intake and the diagnoser only. It never calls the verifier, so its per-case
cost is missing a call that every real diagnosis makes. The direct path above is $0.0084
against Suite A's $0.00343 for that reason alone.

More seriously, Suite A was measured while **escalation was silently broken**. The graph
stored the resolved dated model id and compared it against the configured alias, so
`escalate()` returned the cheap tier unchanged and every escalated case re-ran Haiku at
Haiku prices. Fixing that did not make the system more expensive. It revealed what the
design in the spec actually costs, and the escalated column above is the first honest
measurement of it.

### The p95 target

The direct path at 5.6 s sits inside the 6-second target. The escalated path at 21.4 s
does not, and no wording changes that: the second diagnosis and the second verification
are simply more work, and `effort="high"` on the strong tier is slow by design.

Anyone quoting a single p95 for this system is averaging two different things. Report the
two paths separately and report the escalation rate beside them.

### A 617-second diagnosis

One submission in the batch recorded 617 seconds. The retry layers multiply and nothing
capped the total: the SDK's default of two retries gives three attempts, the transient-400
handling adds three more, and a diagnosis makes up to four calls. That is fifty-four
minutes of worst case.

The SDK is now capped at one retry with a 60-second timeout, so a single call is bounded
at about two minutes, and the graph skips escalation once a diagnosis has already spent
45 seconds. Escalation is worth roughly fifteen extra seconds on a normal request and
worth nothing on one that is already slow.

## Still not measured

**Cache hit rate in steady state.** `cache_hit` is recorded per call, but a meaningful
rate needs sustained traffic against a warm prefix. Repeat submissions of identical code
were observed served from the `code_hash` cache in about 20 ms against roughly 6 s
uncached, which is the cache working, not a hit rate.
