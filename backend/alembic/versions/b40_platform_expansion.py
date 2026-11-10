"""platform expansion: admin user flag, vendor management, vendor plans

Revision ID: b40_platform_expansion
Revises: b30_paypal_webhooks
Create Date: 2026-11-11 03:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b40_platform_expansion'
down_revision: Union[str, Sequence[str], None] = 'b30_paypal_webhooks'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    # 1. Add is_admin to users if not present
    user_cols = [c["name"] for c in insp.get_columns("users")]
    if "is_admin" not in user_cols:
        op.add_column(
            "users",
            sa.Column("is_admin", sa.Boolean(), server_default=sa.text("false"), nullable=False)
        )

    # 2. Create vendors table if not exists
    if "vendors" not in tables:
        op.create_table(
            "vendors",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("category", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("website_url", sa.String(length=255), nullable=True),
            sa.Column("rating", sa.Float(), server_default="4.5", nullable=True),
            sa.Column("is_recommended", sa.Boolean(), server_default=sa.text("true"), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_vendors_id", "vendors", ["id"])
        op.create_index("ix_vendors_name", "vendors", ["name"], unique=True)
        op.create_index("ix_vendors_category", "vendors", ["category"])

    # 3. Create vendor_plans table if not exists
    if "vendor_plans" not in tables:
        op.create_table(
            "vendor_plans",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("vendor_id", sa.Integer(), sa.ForeignKey("vendors.id", ondelete="CASCADE"), nullable=False),
            sa.Column("plan_name", sa.String(length=120), nullable=False),
            sa.Column("price", sa.Float(), server_default="0.0", nullable=False),
            sa.Column("cadence", sa.String(length=30), server_default="monthly", nullable=False),
            sa.Column("currency", sa.String(length=10), server_default="USD", nullable=False),
            sa.Column("features", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
        op.create_index("ix_vendor_plans_id", "vendor_plans", ["id"])
        op.create_index("ix_vendor_plans_vendor_id", "vendor_plans", ["vendor_id"])


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    tables = insp.get_table_names()

    if "vendor_plans" in tables:
        op.drop_table("vendor_plans")
    if "vendors" in tables:
        op.drop_table("vendors")

    user_cols = [c["name"] for c in insp.get_columns("users")]
    if "is_admin" in user_cols:
        op.drop_column("users", "is_admin")

