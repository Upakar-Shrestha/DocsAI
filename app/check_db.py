import asyncio

from sqlalchemy import text

from app.infrastructure.database import engine


async def check():
    async with engine.connect() as conn:
        result = await conn.execute(
            text("""
                SELECT
                    current_database(),
                    current_schema()
            """)
        )

        print(result.fetchone())

        result = await conn.execute(
            text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
        )

        print("Tables:")
        for row in result:
            print(row[0])

    await engine.dispose()


asyncio.run(check())