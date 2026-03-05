#!/usr/bin/env python3
"""Verify migration was applied successfully"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    # Check users table
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='users' AND column_name IN ('birth_nakshatra', 'birth_rashi')
    """))
    user_cols = [r[0] for r in result]
    print(f"Users table columns: {user_cols}")
    
    # Check family_members table
    result2 = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='family_members' AND column_name IN ('birth_nakshatra', 'birth_rashi')
    """))
    family_cols = [r[0] for r in result2]
    print(f"Family members table columns: {family_cols}")
    
    if len(user_cols) == 2 and len(family_cols) == 2:
        print("\n[OK] Migration verified successfully!")
    else:
        print("\n[X] Migration incomplete!")
