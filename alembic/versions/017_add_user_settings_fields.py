"""Add settings, notification preferences, and privacy fields to users table

Revision ID: 017
Revises: 016
Create Date: 2026-03-30

"""
from alembic import op
import sqlalchemy as sa

revision = '017'
down_revision = '016'
branch_labels = None
depends_on = None


def upgrade():
    # Language & Timezone
    op.add_column('users', sa.Column('language', sa.String(10), nullable=False, server_default='en'))
    op.add_column('users', sa.Column('timezone', sa.String(50), nullable=False, server_default='Australia/Sydney'))

    # Notification preferences
    op.add_column('users', sa.Column('notify_email_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.add_column('users', sa.Column('notify_in_app_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.add_column('users', sa.Column('notify_capsule_unlock', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.add_column('users', sa.Column('notify_new_message', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.add_column('users', sa.Column('notify_subscription_updates', sa.Boolean(), nullable=False, server_default=sa.text('1')))
    op.add_column('users', sa.Column('notify_mentor_approved', sa.Boolean(), nullable=False, server_default=sa.text('1')))

    # Privacy / Legal
    op.add_column('users', sa.Column('privacy_accepted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('tos_accepted_at', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('age_confirmed', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade():
    op.drop_column('users', 'age_confirmed')
    op.drop_column('users', 'tos_accepted_at')
    op.drop_column('users', 'privacy_accepted_at')
    op.drop_column('users', 'notify_mentor_approved')
    op.drop_column('users', 'notify_subscription_updates')
    op.drop_column('users', 'notify_new_message')
    op.drop_column('users', 'notify_capsule_unlock')
    op.drop_column('users', 'notify_in_app_enabled')
    op.drop_column('users', 'notify_email_enabled')
    op.drop_column('users', 'timezone')
    op.drop_column('users', 'language')
