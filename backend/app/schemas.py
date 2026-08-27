from datetime import datetime

from pydantic import BaseModel, ConfigDict


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


# ---- Waiters ----

class WaiterOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    waiter_id: int
    name: str
    username: str
    role: str


class WaiterCreate(BaseModel):
    name: str
    username: str
    password: str
    role: str = "waiter"


class WaiterUpdate(BaseModel):
    name: str | None = None
    password: str | None = None
    role: str | None = None


# ---- Customers ----

class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: int
    name: str


class CustomerCreate(BaseModel):
    name: str


# ---- Products ----

class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    name: str
    category: str
    price: float
    active: bool


class ProductCreate(BaseModel):
    name: str
    category: str
    price: float


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    price: float | None = None
    active: bool | None = None


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
