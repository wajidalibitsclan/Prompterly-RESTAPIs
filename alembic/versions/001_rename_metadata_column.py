"""Rename metadata to message_metadata in chat_messages

Revision ID: rename_metadata_column
Revises: 
Create Date: 2024-11-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rename_metadata_column'
down_revision = None
depends_on = None


def upgrade():
    # Rename column metadata to message_metadata
    op.alter_column('chat_messages', 'metadata', 
                    new_column_name='message_metadata')


def downgrade():
    # Revert: rename message_metadata back to metadata
    op.alter_column('chat_messages', 'message_metadata',
                    new_column_name='metadata')
