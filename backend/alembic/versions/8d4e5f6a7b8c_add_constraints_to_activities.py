"""add constraints to activities

Revision ID: 8d4e5f6a7b8c
Revises: 7c3d4e5f6a7b
Create Date: 2026-05-01 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8d4e5f6a7b8c'
down_revision: Union[str, Sequence[str], None] = '7c3d4e5f6a7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('constraints', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('activities', 'constraints')
