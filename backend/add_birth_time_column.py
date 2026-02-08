#!/usr/bin/env python3
"""
Quick script to add birth_time column to family_members table.
Run this once to add the missing column.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings

def add_birth_time_column():
    """Add birth_time column to family_members table"""
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            # Check if column already exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='family_members' AND column_name='birth_time'
            """))
            
            if result.fetchone():
                print("Column 'birth_time' already exists. No changes needed.")
                return
            
            # Add the column with default value
            conn.execute(text("""
                ALTER TABLE family_members 
                ADD COLUMN birth_time VARCHAR(10) NOT NULL DEFAULT '00:00'
            """))
            conn.commit()
            print("✅ Successfully added 'birth_time' column to 'family_members' table")
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        sys.exit(1)
    finally:
        engine.dispose()

if __name__ == "__main__":
    add_birth_time_column()

