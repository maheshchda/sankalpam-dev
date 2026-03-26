from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import (
    inspect as sqla_inspect,
    MetaData,
    Table,
    select,
    and_,
    update as sql_update,
    delete as sql_delete,
    types as sqltypes,
)
from typing import List, Optional, Any, Dict
import json
import secrets
import string
import enum
import decimal
from datetime import datetime, timedelta

from app.database import get_db, engine
from app.models import (
    User, Pooja, SankalpamTemplate, Language, PoojaSession,
    AdminRole, UserAdminRole, ALL_PERMISSIONS, PERMISSION_CODES,
)
from app.schemas import PoojaCreate, PoojaResponse, SankalpamTemplateCreate, SankalpamTemplateResponse
from app.dependencies import get_admin_user
from app.auth import verify_password, create_access_token, get_password_hash
from app.config import settings
from app.services.template_service import identify_variables
from app.services.email_service import send_password_reset_email
from pydantic import BaseModel

router = APIRouter()


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str
    is_admin: bool
    username: str


class AdminStats(BaseModel):
    total_users: int
    active_users: int
    inactive_users: int
    verified_users: int
    unverified_users: int
    admin_users: int
    total_poojas: int
    total_sessions: int


class AdminUserResponse(BaseModel):
    id: int
    username: str
    email: str
    phone: str
    first_name: str
    last_name: str
    is_active: bool
    is_admin: bool
    email_verified: bool
    phone_verified: bool
    preferred_language: str
    created_at: datetime
    birth_city: Optional[str] = None
    birth_state: Optional[str] = None
    birth_country: Optional[str] = None
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    current_country: Optional[str] = None
    assigned_roles: List[str] = []

    model_config = {"from_attributes": True}


class SetAdminRequest(BaseModel):
    is_admin: bool


class AdminRoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str]


class AdminRoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[List[str]] = None


class AdminRoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: List[str]
    is_system_role: bool
    created_at: datetime
    user_count: int = 0

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    role_id: int


class PermissionInfo(BaseModel):
    code: str
    description: str


class AdminCreateUser(BaseModel):
    username: str
    password: str
    email: str
    phone: str
    first_name: str
    last_name: str
    gotram: Optional[str] = "N/A"
    birth_city: Optional[str] = "N/A"
    birth_state: Optional[str] = "N/A"
    birth_country: Optional[str] = "India"
    birth_time: Optional[str] = "00:00"
    birth_date: Optional[str] = "1990-01-01"
    preferred_language: Optional[str] = "english"
    is_admin: Optional[bool] = False
    is_active: Optional[bool] = True
    auto_verify: Optional[bool] = True   # skip email/phone verification requirement


