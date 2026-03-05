"""
Fix nullable constraints on family_members table.
Run: python fix_nullable_columns.py
"""
import sys
sys.path.insert(0, '.')

from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    print("Altering date_of_birth to nullable...")
    conn.execute(text(
        "ALTER TABLE family_members ALTER COLUMN date_of_birth DROP NOT NULL"
    ))
    print("Altering birth_time to nullable...")
    conn.execute(text(
        "ALTER TABLE family_members ALTER COLUMN birth_time DROP NOT NULL"
    ))
    conn.commit()
    print("Done. Both columns are now nullable.")

    result = conn.execute(text("""
        SELECT column_name, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'family_members'
          AND column_name IN ('date_of_birth', 'birth_time')
    """))
    for row in result:
        print(f"  {row[0]}: is_nullable={row[1]}")
