"""remove remainder_handling from activities

Revision ID: 7c3d4e5f6a7b
Revises: 6b2c3d4e5f6a
Create Date: 2026-05-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7c3d4e5f6a7b'
down_revision: Union[str, Sequence[str], None] = '6b2c3d4e5f6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('activities', 'remainder_handling')


def downgrade() -> None:
    op.add_column('activities', sa.Column('remainder_handling', sa.String(10), nullable=False, server_default='evenly'))
