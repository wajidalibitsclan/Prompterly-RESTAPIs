"""Add support_styles + support_style_versions tables; thread version pin

Revision ID: 029
Revises: 028
Create Date: 2026-05-26

S1 / S19 / S20 of the Prompterly Support Style task list. Tables are
created empty — the runtime catalogue in `app/core/support_style.py`
populates them on startup via `sync_support_style_versions_with_db`.
"""
from alembic import op
import sqlalchemy as sa


revision = '029'
down_revision = '028'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    def table_exists(name):
        return conn.execute(sa.text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema=DATABASE() AND table_name=:name"
        ), {"name": name}).scalar() > 0

    def column_exists(table, column):
        return conn.execute(sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema=DATABASE() AND table_name=:t AND column_name=:c"
        ), {"t": table, "c": column}).scalar() > 0

    if not table_exists('support_styles'):
        op.create_table(
            'support_styles',
            sa.Column('slug', sa.String(24), primary_key=True),
            sa.Column('name', sa.String(64), nullable=False),
            sa.Column('description', sa.String(255), nullable=False),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )

    if not table_exists('support_style_versions'):
        op.create_table(
            'support_style_versions',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('style_slug', sa.String(24),
                      sa.ForeignKey('support_styles.slug'), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('prompt_snippet', sa.Text(), nullable=False),
            sa.Column('snippet_hash', sa.String(64), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column('change_notes', sa.Text(), nullable=True),
            sa.Column('created_by', sa.Integer(),
                      sa.ForeignKey('users.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.UniqueConstraint('style_slug', 'version_number',
                                name='uq_support_style_version_number'),
        )
        op.create_index(
            'ix_support_style_versions_style_slug',
            'support_style_versions', ['style_slug'],
        )
        op.create_index(
            'ix_support_style_version_slug_hash',
            'support_style_versions', ['style_slug', 'snippet_hash'],
        )

    if not column_exists('chat_threads', 'support_style_version_id'):
        op.add_column(
            'chat_threads',
            sa.Column(
                'support_style_version_id',
                sa.Integer(),
                sa.ForeignKey('support_style_versions.id'),
                nullable=True,
            ),
        )


def downgrade():
    # Drop the FK column first so the parent table can be dropped.
    conn = op.get_bind()

    def column_exists(table, column):
        return conn.execute(sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema=DATABASE() AND table_name=:t AND column_name=:c"
        ), {"t": table, "c": column}).scalar() > 0

    if column_exists('chat_threads', 'support_style_version_id'):
        op.drop_column('chat_threads', 'support_style_version_id')
    op.drop_table('support_style_versions')
    op.drop_table('support_styles')
