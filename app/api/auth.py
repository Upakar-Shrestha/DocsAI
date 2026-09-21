from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from app.auth.service import authenticate_user, register_user
from app.core.security import create_access_token
from app.api.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schema import RegisterRequest, TokenResponse, LoginRequest
from app.core.schema import ResponseEnvelope
from app.core.config import settings
from app.user.model import User

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
async def login(login_request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access token."""
    user = await authenticate_user(db, login_request.email, login_request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    return ResponseEnvelope(
        success=True,
        message="Login successful.",
        data={"access_token": access_token,
            "token_type": "bearer",
        },
    )

@router.post("/register", response_model=ResponseEnvelope[TokenResponse])
async def register(register_request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        new_user = await register_user(db, register_request.email, register_request.password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    access_token = create_access_token(
        data={"sub": str(new_user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return ResponseEnvelope(success=True, message="Registration successful.", data={"access_token": access_token, "token_type": "bearer"})