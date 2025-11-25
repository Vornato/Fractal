"""Initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2025-11-25 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # user_status enum (non-native to keep compatibility across SQLite/Postgres)
    user_status_enum = sa.Enum(
        "permanent",
        "temporary",
        "door",
        "declined",
        name="user_status",
        native_enum=False,
        length=20,
    )

    # Drop legacy tables if they exist (handles local preexisting DB when rerunning initial migration)
    with op.batch_alter_table("users", schema=None) as batch_op:
        pass
    op.execute("DROP TABLE IF EXISTS password_reset_tokens")
    op.execute("DROP TABLE IF EXISTS event_settings")
    op.execute("DROP TABLE IF EXISTS bookings")
    op.execute("DROP TABLE IF EXISTS users")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("id_number", sa.String(length=100)),
        sa.Column("gender", sa.String(length=20)),
        sa.Column("dob", sa.Date()),
        sa.Column("social_link", sa.String(length=255)),
        sa.Column("city", sa.String(length=120)),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            user_status_enum,
            nullable=False,
            server_default="temporary",
            default="temporary",
        ),
        sa.Column("profile_photo_path", sa.String(length=255)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id_number"), "users", ["id_number"], unique=True)

    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
        sa.Column("language", sa.String(length=10)),
        sa.Column("event_title", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50)),
        sa.Column("guests", sa.Integer(), server_default="1"),
        sa.Column("tier", sa.String(length=50)),
        sa.Column("payment", sa.String(length=50)),
        sa.Column("payment_id", sa.String(length=120)),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="received"),
    )

    op.create_table(
        "event_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_name", sa.String(length=255)),
        sa.Column("event_date", sa.String(length=255)),
        sa.Column("face_control", sa.String(length=255)),
        sa.Column("tickets_info", sa.String(length=255)),
        sa.Column("ticket_categories", sa.JSON()),
        sa.Column("location", sa.String(length=255)),
        sa.Column("booking_description", sa.Text()),
        sa.Column("event_description", sa.Text()),
    )

    op.create_table(
        "password_reset_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("token", sa.String(length=255), unique=True, nullable=False, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used", sa.Boolean(), server_default="0", default=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
        ),
    )


def downgrade():
    op.drop_table("password_reset_tokens")
    op.drop_table("event_settings")
    op.drop_table("bookings")
    op.drop_index(op.f("ix_users_id_number"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
