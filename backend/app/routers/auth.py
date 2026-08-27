from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import get_current_waiter
from app.models import Waiter
from app.schemas import ChangePasswordRequest, LoginRequest, LoginResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> LoginResponse:
    result = await db.execute(select(Waiter).where(Waiter.username == body.username))
    waiter = result.scalar_one_or_none()

    if waiter is None or not verify_password(body.password, waiter.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nom d'utilisateur ou mot de passe invalide",
        )

    if not waiter.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ce compte a été désactivé",
        )

    token = create_access_token(waiter_id=waiter.waiter_id, username=waiter.username, role=waiter.role)
    return LoginResponse(
        access_token=token,
        waiter_id=waiter.waiter_id,
        name=waiter.name,
        role=waiter.role,
    )


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_own_password(
    body: ChangePasswordRequest,
    waiter: Waiter = Depends(get_current_waiter),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Self-service password change — any authenticated waiter, for their own
    account only. (Admins setting *another* waiter's password go through
    PUT /admin/waiters/{id} instead, which doesn't require the old password.)"""
    if not verify_password(body.current_password, waiter.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Mot de passe actuel incorrect")

    waiter.password_hash = hash_password(body.new_password)
    await db.commit()
