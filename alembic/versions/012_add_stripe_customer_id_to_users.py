"""Add stripe_customer_id to users table

Revision ID: 012
Revises: 011
Create Date: 2026-01-16
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012'
down_revision = '011_add_rag_to_public_chatbot'
branch_labels = None
depends_on = None


def upgrade():
    # Add stripe_customer_id column to users table
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(255), nullable=True))
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=False)


def downgrade():
    op.drop_index('ix_users_stripe_customer_id', table_name='users')
    op.drop_column('users', 'stripe_customer_id')
