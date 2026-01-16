"""Add public chatbot tables

Revision ID: 010
Revises: 009
Create Date: 2026-01-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    # Create public_chatbot_config table
    op.create_table(
        'public_chatbot_config',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False, server_default='Prompterly Assistant'),
        sa.Column('welcome_message', sa.Text(), nullable=False, server_default='Hi! How can I help you today?'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('input_placeholder', sa.String(255), nullable=False, server_default="What's on your mind?"),
        sa.Column('header_subtitle', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_public_chatbot_config_id'), 'public_chatbot_config', ['id'], unique=False)

    # Create public_chat_messages table
    op.create_table(
        'public_chat_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_public_chat_messages_id'), 'public_chat_messages', ['id'], unique=False)
    op.create_index(op.f('ix_public_chat_messages_session_id'), 'public_chat_messages', ['session_id'], unique=False)

    # Insert default config
    op.execute("""
        INSERT INTO public_chatbot_config (name, welcome_message, system_prompt, input_placeholder, header_subtitle, is_enabled)
        VALUES (
            'Prompterly Assistant',
            'Hi! How can I help you?',
            'You are a helpful assistant for Prompterly, an AI coaching platform. Help users understand what Prompterly offers and answer their questions about the platform. Be friendly, helpful, and concise.',
            'What''s on your mind?',
            'Ask me anything about Prompterly',
            true
        )
    """)


def downgrade():
    op.drop_index(op.f('ix_public_chat_messages_session_id'), table_name='public_chat_messages')
    op.drop_index(op.f('ix_public_chat_messages_id'), table_name='public_chat_messages')
    op.drop_table('public_chat_messages')
    op.drop_index(op.f('ix_public_chatbot_config_id'), table_name='public_chatbot_config')
    op.drop_table('public_chatbot_config')