class AdminUpdateUser(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    gotram: Optional[str] = None
    birth_city: Optional[str] = None
    birth_state: Optional[str] = None
    birth_country: Optional[str] = None
    birth_time: Optional[str] = None
    birth_date: Optional[str] = None
    current_city: Optional[str] = None
    current_state: Optional[str] = None
    current_country: Optional[str] = None
    preferred_language: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
    email_verified: Optional[bool] = None
    phone_verified: Optional[bool] = None


# ── Permission helpers ────────────────────────────────────────────────────────

def _get_user_permissions(user: User, db: Session) -> set:
    """Return the full set of permission codes for an admin user."""
    user_roles = db.query(UserAdminRole).filter(UserAdminRole.user_id == user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    if not role_ids:
        return set()
    roles = db.query(AdminRole).filter(AdminRole.id.in_(role_ids)).all()
    perms: set = set()
    for role in roles:
        ps = json.loads(role.permissions or "[]")
        if "*" in ps:
            return {"*"}          # wildcard = everything
        perms.update(ps)
    return perms


def _check_permission(user: User, permission: str, db: Session):
    """Raise 403 if the admin user does not have the required permission."""
    perms = _get_user_permissions(user, db)
    if "*" not in perms and permission not in perms:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied. Required: '{permission}'.",
        )


def _user_with_roles(user: User, db: Session) -> AdminUserResponse:
    user_roles = db.query(UserAdminRole).filter(UserAdminRole.user_id == user.id).all()
    role_ids = [ur.role_id for ur in user_roles]
    roles = db.query(AdminRole).filter(AdminRole.id.in_(role_ids)).all() if role_ids else []
    resp = AdminUserResponse.model_validate(user)
    resp.assigned_roles = [r.name for r in roles]
    return resp


# ── Admin login ───────────────────────────────────────────────────────────────

@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    login_input = (form_data.username or "").strip()
    user = db.query(User).filter(User.username == login_input).first()
    if not user:
        user = db.query(User).filter(User.email == login_input).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is inactive")
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This account does not have admin privileges.",
        )

    expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = create_access_token(data={"sub": user.username}, expires_delta=expires)
    return {"access_token": token, "token_type": "bearer", "is_admin": True, "username": user.username}


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=AdminStats)
async def get_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "view_stats", db)
    return AdminStats(
        total_users=db.query(User).count(),
        active_users=db.query(User).filter(User.is_active == True).count(),
        inactive_users=db.query(User).filter(User.is_active == False).count(),
        verified_users=db.query(User).filter(User.email_verified == True, User.phone_verified == True).count(),
        unverified_users=db.query(User).filter(
            (User.email_verified == False) | (User.phone_verified == False)
        ).count(),
        admin_users=db.query(User).filter(User.is_admin == True).count(),
        total_poojas=db.query(Pooja).count(),
        total_sessions=db.query(PoojaSession).count(),
    )


# ── Available permissions list ────────────────────────────────────────────────

@router.get("/permissions", response_model=List[PermissionInfo])
async def list_permissions(current_user: User = Depends(get_admin_user)):
    return [PermissionInfo(code=p[0], description=p[1]) for p in ALL_PERMISSIONS]


# ── Role management ───────────────────────────────────────────────────────────

@router.get("/roles", response_model=List[AdminRoleResponse])
async def list_roles(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    roles = db.query(AdminRole).order_by(AdminRole.name).all()
    result = []
    for role in roles:
        user_count = db.query(UserAdminRole).filter(UserAdminRole.role_id == role.id).count()
        r = AdminRoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=json.loads(role.permissions or "[]"),
            is_system_role=role.is_system_role,
            created_at=role.created_at,
            user_count=user_count,
        )
        result.append(r)
    return result


