import uuid
from app.api.dependencies import get_current_user, get_db
from app.core.schema import ResponseEnvelope
from app.document import service
from app.document.schema import ChatRequest, ChatResponse, ChatSourceChunk, DocumentResponse
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import BackgroundTasks

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
    background_tasks: BackgroundTasks = None,
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

    background_tasks.add_task(service.process_document, new_document.id)

    return ResponseEnvelope(
        success=True,
        message="Document created successfully.",
        data=new_document,
    )

@router.post("/documents/{document_id}/chat", response_model=ResponseEnvelope[ChatResponse])
async def chat_with_document(
    document_id: uuid.UUID,
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
   ):
    answer, chunks = await service.answer_question(db, document_id, chat_request.question, current_user.id)
    return ResponseEnvelope(
        success=True,
        message="Answer generated successfully.",
        data=ChatResponse(
            answer=answer,
            sources=[ChatSourceChunk(chunk_index=c.chunk_index, content=c.content) for c in chunks],
        ),
    ) 