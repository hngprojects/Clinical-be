"""merge migration heads

Revision ID: 5484a268c4ad
Revises: aabbb6d8362b, f2680efe11e5
Create Date: 2026-05-09 18:13:08.859695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5484a268c4ad'
down_revision: Union[str, None] = ('aabbb6d8362b', 'f2680efe11e5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
