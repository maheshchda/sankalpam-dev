#!/usr/bin/env python3
"""
Apply database migration to add birth_nakshatra, birth_rashi and birth_pada fields
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import engine

def apply_migration():
    """Apply migration to add birth_nakshatra, birth_rashi and birth_pada columns"""
    print("Applying migration: Add birth_nakshatra, birth_rashi and birth_pada...")
    
    with engine.connect() as conn:
        try:
            # Check if columns already exist (users)
            check_users = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='birth_nakshatra'
            """)
            result = conn.execute(check_users)
            if result.fetchone():
                print("Columns already exist in users table. Skipping birth_nakshatra/birth_rashi...")
            else:
                # Add columns to users table
                print("Adding columns to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN birth_nakshatra VARCHAR(50)"))
                conn.execute(text("ALTER TABLE users ADD COLUMN birth_rashi VARCHAR(50)"))
                print("[OK] Added columns to users table")

            # Add birth_pada to users if missing
            check_users_pada = text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='users' AND column_name='birth_pada'
                """
            )
            result = conn.execute(check_users_pada)
            if result.fetchone():
                print("Column birth_pada already exists in users table. Skipping...")
            else:
                print("Adding birth_pada to users table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN birth_pada VARCHAR(10)"))
                print("[OK] Added birth_pada to users table")
            
            # Check if columns already exist in family_members
            check_family = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='family_members' AND column_name='birth_nakshatra'
            """)
            result = conn.execute(check_family)
            if result.fetchone():
                print("Columns already exist in family_members table. Skipping birth_nakshatra/birth_rashi...")
            else:
                # Add columns to family_members table
                print("Adding columns to family_members table...")
                conn.execute(text("ALTER TABLE family_members ADD COLUMN birth_nakshatra VARCHAR(50)"))
                conn.execute(text("ALTER TABLE family_members ADD COLUMN birth_rashi VARCHAR(50)"))
                print("[OK] Added columns to family_members table")

            # Add birth_pada to family_members if missing
            check_family_pada = text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name='family_members' AND column_name='birth_pada'
                """
            )
            result = conn.execute(check_family_pada)
            if result.fetchone():
                print("Column birth_pada already exists in family_members table. Skipping...")
            else:
                print("Adding birth_pada to family_members table...")
                conn.execute(text("ALTER TABLE family_members ADD COLUMN birth_pada VARCHAR(10)"))
                print("[OK] Added birth_pada to family_members table")
            
            conn.commit()
            print("\n[OK] Migration applied successfully!")
            
        except Exception as e:
            conn.rollback()
            print(f"\n[X] Error applying migration: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    apply_migration()
