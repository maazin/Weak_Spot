"""initial schema

Revision ID: 18430d734d7b
Revises:
Create Date: 2026-08-05 02:09:11.474622
"""

from __future__ import annotations

from collections.abc import Sequence

import pgvector.sqlalchemy
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "18430d734d7b"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Both extensions have to exist before anything below references them: `vector` for
    # the embedding columns, `pg_trgm` for the fuzzy slug lookups the retriever's keyword
    # arm does. Creating them here rather than at app startup means a fresh database is
    # brought up entirely by `alembic upgrade head`.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        "eval_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("suite", sa.String(length=8), nullable=False),
        sa.Column("commit_sha", sa.String(length=40), nullable=False),
        sa.Column("metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "patterns",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("family", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("correct_approach", sa.Text(), nullable=False),
        sa.Column("practice_tags", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
        sa.CheckConstraint(
            "family in ('pattern_selection','implementation','complexity','comprehension')",
            name="ck_pattern_family",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_patterns_family"), "patterns", ["family"], unique=False)
    op.create_table(
        "problems",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", sa.String(length=200), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("difficulty", sa.String(length=16), nullable=False),
        sa.Column("tags", sa.ARRAY(sa.String()), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.vector.VECTOR(dim=1024), nullable=True),
        sa.CheckConstraint("difficulty in ('easy','medium','hard')", name="ck_problem_difficulty"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_problems_fts",
        "problems",
        [sa.literal_column("to_tsvector('english', title)")],
        unique=False,
        postgresql_using="gin",
    )
    op.create_index(op.f("ix_problems_slug"), "problems", ["slug"], unique=True)
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("github_id", sa.String(length=64), nullable=False),
        sa.Column("handle", sa.String(length=128), nullable=False),
        sa.Column("api_token", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_api_token"), "users", ["api_token"], unique=True)
    op.create_index(op.f("ix_users_github_id"), "users", ["github_id"], unique=True)
    op.create_table(
        "pattern_problems",
        sa.Column("pattern_id", sa.String(length=120), nullable=False),
        sa.Column("problem_id", sa.String(length=36), nullable=False),
        sa.Column("strength", sa.Float(), nullable=False),
        sa.Column("curated", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["pattern_id"], ["patterns.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("pattern_id", "problem_id"),
    )
    op.create_table(
        "review_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("problem_id", sa.String(length=36), nullable=False),
        sa.Column("pattern_id", sa.String(length=120), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("interval_days", sa.Float(), nullable=False),
        sa.Column("ease", sa.Float(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("last_result", sa.String(length=16), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["pattern_id"],
            ["patterns.id"],
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "problem_id", name="uq_review_user_problem"),
    )
    op.create_index(op.f("ix_review_items_due_at"), "review_items", ["due_at"], unique=False)
    op.create_index("ix_review_user_due", "review_items", ["user_id", "due_at"], unique=False)
    op.create_table(
        "submissions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("problem_id", sa.String(length=36), nullable=False),
        sa.Column("language", sa.String(length=20), nullable=False),
        sa.Column("failure_type", sa.String(length=32), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("code_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "failure_type in ('wrong_answer', 'tle', 'mle', 'runtime_error', 'gave_up', 'looked_at_solution')",
            name="ck_submission_failure_type",
        ),
        sa.CheckConstraint(
            "language in ('python', 'java', 'cpp', 'javascript', 'go')",
            name="ck_submission_language",
        ),
        sa.ForeignKeyConstraint(
            ["problem_id"],
            ["problems.id"],
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_submissions_code_hash"), "submissions", ["code_hash"], unique=False)
    op.create_index(op.f("ix_submissions_created_at"), "submissions", ["created_at"], unique=False)
    op.create_index(
        "ix_submissions_user_created", "submissions", ["user_id", "created_at"], unique=False
    )
    op.create_table(
        "diagnoses",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("submission_id", sa.String(length=36), nullable=False),
        sa.Column("pattern_id", sa.String(length=120), nullable=False),
        sa.Column("alternate_pattern_id", sa.String(length=120), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_spans", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("model_tier", sa.String(length=40), nullable=False),
        sa.Column("verifier_passed", sa.Boolean(), nullable=False),
        sa.Column("verifier_failures", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("cost_usd", sa.Float(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("trace_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["alternate_pattern_id"],
            ["patterns.id"],
        ),
        sa.ForeignKeyConstraint(
            ["pattern_id"],
            ["patterns.id"],
        ),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("diagnoses")
    op.drop_index("ix_submissions_user_created", table_name="submissions")
    op.drop_index(op.f("ix_submissions_created_at"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_code_hash"), table_name="submissions")
    op.drop_table("submissions")
    op.drop_index("ix_review_user_due", table_name="review_items")
    op.drop_index(op.f("ix_review_items_due_at"), table_name="review_items")
    op.drop_table("review_items")
    op.drop_table("pattern_problems")
    op.drop_index(op.f("ix_users_github_id"), table_name="users")
    op.drop_index(op.f("ix_users_api_token"), table_name="users")
    op.drop_table("users")
    op.drop_index(op.f("ix_problems_slug"), table_name="problems")
    op.drop_index("ix_problems_fts", table_name="problems", postgresql_using="gin")
    op.drop_table("problems")
    op.drop_index(op.f("ix_patterns_family"), table_name="patterns")
    op.drop_table("patterns")
    op.drop_table("eval_runs")
    # ### end Alembic commands ###
