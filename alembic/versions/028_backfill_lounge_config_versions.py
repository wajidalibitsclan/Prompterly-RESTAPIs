"""Backfill lounge_config_versions v1 for every existing lounge

Revision ID: 028
Revises: 027
Create Date: 2026-05-26

Security Standard §15. Lounges created before the versioning code shipped
have no `LoungeConfigVersion` row. Without a baseline v1, the rollback
endpoint has nothing to roll back TO and any new chat thread against such
a lounge will be created with `config_version_id=NULL` (audit gap).

This migration inserts a synthetic v1 for every lounge that doesn't have
one yet. The snapshot uses the same JSON shape as
`lounge_versioning_service._snapshot_payload`.
"""
import json

from alembic import op
import sqlalchemy as sa


revision = '028'
down_revision = '027'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Find lounges that have NO config version yet.
    rows = conn.execute(sa.text("""
        SELECT l.id, l.title, l.description, l.about, l.category_id,
               l.access_type, l.max_members, l.brand_color, l.mentor_id,
               l.is_public_listing
        FROM lounges l
        LEFT JOIN lounge_config_versions v ON v.lounge_id = l.id
        WHERE v.id IS NULL
    """)).fetchall()

    if not rows:
        return

    for r in rows:
        payload = {
            "title": r[1],
            "description": r[2],
            "about": r[3],
            "category_id": r[4],
            "access_type": r[5],
            "max_members": r[6],
            "brand_color": r[7],
            "mentor_id": r[8],
            "is_public_listing": bool(r[9]) if r[9] is not None else None,
        }
        conn.execute(
            sa.text("""
                INSERT INTO lounge_config_versions
                    (lounge_id, version_number, prompt_templates,
                     change_notes, is_active, created_at)
                VALUES
                    (:lounge_id, 1, :payload,
                     :notes, 1, CURRENT_TIMESTAMP)
            """),
            {
                "lounge_id": r[0],
                "payload": json.dumps(payload),
                "notes": "Backfilled v1 — lounge predates config versioning",
            },
        )


def downgrade():
    # Backfilled rows are indistinguishable from genuine v1 rows by design.
    # Downgrade is a no-op — operators who really want to clear backfill
    # data should do it with explicit SQL using the change_notes filter.
    pass
