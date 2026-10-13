"""Add email/phone to customers (for receipt delivery) and email_status/
email_error/email_sent_at to bills (to track each send attempt).

Existing customer rows are backfilled with placeholder contact info rather
than left NULL, per an earlier decision to review/correct each one by hand
through the admin "Clients" page afterwards. CHANGE_BEFORE_PROD: these
placeholders are the operator's own contact details, used deliberately as
a temporary default — swap them (or drop the backfill UPDATE entirely) if
that's no longer the intent by the time this runs against real customers.

Revision ID: 0002_customer_email
Revises: 0001_baseline
Create Date: 2026-10-13

"""
# Revision ids must stay <= 32 chars: alembic_version.version_num is a
# VARCHAR(32) by default, and Alembic doesn't widen it for you — a longer
# id fails on upgrade with "value too long for type character varying(32)"
# (discovered the hard way against production: Postgres DDL is
# transactional, so it rolled back cleanly rather than leaving a partial
# schema, but it's still worth avoiding).
from alembic import op
import sqlalchemy as sa

revision = "0002_customer_email"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None

DEFAULT_EMAIL = "guy.masumbuko@gmail.com"
DEFAULT_PHONE = "+12027132622"


def upgrade() -> None:
    op.add_column("customers", sa.Column("email", sa.String(255), nullable=True))
    op.add_column("customers", sa.Column("phone", sa.String(32), nullable=True))

    op.add_column(
        "bills",
        sa.Column("email_status", sa.String(16), nullable=False, server_default="none"),
    )
    op.add_column("bills", sa.Column("email_error", sa.Text(), nullable=True))
    op.add_column("bills", sa.Column("email_sent_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        sa.text(
            "UPDATE customers SET email = :email, phone = :phone WHERE email IS NULL"
        ).bindparams(email=DEFAULT_EMAIL, phone=DEFAULT_PHONE)
    )


def downgrade() -> None:
    op.drop_column("bills", "email_sent_at")
    op.drop_column("bills", "email_error")
    op.drop_column("bills", "email_status")
    op.drop_column("customers", "phone")
    op.drop_column("customers", "email")
