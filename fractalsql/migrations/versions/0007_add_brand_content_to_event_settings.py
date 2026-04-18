"""add brand_content to event_settings

Revision ID: 0007_brand_content
Revises: 0006_login_lock
Create Date: 2026-04-18
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0007_brand_content"
down_revision = "0006_login_lock"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("event_settings") as batch_op:
        batch_op.add_column(sa.Column("brand_content", sa.JSON()))


def downgrade():
    with op.batch_alter_table("event_settings") as batch_op:
        batch_op.drop_column("brand_content")
