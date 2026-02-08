#!/usr/bin/env python3
"""
Script to make a user an admin.
Usage: python make_admin.py <username>
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.database import Base
from app.config import settings

def make_admin(username: str):
    """Make a user an admin"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print(f"❌ User '{username}' not found!")
            return False
        
        if user.is_admin:
            print(f"✅ User '{username}' is already an admin!")
            return True
        
        user.is_admin = True
        db.commit()
        print(f"✅ Successfully made '{username}' an admin!")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python make_admin.py <username>")
        sys.exit(1)
    
    username = sys.argv[1]
    make_admin(username)

