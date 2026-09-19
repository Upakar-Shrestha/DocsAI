from fastapi import Depends, HTTPException
import jwt
from sqlalchemy import select
from app.user.model import User
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.database import async_session
from app.core.config import settings
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer()

async def get_db():
    async with async_session() as session:
        yield session

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme), db: AsyncSession = Depends(get_db)) -> User:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user