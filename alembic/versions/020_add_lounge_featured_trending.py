"""Add is_featured and is_trending to lounges

Revision ID: 020
Revises: 019
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa

revision = '020'
down_revision = '019'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    def column_exists(table, column):
        result = conn.execute(sa.text(
            f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{column}'"
        )).scalar()
        return result > 0

    if not column_exists('lounges', 'is_featured'):
        op.add_column('lounges', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    if not column_exists('lounges', 'is_trending'):
        op.add_column('lounges', sa.Column('is_trending', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade():
    op.drop_column('lounges', 'is_trending')
    op.drop_column('lounges', 'is_featured')
