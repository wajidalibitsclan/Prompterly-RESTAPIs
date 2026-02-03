"""Add about and brand_color columns to lounges table

Revision ID: 013
Revises: 012
Create Date: 2026-01-30
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013'
down_revision = '012'
branch_labels = None
depends_on = None


def upgrade():
    # Add about column to lounges table (for bullet points stored as JSON array)
    op.add_column('lounges', sa.Column('about', sa.Text(), nullable=True))

    # Add brand_color column to lounges table (hex color code for lounge card)
    op.add_column('lounges', sa.Column('brand_color', sa.String(7), nullable=True, server_default='#9ECCF2'))


def downgrade():
    op.drop_column('lounges', 'brand_color')
    op.drop_column('lounges', 'about')
