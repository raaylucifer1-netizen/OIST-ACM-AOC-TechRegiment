import asyncio
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, async_session, init_db
from app.models.user import User
from app.utils.csv_importer import import_from_path
from app.auth.hashing import hash_password

async def seed():
    # Make sure tables exist
    import app.models
    await init_db()

    async with async_session() as db:
        # Create a default user
        user = User(
            email="admin@personax.ai",
            full_name="Admin User",
            hashed_password=hash_password("admin123"),
            is_verified=True,
            role="admin"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"Created admin user with ID: {user.id}")

        csv_path = r"D:\AARU\Personas\personas_20000.csv"
        if os.path.exists(csv_path):
            print(f"Importing personas from {csv_path}...")
            result = await import_from_path(db, csv_path, user.id)
            print("Import result:", result)
        else:
            print(f"CSV file not found at {csv_path}")

if __name__ == "__main__":
    asyncio.run(seed())
