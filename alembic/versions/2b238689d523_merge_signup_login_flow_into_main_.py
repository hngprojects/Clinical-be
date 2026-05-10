"""merge signup-login-flow into main migration chain

Revision ID: 2b238689d523
Revises: 5484a268c4ad, b9f2c1a47e21
Create Date: 2026-05-10 09:24:41.753214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2b238689d523'
down_revision: Union[str, None] = ('5484a268c4ad', 'b9f2c1a47e21')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
