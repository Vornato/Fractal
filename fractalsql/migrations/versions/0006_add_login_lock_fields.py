"""add login lock fields

Revision ID: 0006_add_login_lock_fields
Revises: 0005_add_user_id_to_bookings
Create Date: 2025-11-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006_add_login_lock_fields"
down_revision = "0005_add_user_id_to_bookings"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("failed_attempts", sa.Integer(), server_default="0", nullable=False))
        batch_op.add_column(sa.Column("lock_until", sa.DateTime(timezone=True)))


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("lock_until")
        batch_op.drop_column("failed_attempts")
