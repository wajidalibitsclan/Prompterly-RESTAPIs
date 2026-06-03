"""Backfill mentors rows for users with role=mentor but no mentor profile

Revision ID: 030
Revises: 029
Create Date: 2026-05-26

Before this migration, the admin "Change user role" endpoint only flipped
`users.role` and did not create the matching row in the `mentors` table.
The lounge admin UI queries `mentors WHERE status='approved'` to populate
its mentor dropdown, so any user promoted via that path was invisible to
the lounge editor.

The endpoint is now fixed (see admin.update_user_role) to keep both
tables in sync. This migration cleans up the rows that were stranded by
the bug: any user with `role='mentor'` who has no row in `mentors` gets
an APPROVED mentor row created here.
"""
from alembic import op
import sqlalchemy as sa


revision = '030'
down_revision = '029'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Find users with role='mentor' but no mentor row.
    stranded = conn.execute(sa.text("""
        SELECT u.id
        FROM users u
        LEFT JOIN mentors m ON m.user_id = u.id
        WHERE u.role = 'mentor' AND m.id IS NULL
    """)).fetchall()

    if not stranded:
        return

    for row in stranded:
        conn.execute(
            sa.text("""
                INSERT INTO mentors
                    (user_id, status, experience_years, created_at, updated_at)
                VALUES
                    (:user_id, 'approved', 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {"user_id": row[0]},
        )


def downgrade():
    # Backfilled rows are indistinguishable from genuine ones. Removing
    # them would corrupt lounges that may have been linked to them in the
    # meantime. Downgrade is intentionally a no-op.
    pass
