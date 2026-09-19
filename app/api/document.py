from app.api.dependencies import get_current_user, get_db
from app.core.schema import ResponseEnvelope
from app.document import service
from app.document.schema import DocumentCreate, DocumentResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.model import User

router = APIRouter(tags=["Documents"])

@router.get("/documents", status_code=200, response_model=ResponseEnvelope[list[DocumentResponse]])
async def get_documents(db: AsyncSession = Depends(get_db)):
    """Get all documents."""
    documents = await service.get_all_documents(db)
    return ResponseEnvelope(
        success=True,
        message="Documents retrieved successfully",
        data=documents,
    )   

@router.post("/documents", status_code=201, response_model=ResponseEnvelope[DocumentResponse])
async def create_document(document: DocumentCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new document."""
    new_document = await service.create_document(db, document, current_user.id)
    return ResponseEnvelope(
        success=True,
        message="Document created successfully.",
        data=new_document,
    )
          