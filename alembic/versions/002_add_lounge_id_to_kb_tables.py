"""Add lounge_id to knowledge base tables

Revision ID: 002_add_lounge_id
Revises: 001_rename_metadata_column
Create Date: 2025-12-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_lounge_id'
down_revision: Union[str, None] = 'rename_metadata_column'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add lounge_id column to kb_categories
    op.add_column('kb_categories', sa.Column('lounge_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_kb_categories_lounge_id'), 'kb_categories', ['lounge_id'], unique=False)
    op.create_foreign_key(
        'fk_kb_categories_lounge_id',
        'kb_categories', 'lounges',
        ['lounge_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add lounge_id column to kb_prompts
    op.add_column('kb_prompts', sa.Column('lounge_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_kb_prompts_lounge_id'), 'kb_prompts', ['lounge_id'], unique=False)
    op.create_foreign_key(
        'fk_kb_prompts_lounge_id',
        'kb_prompts', 'lounges',
        ['lounge_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add lounge_id column to kb_documents
    op.add_column('kb_documents', sa.Column('lounge_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_kb_documents_lounge_id'), 'kb_documents', ['lounge_id'], unique=False)
    op.create_foreign_key(
        'fk_kb_documents_lounge_id',
        'kb_documents', 'lounges',
        ['lounge_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add lounge_id column to kb_faqs
    op.add_column('kb_faqs', sa.Column('lounge_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_kb_faqs_lounge_id'), 'kb_faqs', ['lounge_id'], unique=False)
    op.create_foreign_key(
        'fk_kb_faqs_lounge_id',
        'kb_faqs', 'lounges',
        ['lounge_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Remove from kb_faqs
    op.drop_constraint('fk_kb_faqs_lounge_id', 'kb_faqs', type_='foreignkey')
    op.drop_index(op.f('ix_kb_faqs_lounge_id'), table_name='kb_faqs')
    op.drop_column('kb_faqs', 'lounge_id')

    # Remove from kb_documents
    op.drop_constraint('fk_kb_documents_lounge_id', 'kb_documents', type_='foreignkey')
    op.drop_index(op.f('ix_kb_documents_lounge_id'), table_name='kb_documents')
    op.drop_column('kb_documents', 'lounge_id')

    # Remove from kb_prompts
    op.drop_constraint('fk_kb_prompts_lounge_id', 'kb_prompts', type_='foreignkey')
    op.drop_index(op.f('ix_kb_prompts_lounge_id'), table_name='kb_prompts')
    op.drop_column('kb_prompts', 'lounge_id')

    # Remove from kb_categories
    op.drop_constraint('fk_kb_categories_lounge_id', 'kb_categories', type_='foreignkey')
    op.drop_index(op.f('ix_kb_categories_lounge_id'), table_name='kb_categories')
    op.drop_column('kb_categories', 'lounge_id')
