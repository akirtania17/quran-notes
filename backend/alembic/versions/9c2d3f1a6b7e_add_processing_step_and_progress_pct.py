"""Add processing_step and progress_pct to sessions

Revision ID: 9c2d3f1a6b7e
Revises: 75b65471aeda
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c2d3f1a6b7e"
down_revision = "75b65471aeda"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("processing_step", sa.String(length=30), nullable=True))
    op.add_column("sessions", sa.Column("progress_pct", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "progress_pct")
    op.drop_column("sessions", "processing_step")


