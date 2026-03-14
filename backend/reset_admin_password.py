"""
Reset the Admin_SKLPM password to a new known value.

Usage:
    cd backend
    set DB_CONNECTION_STRING=postgresql://...   (or use .env)
    python reset_admin_password.py

New password will be: SKLPM2026
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

ADMIN_USERNAME = "Admin_SKLPM"
NEW_PASSWORD = "SKLPM2026"


def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if not user:
            print(f"Admin user '{ADMIN_USERNAME}' not found.")
            return 1
        user.hashed_password = get_password_hash(NEW_PASSWORD)
        user.is_active = True
        db.commit()
        print("=" * 50)
        print("  Admin password reset successfully!")
        print("=" * 50)
        print(f"  Username : {ADMIN_USERNAME}")
        print(f"  Password : {NEW_PASSWORD}")
        print(f"  Login at : https://www.poojasankalp.org/admin/login")
        print("=" * 50)
        return 0
    except Exception as e:
        db.rollback()
        print("Error:", e)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
