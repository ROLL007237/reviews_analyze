"""create product_stats and alerts tables

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
        "product_stats",
        sa.Column("product_id", sa.String(length=128), primary_key=True),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("positive", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("negative", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("neutral", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("product_id", sa.String(length=128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("negative_ratio", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_alerts_product_id", "alerts", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_alerts_product_id", table_name="alerts")
    op.drop_table("alerts")
    op.drop_table("product_stats")
