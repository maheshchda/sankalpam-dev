"""
Set a known password for user maheshc11 (by email or username).
Run from backend: python set_password_maheshc11.py

Login after running:
  Username: maheshc11
  Password: Sankalpam1
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

NEW_PASSWORD = "Sankalpam1"

def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(
            (User.email == "maheshc11@gmail.com") | (User.username == "maheshc11") | (User.username == "maheshc11@gmail.com")
        ).first()
        if not user:
            print("User not found with email maheshc11@gmail.com or username maheshc11.")
            return 1
        user.hashed_password = get_password_hash(NEW_PASSWORD)
        user.email_verified = True
        user.phone_verified = True
        db.commit()
        print("Password updated and email/phone marked verified.")
        print("")
        print("Login with (use either):")
        print("  Username: ", user.username, "  OR  Email: ", user.email)
        print("  Password:", NEW_PASSWORD)
        return 0
    except Exception as e:
        db.rollback()
        print("Error:", e)
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
