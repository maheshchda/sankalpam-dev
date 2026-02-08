#!/usr/bin/env python3
"""
Reset password for a user by email
This script helps reset passwords when the email reset flow isn't working
"""
import sys
from app.database import SessionLocal
from app.models import User, VerificationToken, VerificationStatus
from app.auth import get_password_hash
from datetime import datetime, timedelta
import secrets

def reset_user_password(email: str, new_password: str = None):
    """Reset password for a user"""
    db = SessionLocal()
    
    try:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"[X] User with email '{email}' not found in database")
            print("\nAvailable users:")
            users = db.query(User).all()
            if users:
                for u in users:
                    print(f"  - {u.username} ({u.email})")
            else:
                print("  No users found in database")
            return False
        
        print(f"[OK] Found user: {user.username} ({user.email})")
        print(f"     Is Active: {user.is_active}")
        print()
        
        # If new password not provided, generate one or ask
        if not new_password:
            print("Options:")
            print("1. Generate a new random password")
            print("2. Enter a new password manually")
            choice = input("\nEnter choice (1 or 2): ").strip()
            
            if choice == "1":
                # Generate random password
                new_password = secrets.token_urlsafe(12)
                print(f"\nGenerated password: {new_password}")
                print("(Save this password - it won't be shown again)")
            elif choice == "2":
                import getpass
                new_password = getpass.getpass("Enter new password: ")
                confirm = getpass.getpass("Confirm password: ")
                if new_password != confirm:
                    print("[X] Passwords don't match!")
                    return False
            else:
                print("[X] Invalid choice")
                return False
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        
        print(f"\n[OK] Password reset successfully for {user.email}!")
        if choice == "1":
            print(f"New password: {new_password}")
        print("\nUser can now login with the new password.")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def get_reset_token(email: str):
    """Get or create a reset token for the user"""
    db = SessionLocal()
    
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"[X] User with email '{email}' not found")
            return None
        
        # Check for existing valid tokens
        existing_token = db.query(VerificationToken).filter(
            VerificationToken.user_id == user.id,
            VerificationToken.token_type == "password_reset",
            VerificationToken.status == VerificationStatus.PENDING,
            VerificationToken.expires_at > datetime.utcnow()
        ).first()
        
        if existing_token:
            print(f"[OK] Found existing reset token (expires: {existing_token.expires_at})")
            print(f"Token: {existing_token.token}")
            return existing_token.token
        
        # Create new token
        reset_token = secrets.token_urlsafe(32)
        db_reset_token = VerificationToken(
            user_id=user.id,
            token=reset_token,
            token_type="password_reset",
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.add(db_reset_token)
        db.commit()
        
        print(f"[OK] Created new reset token (expires in 1 hour)")
        print(f"Token: {reset_token}")
        print("\nYou can use this token with the /api/auth/reset-password endpoint")
        return reset_token
        
    except Exception as e:
        db.rollback()
        print(f"[X] Error: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("  Reset User Password")
    print("="*60)
    print()
    
    if len(sys.argv) < 2:
        email = input("Enter user email: ").strip()
    else:
        email = sys.argv[1]
    
    print()
    print("Choose an option:")
    print("1. Reset password directly (recommended)")
    print("2. Generate reset token (use with API endpoint)")
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        reset_user_password(email)
    elif choice == "2":
        get_reset_token(email)
    else:
        print("[X] Invalid choice")
