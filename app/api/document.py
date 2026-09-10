from uuid import uuid4

from app.document.schema import DocumentCreate, DocumentResponse
from fastapi import APIRouter

router = APIRouter(tags=["Documents"])

@router.get("/documents", status_code=200)
async def get_documents():
    """Get all documents."""
    return {"documents": []}

@router.post("/documents", status_code=201, response_model=DocumentResponse)
async def create_document(document: DocumentCreate):
    """Create a new document."""
    return DocumentResponse(
        id=str(uuid4()),
        title=document.title,
        content=document.content,
        author_id=document.author_id,
    )

