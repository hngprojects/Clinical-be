"""update user medical_case lab_result tables

Revision ID: 2306685d216c
Revises: 90aeb7c687d7
Create Date: 2026-05-09 10:21:57.882420

"""

from typing import Sequence, Union

revision: str = "2306685d216c"
down_revision: Union[str, None] = "90aeb7c687d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Schema is created in a88e01cfb395 (plural table names). This revision is kept
    # only to preserve revision-chain compatibility with existing alembic_version rows.
    pass


def downgrade() -> None:
    pass
