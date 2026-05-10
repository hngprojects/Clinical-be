"""add otp_codes table and split user.name into first_name/last_name

Revision ID: b9f2c1a47e21
Revises: aabbb6d8362b
Create Date: 2026-05-09 20:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "b9f2c1a47e21"
down_revision: Union[str, None] = "aabbb6d8362b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
	# --- users.name -> first_name + last_name ---
	op.add_column("users", sa.Column("first_name", sa.String(), nullable=True))
	op.add_column("users", sa.Column("last_name", sa.String(), nullable=True))

	# Backfill: split existing `name` on the first whitespace. Single-name rows
	# get a "-" placeholder for last_name so the NOT NULL alter below succeeds
	# and `UserBase.last_name` (Field(min_length=1)) can serialize the row.
	op.execute(
		"""
		UPDATE users
		SET
			first_name = COALESCE(NULLIF(split_part(name, ' ', 1), ''), name),
			last_name  = CASE
				WHEN position(' ' in name) > 0
					THEN trim(substring(name from position(' ' in name) + 1))
				ELSE '-'
			END
		WHERE first_name IS NULL OR last_name IS NULL
		"""
	)

	op.alter_column("users", "first_name", existing_type=sa.String(), nullable=False)
	op.alter_column("users", "last_name", existing_type=sa.String(), nullable=False)

	op.drop_column("users", "name")

	op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)

	# --- otp_codes ---
	# Use postgresql.ENUM with create_type=False so the column does NOT register
	# a `before_create` listener (which would otherwise try to re-create the
	# type without checkfirst inside the same transaction). We then create the
	# type explicitly with checkfirst=True so the migration is idempotent.
	purpose_enum = postgresql.ENUM(
		"email_verification",
		"login",
		name="otppurpose",
		create_type=False,
	)
	purpose_enum.create(op.get_bind(), checkfirst=True)

	op.create_table(
		"otp_codes",
		sa.Column("id", sa.UUID(), nullable=False),
		sa.Column("user_id", sa.UUID(), nullable=False),
		sa.Column("code_hash", sa.String(), nullable=False),
		sa.Column("purpose", purpose_enum, nullable=False),
		sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
		sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
		sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
		sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
		sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
		sa.PrimaryKeyConstraint("id"),
	)
	op.create_index(op.f("ix_otp_codes_user_id"), "otp_codes", ["user_id"], unique=False)
	op.create_index(op.f("ix_otp_codes_purpose"), "otp_codes", ["purpose"], unique=False)


def downgrade() -> None:
	op.drop_index(op.f("ix_otp_codes_purpose"), table_name="otp_codes")
	op.drop_index(op.f("ix_otp_codes_user_id"), table_name="otp_codes")
	op.drop_table("otp_codes")

	purpose_enum = postgresql.ENUM(
		"email_verification",
		"login",
		name="otppurpose",
		create_type=False,
	)
	purpose_enum.drop(op.get_bind(), checkfirst=True)

	op.drop_index(op.f("ix_users_email"), table_name="users")

	op.add_column("users", sa.Column("name", sa.String(), nullable=True))
	op.execute(
		"""
		UPDATE users
		SET name = trim(both ' ' from concat_ws(' ', first_name, last_name))
		"""
	)
	op.alter_column("users", "name", existing_type=sa.String(), nullable=False)

	op.drop_column("users", "last_name")
	op.drop_column("users", "first_name")
