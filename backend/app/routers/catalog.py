from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_waiter
from app.models import Customer, Product, Waiter
from app.schemas import CustomerOut, ProductOut

router = APIRouter(dependencies=[Depends(get_current_waiter)], tags=["catalog"])


@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(db: AsyncSession = Depends(get_db)) -> list[Customer]:
    result = await db.execute(select(Customer).order_by(Customer.name))
    return list(result.scalars().all())


@router.get("/products", response_model=list[ProductOut])
async def list_products(db: AsyncSession = Depends(get_db)) -> list[Product]:
    result = await db.execute(
        select(Product).where(Product.active.is_(True)).order_by(Product.category, Product.name)
    )
    return list(result.scalars().all())
