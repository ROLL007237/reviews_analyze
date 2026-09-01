"""create review_analysis table

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "review_analysis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("review_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("sentiment", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("topics", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_review_analysis_review_id", "review_analysis", ["review_id"], unique=True)
    op.create_index("ix_review_analysis_product_id", "review_analysis", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_review_analysis_product_id", table_name="review_analysis")
    op.drop_index("ix_review_analysis_review_id", table_name="review_analysis")
    op.drop_table("review_analysis")
