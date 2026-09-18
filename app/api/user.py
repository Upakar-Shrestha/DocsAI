from app.api.dependencies import get_db
from app.core.schema import ResponseEnvelope
from app.user import service
from app.user.schema import UserCreate, UserResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Users"])

@router.post("/users", status_code=201, response_model=ResponseEnvelope[UserResponse])
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user."""
    new_user = await service.create_user(db, user)
    return ResponseEnvelope(
        success=True,
        message="User created successfully.",
        data=new_user,
    )

