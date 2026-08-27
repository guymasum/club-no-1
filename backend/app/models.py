from datetime import datetime, UTC

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Waiter(Base):
    __tablename__ = "waiters"

    waiter_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False, default="waiter")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(back_populates="waiter")


class Customer(Base):
    __tablename__ = "customers"

    customer_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[list["Order"]] = relationship(back_populates="customer")


class StockItem(Base):
    """A physical inventory item (e.g. one wine, tracked as bottles). Stock is
    counted in *portions*, not containers/bottles, to keep the math in whole
    numbers: a bottle poured as 5 glasses holds 5 portions, so a partially
    opened bottle is just a smaller portion count, never a fraction of a
    bottle. A beer's container IS its portion (portions_per_container=1)."""

    __tablename__ = "stock_items"

    stock_item_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    portions_per_container: Mapped[int] = mapped_column(default=1)
    quantity_on_hand: Mapped[int] = mapped_column(default=0)  # in portions
    low_stock_threshold: Mapped[int | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    products: Mapped[list["Product"]] = relationship(back_populates="stock_item")


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(16), nullable=False)  # 'beer' | 'wine' | 'whisky' | 'food'
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Stock tracking is optional (food isn't tracked). When stock_item_id is
    # set, selling one unit of *this* product consumes portions_per_sale
    # portions from the shared stock_item — e.g. a wine's "bottle" product
    # consumes 5 portions and its "glass" product (same stock_item) consumes 1.
    stock_item_id: Mapped[int | None] = mapped_column(ForeignKey("stock_items.stock_item_id"))
    portions_per_sale: Mapped[int] = mapped_column(default=1)

    stock_item: Mapped["StockItem | None"] = relationship(back_populates="products")


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(primary_key=True)
    waiter_id: Mapped[int] = mapped_column(ForeignKey("waiters.waiter_id"), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.customer_id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")  # 'open' | 'billed'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    waiter: Mapped["Waiter"] = relationship(back_populates="orders")
    customer: Mapped["Customer | None"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
    bill: Mapped["Bill | None"] = relationship(back_populates="order", uselist=False)


class OrderItem(Base):
    __tablename__ = "order_items"

    item_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.product_id"), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()


class Bill(Base):
    __tablename__ = "bills"
    __table_args__ = (UniqueConstraint("order_id"),)

    bill_id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id"), nullable=False)
    transaction_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="bill")


def utcnow() -> datetime:
    return datetime.now(UTC)
