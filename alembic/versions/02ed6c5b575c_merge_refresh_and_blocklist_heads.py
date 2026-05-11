"""merge refresh and blocklist heads

Revision ID: 02ed6c5b575c
Revises: c3d8e4f12a9b, 252e1692f5a4
Create Date: 2026-05-11 21:25:13.448553

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '02ed6c5b575c'
down_revision: Union[str, None] = ('c3d8e4f12a9b', '252e1692f5a4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
