"""Add lounge_resources table for mentor documents

Revision ID: 009_add_lounge_resources
Revises: 008_add_lounge_id_to_notes
Create Date: 2026-01-14
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009_add_lounge_resources'
down_revision: Union[str, None] = '008_add_lounge_id_to_notes'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create lounge_resources table
    op.create_table(
        'lounge_resources',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('lounge_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('uploaded_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['lounge_id'], ['lounges.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_lounge_resources_id', 'lounge_resources', ['id'])
    op.create_index('ix_lounge_resources_lounge_id', 'lounge_resources', ['lounge_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_lounge_resources_lounge_id', table_name='lounge_resources')
    op.drop_index('ix_lounge_resources_id', table_name='lounge_resources')

    # Drop table
    op.drop_table('lounge_resources')
