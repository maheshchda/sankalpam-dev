#!/usr/bin/env python3
"""
Directly reset password for a user by email
Usage: python reset_password_direct.py <email> [new_password]
If new_password is not provided, a random one will be generated
"""
import sys
import secrets
from app.database import SessionLocal
from app.models import User
from app.auth import get_password_hash

def reset_password(email: str, new_password: str = None):
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"[X] User with email '{email}' not found")
            print("\nAvailable users:")
            users = db.query(User).all()
            for u in users:
                print(f"  - {u.username} ({u.email})")
            return False
        
        # Generate password if not provided
        if not new_password:
            new_password = secrets.token_urlsafe(12)
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        print(f"[OK] Password reset successfully!")
        print(f"Email: {user.email}")
        print(f"Username: {user.username}")
        print(f"New Password: {new_password}")
        print("\nUser can now login with this password.")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reset_password_direct.py <email> [new_password]")
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2] if len(sys.argv) > 2 else None
    
    reset_password(email, new_password)
