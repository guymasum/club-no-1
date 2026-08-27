"""Seed the database with the initial waiters, menu, and stock.

Usage: python -m app.seed
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_models
from app.models import Product, StockItem, Waiter
from app.security import hash_password

DEFAULT_PASSWORD = "clubno1"

WAITERS = [
    {"name": "Josée", "username": "josee", "role": "admin"},
    {"name": "Mimi", "username": "mimi", "role": "waiter"},
    {"name": "Victor", "username": "victor", "role": "waiter"},
]

FOOD_PRODUCTS = [
    {"name": "Brochettes de langues", "price": 8.00},
    {"name": "Brochette de musoso", "price": 7.00},
    {"name": "Brochettes de poisson", "price": 9.00},
]

# Each entry is one stock item (one physical product line) plus the one or
# more sellable products drawn from it. portions_per_container=1 for beer
# means "container" and "portion" are the same thing (a bottle IS a sale).
# Wine/whisky pour multiple portions (glasses) per bottle, so the bottle-sale
# and glass-sale products share a stock item but consume different amounts.
STOCKED_PRODUCTS = [
    {
        "stock_name": "Primus",
        "portions_per_container": 1,
        "quantity_on_hand": 48,
        "sales": [{"name": "Primus (beer)", "category": "beer", "price": 1000, "portions_per_sale": 1}],
    },
    {
        "stock_name": "Skol",
        "portions_per_container": 1,
        "quantity_on_hand": 48,
        "sales": [{"name": "Skol (beer)", "category": "beer", "price": 1000, "portions_per_sale": 1}],
    },
    {
        "stock_name": "Vin maison",
        "portions_per_container": 5,  # 5 glasses per bottle
        "quantity_on_hand": 15,  # 3 bottles
        "sales": [
            {"name": "Vin maison (verre)", "category": "wine", "price": 3500, "portions_per_sale": 1},
            {"name": "Vin maison (bouteille)", "category": "wine", "price": 15000, "portions_per_sale": 5},
        ],
    },
    {
        "stock_name": "Johnnie Walker Red",
        "portions_per_container": 15,  # 15 shots per bottle
        "quantity_on_hand": 30,  # 2 bottles
        "sales": [
            {"name": "Johnnie Walker Red (verre)", "category": "whisky", "price": 4000, "portions_per_sale": 1},
            {
                "name": "Johnnie Walker Red (bouteille)",
                "category": "whisky",
                "price": 45000,
                "portions_per_sale": 15,
            },
        ],
    },
]


async def seed() -> None:
    await init_models()
    async with AsyncSessionLocal() as db:
        for w in WAITERS:
            existing = await db.execute(select(Waiter).where(Waiter.username == w["username"]))
            if existing.scalar_one_or_none() is not None:
                continue
            db.add(
                Waiter(
                    name=w["name"],
                    username=w["username"],
                    password_hash=hash_password(DEFAULT_PASSWORD),
                    role=w["role"],
                )
            )

        for p in FOOD_PRODUCTS:
            existing = await db.execute(select(Product).where(Product.name == p["name"]))
            if existing.scalar_one_or_none() is not None:
                continue
            db.add(Product(name=p["name"], category="food", price=p["price"]))

        for entry in STOCKED_PRODUCTS:
            result = await db.execute(select(StockItem).where(StockItem.name == entry["stock_name"]))
            stock_item = result.scalar_one_or_none()
            if stock_item is None:
                stock_item = StockItem(
                    name=entry["stock_name"],
                    portions_per_container=entry["portions_per_container"],
                    quantity_on_hand=entry["quantity_on_hand"],
                )
                db.add(stock_item)
                await db.flush()  # assigns stock_item.stock_item_id for the products below

            for sale in entry["sales"]:
                existing = await db.execute(select(Product).where(Product.name == sale["name"]))
                if existing.scalar_one_or_none() is not None:
                    continue
                db.add(
                    Product(
                        name=sale["name"],
                        category=sale["category"],
                        price=sale["price"],
                        stock_item_id=stock_item.stock_item_id,
                        portions_per_sale=sale["portions_per_sale"],
                    )
                )

        await db.commit()
    print("Seed complete. Default password for all waiters:", DEFAULT_PASSWORD)


if __name__ == "__main__":
    asyncio.run(seed())
