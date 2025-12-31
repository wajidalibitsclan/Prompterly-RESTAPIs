"""Add reply_to_id to chat_messages table

Revision ID: 006_add_reply_to_id
Revises: 005_add_contact_messages
Create Date: 2025-12-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006_add_reply_to_id'
down_revision: Union[str, None] = '005_add_contact_messages'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reply_to_id column to chat_messages table
    op.add_column(
        'chat_messages',
        sa.Column('reply_to_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraint (self-referential)
    op.create_foreign_key(
        'fk_chat_messages_reply_to_id',
        'chat_messages',
        'chat_messages',
        ['reply_to_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add index for faster lookups
    op.create_index(
        'ix_chat_messages_reply_to_id',
        'chat_messages',
        ['reply_to_id']
    )


def downgrade() -> None:
    op.drop_index('ix_chat_messages_reply_to_id', table_name='chat_messages')
    op.drop_constraint('fk_chat_messages_reply_to_id', 'chat_messages', type_='foreignkey')
    op.drop_column('chat_messages', 'reply_to_id')
