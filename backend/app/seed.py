"""Seed the database with the initial waiters and menu.

Usage: python -m app.seed
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal, init_models
from app.models import Product, Waiter
from app.security import hash_password

DEFAULT_PASSWORD = "clubno1"

WAITERS = [
    {"name": "Josée", "username": "josee", "role": "admin"},
    {"name": "Mimi", "username": "mimi", "role": "waiter"},
    {"name": "Victor", "username": "victor", "role": "waiter"},
]

PRODUCTS = [
    {"name": "Brochettes de langues", "category": "food", "price": 8.00},
    {"name": "Brochette de musoso", "category": "food", "price": 7.00},
    {"name": "Brochettes de poisson", "category": "food", "price": 9.00},
    {"name": "Primus (beer)", "category": "drink", "price": 3.00},
    {"name": "Skol (beer)", "category": "drink", "price": 3.00},
    {"name": "House wine (glass)", "category": "drink", "price": 5.00},
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

        for p in PRODUCTS:
            existing = await db.execute(select(Product).where(Product.name == p["name"]))
            if existing.scalar_one_or_none() is not None:
                continue
            db.add(Product(name=p["name"], category=p["category"], price=p["price"]))

        await db.commit()
    print("Seed complete. Default password for all waiters:", DEFAULT_PASSWORD)


if __name__ == "__main__":
    asyncio.run(seed())
