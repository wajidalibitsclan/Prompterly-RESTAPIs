"""Add lounge_id to notes table

Revision ID: 008_add_lounge_id_to_notes
Revises: 007_add_lounge_subscriptions
Create Date: 2025-01-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008_add_lounge_id_to_notes'
down_revision: Union[str, None] = '007_add_lounge_subscriptions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add lounge_id column to notes
    op.add_column('notes', sa.Column('lounge_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_notes_lounge_id'), 'notes', ['lounge_id'], unique=False)
    op.create_foreign_key(
        'fk_notes_lounge_id',
        'notes', 'lounges',
        ['lounge_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Remove lounge_id from notes
    op.drop_constraint('fk_notes_lounge_id', 'notes', type_='foreignkey')
    op.drop_index(op.f('ix_notes_lounge_id'), table_name='notes')
    op.drop_column('notes', 'lounge_id')
