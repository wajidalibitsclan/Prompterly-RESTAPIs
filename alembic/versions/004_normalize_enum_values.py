"""Normalize enum values to lowercase

Revision ID: 004_normalize_enum_values
Revises: 42fb2bd0a668
Create Date: 2025-12-18
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '004_normalize_enum_values'
down_revision = '42fb2bd0a668'
branch_labels = None
depends_on = None


def upgrade():
    # Normalize all enum values to lowercase

    # Users table - role column
    op.execute("UPDATE users SET role = LOWER(role) WHERE role != LOWER(role)")

    # Mentors table - status column
    op.execute("UPDATE mentors SET status = LOWER(status) WHERE status != LOWER(status)")

    # Lounges table - access_type column
    op.execute("UPDATE lounges SET access_type = LOWER(access_type) WHERE access_type != LOWER(access_type)")

    # Lounge memberships table - role column
    op.execute("UPDATE lounge_memberships SET role = LOWER(role) WHERE role != LOWER(role)")

    # Chat threads table - status column
    op.execute("UPDATE chat_threads SET status = LOWER(status) WHERE status != LOWER(status)")

    # Chat messages table - sender_type column
    op.execute("UPDATE chat_messages SET sender_type = LOWER(sender_type) WHERE sender_type != LOWER(sender_type)")

    # OAuth accounts table - provider column
    op.execute("UPDATE oauth_accounts SET provider = LOWER(provider) WHERE provider != LOWER(provider)")

    # Time capsules table - status column
    op.execute("UPDATE time_capsules SET status = LOWER(status) WHERE status != LOWER(status)")

    # Subscription plans table - billing_interval column
    op.execute("UPDATE subscription_plans SET billing_interval = LOWER(billing_interval) WHERE billing_interval != LOWER(billing_interval)")

    # Subscriptions table - status column
    op.execute("UPDATE subscriptions SET status = LOWER(status) WHERE status != LOWER(status)")

    # Payments table - provider and status columns
    op.execute("UPDATE payments SET provider = LOWER(provider) WHERE provider != LOWER(provider)")
    op.execute("UPDATE payments SET status = LOWER(status) WHERE status != LOWER(status)")

    # Notifications table - channel and status columns
    op.execute("UPDATE notifications SET channel = LOWER(channel) WHERE channel != LOWER(channel)")
    op.execute("UPDATE notifications SET status = LOWER(status) WHERE status != LOWER(status)")

    # Compliance requests table - request_type and status columns
    op.execute("UPDATE compliance_requests SET request_type = LOWER(request_type) WHERE request_type != LOWER(request_type)")
    op.execute("UPDATE compliance_requests SET status = LOWER(status) WHERE status != LOWER(status)")


def downgrade():
    # No downgrade needed - lowercase values are valid
    pass
