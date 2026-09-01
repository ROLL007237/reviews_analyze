"""create reviews table

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
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("author", sa.String(length=128), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_reviews_product_id", "reviews", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_reviews_product_id", table_name="reviews")
    op.drop_table("reviews")
