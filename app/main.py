from fastapi import FastAPI
import uvicorn
from app.core.config import settings
from app.api.router import api_router   

app = FastAPI(title=settings.APP_NAME, version="0.1.0")
app.include_router(api_router)


def run() -> None:
    """Start the dev server."""
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)       
