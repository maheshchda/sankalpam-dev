from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import UserResponse, UserUpdate
from app.dependencies import get_current_user
from app.auth import verify_password, get_password_hash

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user's profile information"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.
    User can update all fields except username, email, phone (these require separate verification process).
    """
    # Update allowed fields
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    if user_update.gotram is not None:
        current_user.gotram = user_update.gotram
    if user_update.birth_city is not None:
        current_user.birth_city = user_update.birth_city
    if user_update.birth_state is not None:
        current_user.birth_state = user_update.birth_state
    if user_update.birth_country is not None:
        current_user.birth_country = user_update.birth_country
    if user_update.birth_time is not None:
        current_user.birth_time = user_update.birth_time
    if user_update.birth_date is not None:
        current_user.birth_date = user_update.birth_date
    if user_update.birth_nakshatra is not None:
        current_user.birth_nakshatra = user_update.birth_nakshatra
    if user_update.birth_rashi is not None:
        current_user.birth_rashi = user_update.birth_rashi
    if getattr(user_update, "birth_pada", None) is not None:
        current_user.birth_pada = user_update.birth_pada
    if user_update.preferred_language is not None:
        current_user.preferred_language = user_update.preferred_language
    if user_update.current_city is not None:
        current_user.current_city = user_update.current_city
    if user_update.current_state is not None:
        current_user.current_state = user_update.current_state
    if user_update.current_country is not None:
        current_user.current_country = user_update.current_country

    # Handle password update if provided
    if user_update.password is not None:
        current_user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user's account.
    This will also delete all associated family members and pooja sessions.
    """
    db.delete(current_user)
    db.commit()
    return None

