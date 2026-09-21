import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.document.model import Document, DocumentStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.document.schema import DocumentCreate
from app.core.config import settings

async def get_all_documents(db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
    result = await db.execute(select(Document).where(Document.user_id == user_id))
    return result.scalars().all()

async def create_document(db: AsyncSession,
    document_id: uuid.UUID,
    title: str,
    file_path: str,
    user_id: uuid.UUID,
) -> Document:
    new_document = Document(
        id=document_id,
        title=title,
        file_path=file_path,
        content=None,
        user_id=user_id,
        status=DocumentStatus.PENDING,
    )
    

    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)
    return new_document

ALLOWED_CONTENT_TYPES = {"application/pdf"}

async def save_uploaded_file(file: UploadFile, document_id: uuid.UUID) -> str:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_content = await file.read()

    if len(file_content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must not exceed 10 MB.",
        )

    original_filename = file.filename or ""
    extension = Path(original_filename).suffix.lower()

    if extension != ".pdf":
        raise HTTPException(
            status_code=400,
            detail="Only .pdf files are allowed.",
        )

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Generate safe filename
    filename = f"{document_id}{extension}"

    # Create the complete file path
    file_path = upload_dir / filename

    # Save the file
    file_path.write_bytes(file_content)

    # Return path for database
    return str(file_path)