#!/usr/bin/env python3
"""
Diagnostic script to check Sankalpam generation issues
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import SankalpamTemplate, User

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
            return True
    except Exception as e:
        print("[FAIL] Database connection: FAILED")
        print(f"  Error: {str(e)}")
        return False

def check_templates():
    """Check if templates exist"""
    print("\n" + "=" * 60)
    print("CHECKING TEMPLATES")
    print("=" * 60)
    try:
        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        templates = db.query(SankalpamTemplate).filter(
            SankalpamTemplate.is_active == True
        ).all()
        
        print(f"[OK] Found {len(templates)} active template(s)")
        
        if len(templates) == 0:
            print("\n  [FAIL] NO TEMPLATES FOUND!")
            print("  SOLUTION: Add templates via admin panel or database")
        else:
            print("\n  Templates:")
            for t in templates:
                print(f"    - ID: {t.id}, Name: {t.name}, Language: {t.language}")
        
        db.close()
        return len(templates) > 0
    except Exception as e:
        print("[FAIL] Failed to check templates")
        print(f"  Error: {str(e)}")
        return False

def check_tts_service():
    """Check if TTS service is available"""
    print("\n" + "=" * 60)
    print("CHECKING TTS SERVICE")
    print("=" * 60)
    try:
        from app.services.tts_service import text_to_speech
        print("[OK] TTS service module: LOADED")
        print("  Note: TTS may require additional setup (gTTS, pyttsx3, etc.)")
        return True
    except Exception as e:
        print("[FAIL] TTS service: NOT AVAILABLE")
        print(f"  Error: {str(e)}")
        print("\n  SOLUTION: Install TTS dependencies")
        print("  Run: pip install gtts pyttsx3")
        return False

def check_location_service():
    """Check if location service is available"""
    print("\n" + "=" * 60)
    print("CHECKING LOCATION SERVICE")
    print("=" * 60)
    try:
        from app.services.location_service import get_location_from_coordinates
        print("[OK] Location service module: LOADED")
        print("  Uses OpenStreetMap Nominatim (free, no API key needed)")
        return True
    except Exception as e:
        print("[FAIL] Location service: NOT AVAILABLE")
        print(f"  Error: {str(e)}")
        return False

def check_backend_running():
    """Check if backend is running"""
    print("\n" + "=" * 60)
    print("CHECKING BACKEND SERVER")
    print("=" * 60)
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=2)
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
    print("SANKALPAM GENERATION DIAGNOSTIC")
    print("=" * 60)
    print()
    
    db_ok = check_database()
    templates_ok = check_templates() if db_ok else False
    tts_ok = check_tts_service()
    location_ok = check_location_service()
    backend_ok = check_backend_running()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    issues = []
    if not db_ok:
        issues.append("Database not connected")
    if not templates_ok:
        issues.append("No templates in database")
    if not tts_ok:
        issues.append("TTS service not available")
    if not location_ok:
        issues.append("Location service not available")
    if not backend_ok:
        issues.append("Backend server not running")
    
    if issues:
        print("[ERROR] Issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("[SUCCESS] All checks passed!")
        print("\nIf generation still fails:")
        print("  1. Check browser console for errors (F12)")
        print("  2. Check backend terminal for error messages")
        print("  3. Verify you're logged in")
        print("  4. Check all required fields are filled")
    
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()

