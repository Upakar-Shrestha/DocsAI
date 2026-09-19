from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password
from app.user.model import User


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    user = await db.execute(
        select(User).where(User.email == email)
    )
    user = user.scalar_one_or_none()
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user