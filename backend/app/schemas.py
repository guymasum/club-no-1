from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---- Auth ----

class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    waiter_id: int
    name: str
    role: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=4)


# ---- Waiters ----

class WaiterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    waiter_id: int
    name: str
    username: str
    role: str
    active: bool


class WaiterCreate(BaseModel):
    name: str
    username: str
    password: str = Field(min_length=4)
    role: str = "waiter"


class WaiterUpdate(BaseModel):
    name: str | None = None
    password: str | None = Field(default=None, min_length=4)
    role: str | None = None
    active: bool | None = None


# ---- Customers ----

class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    name: str


class CustomerCreate(BaseModel):
    name: str


class CustomerUpdate(BaseModel):
    name: str


# ---- Stock ----

class StockItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    stock_item_id: int
    name: str
    portions_per_container: int
    quantity_on_hand: int
    low_stock_threshold: int | None


class StockItemCreate(BaseModel):
    name: str
    portions_per_container: int = 1
    quantity_on_hand: int = 0
    low_stock_threshold: int | None = None


class StockItemUpdate(BaseModel):
    name: str | None = None
    portions_per_container: int | None = None
    low_stock_threshold: int | None = None


class StockAdjustment(BaseModel):
    delta: int  # positive for a delivery received, negative for breakage/correction


# ---- Products ----

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    name: str
    category: str
    price: float
    active: bool
    stock_item_id: int | None
    portions_per_sale: int
    # How many more times this specific product can be sold given current
    # stock (quantity_on_hand // portions_per_sale). None when untracked.
    stock_remaining: int | None = None


class ProductCreate(BaseModel):
    name: str
    category: str
    price: float
    stock_item_id: int | None = None
    portions_per_sale: int = 1


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    price: float | None = None
    active: bool | None = None
    stock_item_id: int | None = None
    portions_per_sale: int | None = None
    # `stock_item_id: null` is indistinguishable from "field omitted" once
    # parsed, so unlinking an already-tracked product needs an explicit flag.
    clear_stock_item: bool = False


# ---- Orders ----

class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: float


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    waiter_id: int
    waiter_name: str
    customer_id: int | None
    customer_name: str | None
    status: str
    created_at: datetime
    items: list[OrderItemOut] = []


class OrderCreate(BaseModel):
    customer_id: int | None = None


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1


# ---- Bills ----

class BillSummaryOut(BaseModel):
    """Row shape for the finalized-bills list — no line items, so listing
    hundreds of bills doesn't drag in every order's products."""

    model_config = ConfigDict(from_attributes=True)

    bill_id: int
    transaction_id: str
    total: float
    generated_at: datetime
    waiter_name: str
    customer_name: str | None


class BillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    bill_id: int
    order_id: int
    transaction_id: str
    total: float
    generated_at: datetime
    waiter_name: str
    customer_name: str | None
    items: list[OrderItemOut] = []
