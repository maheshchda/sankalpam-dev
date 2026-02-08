#!/usr/bin/env python3
"""
Diagnostic script to check login issues
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import User

def check_database():
    """Check if database is accessible"""
    print("=" * 60)
    print("CHECKING DATABASE CONNECTION")
    print("=" * 60)
    try:
        engine = create_engine(settings.database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("[OK] Database connection: SUCCESS")
            print(f"  Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'hidden'}")
            return True
    except Exception as e:
        print("[FAIL] Database connection: FAILED")
        print(f"  Error: {str(e)}")
        print("\n  SOLUTION: Install and start PostgreSQL")
        print("  See: C:\\Projects\\sankalpam-dev\\DATABASE-SETUP.md")
        return False

def check_users():
    """Check if users exist in database"""
    print("\n" + "=" * 60)
    print("CHECKING USERS")
    print("=" * 60)
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        users = db.query(User).all()
        print(f"[OK] Found {len(users)} user(s) in database")
        
        if len(users) == 0:
            print("\n  [FAIL] NO USERS FOUND!")
            print("  SOLUTION: Create an admin user")
            print("  Run: python create_admin_user.py")
        else:
            print("\n  Users:")
            for user in users:
                status = "ACTIVE" if user.is_active else "INACTIVE"
                admin = " (ADMIN)" if user.is_admin else ""
                print(f"    - {user.username} ({user.email}) - {status}{admin}")
        
        db.close()
        return len(users) > 0
    except Exception as e:
        print("[FAIL] Failed to check users")
        print(f"  Error: {str(e)}")
        return False

def check_backend_running():
    """Check if backend is running"""
    print("\n" + "=" * 60)
    print("CHECKING BACKEND SERVER")
    print("=" * 60)
    try:
        import requests
        response = requests.get("http://localhost:8000/docs", timeout=2)
        if response.status_code == 200:
            print("[OK] Backend server: RUNNING")
            print("  URL: http://localhost:8000")
            return True
        else:
            print("[FAIL] Backend server: NOT RESPONDING")
            return False
    except Exception as e:
        print("[FAIL] Backend server: NOT RUNNING")
        print("  Error: Cannot connect to http://localhost:8000")
        print("\n  SOLUTION: Start the backend server")
        print("  Run: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False

def main():
    print("\n" + "=" * 60)
    print("LOGIN ISSUE DIAGNOSTIC")
    print("=" * 60)
    print()
    
    db_ok = check_database()
    users_ok = check_users() if db_ok else False
    backend_ok = check_backend_running()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not db_ok:
        print("[ERROR] ISSUE: Database not connected")
        print("   Fix: Install PostgreSQL (see DATABASE-SETUP.md)")
    elif not users_ok:
        print("[ERROR] ISSUE: No users in database")
        print("   Fix: Run 'python create_admin_user.py'")
    elif not backend_ok:
        print("[ERROR] ISSUE: Backend server not running")
        print("   Fix: Start backend with 'uvicorn main:app --reload'")
    else:
        print("[SUCCESS] All checks passed!")
        print("\nIf login still fails:")
        print("  1. Check browser console for errors (F12)")
        print("  2. Check backend terminal for error messages")
        print("  3. Verify you're using the correct username/password")
        print("  4. Default admin: username='admin', password='Admin@123'")
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()

