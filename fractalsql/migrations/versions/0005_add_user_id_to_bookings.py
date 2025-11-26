"""add user_id to bookings

Revision ID: 0005_add_user_id_to_bookings
Revises: 0004_add_allowed_tiers
Create Date: 2025-11-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0005_add_user_id_to_bookings"
down_revision = "0004_add_allowed_tiers"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_bookings_user_id_users", "users", ["user_id"], ["id"])
        batch_op.create_index(batch_op.f("ix_bookings_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_index(batch_op.f("ix_bookings_user_id"))
        batch_op.drop_constraint("fk_bookings_user_id_users", type_="foreignkey")
        batch_op.drop_column("user_id")
