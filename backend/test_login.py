#!/usr/bin/env python3
"""Test login credentials"""
from app.database import SessionLocal
from app.models import User
from app.auth import verify_password

email = "maheshc11@gmail.com"
test_password = "fZtAUQLsm-szETQc"

db = SessionLocal()
try:
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"[X] User with email '{email}' not found")
        sys.exit(1)
    
    print(f"[OK] User found:")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Is Active: {user.is_active}")
    print(f"  Has password hash: {bool(user.hashed_password)}")
    print()
    
    # Test password verification
    print(f"Testing password: {test_password}")
    result = verify_password(test_password, user.hashed_password)
    print(f"Password verification result: {result}")
    print()
    
    if result:
        print("[OK] Password is correct!")
        print(f"\nYou should login with:")
        print(f"  Username: {user.username}")
        print(f"  Password: {test_password}")
    else:
        print("[X] Password verification failed")
        print("\nThe password hash might be incorrect. Let's reset it again...")
        
finally:
    db.close()
