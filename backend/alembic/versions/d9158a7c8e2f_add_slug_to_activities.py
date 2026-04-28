"""add slug to activities

Revision ID: d9158a7c8e2f
Revises: 4373c7646a4b
Create Date: 2026-04-28 15:30:00.000000

"""
import secrets
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9158a7c8e2f'
down_revision: Union[str, Sequence[str], None] = '4373c7646a4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('activities')]

    if 'slug' not in columns:
        op.add_column('activities', sa.Column('slug', sa.String(12), nullable=True))
        op.create_index(op.f('ix_activities_slug'), 'activities', ['slug'], unique=True)

    rows = conn.execute(sa.text("SELECT id FROM activities WHERE slug IS NULL")).fetchall()
    for (aid,) in rows:
        slug = secrets.token_hex(6)
        conn.execute(
            sa.text("UPDATE activities SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": aid},
        )

    op.alter_column('activities', 'slug',
                    nullable=False,
                    existing_type=sa.String(12),
                    existing_nullable=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_activities_slug'), table_name='activities')
    op.drop_column('activities', 'slug')
