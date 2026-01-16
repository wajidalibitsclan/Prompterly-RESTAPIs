"""Add RAG fields to public chatbot config

Revision ID: 011
Revises: 010
Create Date: 2026-01-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add embedding columns for RAG
    op.add_column('public_chatbot_config', sa.Column('system_prompt_embedding', sa.JSON(), nullable=True))
    op.add_column('public_chatbot_config', sa.Column('embedding_model', sa.String(100), nullable=True))

    # Add RAG settings
    op.add_column('public_chatbot_config', sa.Column('use_rag', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('public_chatbot_config', sa.Column('rag_similarity_threshold', sa.Integer(), nullable=False, server_default='70'))


def downgrade() -> None:
    op.drop_column('public_chatbot_config', 'rag_similarity_threshold')
    op.drop_column('public_chatbot_config', 'use_rag')
    op.drop_column('public_chatbot_config', 'embedding_model')
    op.drop_column('public_chatbot_config', 'system_prompt_embedding')
