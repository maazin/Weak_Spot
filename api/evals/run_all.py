"""Run the evaluation suites, persist to `eval_runs`, and render a PR comment.

    python -m evals.run_all --commit-sha $SHA --report /tmp/evals.md
    python -m evals.run_all --suites C            # offline-only suite
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from weakspot.db import session_scope
from weakspot.models import EvalRun

from . import suites

logger = logging.getLogger(__name__)

RUNNERS = {
    "A": ("diagnosis accuracy", suites.run_suite_a),
    "B": ("judge calibration", suites.run_suite_b),
    "C": ("retrieval quality", suites.run_suite_c),
    "D": ("prompt injection", suites.run_suite_d),
}


def persist(suite: str, commit_sha: str, metrics: dict[str, Any]) -> None:
    try:
        with session_scope() as db:
            db.add(EvalRun(suite=suite, commit_sha=commit_sha, metrics=metrics))
    except Exception:
        logger.warning("could not persist eval_run for suite %s", suite)


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_report(results: dict[str, dict[str, Any]], commit_sha: str) -> str:
    lines = ["## Weakspot evaluation", "", f"commit `{commit_sha[:8]}`", ""]

    if "D" in results:
        d = results["D"]
        verdict = "PASS" if d["passed"] else "FAIL"
        lines += [
            f"### Suite D — prompt injection: **{verdict}** (hard gate)",
            "",
            f"- valid taxonomy diagnoses: {d['valid_diagnoses']}/{d['cases']}",
            f"- followed the injected instruction: {d['followed_injection']}",
        ]
        if d["violations"]:
            lines.append("")
            lines.append("| case | what happened |")
            lines.append("|---|---|")
            for v in d["violations"]:
                lines.append(f"| `{v['id']}` | {v['reason']} |")
        lines.append("")

    if "A" in results:
        a = results["A"]
        lines += [
            "### Suite A — diagnosis accuracy",
            "",
            "| metric | value |",
            "|---|---|",
            f"| top-1 accuracy | {_pct(a['top_1_accuracy'])} |",
            f"| top-2 accuracy | {_pct(a['top_2_accuracy'])} |",
            f"| macro F1 | {a['macro_f1']:.3f} |",
            f"| family accuracy | {_pct(a['family_accuracy'])} |",
            f"| cost per case | ${a['cost_per_case_usd']:.5f} |",
            f"| scored / errored | {a['scored']} / {a['errors']} |",
            "",
        ]

    if "B" in results:
        b = results["B"]
        lines += [
            "### Suite B — judge calibration",
            "",
            "| dimension | exact | adjacent | kappa |",
            "|---|---|---|---|",
        ]
        for dimension in ("clarity", "correctness", "avoids_solution", "overall"):
            row = b.get(dimension, {})
            lines.append(
                f"| {dimension} | {_pct(row.get('exact_agreement', 0))} | "
                f"{_pct(row.get('adjacent_agreement', 0))} | "
                f"{row.get('cohens_kappa', 0):.3f} |"
            )
        lines.append("")

    if "C" in results:
        c = results["C"]
        lines += [
            "### Suite C — retrieval quality",
            "",
            "| arm | precision@3 | MRR |",
            "|---|---|---|",
        ]
        for arm in ("keyword_only", "vector_only", "hybrid_rrf"):
            row = c.get(arm, {})
            lines.append(
                f"| {arm} | {row.get('precision_at_3', 0):.3f} | {row.get('mrr', 0):.3f} |"
            )
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Run Weakspot evaluation suites.")
    parser.add_argument("--commit-sha", default="local")
    parser.add_argument("--suites", default="ABCD", help="subset, e.g. 'AD'")
    parser.add_argument("--report", type=Path, help="write the markdown report here")
    parser.add_argument("--json", type=Path, help="write raw metrics here")
    args = parser.parse_args()

    results: dict[str, dict[str, Any]] = {}
    for suite in args.suites.upper():
        if suite not in RUNNERS:
            continue
        label, runner = RUNNERS[suite]
        logger.info("running suite %s (%s)", suite, label)
        metrics = runner()
        results[suite] = metrics
        persist(suite, args.commit_sha, metrics)

    report = render_report(results, args.commit_sha)
    print(report)

    if args.report:
        args.report.write_text(report, encoding="utf-8")
    if args.json:
        args.json.write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Suite D is a hard gate: a failure has to fail the build.
    if "D" in results and not results["D"]["passed"]:
        logger.error("Suite D failed — blocking merge")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
