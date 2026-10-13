"""Baseline — captures the schema as it existed under create_all(), before
Alembic was introduced. Running `alembic upgrade head` against a database
that already has these tables (created by the app's old create_all() path)
will fail on this revision with "table already exists" — in that case,
stamp it instead of running it: `alembic stamp 0001_baseline`.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-10-13

"""
from alembic import op
import sqlalchemy as sa

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "waiters",
        sa.Column("waiter_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("username", sa.String(64), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(16), nullable=False, server_default="waiter"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_waiters_username", "waiters", ["username"], unique=True)

    op.create_table(
        "customers",
        sa.Column("customer_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "stock_items",
        sa.Column("stock_item_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("portions_per_container", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "products",
        sa.Column("product_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category", sa.String(16), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "stock_item_id", sa.Integer(), sa.ForeignKey("stock_items.stock_item_id"), nullable=True
        ),
        sa.Column("portions_per_sale", sa.Integer(), nullable=False, server_default="1"),
    )

    op.create_table(
        "orders",
        sa.Column("order_id", sa.Integer(), primary_key=True),
        sa.Column("waiter_id", sa.Integer(), sa.ForeignKey("waiters.waiter_id"), nullable=False),
        sa.Column(
            "customer_id",
            sa.Integer(),
            sa.ForeignKey("customers.customer_id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "order_items",
        sa.Column("item_id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.order_id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.product_id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
    )

    op.create_table(
        "bills",
        sa.Column("bill_id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.order_id"), nullable=False),
        sa.Column("transaction_id", sa.String(32), nullable=False),
        sa.Column("total", sa.Numeric(10, 2), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("order_id"),
        sa.UniqueConstraint("transaction_id"),
    )

    op.create_table(
        "suppliers",
        sa.Column("supplier_id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("phone", sa.String(32), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "purchase_orders",
        sa.Column("purchase_order_id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.supplier_id"), nullable=False),
        sa.Column("invoice_number", sa.String(64), nullable=False),
        sa.Column("order_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "purchase_order_items",
        sa.Column("purchase_order_item_id", sa.Integer(), primary_key=True),
        sa.Column(
            "purchase_order_id",
            sa.Integer(),
            sa.ForeignKey("purchase_orders.purchase_order_id"),
            nullable=False,
        ),
        sa.Column("stock_item_id", sa.Integer(), sa.ForeignKey("stock_items.stock_item_id"), nullable=False),
        sa.Column("quantity_received", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("purchase_order_items")
    op.drop_table("purchase_orders")
    op.drop_table("suppliers")
    op.drop_table("bills")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("stock_items")
    op.drop_table("customers")
    op.drop_index("ix_waiters_username", table_name="waiters")
    op.drop_table("waiters")
