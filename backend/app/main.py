from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, auth, bills, catalog, orders

# Schema is now owned by Alembic migrations (see migrations/), not
# create_all() on startup — the Docker image runs `alembic upgrade head`
# before uvicorn starts (see Dockerfile). Local dev without Docker: run
# `alembic upgrade head` once against your DATABASE_URL before starting
# the app, and again after pulling any migration that adds one.
app = FastAPI(title="Club No. 1 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://club-no-1-frontend-production.up.railway.app",
        "http://localhost:3000",  # local Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(orders.router)
app.include_router(bills.router)
app.include_router(admin.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
