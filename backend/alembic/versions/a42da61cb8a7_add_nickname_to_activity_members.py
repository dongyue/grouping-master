"""add nickname to activity_members — backfill then NOT NULL

Revision ID: a42da61cb8a7
Revises: b1c6d7e8f9a0
Create Date: 2026-05-03 15:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a42da61cb8a7'
down_revision: Union[str, None] = 'b1c6d7e8f9a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activity_members', sa.Column('nickname', sa.String(50), nullable=True))
    op.execute(
        "UPDATE activity_members am JOIN users u ON am.user_id = u.id "
        "SET am.nickname = u.nickname WHERE am.nickname IS NULL"
    )
    op.alter_column('activity_members', 'nickname', existing_type=sa.String(50), nullable=False)


def downgrade() -> None:
    op.drop_column('activity_members', 'nickname')
