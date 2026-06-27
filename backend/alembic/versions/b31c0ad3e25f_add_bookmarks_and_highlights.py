"""Add bookmarks and highlights

Revision ID: b31c0ad3e25f
Revises: 2c1d7d2f4f8a
Create Date: 2025-12-22

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b31c0ad3e25f"
down_revision = "2c1d7d2f4f8a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sessions.bookmarked
    op.add_column(
        "sessions",
        sa.Column("bookmarked", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )

    # highlights table
    op.create_table(
        "highlights",
        sa.Column("id", sa.String(length=50), nullable=False),
        sa.Column("session_id", sa.String(length=50), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_highlights_session_id"), "highlights", ["session_id"], unique=False)
    op.create_index("ix_highlights_session_created", "highlights", ["session_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_highlights_session_created", table_name="highlights")
    op.drop_index(op.f("ix_highlights_session_id"), table_name="highlights")
    op.drop_table("highlights")
    op.drop_column("sessions", "bookmarked")


