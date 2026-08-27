from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.deps import get_current_waiter
from app.models import Customer, Product, Waiter
from app.product_utils import to_product_out
from app.schemas import CustomerOut, ProductOut

router = APIRouter(dependencies=[Depends(get_current_waiter)], tags=["catalog"])


@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(db: AsyncSession = Depends(get_db)) -> list[Customer]:
    result = await db.execute(select(Customer).order_by(Customer.name))
    return list(result.scalars().all())


@router.get("/products", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[ProductOut]:
    result = await db.execute(
        select(Product)
        .where(Product.active.is_(True))
        .options(selectinload(Product.stock_item))
        .order_by(Product.category, Product.name)
    )
    return [to_product_out(p) for p in result.scalars().all()]
