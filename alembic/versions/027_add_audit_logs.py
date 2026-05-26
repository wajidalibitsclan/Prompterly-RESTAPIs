"""Add audit_logs table for security/compliance audit trail

Revision ID: 027
Revises: 026
Create Date: 2026-05-26

Security Standard §8/§9. The `audit_logs` table existed in the legacy
`database/prompterly_complete.sql` seed but had no Alembic migration, so
fresh alembic-managed deployments did not create it. This revision is
idempotent: it creates the table only if absent, and adds the `user_uuid`
column on installations that already have the table.
"""
from alembic import op
import sqlalchemy as sa


revision = '027'
down_revision = '026'
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

    def index_exists(table, name):
        return conn.execute(sa.text(
            "SELECT COUNT(*) FROM information_schema.statistics "
            "WHERE table_schema=DATABASE() AND table_name=:t AND index_name=:n"
        ), {"t": table, "n": name}).scalar() > 0

    if not table_exists('audit_logs'):
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
            sa.Column('user_uuid', sa.String(36), nullable=True),
            sa.Column('action', sa.String(100), nullable=False),
            sa.Column('entity_type', sa.String(100), nullable=True),
            sa.Column('entity_id', sa.Integer(), nullable=True),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.String(500), nullable=True),
            sa.Column('changes', sa.JSON(), nullable=True),
            sa.Column('metadata', sa.JSON(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
        )
        op.create_index('ix_audit_logs_user_id', 'audit_logs', ['user_id'])
        op.create_index('ix_audit_logs_user_uuid', 'audit_logs', ['user_uuid'])
        op.create_index('ix_audit_logs_action', 'audit_logs', ['action'])
        op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])
    else:
        # Bring an existing legacy table up to the current model shape.
        if not column_exists('audit_logs', 'user_uuid'):
            op.add_column('audit_logs', sa.Column('user_uuid', sa.String(36), nullable=True))
        if not column_exists('audit_logs', 'created_at'):
            op.add_column('audit_logs', sa.Column(
                'created_at', sa.DateTime(),
                nullable=False, server_default=sa.func.now(),
            ))
        if not index_exists('audit_logs', 'ix_audit_logs_user_uuid'):
            op.create_index('ix_audit_logs_user_uuid', 'audit_logs', ['user_uuid'])
        if not index_exists('audit_logs', 'ix_audit_logs_created_at'):
            op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade():
    # Audit logs are intentionally preserved on downgrade — operators who
    # really want to drop them should do so explicitly outside of alembic.
    pass
