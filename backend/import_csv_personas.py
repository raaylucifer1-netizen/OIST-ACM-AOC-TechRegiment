r"""
Import all 20,000 personas from the CSV file at D:\AARU\Personas\personas_20000.csv
into the database for ALL registered users.

Usage:
    python import_csv_personas.py
    python import_csv_personas.py "D:\AARU\Personas\personas_20000.csv"
"""

import asyncio
import csv
import sys
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.database import async_session
from app.models.user import User
from app.models.persona import Persona


def parse_int(val):
    """Safely parse a value to int."""
    if val is None or str(val).strip() == '':
        return 0
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return 0


def parse_str(val):
    """Safely parse a value to stripped string."""
    if val is None:
        return ''
    return str(val).strip()


async def import_csv_personas(csv_path: str):
    """Read the CSV and import all personas for every user in the DB."""

    # -- Step 1: Get all users --
    async with async_session() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        if not users:
            print("[ERROR] No users found in database. Register first, then re-run.")
            return
        print(f"[OK] Found {len(users)} user(s): {[u.email for u in users]}")

    # -- Step 2: Read entire CSV into memory --
    print(f"\n[INFO] Reading CSV: {csv_path}")
    rows_data: list[dict] = []

    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("persona_id") or "").strip()
            if not pid:
                continue
            rows_data.append(row)

    total_rows = len(rows_data)
    print(f"   Loaded {total_rows:,} personas from CSV.\n")

    if total_rows == 0:
        print("[ERROR] No data rows found. Check your CSV file.")
        return

    # -- Step 3: For each user, clear old data & batch-insert --
    batch_size = 2000

    for user in users:
        print(f"[USER] Processing user: {user.email}")

        async with async_session() as db:
            # Count existing personas
            count_result = await db.execute(
                select(func.count(Persona.id)).where(Persona.user_id == user.id)
            )
            existing = count_result.scalar() or 0
            print(f"   Existing personas: {existing:,}")

            # Delete existing to avoid duplicates
            if existing > 0:
                print(f"   [DELETE] Removing {existing:,} old personas...")
                await db.execute(delete(Persona).where(Persona.user_id == user.id))
                await db.commit()

            # Batch insert
            batch: list[Persona] = []
            count = 0

            for row in rows_data:
                p = Persona(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    project_id=None,
                    persona_id=parse_str(row.get("persona_id")),
                    age=parse_int(row.get("age")),
                    gender=parse_str(row.get("gender")),
                    city=parse_str(row.get("city")),
                    state=parse_str(row.get("state")),
                    education=parse_str(row.get("education")),
                    occupation=parse_str(row.get("occupation")),
                    income_inr=parse_int(row.get("income_inr")),
                    language=parse_str(row.get("language")),
                    marital_status=parse_str(row.get("marital_status")),
                    children=parse_int(row.get("children")),
                    lifestyle=parse_str(row.get("lifestyle")),
                    shopping_frequency=parse_str(row.get("shopping_frequency")),
                    online_shopping_pct=parse_int(row.get("online_shopping_pct")),
                    offline_shopping_pct=parse_int(row.get("offline_shopping_pct")),
                    payment_method=parse_str(row.get("payment_method")),
                    vehicle=parse_str(row.get("vehicle")),
                    technology_adoption=parse_str(row.get("technology_adoption")),
                    health_consciousness=parse_int(row.get("health_consciousness")),
                    food_preference=parse_str(row.get("food_preference")),
                    political_interest=parse_str(row.get("political_interest")),
                    social_media_usage=parse_int(row.get("social_media_usage")),
                    brand_loyalty=parse_int(row.get("brand_loyalty")),
                    price_sensitivity=parse_int(row.get("price_sensitivity")),
                    risk_taking=parse_int(row.get("risk_taking")),
                    impulse_buying=parse_int(row.get("impulse_buying")),
                    discount_preference=parse_int(row.get("discount_preference")),
                    premium_preference=parse_int(row.get("premium_preference")),
                    preferred_brand=parse_str(row.get("preferred_brand")),
                    communication_style=parse_str(row.get("communication_style")),
                    response_length=parse_str(row.get("response_length")),
                    openness=parse_int(row.get("openness")),
                    conscientiousness=parse_int(row.get("conscientiousness")),
                    extraversion=parse_int(row.get("extraversion")),
                    agreeableness=parse_int(row.get("agreeableness")),
                    neuroticism=parse_int(row.get("neuroticism")),
                    confidence=parse_int(row.get("confidence")),
                    optimism=parse_int(row.get("optimism")),
                    patience=parse_int(row.get("patience")),
                    curiosity=parse_int(row.get("curiosity")),
                    practicality=parse_int(row.get("practicality")),
                    emotional_score=parse_int(row.get("emotional_score")),
                )
                batch.append(p)
                count += 1

                if len(batch) >= batch_size:
                    db.add_all(batch)
                    await db.commit()
                    print(f"   [OK] Inserted {count:,} / {total_rows:,} personas...")
                    batch = []

            # Insert remaining batch
            if batch:
                db.add_all(batch)
                await db.commit()

            print(f"   [DONE] Imported {count:,} personas for {user.email}\n")

    print("=" * 60)
    print(f"[SUCCESS] All done! {total_rows:,} personas imported for {len(users)} user(s).")
    print("=" * 60)


if __name__ == "__main__":
    csv_path = (
        sys.argv[1]
        if len(sys.argv) > 1
        else r"D:\AARU\Personas\personas_20000.csv"
    )
    asyncio.run(import_csv_personas(csv_path))
