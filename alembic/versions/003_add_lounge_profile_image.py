"""Add profile_image_id to lounges table

Revision ID: 003_add_lounge_profile_image
Revises: 002_add_lounge_id
Create Date: 2025-12-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_add_lounge_profile_image'
down_revision: Union[str, None] = '002_add_lounge_id'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add profile_image_id column to lounges table
    op.add_column('lounges', sa.Column('profile_image_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_lounges_profile_image_id'), 'lounges', ['profile_image_id'], unique=False)
    op.create_foreign_key(
        'fk_lounges_profile_image_id',
        'lounges', 'files',
        ['profile_image_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    op.drop_constraint('fk_lounges_profile_image_id', 'lounges', type_='foreignkey')
    op.drop_index(op.f('ix_lounges_profile_image_id'), table_name='lounges')
    op.drop_column('lounges', 'profile_image_id')
