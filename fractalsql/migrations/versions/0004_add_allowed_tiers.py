"""add allowed_tiers to event_settings

Revision ID: 0004_allowed_tiers
Revises: 0003_pay_fields
Create Date: 2025-11-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0004_allowed_tiers"
down_revision = "0003_pay_fields"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("event_settings") as batch_op:
        batch_op.add_column(sa.Column("allowed_tiers", sa.JSON()))


def downgrade():
    with op.batch_alter_table("event_settings") as batch_op:
        batch_op.drop_column("allowed_tiers")
