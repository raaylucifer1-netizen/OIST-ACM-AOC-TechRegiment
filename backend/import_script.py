import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import async_session
from app.utils.csv_importer import import_from_path

async def main():
    user_id = "212b108c-52c5-4c6f-bffb-13d5ab3868db"
    filepath = r"D:\AARU\Personas\personas_20000(1).xlsx"
    
    async with async_session() as db:
        print("Starting import...")
        result = await import_from_path(db, filepath, user_id)
        print("Import complete:", result)

if __name__ == "__main__":
    asyncio.run(main())
