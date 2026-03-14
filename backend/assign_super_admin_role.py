"""
Assign Super Admin role to Admin_SKLPM. Run after create_super_admin.py.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal
from app.models import User, AdminRole, UserAdminRole

def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == "Admin_SKLPM").first()
        role = db.query(AdminRole).filter(AdminRole.name == "Super Admin").first()
        if not user:
            print("Admin_SKLPM user not found. Run create_super_admin.py first.")
            return 1
        if not role:
            print("Super Admin role not found. Start the backend once to seed roles.")
            return 1
        existing = db.query(UserAdminRole).filter(
            UserAdminRole.user_id == user.id,
            UserAdminRole.role_id == role.id,
        ).first()
        if existing:
            print("Admin_SKLPM already has Super Admin role.")
            return 0
        db.add(UserAdminRole(
            user_id=user.id,
            role_id=role.id,
            assigned_by=user.id,
        ))
        db.commit()
        print("Super Admin role assigned to Admin_SKLPM successfully.")
        return 0
    except Exception as e:
        db.rollback()
        print("Error:", e)
        return 1
    finally:
        db.close()

if __name__ == "__main__":
    sys.exit(main())
