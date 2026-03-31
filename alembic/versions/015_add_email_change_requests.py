"""Add email_change_requests table

Revision ID: 015
Revises: 014
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015'
down_revision = '014'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'email_change_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('old_email', sa.String(255), nullable=False),
        sa.Column('new_email', sa.String(255), nullable=False),
        sa.Column('recovery_token', sa.String(500), nullable=True),
        sa.Column('recovery_expires_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('reverted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_email_change_requests_user_id', 'email_change_requests', ['user_id'])
    op.create_index('ix_email_change_requests_id', 'email_change_requests', ['id'])


def downgrade():
    op.drop_index('ix_email_change_requests_user_id', table_name='email_change_requests')
    op.drop_index('ix_email_change_requests_id', table_name='email_change_requests')
    op.drop_table('email_change_requests')
