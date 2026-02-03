"""Add newsletter subscribers table

Revision ID: 014
Revises: 013
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014'
down_revision = '013'
branch_labels = None
depends_on = None


def upgrade():
    # Create newsletter_subscribers table
    op.create_table(
        'newsletter_subscribers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('subscribed_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('unsubscribed_at', sa.DateTime(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('source', sa.String(100), nullable=False, server_default='footer'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_newsletter_subscribers_id'), 'newsletter_subscribers', ['id'], unique=False)
    op.create_index(op.f('ix_newsletter_subscribers_email'), 'newsletter_subscribers', ['email'], unique=True)
    op.create_index(op.f('ix_newsletter_subscribers_status'), 'newsletter_subscribers', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_newsletter_subscribers_status'), table_name='newsletter_subscribers')
    op.drop_index(op.f('ix_newsletter_subscribers_email'), table_name='newsletter_subscribers')
    op.drop_index(op.f('ix_newsletter_subscribers_id'), table_name='newsletter_subscribers')
    op.drop_table('newsletter_subscribers')
