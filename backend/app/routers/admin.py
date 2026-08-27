from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_admin
from app.models import Customer, Product, Waiter
from app.schemas import (
    CustomerCreate,
    CustomerOut,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    WaiterCreate,
    WaiterOut,
    WaiterUpdate,
)
from app.security import hash_password

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---- Waiters ----

@router.post("/waiters", response_model=WaiterOut, status_code=status.HTTP_201_CREATED)
async def create_waiter(body: WaiterCreate, db: AsyncSession = Depends(get_db)) -> Waiter:
    existing = await db.execute(select(Waiter).where(Waiter.username == body.username))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    waiter = Waiter(
        name=body.name,
        username=body.username,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    db.add(waiter)
    await db.commit()
    await db.refresh(waiter)
    return waiter


@router.get("/waiters", response_model=list[WaiterOut])
async def list_waiters(db: AsyncSession = Depends(get_db)) -> list[Waiter]:
    result = await db.execute(select(Waiter).order_by(Waiter.name))
    return list(result.scalars().all())


@router.put("/waiters/{waiter_id}", response_model=WaiterOut)
async def update_waiter(waiter_id: int, body: WaiterUpdate, db: AsyncSession = Depends(get_db)) -> Waiter:
    waiter = await db.get(Waiter, waiter_id)
    if waiter is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Waiter not found")

    if body.name is not None:
        waiter.name = body.name
    if body.password is not None:
        waiter.password_hash = hash_password(body.password)
    if body.role is not None:
        waiter.role = body.role

    await db.commit()
    await db.refresh(waiter)
    return waiter


# ---- Products ----

@router.get("/products", response_model=list[ProductOut])
async def list_all_products(db: AsyncSession = Depends(get_db)) -> list[Product]:
    """Unlike GET /products (waiter-facing, active only), this includes
    inactive products so admins can find and reactivate them."""
    result = await db.execute(select(Product).order_by(Product.category, Product.name))
    return list(result.scalars().all())


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(body: ProductCreate, db: AsyncSession = Depends(get_db)) -> Product:
    product = Product(name=body.name, category=body.category, price=body.price)
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, body: ProductUpdate, db: AsyncSession = Depends(get_db)) -> Product:
    product = await db.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")

    if body.name is not None:
        product.name = body.name
    if body.category is not None:
        product.category = body.category
    if body.price is not None:
        product.price = body.price
    if body.active is not None:
        product.active = body.active

    await db.commit()
    await db.refresh(product)
    return product


# ---- Customers ----

@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(body: CustomerCreate, db: AsyncSession = Depends(get_db)) -> Customer:
    customer = Customer(name=body.name)
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer
