from fastapi import APIRouter
from app.api.document import router as document_router
from app.health.health import router as health_router
from app.api.user import router as user_router
from app.api.auth import router as auth_router

api_router = APIRouter()
api_router.include_router(document_router)
api_router.include_router(health_router)
api_router.include_router(user_router)
api_router.include_router(auth_router)