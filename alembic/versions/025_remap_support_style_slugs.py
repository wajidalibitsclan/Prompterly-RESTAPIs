"""Remap legacy support_style slugs to the new 4-style taxonomy

The original implementation shipped with motivational / analytical /
empathetic. The Prompterly Support Style spec replaces those with
Mentor's Style (default) / Soundboard / Reality Check / Pep Talk.

The application-level resolver already maps old slugs to new ones via a
legacy alias table (app/core/support_style.py), so old data wouldn't
break — but storing the canonical slug in the DB keeps reporting,
filtering, and admin dashboards honest. This migration backfills both
`users.support_style` and `chat_threads.support_style`.

Revision ID: 025
Revises: 024
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '025'
down_revision = '024'
branch_labels = None
depends_on = None


# Source-of-truth alias map. Keep in sync with _LEGACY_ALIASES in
# app/core/support_style.py — it's only here as raw SQL because Alembic
# migrations should not import application code (the model schema may
# have moved on by the time this runs).
_REMAP = {
    'motivational': 'pep_talk',
    'empathetic': 'soundboard',
    'analytical': 'reality_check',
}


def _remap_table(table: str) -> None:
    bind = op.get_bind()
    for old, new in _REMAP.items():
        bind.execute(
            sa.text(f"UPDATE {table} SET support_style = :new "
                    f"WHERE support_style = :old"),
            {"old": old, "new": new},
        )


def upgrade():
    _remap_table('users')
    _remap_table('chat_threads')


def downgrade():
    # Best-effort reverse: pep_talk -> motivational, etc. Lossy because
    # the new taxonomy includes 'mentors_style' which has no pre-existing
    # equivalent, so any mentors_style rows are left untouched and become
    # NULL in the legacy schema's terms (the application defaults to
    # motivational when the slug is unknown).
    bind = op.get_bind()
    reverse = {v: k for k, v in _REMAP.items()}
    for new, old in reverse.items():
        for table in ('users', 'chat_threads'):
            bind.execute(
                sa.text(f"UPDATE {table} SET support_style = :old "
                        f"WHERE support_style = :new"),
                {"old": old, "new": new},
            )
    # mentors_style had no analogue — clear it.
    for table in ('users', 'chat_threads'):
        bind.execute(
            sa.text(f"UPDATE {table} SET support_style = NULL "
                    f"WHERE support_style = 'mentors_style'")
        )
