"""add token blocklist

Revision ID: c3d8e4f12a9b
Revises: b4c7d2e9f01a
Create Date: 2026-05-11

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c3d8e4f12a9b"
down_revision: Union[str, None] = "b9f2c1a47e21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "token_blocklist",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("jti"),
    )
    op.create_index("ix_token_blocklist_jti", "token_blocklist", ["jti"], unique=True)
    op.create_index("ix_token_blocklist_expires_at", "token_blocklist", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_token_blocklist_expires_at", table_name="token_blocklist")
    op.drop_index("ix_token_blocklist_jti", table_name="token_blocklist")
    op.drop_table("token_blocklist")
