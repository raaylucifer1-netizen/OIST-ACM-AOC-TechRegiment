"""
Fix duplicate personas and ensure all 20,000 unique personas from
D:\AARU\Personas\personas_20000.csv are imported for both main users.
Run with: python scratch/fix_and_import.py
"""
import sqlite3
import csv
import uuid
from datetime import datetime, timezone

DB_PATH = r"D:\AARU\backend\data\personax.db"
CSV_PATH = r"D:\AARU\Personas\personas_20000.csv"

# Users to import for
USERS = [
    ("212b108c-52c5-4c6f-bffb-13d5ab3868db", "raaylucifer1@gmail.com"),
    ("25222d3d-990b-40db-b5de-49dc151337c1", "raaylucifer@gmail.com"),
]

INT_COLS = [
    "age", "income_inr", "children", "online_shopping_pct", "offline_shopping_pct",
    "health_consciousness", "social_media_usage", "brand_loyalty", "price_sensitivity",
    "risk_taking", "impulse_buying", "discount_preference", "premium_preference",
    "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism",
    "confidence", "optimism", "patience", "curiosity", "practicality", "emotional_score",
]

COLUMNS = [
    "persona_id", "age", "gender", "city", "state", "education", "occupation",
    "income_inr", "language", "marital_status", "children", "lifestyle",
    "shopping_frequency", "online_shopping_pct", "offline_shopping_pct",
    "payment_method", "vehicle", "technology_adoption", "health_consciousness",
    "food_preference", "political_interest", "social_media_usage", "brand_loyalty",
    "price_sensitivity", "risk_taking", "impulse_buying", "discount_preference",
    "premium_preference", "preferred_brand", "communication_style", "response_length",
    "openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism",
    "confidence", "optimism", "patience", "curiosity", "practicality", "emotional_score",
]

def read_csv():
    rows = []
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def fix_user(conn, user_id, email, csv_rows):
    cur = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    # Delete all existing personas for this user
    cur.execute("DELETE FROM personas WHERE user_id = ?", (user_id,))
    deleted = cur.rowcount
    print(f"  Deleted {deleted} existing personas for {email}")

    # Insert fresh from CSV
    inserted = 0
    failed = 0
    batch = []

    for row in csv_rows:
        try:
            pid = str(uuid.uuid4())
            values = [
                pid,           # id
                user_id,       # user_id
                None,          # project_id
                now,           # created_at
                now,           # updated_at
            ]
            for col in COLUMNS:
                val = row.get(col, "")
                if col in INT_COLS:
                    try:
                        values.append(int(float(val)) if val and str(val).strip() != "" else 0)
                    except (ValueError, TypeError):
                        values.append(0)
                else:
                    values.append(str(val).strip() if val else "")

            batch.append(tuple(values))
            inserted += 1

            if len(batch) >= 500:
                cur.executemany(
                    f"INSERT INTO personas (id, user_id, project_id, created_at, updated_at, {', '.join(COLUMNS)}) VALUES ({', '.join(['?'] * (5 + len(COLUMNS)))})",
                    batch
                )
                conn.commit()
                batch = []
                print(f"  Inserted {inserted} so far...")

        except Exception as e:
            failed += 1
            if failed <= 5:
                print(f"  Error on row: {e}")

    if batch:
        cur.executemany(
            f"INSERT INTO personas (id, user_id, project_id, created_at, updated_at, {', '.join(COLUMNS)}) VALUES ({', '.join(['?'] * (5 + len(COLUMNS)))})",
            batch
        )
        conn.commit()

    # Verify
    cur.execute("SELECT COUNT(*) FROM personas WHERE user_id = ?", (user_id,))
    final_count = cur.fetchone()[0]
    print(f"  Done: {inserted} inserted, {failed} failed. Final count in DB: {final_count}")
    return inserted


def main():
    print(f"Reading CSV: {CSV_PATH}")
    csv_rows = read_csv()
    print(f"CSV rows: {len(csv_rows)}")

    conn = sqlite3.connect(DB_PATH)

    for user_id, email in USERS:
        print(f"\nProcessing user: {email}")
        fix_user(conn, user_id, email, csv_rows)

    conn.close()
    print("\nAll done!")

if __name__ == "__main__":
    main()
