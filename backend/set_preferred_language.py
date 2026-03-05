"""
One-time script to set a user's preferred_language to Telugu (or another language) by email.
Run from backend dir with venv active:
  python set_preferred_language.py maheshc11@gmail.com te
  python set_preferred_language.py maheshc11@gmail.com telugu
"""
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User, Language

def main():
    if len(sys.argv) < 3:
        print("Usage: python set_preferred_language.py <email> <language>")
        print("  language: 'te' or 'telugu' for Telugu, 'hi'/'hindi', 'sa'/'sanskrit', etc.")
        sys.exit(1)
    email = sys.argv[1].strip().lower()
    lang_arg = sys.argv[2].strip().lower()
    lang = Language.from_code(lang_arg) if len(lang_arg) == 2 else Language(lang_arg) if lang_arg in [e.value for e in Language] else None
    if not lang:
        print(f"Unknown language: {lang_arg}. Use e.g. te, telugu, hi, sanskrit")
        sys.exit(1)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user found with email: {email}")
            sys.exit(1)
        old = user.preferred_language
        user.preferred_language = lang
        db.commit()
        print(f"Updated {email}: preferred_language {old.value} -> {lang.value} (code: {lang.code})")
    finally:
        db.close()

if __name__ == "__main__":
    main()
