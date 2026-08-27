from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_waiter
from app.models import Customer, Order, OrderItem, Product, Waiter
from app.schemas import OrderCreate, OrderItemCreate, OrderItemOut, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"], dependencies=[Depends(get_current_waiter)])


def _to_order_out(order: Order) -> OrderOut:
    return OrderOut(
        order_id=order.order_id,
        waiter_id=order.waiter_id,
        waiter_name=order.waiter.name,
        customer_id=order.customer_id,
        customer_name=order.customer.name if order.customer else None,
        status=order.status,
        created_at=order.created_at,
        items=[
            OrderItemOut(
                item_id=item.item_id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
            )
            for item in order.items
        ],
    )


async def _get_open_order(order_id: int, db: AsyncSession) -> Order:
    result = await db.execute(
        select(Order)
        .where(Order.order_id == order_id)
        .options(
            selectinload(Order.waiter),
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        # Needed because this helper is called more than once per request (e.g.
        # add_item loads, mutates, commits, then reloads) and expire_on_commit
        # is False, so the identity map would otherwise hand back a stale
        # `items` collection instead of re-querying it.
        .execution_options(populate_existing=True)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


@router.get("", response_model=list[OrderOut])
async def list_open_orders(db: AsyncSession = Depends(get_db)) -> list[OrderOut]:
    result = await db.execute(
        select(Order)
        .where(Order.status == "open")
        .options(
            selectinload(Order.waiter),
            selectinload(Order.customer),
            selectinload(Order.items).selectinload(OrderItem.product),
        )
        .order_by(Order.created_at.desc())
    )
    return [_to_order_out(o) for o in result.scalars().all()]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)) -> OrderOut:
    order = await _get_open_order(order_id, db)
    return _to_order_out(order)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    waiter: Waiter = Depends(get_current_waiter),
    db: AsyncSession = Depends(get_db),
) -> OrderOut:
    if body.customer_id is not None:
        customer = await db.get(Customer, body.customer_id)
        if customer is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Customer not found")

    order = Order(waiter_id=waiter.waiter_id, customer_id=body.customer_id, status="open")
    db.add(order)
    await db.commit()
    return await get_order(order.order_id, db)


@router.post("/{order_id}/items", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def add_item(order_id: int, body: OrderItemCreate, db: AsyncSession = Depends(get_db)) -> OrderOut:
    order = await _get_open_order(order_id, db)
    if order.status != "open":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order is already billed")
    if body.quantity < 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Quantity must be at least 1")

    product = await db.get(Product, body.product_id)
    if product is None or not product.active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found or inactive")

    db.add(
        OrderItem(
            order_id=order_id,
            product_id=product.product_id,
            quantity=body.quantity,
            unit_price=product.price,
        )
    )
    await db.commit()
    return await get_order(order_id, db)


@router.delete("/{order_id}/items/{item_id}", response_model=OrderOut)
async def remove_item(order_id: int, item_id: int, db: AsyncSession = Depends(get_db)) -> OrderOut:
    order = await _get_open_order(order_id, db)
    if order.status != "open":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Order is already billed")

    item = next((i for i in order.items if i.item_id == item_id), None)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Item not found on this order")

    await db.delete(item)
    await db.commit()
    return await get_order(order_id, db)
