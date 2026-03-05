"""Apply deceased-fields migration directly to the family_members table."""
from app.database import engine
from sqlalchemy import text

COLS = [
    ("is_deceased",   "BOOLEAN NOT NULL DEFAULT FALSE"),
    ("date_of_death", "TIMESTAMP WITH TIME ZONE"),
    ("time_of_death", "VARCHAR(10)"),
    ("death_city",    "VARCHAR(100)"),
    ("death_state",   "VARCHAR(100)"),
    ("death_country", "VARCHAR(100)"),
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
