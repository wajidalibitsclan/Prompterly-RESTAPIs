"""Add lounge stripe fields and lounge_subscriptions table

Revision ID: 007_add_lounge_subscriptions
Revises: 006_add_reply_to_id
Create Date: 2025-12-31
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '007_add_lounge_subscriptions'
down_revision: Union[str, None] = '006_add_reply_to_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Stripe columns to lounges table
    op.add_column(
        'lounges',
        sa.Column('stripe_product_id', sa.String(255), nullable=True)
    )
    op.add_column(
        'lounges',
        sa.Column('stripe_monthly_price_id', sa.String(255), nullable=True)
    )
    op.add_column(
        'lounges',
        sa.Column('stripe_yearly_price_id', sa.String(255), nullable=True)
    )

    # Create index for stripe_product_id
    op.create_index(
        'ix_lounges_stripe_product_id',
        'lounges',
        ['stripe_product_id']
    )

    # Create lounge_subscriptions table
    op.create_table(
        'lounge_subscriptions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('lounge_id', sa.Integer(), nullable=False),
        sa.Column('plan_type', sa.String(20), nullable=False),  # 'monthly' or 'yearly'
        sa.Column('stripe_subscription_id', sa.String(255), nullable=False),
        sa.Column('stripe_price_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('started_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('renews_at', sa.DateTime(), nullable=False),
        sa.Column('canceled_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['lounge_id'], ['lounges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for lounge_subscriptions
    op.create_index('ix_lounge_subscriptions_id', 'lounge_subscriptions', ['id'])
    op.create_index('ix_lounge_subscriptions_user_id', 'lounge_subscriptions', ['user_id'])
    op.create_index('ix_lounge_subscriptions_lounge_id', 'lounge_subscriptions', ['lounge_id'])
    op.create_index(
        'ix_lounge_subscriptions_stripe_subscription_id',
        'lounge_subscriptions',
        ['stripe_subscription_id'],
        unique=True
    )
    op.create_index(
        'ix_lounge_subscriptions_user_lounge',
        'lounge_subscriptions',
        ['user_id', 'lounge_id']
    )


def downgrade() -> None:
    # Drop lounge_subscriptions table
    op.drop_index('ix_lounge_subscriptions_user_lounge', table_name='lounge_subscriptions')
    op.drop_index('ix_lounge_subscriptions_stripe_subscription_id', table_name='lounge_subscriptions')
    op.drop_index('ix_lounge_subscriptions_lounge_id', table_name='lounge_subscriptions')
    op.drop_index('ix_lounge_subscriptions_user_id', table_name='lounge_subscriptions')
    op.drop_index('ix_lounge_subscriptions_id', table_name='lounge_subscriptions')
    op.drop_table('lounge_subscriptions')

    # Drop Stripe columns from lounges table
    op.drop_index('ix_lounges_stripe_product_id', table_name='lounges')
    op.drop_column('lounges', 'stripe_yearly_price_id')
    op.drop_column('lounges', 'stripe_monthly_price_id')
    op.drop_column('lounges', 'stripe_product_id')
