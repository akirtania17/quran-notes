"""Add ayah linking fields to sessions

Revision ID: 0a6f1b2c3d4e
Revises: b31c0ad3e25f
Create Date: 2025-12-26

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0a6f1b2c3d4e"
down_revision = "b31c0ad3e25f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("matched_surah", sa.Integer(), nullable=True))
    op.add_column("sessions", sa.Column("matched_ayah", sa.Integer(), nullable=True))
    op.add_column("sessions", sa.Column("matched_ayah_text_ar", sa.Text(), nullable=True))
    op.add_column("sessions", sa.Column("matched_confidence_pct", sa.Integer(), nullable=True))
    op.add_column("sessions", sa.Column("matched_method", sa.String(length=50), nullable=True))
    op.add_column("sessions", sa.Column("matched_candidates_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("sessions", "matched_candidates_json")
    op.drop_column("sessions", "matched_method")
    op.drop_column("sessions", "matched_confidence_pct")
    op.drop_column("sessions", "matched_ayah_text_ar")
    op.drop_column("sessions", "matched_ayah")
    op.drop_column("sessions", "matched_surah")


