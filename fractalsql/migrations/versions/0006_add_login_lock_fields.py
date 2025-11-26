"""add login lock fields

Revision ID: 0006_login_lock
Revises: 0005_user_fk
Create Date: 2025-11-25
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0006_login_lock"
down_revision = "0005_user_fk"
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
