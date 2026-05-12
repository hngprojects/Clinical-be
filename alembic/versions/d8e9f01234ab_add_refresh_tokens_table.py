"""add refresh_tokens table

Revision ID: d8e9f01234ab
Revises: b9f2c1a47e21
Create Date: 2026-05-10

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d8e9f01234ab"
down_revision: Union[str, None] = "b9f2c1a47e21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	op.create_table(
		"refresh_tokens",
		sa.Column("id", sa.UUID(), nullable=False),
		sa.Column("user_id", sa.UUID(), nullable=False),
		sa.Column("token_hash", sa.String(length=64), nullable=False),
		sa.Column("is_revoked", sa.Boolean(), nullable=False),
		sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
		sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
		sa.PrimaryKeyConstraint("id"),
		sa.UniqueConstraint("token_hash"),
	)
 
	op.create_index(
		op.f("ix_refresh_tokens_user_id"),
		"refresh_tokens",
		["user_id"],
		unique=False,
	)
 


def downgrade() -> None:
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
