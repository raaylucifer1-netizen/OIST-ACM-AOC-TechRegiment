import asyncio
import openpyxl
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import async_session
from app.models.user import User
from app.models.persona import Persona
import uuid

async def import_personas_all_users(excel_path: str):
    print("Reading users from the database...")
    async with async_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        if not users:
            print("No users found in database. Cannot import personas. Please register first.")
            return
        print(f"Found {len(users)} users: {[u.email for u in users]}")

    print(f"Loading Excel file {excel_path} once...")
    wb = openpyxl.load_workbook(excel_path, read_only=True)
    sheet = wb.active
    
    print("Parsing rows into memory...")
    headers = []
    rows_data = []
    
    for idx, row in enumerate(sheet.iter_rows(values_only=True)):
        if idx == 0:
            headers = [str(h).strip() if h else "" for h in row]
            continue
        
        row_dict = dict(zip(headers, row))
        if not row_dict.get('persona_id'):
            continue # Skip empty rows
        rows_data.append(row_dict)
    
    total_rows = len(rows_data)
    print(f"Loaded {total_rows} personas from Excel sheet.")

    def parse_int(val):
        if val is None or val == '':
            return 0
        try:
            return int(float(val))
        except:
            return 0
            
    def parse_str(val):
        if val is None:
            return ''
        return str(val).strip()

    # We will do batch insert per user
    batch_size = 2000
    for user in users:
        print(f"\nProcessing personas for user: {user.email}")
        
        async with async_session() as db:
            # Delete existing personas for this user to avoid duplication
            print(f"Cleaning existing personas for user {user.email}...")
            await db.execute(delete(Persona).where(Persona.user_id == user.id))
            await db.commit()
            
            # Batch insertion
            batch = []
            count = 0
            for row_dict in rows_data:
                p = Persona(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    project_id=None,
                    persona_id=parse_str(row_dict.get('persona_id')),
                    age=parse_int(row_dict.get('age')),
                    gender=parse_str(row_dict.get('gender')),
                    city=parse_str(row_dict.get('city')),
                    state=parse_str(row_dict.get('state')),
                    education=parse_str(row_dict.get('education')),
                    occupation=parse_str(row_dict.get('occupation')),
                    income_inr=parse_int(row_dict.get('income_inr')),
                    language=parse_str(row_dict.get('language')),
                    marital_status=parse_str(row_dict.get('marital_status')),
                    children=parse_int(row_dict.get('children')),
                    lifestyle=parse_str(row_dict.get('lifestyle')),
                    shopping_frequency=parse_str(row_dict.get('shopping_frequency')),
                    online_shopping_pct=parse_int(row_dict.get('online_shopping_pct')),
                    offline_shopping_pct=parse_int(row_dict.get('offline_shopping_pct')),
                    payment_method=parse_str(row_dict.get('payment_method')),
                    vehicle=parse_str(row_dict.get('vehicle')),
                    technology_adoption=parse_str(row_dict.get('technology_adoption')),
                    health_consciousness=parse_int(row_dict.get('health_consciousness')),
                    food_preference=parse_str(row_dict.get('food_preference')),
                    political_interest=parse_str(row_dict.get('political_interest')),
                    social_media_usage=parse_int(row_dict.get('social_media_usage')),
                    brand_loyalty=parse_int(row_dict.get('brand_loyalty')),
                    price_sensitivity=parse_int(row_dict.get('price_sensitivity')),
                    risk_taking=parse_int(row_dict.get('risk_taking')),
                    impulse_buying=parse_int(row_dict.get('impulse_buying')),
                    discount_preference=parse_int(row_dict.get('discount_preference')),
                    premium_preference=parse_int(row_dict.get('premium_preference')),
                    preferred_brand=parse_str(row_dict.get('preferred_brand')),
                    communication_style=parse_str(row_dict.get('communication_style')),
                    response_length=parse_str(row_dict.get('response_length')),
                    openness=parse_int(row_dict.get('openness')),
                    conscientiousness=parse_int(row_dict.get('conscientiousness')),
                    extraversion=parse_int(row_dict.get('extraversion')),
                    agreeableness=parse_int(row_dict.get('agreeableness')),
                    neuroticism=parse_int(row_dict.get('neuroticism')),
                    confidence=parse_int(row_dict.get('confidence')),
                    optimism=parse_int(row_dict.get('optimism')),
                    patience=parse_int(row_dict.get('patience')),
                    curiosity=parse_int(row_dict.get('curiosity')),
                    practicality=parse_int(row_dict.get('practicality')),
                    emotional_score=parse_int(row_dict.get('emotional_score')),
                )
                batch.append(p)
                count += 1
                
                if len(batch) >= batch_size:
                    db.add_all(batch)
                    await db.commit()
                    print(f"Inserted {count}/{total_rows} personas for {user.email}...")
                    batch = []
            
            if batch:
                db.add_all(batch)
                await db.commit()
                print(f"Completed: Inserted {count}/{total_rows} personas for {user.email}.")

    print("\nAll users' personas imported successfully!")

if __name__ == "__main__":
    import sys
    excel_path = sys.argv[1] if len(sys.argv) > 1 else r"D:\AARU\Personas\personas_20000(1).xlsx"
    asyncio.run(import_personas_all_users(excel_path))
