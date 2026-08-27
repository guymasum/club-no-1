import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Product, Waiter
from app.security import hash_password

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)

    # SQLite ignores foreign keys (including ON DELETE actions) unless told
    # otherwise, so the customer-delete -> orders.customer_id=NULL behavior
    # would silently no-op in tests without this.
    @event.listens_for(engine.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with session_maker() as session:
        yield session

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def seeded(db_session):
    admin = Waiter(name="Josee", username="josee", password_hash=hash_password("clubno1"), role="admin")
    waiter = Waiter(name="Mimi", username="mimi", password_hash=hash_password("clubno1"), role="waiter")
    food = Product(name="Brochettes de langues", category="food", price=8.00)
    drink = Product(name="Primus", category="drink", price=3.00)
    db_session.add_all([admin, waiter, food, drink])
    await db_session.commit()
    await db_session.refresh(admin)
    await db_session.refresh(waiter)
    await db_session.refresh(food)
    await db_session.refresh(drink)
    return {"admin": admin, "waiter": waiter, "food": food, "drink": drink}


async def auth_headers(client: AsyncClient, username: str, password: str = "clubno1") -> dict[str, str]:
    resp = await client.post("/auth/login", json={"username": username, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
