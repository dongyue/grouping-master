"""add member_attributes table

Revision ID: 9e5f6a7b8c9d
Revises: 8d4e5f6a7b8c
Create Date: 2026-05-02 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9e5f6a7b8c9d'
down_revision: Union[str, Sequence[str], None] = '8d4e5f6a7b8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'member_attributes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('member_id', sa.Integer(), sa.ForeignKey('activity_members.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attribute_name', sa.String(100), nullable=False),
        sa.Column('attribute_value', sa.String(100), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('member_id', 'attribute_name', name='uq_member_attribute'),
    )


def downgrade() -> None:
    op.drop_table('member_attributes')
