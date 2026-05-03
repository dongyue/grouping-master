"""add member preferences to activities

Revision ID: d7b34759a402
Revises: a42da61cb8a7
Create Date: 2026-05-04 00:14:33.616275

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd7b34759a402'
down_revision: Union[str, Sequence[str], None] = 'a42da61cb8a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('allow_want_preferences', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
    op.add_column('activities', sa.Column('max_want_count', sa.Integer(), nullable=False, server_default=sa.text('1')))
    op.add_column('activities', sa.Column('allow_avoid_preferences', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')))
    op.add_column('activities', sa.Column('max_avoid_count', sa.Integer(), nullable=False, server_default=sa.text('1')))


def downgrade() -> None:
    op.drop_column('activities', 'allow_avoid_preferences')
    op.drop_column('activities', 'max_avoid_count')
    op.drop_column('activities', 'allow_want_preferences')
    op.drop_column('activities', 'max_want_count')
