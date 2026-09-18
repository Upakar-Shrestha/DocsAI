from datetime import datetime

from pydantic import BaseModel, EmailStr
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    created_at: datetime