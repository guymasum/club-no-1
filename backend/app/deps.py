from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Waiter
from app.security import InvalidTokenError, decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Impossible de valider les identifiants",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_waiter(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> Waiter:
    try:
        payload = decode_access_token(token)
    except InvalidTokenError as exc:
        raise CREDENTIALS_EXCEPTION from exc

    waiter_id = payload.get("sub")
    if waiter_id is None:
        raise CREDENTIALS_EXCEPTION

    waiter = await db.get(Waiter, int(waiter_id))
    if waiter is None or not waiter.active:
        # An inactive (removed) waiter loses access immediately, even with a
        # still-unexpired token, rather than waiting out the 8h JWT expiry.
        raise CREDENTIALS_EXCEPTION
    return waiter


async def require_admin(waiter: Waiter = Depends(get_current_waiter)) -> Waiter:
    if waiter.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Rôle administrateur requis",
        )
    return waiter
