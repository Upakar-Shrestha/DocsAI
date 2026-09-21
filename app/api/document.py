import uuid
from app.api.dependencies import get_current_user, get_db
from app.core.schema import ResponseEnvelope
from app.document import service
from app.document.service import save_uploaded_file, create_document, get_all_documents
from app.document.schema import DocumentResponse
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.model import User

router = APIRouter(tags=["Documents"])

@router.get("/documents", status_code=200, response_model=ResponseEnvelope[list[DocumentResponse]])
async def get_documents(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get all documents."""
    documents = await service.get_all_documents(db, current_user.id)
    return ResponseEnvelope(
        success=True,
        message="Documents retrieved successfully",
        data=documents,
    )   

@router.post("/documents", status_code=201, response_model=ResponseEnvelope[DocumentResponse])
async def create_document(
    title: str = Form(...),
    file: UploadFile = File(...), 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)):

    """Create a new document."""

    document_id = uuid.uuid4()

    file_path = await service.save_uploaded_file(
        file=file,
        document_id=document_id,
    )

    new_document = await service.create_document(
        db=db,
        document_id=document_id,
        title=title,
        file_path=file_path,
        user_id=current_user.id,
    )

    return ResponseEnvelope(
        success=True,
        message="Document created successfully.",
        data=new_document,
    )
          