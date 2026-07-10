import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "..", "data", "personax.db")
db_path = os.path.abspath(db_path)

print(f"Connecting to database at {db_path}...")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check current columns in conversations
cursor.execute("PRAGMA table_info(conversations)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Current columns in 'conversations': {columns}")

if "product_name" not in columns:
    print("Adding 'product_name' column...")
    cursor.execute("ALTER TABLE conversations ADD COLUMN product_name VARCHAR(255)")
    print("[OK] 'product_name' added")

if "product_description" not in columns:
    print("Adding 'product_description' column...")
    cursor.execute("ALTER TABLE conversations ADD COLUMN product_description TEXT")
    print("[OK] 'product_description' added")

conn.commit()
conn.close()
print("Migration completed successfully!")
