"""Phase 2 — build the problem index and the pattern-problem graph.

Metadata only. This module deliberately has no code path that fetches, stores, or
renders a problem statement or an editorial; the canonical URL is the only pointer to
the original, and the UI links out to it.

Run:
    python -m weakspot.ingest.seed              # load + embed + link
    python -m weakspot.ingest.seed --no-embed   # metadata only, no API key needed
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import yaml
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import session_scope, upgrade_to_head
from ..embeddings import embed, pattern_embedding_text, problem_embedding_text
from ..models import Pattern, PatternProblem, Problem
from ..taxonomy import get_taxonomy

logger = logging.getLogger(__name__)

SEED_PATH = Path(__file__).with_name("problems_seed.jsonl")
PROBLEM_URL = "https://leetcode.com/problems/{slug}/"

# Pairs above this cosine similarity are written as generated links. The strongest
# REVIEW_TOP_N are the ones worth a human's time, per spec: `--review` exports them and
# `--apply-review` folds the decisions back in.
LINK_THRESHOLD = 0.35
LINKS_PER_PATTERN = 12
REVIEW_TOP_N = 200

# Hand corrections live here, tracked in git, and are re-applied on every seed so a
# reseed never silently discards them.
OVERRIDES_PATH = Path(__file__).resolve().parents[3] / "taxonomy" / "pair_overrides.yaml"


def load_seed(path: Path = SEED_PATH) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))
    return records


def upsert_problems(db: Session, records: list[dict]) -> list[Problem]:
    existing = {p.slug: p for p in db.query(Problem).all()}
    out: list[Problem] = []

    for rec in records:
        slug = rec["slug"]
        problem = existing.get(slug)
        if problem is None:
            problem = Problem(slug=slug)
            db.add(problem)
        problem.title = rec["title"]
        problem.difficulty = rec["difficulty"]
        problem.tags = list(rec["tags"])
        problem.url = rec.get("url") or PROBLEM_URL.format(slug=slug)
        out.append(problem)

    db.flush()
    return out


def upsert_patterns(db: Session) -> list[Pattern]:
    taxonomy = get_taxonomy()
    existing = {p.id: p for p in db.query(Pattern).all()}
    out: list[Pattern] = []

    for entry in taxonomy.entries:
        pattern = existing.get(entry.id)
        if pattern is None:
            pattern = Pattern(id=entry.id)
            db.add(pattern)
        pattern.family = entry.family
        pattern.name = entry.name
        pattern.correct_approach = entry.correct_approach
        pattern.practice_tags = list(entry.practice_tags)
        out.append(pattern)

    db.flush()
    return out


def embed_problems(db: Session, problems: list[Problem]) -> None:
    pending = [p for p in problems if p.embedding is None]
    if not pending:
        return
    texts = [problem_embedding_text(p.title, list(p.tags), p.difficulty) for p in pending]
    logger.info("embedding %d problems", len(pending))
    for problem, vector in zip(pending, embed(texts, input_type="document"), strict=True):
        problem.embedding = vector
    db.flush()


def embed_patterns(db: Session, patterns: list[Pattern]) -> None:
    pending = [p for p in patterns if p.embedding is None]
    if not pending:
        return
    texts = [
        pattern_embedding_text(p.name, p.correct_approach, list(p.practice_tags)) for p in pending
    ]
    logger.info("embedding %d patterns", len(pending))
    for pattern, vector in zip(pending, embed(texts, input_type="document"), strict=True):
        pattern.embedding = vector
    db.flush()


def link_by_similarity(db: Session) -> int:
    """Generate pattern_problems from embedding similarity.

    Curated rows (`curated = true`) are never overwritten — hand corrections survive
    a re-run, which is the whole point of separating the two.

    Every non-curated link this pass does *not* endorse is removed. Without that the
    table becomes the union of every linking strategy ever run against it: seeding once
    with `--no-embed` and again with embeddings leaves the tag-overlap links behind
    alongside the similarity ones, and the result depends on the order someone happened
    to run commands in rather than on the current inputs.
    """
    written = 0
    keep: set[tuple[str, str]] = set()
    patterns = db.query(Pattern).filter(Pattern.embedding.isnot(None)).all()

    for pattern in patterns:
        rows = db.execute(
            text(
                """
                SELECT id, 1 - (embedding <=> CAST(:vec AS vector)) AS similarity
                  FROM problems
                 WHERE embedding IS NOT NULL
                 ORDER BY embedding <=> CAST(:vec AS vector)
                 LIMIT :limit
                """
            ),
            {"vec": list(pattern.embedding), "limit": LINKS_PER_PATTERN},
        ).fetchall()

        for problem_id, similarity in rows:
            if similarity < LINK_THRESHOLD:
                continue
            keep.add((pattern.id, problem_id))
            existing = db.get(PatternProblem, (pattern.id, problem_id))
            if existing is not None:
                if not existing.curated:
                    existing.strength = float(similarity)
                continue
            db.add(
                PatternProblem(
                    pattern_id=pattern.id,
                    problem_id=problem_id,
                    strength=float(similarity),
                    curated=False,
                )
            )
            written += 1

    db.flush()

    stale = [
        row
        for row in db.query(PatternProblem).filter(PatternProblem.curated.is_(False)).all()
        if (row.pattern_id, row.problem_id) not in keep
    ]
    for row in stale:
        db.delete(row)
    if stale:
        logger.info("removed %d stale non-curated links", len(stale))

    db.flush()
    return written


def link_by_tag_overlap(db: Session) -> int:
    """Tag-overlap links — the fallback when no embeddings exist yet.

    Keeps the retriever's keyword arm useful without an API key, so the whole system
    is runnable offline.
    """
    written = 0
    for pattern in db.query(Pattern).all():
        rows = db.execute(
            text(
                """
                SELECT id,
                       cardinality(ARRAY(SELECT UNNEST(tags::text[]) INTERSECT
                                         SELECT UNNEST(CAST(:tags AS text[])))) AS overlap
                  FROM problems
                 WHERE tags::text[] && CAST(:tags AS text[])
                 ORDER BY overlap DESC
                 LIMIT :limit
                """
            ),
            {"tags": list(pattern.practice_tags), "limit": LINKS_PER_PATTERN},
        ).fetchall()

        for problem_id, overlap in rows:
            if db.get(PatternProblem, (pattern.id, problem_id)) is not None:
                continue
            db.add(
                PatternProblem(
                    pattern_id=pattern.id,
                    problem_id=problem_id,
                    strength=min(1.0, overlap / 3.0),
                    curated=False,
                )
            )
            written += 1

    db.flush()
    return written


def load_overrides(
    path: Path = OVERRIDES_PATH,
) -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """Read the hand-review decisions as (confirmed, rejected) sets of (pattern, slug)."""
    if not path.exists():
        return set(), set()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def pairs(key: str) -> set[tuple[str, str]]:
        return {(e["pattern_id"], e["problem_slug"]) for e in (data.get(key) or [])}

    return pairs("confirmed"), pairs("rejected")


def apply_overrides(db: Session, path: Path = OVERRIDES_PATH) -> dict[str, int]:
    """Mark confirmed pairs curated and delete rejected ones.

    Curated rows survive later reseeds untouched, so a human decision is made once.
    """
    confirmed, rejected = load_overrides(path)
    if not confirmed and not rejected:
        return {"confirmed": 0, "rejected": 0}

    slug_to_id = {slug: pid for pid, slug in db.query(Problem.id, Problem.slug).all()}
    applied = {"confirmed": 0, "rejected": 0}

    for pattern_id, slug in confirmed:
        problem_id = slug_to_id.get(slug)
        if problem_id is None:
            logger.warning("override references unknown problem %r", slug)
            continue
        row = db.get(PatternProblem, (pattern_id, problem_id))
        if row is None:
            # A confirmed pair the generator missed is still a pair a human wants.
            db.add(
                PatternProblem(
                    pattern_id=pattern_id, problem_id=problem_id, strength=1.0, curated=True
                )
            )
        else:
            row.curated = True
            row.strength = max(row.strength, 1.0)
        applied["confirmed"] += 1

    for pattern_id, slug in rejected:
        problem_id = slug_to_id.get(slug)
        if problem_id is None:
            continue
        row = db.get(PatternProblem, (pattern_id, problem_id))
        if row is not None:
            db.delete(row)
            applied["rejected"] += 1

    db.flush()
    return applied


def export_for_review(db: Session, out: Path, top_n: int = REVIEW_TOP_N) -> int:
    """Write the strongest generated pairs to a YAML file for hand correction.

    Already-curated pairs are skipped — they have been decided. Move an entry under
    `confirmed:` or `rejected:` in the overrides file, then run --apply-review.
    """
    rows = db.execute(
        text(
            """
            SELECT pp.pattern_id, p.slug, p.title, p.difficulty, pp.strength
              FROM pattern_problems pp
              JOIN problems p ON p.id = pp.problem_id
             WHERE pp.curated = false
             ORDER BY pp.strength DESC, pp.pattern_id, p.slug
             LIMIT :limit
            """
        ),
        {"limit": top_n},
    ).fetchall()

    taxonomy = get_taxonomy()
    candidates = [
        {
            "pattern_id": pattern_id,
            "pattern_name": entry.name if (entry := taxonomy.get(pattern_id)) else pattern_id,
            "problem_slug": slug,
            "problem_title": title,
            "difficulty": difficulty,
            "strength": round(float(strength), 4),
        }
        for pattern_id, slug, title, difficulty, strength in rows
    ]

    out.write_text(
        "# Generated pair candidates, strongest first. Review each one and move it into\n"
        "# taxonomy/pair_overrides.yaml under `confirmed:` or `rejected:`, then run\n"
        "#   python -m weakspot.ingest.seed --apply-review\n"
        "# Only pattern_id and problem_slug are read; the other fields are for reading.\n"
        + yaml.safe_dump({"candidates": candidates}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return len(candidates)


def run(embed_vectors: bool = True) -> dict[str, int]:
    # Seeding a fresh database is the common case, so bring the schema up rather than
    # failing on a missing table. Idempotent when already at head.
    upgrade_to_head()

    stats: dict[str, int] = {}
    with session_scope() as db:
        problems = upsert_problems(db, load_seed())
        patterns = upsert_patterns(db)
        stats["problems"] = len(problems)
        stats["patterns"] = len(patterns)

        if embed_vectors:
            embed_problems(db, problems)
            embed_patterns(db, patterns)
            stats["links_written"] = link_by_similarity(db)
        else:
            stats["links_written"] = link_by_tag_overlap(db)

        applied = apply_overrides(db)
        stats["confirmed"] = applied["confirmed"]
        stats["rejected"] = applied["rejected"]

        # The count that describes the resulting index, not just this run's inserts.
        # Re-seeding an already-seeded database updates rather than inserts, so
        # `links_written` drops to near zero and reads like the linking collapsed.
        db.flush()
        stats["links"] = db.query(PatternProblem).count()

    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Seed the problem and pattern index.")
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="skip embeddings and link by tag overlap (no VOYAGE_API_KEY needed)",
    )
    parser.add_argument(
        "--review",
        metavar="PATH",
        nargs="?",
        const="pair_candidates.yaml",
        help=f"export the top {REVIEW_TOP_N} generated pairs for hand correction and exit",
    )
    parser.add_argument(
        "--apply-review",
        action="store_true",
        help="apply taxonomy/pair_overrides.yaml to the existing links and exit",
    )
    args = parser.parse_args()

    if args.review:
        with session_scope() as db:
            count = export_for_review(db, Path(args.review))
        print(f"wrote {count} candidates to {args.review}")
        return

    if args.apply_review:
        with session_scope() as db:
            applied = apply_overrides(db)
        print(f"confirmed={applied['confirmed']} rejected={applied['rejected']}")
        return

    stats = run(embed_vectors=not args.no_embed)
    print(
        f"problems={stats['problems']} patterns={stats['patterns']} "
        f"pattern_problems={stats['links']} (new this run: {stats['links_written']}) "
        f"confirmed={stats['confirmed']} rejected={stats['rejected']}"
    )


if __name__ == "__main__":
    main()