@router.post("/roles", response_model=AdminRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    body: AdminRoleCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "role_management", db)
    if db.query(AdminRole).filter(AdminRole.name == body.name).first():
        raise HTTPException(status_code=400, detail="A role with this name already exists")
    invalid = [p for p in body.permissions if p not in PERMISSION_CODES and p != "*"]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown permissions: {invalid}")
    role = AdminRole(
        name=body.name,
        description=body.description,
        permissions=json.dumps(body.permissions),
        is_system_role=False,
        created_by=current_user.id,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return AdminRoleResponse(
        id=role.id, name=role.name, description=role.description,
        permissions=json.loads(role.permissions), is_system_role=role.is_system_role,
        created_at=role.created_at, user_count=0,
    )


@router.put("/roles/{role_id}", response_model=AdminRoleResponse)
async def update_role(
    role_id: int,
    body: AdminRoleUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "role_management", db)
    role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if body.name is not None:
        if db.query(AdminRole).filter(AdminRole.name == body.name, AdminRole.id != role_id).first():
            raise HTTPException(status_code=400, detail="Another role with this name already exists")
        role.name = body.name
    if body.description is not None:
        role.description = body.description
    if body.permissions is not None:
        invalid = [p for p in body.permissions if p not in PERMISSION_CODES and p != "*"]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Unknown permissions: {invalid}")
        role.permissions = json.dumps(body.permissions)
    db.commit()
    db.refresh(role)
    user_count = db.query(UserAdminRole).filter(UserAdminRole.role_id == role.id).count()
    return AdminRoleResponse(
        id=role.id, name=role.name, description=role.description,
        permissions=json.loads(role.permissions), is_system_role=role.is_system_role,
        created_at=role.created_at, user_count=user_count,
    )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    role_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "role_management", db)
    role = db.query(AdminRole).filter(AdminRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(status_code=400, detail="System roles cannot be deleted")
    db.delete(role)
    db.commit()
    return None


# ── User management ───────────────────────────────────────────────────────────

@router.get("/users", response_model=List[AdminUserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_admin: Optional[bool] = Query(None),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "user_management", db)
    q = db.query(User)
    if search:
        term = f"%{search}%"
        q = q.filter(
            User.username.ilike(term) | User.email.ilike(term)
            | User.first_name.ilike(term) | User.last_name.ilike(term)
        )
    if is_active is not None:
        q = q.filter(User.is_active == is_active)
    if is_admin is not None:
        q = q.filter(User.is_admin == is_admin)
    users = q.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return [_user_with_roles(u, db) for u in users]


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "user_management", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_with_roles(user, db)


@router.patch("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "user_management", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    db.commit()
    return {"message": f"User '{user.username}' activated successfully"}


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "user_management", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
    user.is_active = False
    db.commit()
    return {"message": f"User '{user.username}' deactivated successfully"}


@router.patch("/users/{user_id}/set-admin")
async def set_admin_role(
    user_id: int,
    body: SetAdminRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "admin_management", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id and not body.is_admin:
        raise HTTPException(status_code=400, detail="Cannot revoke your own admin privileges")
    user.is_admin = body.is_admin
    db.commit()
    action = "granted" if body.is_admin else "revoked"
    return {"message": f"Admin privileges {action} for '{user.username}'"}


@router.patch("/users/{user_id}/verify-email")
async def manually_verify_email(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "user_verification", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.email_verified = True
    db.commit()
    return {"message": f"Email verified for '{user.username}'"}


@router.patch("/users/{user_id}/verify-phone")
async def manually_verify_phone(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "user_verification", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.phone_verified = True
    db.commit()
    return {"message": f"Phone verified for '{user.username}'"}


@router.post("/users/{user_id}/reset-password")
async def admin_reset_password(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Generate a new random password for a user and email it to them."""
    _check_permission(current_user, "user_password_reset", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a memorable random password: 3 words + 4 digits
    alphabet = string.ascii_letters + string.digits
    new_password = (
        "".join(secrets.choice(string.ascii_uppercase) for _ in range(1))
        + "".join(secrets.choice(string.ascii_lowercase) for _ in range(5))
        + "".join(secrets.choice(string.digits) for _ in range(3))
        + secrets.choice("!@#$")
    )
    # Shuffle to avoid predictable pattern
    pw_list = list(new_password)
    secrets.SystemRandom().shuffle(pw_list)
    new_password = "".join(pw_list)

    user.hashed_password = get_password_hash(new_password)
    db.commit()

    # Send email with new temporary password
    _send_admin_reset_email(user.email, user.username, new_password)

    return {
        "message": f"Password reset for '{user.username}'. New temporary password sent to {user.email}.",
        "temp_password": new_password,  # shown in admin UI for manual fallback
    }


@router.patch("/users/{user_id}/assign-role")
async def assign_role_to_user(
    user_id: int,
    body: AssignRoleRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "role_management", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    role = db.query(AdminRole).filter(AdminRole.id == body.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    existing = db.query(UserAdminRole).filter(
        UserAdminRole.user_id == user_id, UserAdminRole.role_id == body.role_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already has this role")
    db.add(UserAdminRole(user_id=user_id, role_id=body.role_id, assigned_by=current_user.id))
    db.commit()
    return {"message": f"Role '{role.name}' assigned to '{user.username}'"}


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_role_from_user(
    user_id: int,
    role_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "role_management", db)
    ur = db.query(UserAdminRole).filter(
        UserAdminRole.user_id == user_id, UserAdminRole.role_id == role_id
    ).first()
    if not ur:
        raise HTTPException(status_code=404, detail="Role assignment not found")
    db.delete(ur)
    db.commit()
    return None


@router.post("/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: AdminCreateUser,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin creates a new frontend user directly."""
    _check_permission(current_user, "user_management", db)

    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.phone == body.phone).first():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    from datetime import date as date_type
    try:
        bd = date_type.fromisoformat(body.birth_date or "1990-01-01")
    except ValueError:
        bd = date_type(1990, 1, 1)

    try:
        lang = Language(body.preferred_language.lower()) if body.preferred_language else Language.ENGLISH
    except ValueError:
        lang = Language.ENGLISH

    new_user = User(
        username=body.username,
        email=body.email,
        phone=body.phone,
        hashed_password=get_password_hash(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        gotram=body.gotram or "N/A",
        birth_city=body.birth_city or "N/A",
        birth_state=body.birth_state or "N/A",
        birth_country=body.birth_country or "India",
        birth_time=body.birth_time or "00:00",
        birth_date=bd,
        preferred_language=lang,
        is_active=body.is_active if body.is_active is not None else True,
        is_admin=body.is_admin or False,
        email_verified=body.auto_verify if body.auto_verify is not None else True,
        phone_verified=body.auto_verify if body.auto_verify is not None else True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return _user_with_roles(new_user, db)


@router.patch("/users/{user_id}/update", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    body: AdminUpdateUser,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """Admin updates any field of a frontend user."""
    _check_permission(current_user, "user_management", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.email and body.email != user.email:
        if db.query(User).filter(User.email == body.email, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="Email already in use")
        user.email = body.email
    if body.phone and body.phone != user.phone:
        if db.query(User).filter(User.phone == body.phone, User.id != user_id).first():
            raise HTTPException(status_code=400, detail="Phone already in use")
        user.phone = body.phone

    for field in ("first_name", "last_name", "gotram",
                  "birth_city", "birth_state", "birth_country", "birth_time",
                  "current_city", "current_state", "current_country"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(user, field, val)

    if body.birth_date:
        from datetime import date as date_type
        try:
            user.birth_date = date_type.fromisoformat(body.birth_date)
        except ValueError:
            pass

    if body.preferred_language:
        try:
            user.preferred_language = Language(body.preferred_language.lower())
        except ValueError:
            pass

    if body.is_active is not None:
        if user.id == current_user.id and not body.is_active:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        user.is_active = body.is_active
    if body.is_admin is not None:
        user.is_admin = body.is_admin
    if body.email_verified is not None:
        user.email_verified = body.email_verified
    if body.phone_verified is not None:
        user.phone_verified = body.phone_verified

    db.commit()
    db.refresh(user)
    return _user_with_roles(user, db)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "admin_management", db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    db.delete(user)
    db.commit()
    return None


# ── Pooja management ──────────────────────────────────────────────────────────

@router.post("/poojas", response_model=PoojaResponse, status_code=status.HTTP_201_CREATED)
async def create_pooja(
    pooja_data: PoojaCreate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "pooja_management", db)
    db_pooja = Pooja(name=pooja_data.name, description=pooja_data.description,
                     duration_minutes=pooja_data.duration_minutes, created_by=current_user.id)
    db.add(db_pooja); db.commit(); db.refresh(db_pooja)
    return db_pooja


@router.get("/poojas", response_model=List[PoojaResponse])
async def get_all_poojas(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    _check_permission(current_user, "pooja_management", db)
    return db.query(Pooja).all()


@router.put("/poojas/{pooja_id}", response_model=PoojaResponse)
async def update_pooja(
    pooja_id: int, pooja_data: PoojaCreate,
    current_user: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    _check_permission(current_user, "pooja_management", db)
    pooja = db.query(Pooja).filter(Pooja.id == pooja_id).first()
    if not pooja:
        raise HTTPException(status_code=404, detail="Pooja not found")
    pooja.name = pooja_data.name; pooja.description = pooja_data.description
    pooja.duration_minutes = pooja_data.duration_minutes
    db.commit(); db.refresh(pooja)
    return pooja


@router.delete("/poojas/{pooja_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pooja(
    pooja_id: int,
    current_user: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    _check_permission(current_user, "pooja_management", db)
    pooja = db.query(Pooja).filter(Pooja.id == pooja_id).first()
    if not pooja:
        raise HTTPException(status_code=404, detail="Pooja not found")
    pooja.is_active = False; db.commit()
    return None


# ── Template management ───────────────────────────────────────────────────────

@router.post("/templates", response_model=SankalpamTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    template_data: SankalpamTemplateCreate,
    current_user: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    _check_permission(current_user, "template_management", db)
    if not template_data.template_text.strip():
        raise HTTPException(status_code=400, detail="Template text cannot be empty")
    variables = identify_variables(template_data.template_text)
    language_value = template_data.language
    if isinstance(language_value, Language):
        language_value = language_value.value
    elif isinstance(language_value, str):
        try:
            language_value = Language(language_value.lower()).value
        except ValueError:
            language_value = Language.SANSKRIT.value
    template = SankalpamTemplate(
        name=template_data.name, description=template_data.description,
        template_text=template_data.template_text, language=language_value,
        variables=json.dumps(variables), created_by=current_user.id, is_active=True,
    )
    db.add(template); db.commit(); db.refresh(template)
    return template


@router.post("/templates/upload-file", response_model=SankalpamTemplateResponse, status_code=status.HTTP_201_CREATED)
async def upload_template_from_file(
    file: UploadFile = File(...), name: str = Form(...),
    description: Optional[str] = Form(None), language: str = Form("sanskrit"),
    current_user: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    _check_permission(current_user, "template_management", db)
    allowed_extensions = ['.txt', '.md', '.text', '.markdown']
    file_ext = '.' + file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        raise HTTPException(status_code=400, detail=f"Only text files supported: {', '.join(allowed_extensions)}")
    try:
        content = await file.read()
        template_text = content.decode('utf-8')
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
    if not template_text.strip():
        raise HTTPException(status_code=400, detail="Template file is empty")
    variables = identify_variables(template_text)
    template = SankalpamTemplate(
        name=name, description=description, template_text=template_text,
        language=language, variables=json.dumps(variables),
        created_by=current_user.id, is_active=True,
    )
    db.add(template); db.commit(); db.refresh(template)
    return template


@router.get("/templates", response_model=List[SankalpamTemplateResponse])
async def get_all_templates(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    _check_permission(current_user, "template_management", db)
    return db.query(SankalpamTemplate).all()


@router.get("/templates/{template_id}", response_model=SankalpamTemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    _check_permission(current_user, "template_management", db)
    template = db.query(SankalpamTemplate).filter(SankalpamTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.put("/templates/{template_id}", response_model=SankalpamTemplateResponse)
async def update_template(
    template_id: int, template_data: SankalpamTemplateCreate,
    current_user: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    _check_permission(current_user, "template_management", db)
    template = db.query(SankalpamTemplate).filter(SankalpamTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    language_value = template_data.language
    if isinstance(language_value, Language):
        language_value = language_value.value
    elif isinstance(language_value, str):
        try:
            language_value = Language(language_value.lower()).value
        except ValueError:
            language_value = Language.SANSKRIT.value
    template.name = template_data.name; template.description = template_data.description
    template.template_text = template_data.template_text; template.language = language_value
    template.variables = json.dumps(identify_variables(template_data.template_text))
    db.commit(); db.refresh(template)
    return template


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_admin_user), db: Session = Depends(get_db),
):
    _check_permission(current_user, "template_management", db)
    template = db.query(SankalpamTemplate).filter(SankalpamTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template); db.commit()
    return None


# ── Database explorer (PHPMyAdmin-like) ────────────────────────────────────

DB_EXCLUDED_TABLES = {"alembic_version"}

# Never allow editing sensitive columns through the generic editor.
def _is_blocked_edit_column(column_name: str) -> bool:
    name = (column_name or "").lower()
    if name == "hashed_password":
        return True
    if "token" in name:
        return True
    return False


def _jsonify_db_value(val: Any) -> Any:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, enum.Enum):
        return val.value
    if isinstance(val, decimal.Decimal):
        return str(val)
    return val


def _coerce_cell_value(column_name: str, column_type: Any, raw: Any) -> Any:
    """
    Best-effort coercion for common SQL types.
    For complex types (json/text blobs), we keep as-is (string).
    """
    if raw is None:
        return None

    if isinstance(raw, str):
        s = raw.strip()
        if s == "":
            return None
    else:
        s = raw

    if isinstance(column_type, sqltypes.Boolean):
        if isinstance(raw, bool):
            return raw
        if isinstance(raw, (int, float)):
            return bool(raw)
        sval = str(raw).strip().lower()
        return sval in {"1", "true", "t", "yes", "y"}

    if isinstance(column_type, (sqltypes.Integer, sqltypes.BigInteger, sqltypes.SmallInteger)):
        return int(raw)

    if isinstance(column_type, (sqltypes.Float,)):
        return float(raw)

    if isinstance(column_type, sqltypes.Numeric):
        return decimal.Decimal(str(raw))

    if isinstance(column_type, sqltypes.DateTime):
        if isinstance(raw, datetime):
            return raw
        if isinstance(raw, str):
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))

    # Enums and other types: pass through.
    return raw


def _truncate_cell_value(val: Any, max_len: int) -> Any:
    if val is None:
        return None
    if isinstance(val, str) and len(val) > max_len:
        return val[:max_len] + "…"
    return val


def _validate_table_name(table_name: str, current_tables: set[str]) -> None:
    if table_name not in current_tables:
        raise HTTPException(status_code=404, detail="Table not found")


class DbRowPk(BaseModel):
    pk: Dict[str, Any]


class DbRowUpdate(BaseModel):
    pk: Dict[str, Any]
    values: Dict[str, Any]


@router.get("/db/tables")
async def list_db_tables(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "db_table_management", db)
    inspector = sqla_inspect(engine)
    tables = inspector.get_table_names()
    tables = [t for t in tables if t not in DB_EXCLUDED_TABLES]
    tables.sort()
    return {"tables": tables}


@router.get("/db/tables/{table_name}/meta")
async def db_table_meta(
    table_name: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "db_table_management", db)
    inspector = sqla_inspect(engine)
    current_tables = set(inspector.get_table_names())
    current_tables = {t for t in current_tables if t not in DB_EXCLUDED_TABLES}
    _validate_table_name(table_name, current_tables)

    pk_constraint = inspector.get_pk_constraint(table_name) or {}
    pk_cols = pk_constraint.get("constrained_columns") or []

    columns_raw = inspector.get_columns(table_name)
    columns = []
    for c in columns_raw:
        col_name = c.get("name")
        col_type = c.get("type")
        editable = (col_name not in pk_cols) and (not _is_blocked_edit_column(col_name or ""))
        columns.append({
            "name": col_name,
            "sql_type": str(col_type),
            "is_primary_key": col_name in pk_cols,
            "is_editable": editable,
        })

    return {
        "table": table_name,
        "primary_key": pk_cols,
        "columns": columns,
    }


@router.get("/db/tables/{table_name}/rows")
async def db_table_rows(
    table_name: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    max_cell_length: int = Query(250, ge=50, le=2000),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "db_table_management", db)
    inspector = sqla_inspect(engine)
    current_tables = set(inspector.get_table_names())
    current_tables = {t for t in current_tables if t not in DB_EXCLUDED_TABLES}
    _validate_table_name(table_name, current_tables)

    metadata = MetaData()
    tbl = Table(table_name, metadata, autoload_with=engine)
    pk_cols = [c.name for c in tbl.primary_key.columns]

    rows = db.execute(select(tbl).limit(limit).offset(offset)).mappings().all()
    out_rows: list[dict[str, Any]] = []
    for r in rows:
        obj: dict[str, Any] = {}
        for col in tbl.columns:
            v = r[col.name]
            v = _jsonify_db_value(v)
            v = _truncate_cell_value(v, max_cell_length)
            obj[col.name] = v
        out_rows.append(obj)

    return {
        "table": table_name,
        "primary_key": pk_cols,
        "offset": offset,
        "limit": limit,
        "rows": out_rows,
    }


@router.post("/db/tables/{table_name}/row")
async def db_fetch_full_row(
    table_name: str,
    body: DbRowPk,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "db_table_management", db)
    inspector = sqla_inspect(engine)
    current_tables = set(inspector.get_table_names())
    current_tables = {t for t in current_tables if t not in DB_EXCLUDED_TABLES}
    _validate_table_name(table_name, current_tables)

    metadata = MetaData()
    tbl = Table(table_name, metadata, autoload_with=engine)
    pk_cols = [c.name for c in tbl.primary_key.columns]
    if not pk_cols:
        raise HTTPException(status_code=400, detail="Table has no primary key")

    missing = [c for c in pk_cols if c not in body.pk]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing PK fields: {missing}")

    where = and_(*[
        tbl.c[pk] == _coerce_cell_value(pk, tbl.c[pk].type, body.pk[pk])
        for pk in pk_cols
    ])

    row = db.execute(select(tbl).where(where)).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Row not found")

    values: dict[str, Any] = {}
    for col in tbl.columns:
        values[col.name] = _jsonify_db_value(row[col.name])

    return {
        "table": table_name,
        "primary_key": pk_cols,
        "values": values,
    }


@router.patch("/db/tables/{table_name}/row")
async def db_update_row(
    table_name: str,
    body: DbRowUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "db_table_management", db)
    inspector = sqla_inspect(engine)
    current_tables = set(inspector.get_table_names())
    current_tables = {t for t in current_tables if t not in DB_EXCLUDED_TABLES}
    _validate_table_name(table_name, current_tables)

    metadata = MetaData()
    tbl = Table(table_name, metadata, autoload_with=engine)
    pk_cols = [c.name for c in tbl.primary_key.columns]
    if not pk_cols:
        raise HTTPException(status_code=400, detail="Table has no primary key (update blocked)")

    # Validate PK
    missing = [c for c in pk_cols if c not in body.pk]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing PK fields: {missing}")

    # Validate editable columns
    values: dict[str, Any] = {}
    for col_name, raw in (body.values or {}).items():
        if col_name in pk_cols:
            raise HTTPException(status_code=400, detail=f"Editing primary key column '{col_name}' is not allowed")
        if col_name not in tbl.c:
            raise HTTPException(status_code=400, detail=f"Unknown column '{col_name}'")
        if _is_blocked_edit_column(col_name):
            raise HTTPException(status_code=403, detail=f"Editing blocked column '{col_name}' is not allowed")

        values[col_name] = _coerce_cell_value(col_name, tbl.c[col_name].type, raw)

    if not values:
        raise HTTPException(status_code=400, detail="No valid editable columns supplied")

    # Build WHERE from PK columns
    where = and_(*[
        tbl.c[pk] == _coerce_cell_value(pk, tbl.c[pk].type, body.pk[pk])
        for pk in pk_cols
    ])

    stmt = sql_update(tbl).where(where).values(values)
    db.execute(stmt)
    db.commit()

    updated = db.execute(select(tbl).where(where)).mappings().first()
    if not updated:
        raise HTTPException(status_code=404, detail="Row not found after update")

    updated_values: dict[str, Any] = {}
    for col in tbl.columns:
        updated_values[col.name] = _jsonify_db_value(updated[col.name])

    return {"table": table_name, "primary_key": pk_cols, "values": updated_values}


@router.post("/db/tables/{table_name}/row/delete")
async def db_delete_row(
    table_name: str,
    body: DbRowPk,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    _check_permission(current_user, "db_table_management", db)
    inspector = sqla_inspect(engine)
    current_tables = set(inspector.get_table_names())
    current_tables = {t for t in current_tables if t not in DB_EXCLUDED_TABLES}
    _validate_table_name(table_name, current_tables)

    metadata = MetaData()
    tbl = Table(table_name, metadata, autoload_with=engine)
    pk_cols = [c.name for c in tbl.primary_key.columns]
    if not pk_cols:
        raise HTTPException(status_code=400, detail="Table has no primary key (delete blocked)")

    missing = [c for c in pk_cols if c not in body.pk]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing PK fields: {missing}")

    where = and_(*[
        tbl.c[pk] == _coerce_cell_value(pk, tbl.c[pk].type, body.pk[pk])
        for pk in pk_cols
    ])

    db.execute(sql_delete(tbl).where(where))
    db.commit()
    return {"deleted": True}


# ── Internal email helper ─────────────────────────────────────────────────────

def _send_admin_reset_email(to_email: str, username: str, new_password: str) -> bool:
    import smtplib, os
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    email_from = os.getenv("EMAIL_FROM", "noreply@poojasankalpam.com")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    if not smtp_user or not smtp_password:
        print(f"\n{'='*60}")
        print(f"ADMIN PASSWORD RESET (dev mode)")
        print(f"To      : {to_email}")
        print(f"Username: {username}")
        print(f"New pwd : {new_password}")
        print(f"{'='*60}\n")
        return True

    try:
        html = f"""
<!DOCTYPE html>
<html>
<head>
  <style>
    body{{font-family:Arial,sans-serif;line-height:1.6;color:#333}}
    .container{{max-width:600px;margin:0 auto;padding:20px}}
    .header{{background:#ea580c;color:white;padding:20px;text-align:center;border-radius:5px 5px 0 0}}
    .content{{background:#f9fafb;padding:30px;border-radius:0 0 5px 5px}}
    .pwd{{background:#1e293b;color:#f1f5f9;padding:14px 20px;border-radius:6px;font-family:monospace;font-size:20px;letter-spacing:2px;text-align:center;margin:16px 0}}
    .btn{{display:inline-block;padding:12px 28px;background:#ea580c;color:white;text-decoration:none;border-radius:6px;margin:12px 0;font-weight:bold}}
    .footer{{text-align:center;margin-top:20px;color:#6b7280;font-size:12px}}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>Your Password Has Been Reset</h1></div>
    <div class="content">
      <p>Hello <strong>{username}</strong>,</p>
      <p>An administrator has reset your Pooja Sankalpam account password.</p>
      <p>Your new temporary password is:</p>
      <div class="pwd">{new_password}</div>
      <p style="text-align:center">
        <a href="{frontend_url}/login" class="btn">Login Now</a>
      </p>
      <p><strong>Important:</strong> Please change this password immediately after logging in.</p>
      <p>If you did not request this reset, please contact support immediately.</p>
      <div class="footer"><p>Pooja Sankalpam Team</p></div>
    </div>
  </div>
</body>
</html>"""

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your Pooja Sankalpam Password Has Been Reset"
        msg['From'] = email_from
        msg['To'] = to_email
        msg.attach(MIMEText(f"Your new temporary password is: {new_password}\nLogin at: {frontend_url}/login", 'plain'))
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email send failed: {e}")
        return False
