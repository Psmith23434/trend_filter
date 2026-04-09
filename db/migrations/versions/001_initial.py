"""Initial tables: scan_runs + trend_records

Revision ID: 001
Revises:
Create Date: 2026-04-09
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scan_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("signal_count", sa.Integer(), nullable=True),
        sa.Column("cluster_count", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_scan_runs_id", "scan_runs", ["id"])

    op.create_table(
        "trend_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_run_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=True),
        sa.Column("label", sa.String(length=512), nullable=True),
        sa.Column("niche", sa.String(length=64), nullable=True),
        sa.Column("signal_type", sa.String(length=64), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("growth", sa.Float(), nullable=True),
        sa.Column("source_diversity", sa.Float(), nullable=True),
        sa.Column("commercial_intent", sa.Float(), nullable=True),
        sa.Column("novelty", sa.Float(), nullable=True),
        sa.Column("persistence", sa.Float(), nullable=True),
        sa.Column("urgency", sa.String(length=16), nullable=True),
        sa.Column("sources", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("evidence_urls", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("keywords", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("signal_count_in_cluster", sa.Integer(), nullable=True),
        sa.Column("brief", sa.Text(), nullable=True),
        sa.Column("product_ideas", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("action_plan", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trend_records_id", "trend_records", ["id"])
    op.create_index("ix_trend_records_niche", "trend_records", ["niche"])
    op.create_index("ix_trend_records_scan_run_id", "trend_records", ["scan_run_id"])


def downgrade() -> None:
    op.drop_index("ix_trend_records_scan_run_id", table_name="trend_records")
    op.drop_index("ix_trend_records_niche", table_name="trend_records")
    op.drop_index("ix_trend_records_id", table_name="trend_records")
    op.drop_table("trend_records")
    op.drop_index("ix_scan_runs_id", table_name="scan_runs")
    op.drop_table("scan_runs")
