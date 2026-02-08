#!/usr/bin/env python3
"""
Script to create a new admin user.
Creates a default admin user with credentials that can be changed later.
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User
from app.database import Base
from app.config import settings
from app.auth import get_password_hash

def create_admin_user():
    """Create a default admin user"""
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    # Default admin credentials
    admin_username = "admin"
    admin_password = "Admin@123"  # Change this after first login!
    admin_email = "admin@sankalpam.com"
    admin_phone = "9999999999"
    
    try:
        # Check if admin user already exists
        existing_user = db.query(User).filter(
            (User.username == admin_username) | 
            (User.email == admin_email) | 
            (User.phone == admin_phone)
        ).first()
        
        if existing_user:
            if existing_user.is_admin:
                print(f"✅ Admin user '{admin_username}' already exists and is an admin!")
                print(f"\n📧 Username: {admin_username}")
                print(f"📧 Email: {existing_user.email}")
                print(f"📧 Phone: {existing_user.phone}")
                print(f"🔑 Password: (already set - check with user)")
                return True
            else:
                # Make existing user admin
                existing_user.is_admin = True
                db.commit()
                print(f"✅ User '{admin_username}' exists. Made them an admin!")
                print(f"\n📧 Username: {admin_username}")
                print(f"📧 Email: {existing_user.email}")
                print(f"📧 Phone: {existing_user.phone}")
                print(f"🔑 Password: (already set - check with user)")
                return True
        
        # Create new admin user
        hashed_password = get_password_hash(admin_password)
        
        admin_user = User(
            username=admin_username,
            email=admin_email,
            phone=admin_phone,
            hashed_password=hashed_password,
            first_name="Admin",
            last_name="User",
            gotram="Admin",
            birth_city="Unknown",
            birth_state="Unknown",
            birth_country="India",
            birth_time="00:00",
            birth_date=datetime(1990, 1, 1),
            preferred_language="sanskrit",
            email_verified=True,  # Auto-verify for admin
            phone_verified=True,  # Auto-verify for admin
            is_active=True,
            is_admin=True  # Make admin
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("=" * 60)
        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\n📧 Username: {admin_username}")
        print(f"🔑 Password: {admin_password}")
        print(f"📧 Email: {admin_email}")
        print(f"📱 Phone: {admin_phone}")
        print("\n" + "=" * 60)
        print("⚠️  IMPORTANT: Please change the password after first login!")
        print("=" * 60)
        print(f"\n🌐 Login URL: http://localhost:3000/login")
        print(f"⚙️  Admin Panel: http://localhost:3000/admin")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
        engine.dispose()

if __name__ == "__main__":
    create_admin_user()

