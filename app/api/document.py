from app.api.dependencies import get_db
from app.core.schema import ResponseEnvelope
from app.document import service
from app.document.schema import DocumentCreate, DocumentResponse
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

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
async def create_document(document: DocumentCreate, db: AsyncSession = Depends(get_db)):
    """Create a new document."""
    new_document = await service.create_document(db, document)
    return ResponseEnvelope(
        success=True,
        message="Document created successfully.",
        data=new_document,
    )
          