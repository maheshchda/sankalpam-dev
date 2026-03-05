"""
Create the first Super-Admin account for Pooja Sankalpam.

Usage:
    cd backend
    python create_super_admin.py

Default credentials
    Username : Admin_SKLPM
    Password : SKLPM2026

Run this ONCE after first deployment. If the account already exists the
script will print the current status and exit without making changes.
"""
import sys
import os

# Make sure the backend package is importable when run from its own directory
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models import User
from app.auth import get_password_hash

ADMIN_USERNAME = "Admin_SKLPM"
ADMIN_PASSWORD = "SKLPM2026"
ADMIN_EMAIL    = "admin@poojasankalpam.com"
ADMIN_PHONE    = "0000000000"


def create_super_admin():
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if existing:
            print(f"[INFO] Super-admin '{ADMIN_USERNAME}' already exists.")
            print(f"       is_admin   : {existing.is_admin}")
            print(f"       is_active  : {existing.is_active}")
            print(f"       email_verified : {existing.email_verified}")
            print(f"       phone_verified : {existing.phone_verified}")
            return

        admin = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            phone=ADMIN_PHONE,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            first_name="Super",
            last_name="Admin",
            gotram="N/A",
            birth_city="N/A",
            birth_state="N/A",
            birth_country="India",
            birth_time="00:00",
            birth_date="1970-01-01",
            is_active=True,
            is_admin=True,
            email_verified=True,
            phone_verified=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print("=" * 55)
        print("  Super-Admin created successfully!")
        print("=" * 55)
        print(f"  Username : {ADMIN_USERNAME}")
        print(f"  Password : {ADMIN_PASSWORD}")
        print(f"  Login at : http://localhost:3000/admin/login")
        print("=" * 55)
        print("  IMPORTANT: Change the password after first login.")
        print("=" * 55)
    finally:
        db.close()


if __name__ == "__main__":
    create_super_admin()
