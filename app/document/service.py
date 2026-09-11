from app.document.model import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.document.schema import DocumentCreate

async def get_all_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document))
    return result.scalars().all()

async def create_document(db: AsyncSession, document: DocumentCreate) -> Document:
    new_document = Document(
        title=document.title,
        content=document.content,
        user_id=document.user_id,
    )

    db.add(new_document)
    await db.commit()
    await db.refresh(new_document)
    return new_document