"""Add 2FA fields to users table

Revision ID: 016
Revises: 015
Create Date: 2026-03-25

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '016'
down_revision = '015'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('totp_secret', sa.String(32), nullable=True))
    op.add_column('users', sa.Column('is_2fa_enabled', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade():
    op.drop_column('users', 'is_2fa_enabled')
    op.drop_column('users', 'totp_secret')
