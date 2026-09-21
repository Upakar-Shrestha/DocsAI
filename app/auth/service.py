from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password
from app.user.model import User
from app.user.schema import UserCreate
from app.user.service import create_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await db.execute(
        select(User).where(User.email == email)
    )
    user = user.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user

async def register_user(db: AsyncSession, email: str, password: str) -> User:
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none() is not None:
        raise ValueError("Email already registered")  
    return await create_user(db, UserCreate(email=email, password=password))