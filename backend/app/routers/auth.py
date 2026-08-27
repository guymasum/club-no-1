from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Waiter
from app.schemas import LoginRequest, LoginResponse
from app.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    result = await db.execute(select(Waiter).where(Waiter.username == body.username))
    waiter = result.scalar_one_or_none()

    if waiter is None or not verify_password(body.password, waiter.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(waiter_id=waiter.waiter_id, username=waiter.username, role=waiter.role)
    return LoginResponse(
        access_token=token,
        waiter_id=waiter.waiter_id,
        name=waiter.name,
        role=waiter.role,
    )
