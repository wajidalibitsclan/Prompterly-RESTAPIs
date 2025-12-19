"""Add contact_messages table

Revision ID: 005_add_contact_messages
Revises: 004_normalize_enum_values
Create Date: 2025-12-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005_add_contact_messages'
down_revision: Union[str, None] = '004_normalize_enum_values'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create contact_messages table
    op.create_table(
        'contact_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='new'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('replied_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_contact_messages_id'), 'contact_messages', ['id'], unique=False)
    op.create_index(op.f('ix_contact_messages_email'), 'contact_messages', ['email'], unique=False)
    op.create_index(op.f('ix_contact_messages_status'), 'contact_messages', ['status'], unique=False)
    op.create_index(op.f('ix_contact_messages_created_at'), 'contact_messages', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_contact_messages_created_at'), table_name='contact_messages')
    op.drop_index(op.f('ix_contact_messages_status'), table_name='contact_messages')
    op.drop_index(op.f('ix_contact_messages_email'), table_name='contact_messages')
    op.drop_index(op.f('ix_contact_messages_id'), table_name='contact_messages')
    op.drop_table('contact_messages')
