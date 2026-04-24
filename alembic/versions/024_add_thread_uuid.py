"""Add thread_uuid to chat_threads for URL-safe references

Aligns with Security Standard §2.1 — integer primary keys should stay
internal; external references (URL query params, share links, deep links)
use a non-enumerable UUID instead.

Revision ID: 024
Revises: 023
Create Date: 2026-04-21
"""
import uuid
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '024'
down_revision = '023'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add the column as nullable first so the ALTER TABLE succeeds on
    #    a populated table. We'll backfill, then tighten to NOT NULL.
    op.add_column(
        'chat_threads',
        sa.Column('thread_uuid', sa.String(36), nullable=True),
    )

    # 2. Backfill a UUID for every existing row. MySQL's UUID() isn't
    #    used because it's RFC 4122 v1 (time/MAC-based) and leaks info;
    #    we generate v4 UUIDs server-side instead.
    bind = op.get_bind()
    rows = bind.execute(sa.text(
        "SELECT id FROM chat_threads WHERE thread_uuid IS NULL"
    )).fetchall()
    for row in rows:
        bind.execute(
            sa.text("UPDATE chat_threads SET thread_uuid = :u WHERE id = :i"),
            {"u": str(uuid.uuid4()), "i": row[0]},
        )

    # 3. Lock it down: NOT NULL + unique index so new inserts that skip
    #    the default fail loudly instead of creating blank rows.
    op.alter_column(
        'chat_threads', 'thread_uuid',
        existing_type=sa.String(36),
        nullable=False,
    )
    op.create_index(
        'ix_chat_threads_thread_uuid',
        'chat_threads',
        ['thread_uuid'],
        unique=True,
    )


def downgrade():
    op.drop_index('ix_chat_threads_thread_uuid', table_name='chat_threads')
    op.drop_column('chat_threads', 'thread_uuid')
