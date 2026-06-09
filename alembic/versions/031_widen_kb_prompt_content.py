"""Widen kb_prompts.content from TEXT to MEDIUMTEXT for long prompts

TEXT caps at 65,535 bytes, so pasting a very long prompt failed at the DB
write with MySQL error 1406 ("Data too long for column 'content'"). MEDIUMTEXT
raises the ceiling to ~16MB, which comfortably covers any realistic prompt.

Revision ID: 031
Revises: 030
Create Date: 2026-06-09
"""
from alembic import op
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '031'
down_revision = '030'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'kb_prompts', 'content',
        existing_type=mysql.TEXT(),
        type_=mysql.MEDIUMTEXT(),
        existing_nullable=False,
    )


def downgrade():
    # Note: rows longer than 65,535 bytes will fail to downgrade — that's
    # intentional, we don't want to silently truncate prompt content.
    op.alter_column(
        'kb_prompts', 'content',
        existing_type=mysql.MEDIUMTEXT(),
        type_=mysql.TEXT(),
        existing_nullable=False,
    )
