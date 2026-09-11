from app.document.model import Document
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def get_all_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document))
    return result.scalars().all()