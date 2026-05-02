"""add user_attributes table

Revision ID: b1c6d7e8f9a0
Revises: a0f5b6c7d8e9
Create Date: 2026-05-03 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c6d7e8f9a0'
down_revision: Union[str, Sequence[str], None] = 'a0f5b6c7d8e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_attributes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('attribute_name', sa.String(100), nullable=False),
        sa.Column('attribute_value', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'attribute_name', name='uq_user_attribute'),
    )


def downgrade() -> None:
    op.drop_table('user_attributes')
