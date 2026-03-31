"""Add testimonials and how_it_works_steps tables

Revision ID: 021
Revises: 020
Create Date: 2026-03-31
"""
from alembic import op
import sqlalchemy as sa

revision = '021'
down_revision = '020'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    def table_exists(table):
        result = conn.execute(sa.text(
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{table}'"
        )).scalar()
        return result > 0

    if not table_exists('testimonials'):
        op.create_table(
            'testimonials',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('role', sa.String(255), nullable=True),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('avatar_url', sa.String(500), nullable=True),
            sa.Column('rating', sa.Integer(), nullable=False, server_default=sa.text('5')),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('sort_order', sa.Integer(), nullable=False, server_default=sa.text('0')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )

    if not table_exists('how_it_works_steps'):
        op.create_table(
            'how_it_works_steps',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('step_number', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('icon_url', sa.String(500), nullable=True),
            sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade():
    op.drop_table('how_it_works_steps')
    op.drop_table('testimonials')
