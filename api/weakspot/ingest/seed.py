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

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..db import engine, init_extensions, session_scope
from ..embeddings import embed, pattern_embedding_text, problem_embedding_text
from ..models import Base, Pattern, PatternProblem, Problem
from ..taxonomy import get_taxonomy

logger = logging.getLogger(__name__)

SEED_PATH = Path(__file__).with_name("problems_seed.jsonl")
PROBLEM_URL = "https://leetcode.com/problems/{slug}/"

# Pairs above this cosine similarity are written as generated links. The top 200 are
# then hand-corrected (see --review), per spec.
LINK_THRESHOLD = 0.35
LINKS_PER_PATTERN = 12


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
    """
    written = 0
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


def run(embed_vectors: bool = True) -> dict[str, int]:
    init_extensions()
    Base.metadata.create_all(engine)

    stats: dict[str, int] = {}
    with session_scope() as db:
        problems = upsert_problems(db, load_seed())
        patterns = upsert_patterns(db)
        stats["problems"] = len(problems)
        stats["patterns"] = len(patterns)

        if embed_vectors:
            embed_problems(db, problems)
            embed_patterns(db, patterns)
            stats["links"] = link_by_similarity(db)
        else:
            stats["links"] = link_by_tag_overlap(db)

    return stats


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Seed the problem and pattern index.")
    parser.add_argument(
        "--no-embed",
        action="store_true",
        help="skip embeddings and link by tag overlap (no VOYAGE_API_KEY needed)",
    )
    args = parser.parse_args()

    stats = run(embed_vectors=not args.no_embed)
    print(
        f"problems={stats['problems']} patterns={stats['patterns']} "
        f"pattern_problems={stats['links']}"
    )


if __name__ == "__main__":
    main()
