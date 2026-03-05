"""Add death panchang columns to family_members table."""
from app.database import engine
from sqlalchemy import text

COLS = [
    ("death_tithi",     "VARCHAR(100)"),
    ("death_paksha",    "VARCHAR(50)"),
    ("death_nakshatra", "VARCHAR(100)"),
    ("death_vara",      "VARCHAR(50)"),
    ("death_yoga",      "VARCHAR(100)"),
    ("death_karana",    "VARCHAR(100)"),
]

CHECK_SQL = (
    "SELECT 1 FROM information_schema.columns "
    "WHERE table_name='family_members' AND column_name=:col"
)

with engine.connect() as conn:
    for col, definition in COLS:
        exists = conn.execute(text(CHECK_SQL), {"col": col}).fetchone()
        if exists:
            print(f"  SKIP   {col}  (already exists)")
        else:
            conn.execute(text(f"ALTER TABLE family_members ADD COLUMN {col} {definition}"))
            conn.commit()
            print(f"  ADDED  {col}")

print("Migration complete.")
