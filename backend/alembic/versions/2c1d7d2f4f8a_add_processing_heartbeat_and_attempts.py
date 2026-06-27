"""Add processing heartbeat and attempt metadata

Revision ID: 2c1d7d2f4f8a
Revises: 9c2d3f1a6b7e
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2c1d7d2f4f8a"
down_revision = "9c2d3f1a6b7e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("processing_started_at", sa.DateTime(), nullable=True))
    op.add_column("sessions", sa.Column("processing_updated_at", sa.DateTime(), nullable=True))
    op.add_column(
        "sessions",
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("sessions", sa.Column("last_error_step", sa.String(length=30), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "last_error_step")
    op.drop_column("sessions", "attempt_count")
    op.drop_column("sessions", "processing_updated_at")
    op.drop_column("sessions", "processing_started_at")


