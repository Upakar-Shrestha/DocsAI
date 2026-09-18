from app.user.model import User
from app.user.schema import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password

async def create_user(db: AsyncSession, user: UserCreate) -> User:
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user