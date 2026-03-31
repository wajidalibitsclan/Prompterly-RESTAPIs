"""Add account lifecycle fields to users table

Revision ID: 018
Revises: 017
Create Date: 2026-03-31

"""
from alembic import op
import sqlalchemy as sa

revision = '018'
down_revision = '017'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('account_paused_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('data_deletion_scheduled_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('payment_failure_count', sa.Integer(), nullable=False, server_default=sa.text('0')))


def downgrade():
    op.drop_column('users', 'payment_failure_count')
    op.drop_column('users', 'data_deletion_scheduled_at')
    op.drop_column('users', 'account_paused_at')
