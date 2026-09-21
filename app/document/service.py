import uuid
from app.document.model import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.document.schema import DocumentCreate

async def get_all_documents(db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
    result = await db.execute(select(Document).where(Document.user_id == user_id))
    return result.scalars().all()

async def create_document(db: AsyncSession, document: DocumentCreate, user_id: uuid.UUID) -> Document:
    new_document = Document(
        title=document.title,
        content=document.content,
        user_id=user_id,
    )

    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)
    return new_document