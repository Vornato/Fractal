"""add tickets table

Revision ID: 0002_add_tickets
Revises: 0001_initial_schema
Create Date: 2025-11-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_tickets"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, unique=True, index=True),
        sa.Column("ticket_url", sa.String(length=500)),
        sa.Column("qr_url", sa.String(length=500)),
        sa.Column("note", sa.Text()),
        sa.Column("payment_id", sa.String(length=120)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")),
    )


def downgrade():
    op.drop_table("tickets")
