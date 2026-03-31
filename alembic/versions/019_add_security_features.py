"""Add security features: UUID, legal hold, config versioning

Revision ID: 019
Revises: 018
Create Date: 2026-03-31

"""
from alembic import op
import sqlalchemy as sa

revision = '019'
down_revision = '018'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Helper to check if column exists
    def column_exists(table, column):
        result = conn.execute(sa.text(
            f"SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{column}'"
        )).scalar()
        return result > 0

    # Helper to check if table exists
    def table_exists(table):
        result = conn.execute(sa.text(
            f"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{table}'"
        )).scalar()
        return result > 0

    # User UUID for pseudonymisation
    if not column_exists('users', 'user_uuid'):
        op.add_column('users', sa.Column('user_uuid', sa.String(36), nullable=True))

    # Generate UUIDs for existing users
    from uuid import uuid4
    users = conn.execute(sa.text("SELECT id FROM users WHERE user_uuid IS NULL")).fetchall()
    for user in users:
        conn.execute(
            sa.text("UPDATE users SET user_uuid = :uuid WHERE id = :id"),
            {"uuid": str(uuid4()), "id": user[0]}
        )

    # Now make it NOT NULL
    if column_exists('users', 'user_uuid'):
        op.alter_column('users', 'user_uuid', nullable=False, existing_type=sa.String(36))
        try:
            op.create_index('ix_users_user_uuid', 'users', ['user_uuid'], unique=True)
        except Exception:
            pass

    # Legal hold fields
    if not column_exists('users', 'legal_hold'):
        op.add_column('users', sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    if not column_exists('users', 'legal_hold_reason'):
        op.add_column('users', sa.Column('legal_hold_reason', sa.String(500), nullable=True))
    if not column_exists('users', 'legal_hold_set_at'):
        op.add_column('users', sa.Column('legal_hold_set_at', sa.DateTime(), nullable=True))

    # Lounge config versions table
    if not table_exists('lounge_config_versions'):
        op.create_table(
            'lounge_config_versions',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
            sa.Column('lounge_id', sa.Integer(), sa.ForeignKey('lounges.id'), nullable=False),
            sa.Column('version_number', sa.Integer(), nullable=False),
            sa.Column('system_prompt', sa.Text(), nullable=True),
            sa.Column('mentor_framework', sa.Text(), nullable=True),
            sa.Column('prompt_templates', sa.JSON(), nullable=True),
            sa.Column('behavioural_guardrails', sa.Text(), nullable=True),
            sa.Column('tone_config', sa.JSON(), nullable=True),
            sa.Column('ai_model', sa.String(100), nullable=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('change_notes', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_lounge_config_versions_lounge_id', 'lounge_config_versions', ['lounge_id'])

    # Link chat threads to config version
    if not column_exists('chat_threads', 'config_version_id'):
        op.add_column('chat_threads', sa.Column('config_version_id', sa.Integer(),
                      sa.ForeignKey('lounge_config_versions.id'), nullable=True))


def downgrade():
    op.drop_column('chat_threads', 'config_version_id')
    op.drop_index('ix_lounge_config_versions_lounge_id', table_name='lounge_config_versions')
    op.drop_table('lounge_config_versions')
    op.drop_column('users', 'legal_hold_set_at')
    op.drop_column('users', 'legal_hold_reason')
    op.drop_column('users', 'legal_hold')
    op.drop_index('ix_users_user_uuid', table_name='users')
    op.drop_column('users', 'user_uuid')
