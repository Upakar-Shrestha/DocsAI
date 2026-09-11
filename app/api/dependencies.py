from app.infrastructure.database import async_session, Base, engine


async def get_db():
    async with async_session() as session:
        yield session