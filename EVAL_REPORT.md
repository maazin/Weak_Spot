## Weakspot evaluation

commit `local`

### Suite D — prompt injection: **FAIL** (hard gate)

- valid taxonomy diagnoses: 37/40
- followed the injected instruction: 0

### Suite A — diagnosis accuracy

| metric | value |
|---|---|
| top-1 accuracy | 72.3% |
| top-2 accuracy | 81.5% |
| macro F1 | 0.710 |
| family accuracy | 81.5% |
| cost per case | $0.00000 |
| scored / errored | 119 / 5 |

### Suite B — judge calibration

| dimension | exact | adjacent | kappa |
|---|---|---|---|
| clarity | 26.7% | 78.3% | 0.131 |
| correctness | 65.0% | 85.0% | 0.469 |
| avoids_solution | 46.7% | 95.0% | 0.179 |
| overall | 46.1% | 86.1% | 0.258 |

### Suite C — retrieval quality

| arm | precision@3 | MRR |
|---|---|---|
| keyword_only | 0.522 | 0.768 |
| vector_only | 0.348 | 0.561 |
| hybrid_rrf | 0.493 | 0.788 |
