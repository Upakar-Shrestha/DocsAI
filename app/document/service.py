import asyncio
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile
from app.document.model import Chunk, Document, DocumentStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.document.prompts import build_rag_prompt
from app.document.schema import DocumentCreate
from app.core.config import settings
from pypdf import PdfReader
from app.external.llm import generate_answer
from app.infrastructure.database import async_session
from app.external.embeddings import get_embedding


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

def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

async def process_document(document_id: uuid.UUID) -> None:
    async with async_session() as db:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if document is None:
            return  # document was deleted before processing ran; nothing to do

        document.status = DocumentStatus.PROCESSING
        await db.commit()

        try:
            text = extract_text_from_pdf(document.file_path)
            chunks = chunk_text(text)

            for index, chunk_content in enumerate(chunks):
                embedding = await asyncio.to_thread(get_embedding, chunk_content)
                db.add(Chunk(
                    document_id=document.id,
                    content=chunk_content,
                    chunk_index=index,
                    embedding=embedding,
                ))

            document.content = text
            document.status = DocumentStatus.COMPLETED
            await db.commit()

        except Exception:
            document.status = DocumentStatus.FAILED
            await db.commit()
            raise

async def similarity_search(
        db: AsyncSession, query_embedding: list[float], 
        user_id: uuid.UUID, 
        top_k: int = 5,
        document_id: uuid.UUID | None = None
) -> list[Chunk]:
    
    query = (
    select(Chunk)
    .join(Document)
    .where(Document.user_id == user_id)
    )
    if document_id is not None:
        query = query.where(Chunk.document_id == document_id)

    result = await db.execute(
        query.order_by(Chunk.embedding.cosine_distance(query_embedding)).limit(top_k)
    )
    return result.scalars().all()

async def answer_question(db: AsyncSession, document_id: uuid.UUID, question: str, user_id: uuid.UUID) -> tuple[str, list[Chunk]]:
    question_embedding = await asyncio.to_thread(get_embedding, question)
    relevant_chunks = await similarity_search(db, question_embedding, user_id, document_id=document_id, top_k=5)

    if not relevant_chunks:
        return "No relevant content found for this document.", []

    context = "\n\n".join(chunk.content for chunk in relevant_chunks)
    prompt = build_rag_prompt(context, question)

    answer = await asyncio.to_thread(generate_answer, prompt)
    return answer, relevant_chunks
