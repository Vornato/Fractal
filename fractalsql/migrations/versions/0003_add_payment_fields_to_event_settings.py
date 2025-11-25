"""add payment fields to event settings

Revision ID: 0003_add_payment_fields_to_event_settings
Revises: 0002_add_tickets
Create Date: 2025-11-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_add_payment_fields_to_event_settings"
down_revision = "0002_add_tickets"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("event_settings") as batch_op:
        batch_op.add_column(sa.Column("tbc_account", sa.String(length=255)))
        batch_op.add_column(sa.Column("bog_account", sa.String(length=255)))
        batch_op.add_column(sa.Column("transfer_note", sa.Text()))
        batch_op.add_column(sa.Column("qr_url", sa.String(length=500)))


def downgrade():
    with op.batch_alter_table("event_settings") as batch_op:
        batch_op.drop_column("qr_url")
        batch_op.drop_column("transfer_note")
        batch_op.drop_column("bog_account")
        batch_op.drop_column("tbc_account")
