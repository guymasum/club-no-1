from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import require_admin
from app.models import Customer, Product, StockItem, Waiter
from app.product_utils import to_product_out
from app.schemas import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
    ProductCreate,
    ProductOut,
    ProductUpdate,
    StockAdjustment,
    StockItemCreate,
    StockItemOut,
    StockItemUpdate,
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
        raise HTTPException(status.HTTP_409_CONFLICT, "Ce nom d'utilisateur est déjà pris")

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
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Serveur introuvable")

    # "Removing" a waiter is a deactivation, not a hard delete: every order
    # requires a waiter_id for accountability, so historical orders/bills
    # must keep pointing at a real, correctly-named record. Deactivating
    # revokes login (see deps.get_current_waiter) without touching history.
    would_lose_last_admin = (
        waiter.role == "admin"
        and waiter.active
        and ((body.role is not None and body.role != "admin") or body.active is False)
    )
    if would_lose_last_admin:
        active_admins = await db.execute(
            select(func.count()).select_from(Waiter).where(Waiter.role == "admin", Waiter.active.is_(True))
        )
        if active_admins.scalar_one() <= 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "Impossible de retirer le dernier administrateur actif",
            )

    if body.name is not None:
        waiter.name = body.name
    if body.password is not None:
        waiter.password_hash = hash_password(body.password)
    if body.role is not None:
        waiter.role = body.role
    if body.active is not None:
        waiter.active = body.active

    await db.commit()
    await db.refresh(waiter)
    return waiter


# ---- Products ----

async def _load_product_with_stock(product_id: int, db: AsyncSession) -> Product:
    result = await db.execute(
        select(Product).where(Product.product_id == product_id).options(selectinload(Product.stock_item))
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Produit introuvable")
    return product


async def _check_stock_item_exists(stock_item_id: int, db: AsyncSession) -> None:
    if await db.get(StockItem, stock_item_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article de stock introuvable")


@router.get("/products", response_model=list[ProductOut])
async def list_all_products(db: AsyncSession = Depends(get_db)) -> list[ProductOut]:
    """Unlike GET /products (waiter-facing, active only), this includes
    inactive products so admins can find and reactivate them."""
    result = await db.execute(
        select(Product).options(selectinload(Product.stock_item)).order_by(Product.category, Product.name)
    )
    return [to_product_out(p) for p in result.scalars().all()]


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(body: ProductCreate, db: AsyncSession = Depends(get_db)) -> ProductOut:
    if body.portions_per_sale < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le nombre de portions par vente doit être d'au moins 1")
    if body.stock_item_id is not None:
        await _check_stock_item_exists(body.stock_item_id, db)

    product = Product(
        name=body.name,
        category=body.category,
        price=body.price,
        stock_item_id=body.stock_item_id,
        portions_per_sale=body.portions_per_sale,
    )
    db.add(product)
    await db.commit()
    return to_product_out(await _load_product_with_stock(product.product_id, db))


@router.put("/products/{product_id}", response_model=ProductOut)
async def update_product(product_id: int, body: ProductUpdate, db: AsyncSession = Depends(get_db)) -> ProductOut:
    product = await _load_product_with_stock(product_id, db)

    if body.name is not None:
        product.name = body.name
    if body.category is not None:
        product.category = body.category
    if body.price is not None:
        product.price = body.price
    if body.active is not None:
        product.active = body.active
    if body.portions_per_sale is not None:
        if body.portions_per_sale < 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Le nombre de portions par vente doit être d'au moins 1"
            )
        product.portions_per_sale = body.portions_per_sale
    if body.clear_stock_item:
        product.stock_item_id = None
    elif body.stock_item_id is not None:
        await _check_stock_item_exists(body.stock_item_id, db)
        product.stock_item_id = body.stock_item_id

    await db.commit()
    return to_product_out(await _load_product_with_stock(product_id, db))


# ---- Stock ----

@router.get("/stock-items", response_model=list[StockItemOut])
async def list_stock_items(db: AsyncSession = Depends(get_db)) -> list[StockItem]:
    result = await db.execute(select(StockItem).order_by(StockItem.name))
    return list(result.scalars().all())


@router.post("/stock-items", response_model=StockItemOut, status_code=status.HTTP_201_CREATED)
async def create_stock_item(body: StockItemCreate, db: AsyncSession = Depends(get_db)) -> StockItem:
    if body.portions_per_container < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Les portions par contenant doivent être d'au moins 1")
    item = StockItem(
        name=body.name,
        portions_per_container=body.portions_per_container,
        quantity_on_hand=body.quantity_on_hand,
        low_stock_threshold=body.low_stock_threshold,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@router.put("/stock-items/{stock_item_id}", response_model=StockItemOut)
async def update_stock_item(
    stock_item_id: int, body: StockItemUpdate, db: AsyncSession = Depends(get_db)
) -> StockItem:
    item = await db.get(StockItem, stock_item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article de stock introuvable")

    if body.name is not None:
        item.name = body.name
    if body.portions_per_container is not None:
        if body.portions_per_container < 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, "Les portions par contenant doivent être d'au moins 1"
            )
        item.portions_per_container = body.portions_per_container
    if body.low_stock_threshold is not None:
        item.low_stock_threshold = body.low_stock_threshold

    await db.commit()
    await db.refresh(item)
    return item


@router.post("/stock-items/{stock_item_id}/restock", response_model=StockItemOut)
async def restock_item(stock_item_id: int, body: StockAdjustment, db: AsyncSession = Depends(get_db)) -> StockItem:
    """Records a delivery (positive delta) or a correction/breakage
    (negative delta) rather than letting the admin overwrite the raw count,
    so stock changes stay auditable events instead of silent overwrites."""
    item = await db.get(StockItem, stock_item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Article de stock introuvable")

    new_quantity = item.quantity_on_hand + body.delta
    if new_quantity < 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le stock ne peut pas devenir négatif")

    item.quantity_on_hand = new_quantity
    await db.commit()
    await db.refresh(item)
    return item


# ---- Customers ----

@router.post("/customers", response_model=CustomerOut, status_code=status.HTTP_201_CREATED)
async def create_customer(body: CustomerCreate, db: AsyncSession = Depends(get_db)) -> Customer:
    customer = Customer(name=body.name)
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    return customer


@router.put("/customers/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: int, body: CustomerUpdate, db: AsyncSession = Depends(get_db)
) -> Customer:
    customer = await db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")

    customer.name = body.name
    await db.commit()
    await db.refresh(customer)
    return customer


@router.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Hard delete. Any past orders for this customer keep their history —
    `customer_id` just falls back to NULL (displayed as a walk-in), same as
    the ON DELETE SET NULL constraint on orders.customer_id."""
    customer = await db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Client introuvable")

    await db.delete(customer)
    await db.commit()
