"""Make lounge category_id optional

Revision ID: 42fb2bd0a668
Revises: 003_add_lounge_profile_image
Create Date: 2025-12-18 19:18:37.305483

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '42fb2bd0a668'
down_revision = '003_add_lounge_profile_image'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make category_id nullable
    op.alter_column('lounges', 'category_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)


def downgrade() -> None:
    # Make category_id NOT NULL again
    op.alter_column('lounges', 'category_id',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
