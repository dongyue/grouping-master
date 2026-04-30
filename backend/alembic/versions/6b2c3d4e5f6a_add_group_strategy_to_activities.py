"""add group_strategy, group_param, remainder_handling to activities

Revision ID: 6b2c3d4e5f6a
Revises: 5a1b2c3d4e5f
Create Date: 2026-04-30 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '6b2c3d4e5f6a'
down_revision: Union[str, Sequence[str], None] = '5a1b2c3d4e5f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('group_strategy', sa.String(20), nullable=False, server_default='fixed_group_size'))
    op.add_column('activities', sa.Column('group_param', sa.Integer(), nullable=False, server_default='2'))
    op.add_column('activities', sa.Column('remainder_handling', sa.String(10), nullable=False, server_default='evenly'))


def downgrade() -> None:
    op.drop_column('activities', 'remainder_handling')
    op.drop_column('activities', 'group_param')
    op.drop_column('activities', 'group_strategy')
