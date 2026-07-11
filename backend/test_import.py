import asyncio
from app.utils.csv_importer import import_csv
from app.database import async_session

async def test():
    with open(r'D:\AARU\Personas\personas_20000.csv', 'rb') as f:
        file_content = f.read()
    
    async with async_session() as db:
        res = await import_csv(db, file_content, "personas_20000.csv", "test_user_id", "test_project_id")
        print(res)

if __name__ == "__main__":
    asyncio.run(test())
