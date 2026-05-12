"""rename_contact_first_name_to_full_name

Revision ID: e6bcd3ac3f11
Revises: 0eb74ec39b64
Create Date: 2026-05-12 18:44:30.928839

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e6bcd3ac3f11'
down_revision: Union[str, None] = '0eb74ec39b64'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('contact_messages', 'first_name', new_column_name='full_name', existing_type=sa.String(length=100))


def downgrade() -> None:
    op.alter_column('contact_messages', 'full_name', new_column_name='first_name', existing_type=sa.String(length=100))
