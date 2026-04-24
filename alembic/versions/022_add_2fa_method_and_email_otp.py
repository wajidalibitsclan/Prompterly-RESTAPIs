"""Add two_factor_method + email 2FA OTP fields to users table

Security Standard §2.4 / Task 5 follow-up — users can now pick between
a TOTP authenticator app and an emailed one-time code for their 2FA
second factor.

Revision ID: 022
Revises: 021
Create Date: 2026-04-13
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '022'
down_revision = '021'
branch_labels = None
depends_on = None


def upgrade():
    # Which second-factor method the user picked. NULL means 2FA disabled.
    # Values: 'totp' | 'email'. Stored as String(16) for simplicity instead
    # of a DB enum, so adding future methods (e.g. sms, webauthn) doesn't
    # require an ALTER TYPE.
    op.add_column(
        'users',
        sa.Column('two_factor_method', sa.String(16), nullable=True),
    )

    # Transient storage for the most recent outstanding email OTP. Used for
    # both setup confirmation and login-stage verification. Code is stored
    # hashed (SHA-256 hex) so the DB never holds plaintext one-time codes.
    op.add_column(
        'users',
        sa.Column('email_2fa_code_hash', sa.String(64), nullable=True),
    )
    op.add_column(
        'users',
        sa.Column('email_2fa_expires_at', sa.DateTime(), nullable=True),
    )
    # 'setup' while confirming a new enrolment, 'login' during sign-in.
    # Keeps the two flows from accidentally cross-validating each other.
    op.add_column(
        'users',
        sa.Column('email_2fa_purpose', sa.String(16), nullable=True),
    )


def downgrade():
    op.drop_column('users', 'email_2fa_purpose')
    op.drop_column('users', 'email_2fa_expires_at')
    op.drop_column('users', 'email_2fa_code_hash')
    op.drop_column('users', 'two_factor_method')
