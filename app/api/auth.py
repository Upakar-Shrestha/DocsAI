from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from app.auth.service import authenticate_user
from app.core.security import create_access_token
from app.api.dependencies import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schema import TokenResponse, LoginRequest
from app.core.schema import ResponseEnvelope
from app.core.config import settings

router = APIRouter(tags=["Authentication"])


@router.post("/login", response_model=ResponseEnvelope[TokenResponse])
async def login(loginRequest: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return access token."""
    user = await authenticate_user(db, loginRequest.email, loginRequest.password)
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