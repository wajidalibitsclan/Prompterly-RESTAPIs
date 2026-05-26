"""Add processed_stripe_events for webhook idempotency / replay protection

Revision ID: 026
Revises: 025
Create Date: 2026-05-26

Security Standard §11 — Stripe webhook signature is verified at the edge,
but signed payloads can still be replayed (network capture, retried delivery
that escaped a partial-failure window, etc). This table holds every Stripe
event id we've already processed so the handler can short-circuit duplicates.
"""
from alembic import op
import sqlalchemy as sa


revision = '026'
down_revision = '025'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    table_exists = conn.execute(sa.text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema=DATABASE() AND table_name='processed_stripe_events'"
    )).scalar() > 0

    if not table_exists:
        op.create_table(
            'processed_stripe_events',
            sa.Column('event_id', sa.String(64), primary_key=True),
            sa.Column('event_type', sa.String(64), nullable=False),
            sa.Column('processed_at', sa.DateTime(), nullable=False),
        )
        op.create_index(
            'ix_processed_stripe_events_event_type',
            'processed_stripe_events',
            ['event_type'],
        )
        op.create_index(
            'ix_processed_stripe_events_processed_at',
            'processed_stripe_events',
            ['processed_at'],
        )


def downgrade():
    op.drop_index('ix_processed_stripe_events_processed_at', table_name='processed_stripe_events')
    op.drop_index('ix_processed_stripe_events_event_type', table_name='processed_stripe_events')
    op.drop_table('processed_stripe_events')
