import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.utils.csv_importer import import_from_path
from app.models.user import User
from sqlalchemy import select

async def test_import():
    async with async_session() as session:
        # Get first user
        result = await session.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            print("No users found.")
            return
            
        print(f"Testing import for user: {user.email}")
        res = await import_from_path(session, r"d:\AARU\backend\data\personas_20000.csv", user.id)
        print(res)

if __name__ == "__main__":
    asyncio.run(test_import())
