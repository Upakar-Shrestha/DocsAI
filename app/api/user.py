from app.api.dependencies import get_current_user, get_db
from app.core.schema import ResponseEnvelope
from app.user import service
from app.user.model import User
from app.user.schema import UserCreate, UserResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(tags=["Users"])

@router.get("/me", status_code=200, response_model=ResponseEnvelope[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):

    return ResponseEnvelope(
        success=True,
        message="User retrieved successfully.",
        data=UserResponse(id=current_user.id, email=current_user.email, created_at=current_user.created_at),
    )
