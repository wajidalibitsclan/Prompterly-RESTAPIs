"""Add support_style (tone mode) to users and chat_threads

Support Style Selector (Tone Modes) — MVP 2 task.
Three modes: 'motivational' | 'analytical' | 'empathetic'. Stored as a short
VARCHAR rather than a DB ENUM so adding future tones (e.g. 'direct',
'socratic') is a code change only, not an ALTER TYPE migration.

Revision ID: 023
Revises: 022
Create Date: 2026-04-21
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '023'
down_revision = '022'
branch_labels = None
depends_on = None


def upgrade():
    # User-level default. NULL means "use the global default (motivational)".
    # Filled in when a user explicitly picks a tone from the sidebar.
    op.add_column(
        'users',
        sa.Column('support_style', sa.String(24), nullable=True),
    )

    # Per-thread override so users can switch tone mid-conversation without
    # touching their account-level default.
    op.add_column(
        'chat_threads',
        sa.Column('support_style', sa.String(24), nullable=True),
    )


def downgrade():
    op.drop_column('chat_threads', 'support_style')
    op.drop_column('users', 'support_style')
