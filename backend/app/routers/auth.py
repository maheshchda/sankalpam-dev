from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
import secrets
from datetime import datetime

from app.database import get_db
from app.models import User, VerificationToken, VerificationStatus
from app.schemas import UserCreate, UserResponse, Token, LoginRequest, VerificationRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.auth import verify_password, get_password_hash, create_access_token
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if username exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=400,
                detail="Username already registered"
            )
        
        # Check if email exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )
        
        # Check if phone exists
        if db.query(User).filter(User.phone == user_data.phone).first():
            raise HTTPException(
                status_code=400,
                detail="Phone number already registered"
            )
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            hashed_password=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            gotram=user_data.gotram,
            birth_city=user_data.birth_city,
            birth_state=user_data.birth_state,
            birth_country=user_data.birth_country,
            birth_time=user_data.birth_time,
            birth_date=user_data.birth_date,
            preferred_language=user_data.preferred_language
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Generate verification tokens
        # Email verification token
        email_token = secrets.token_urlsafe(32)
        db_email_token = VerificationToken(
            user_id=db_user.id,
            token=email_token,
            token_type="email",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        db.add(db_email_token)
        
        # Phone verification token (OTP)
        phone_otp = f"{secrets.randbelow(900000) + 100000:06d}"  # 6 digit OTP
        db_phone_token = VerificationToken(
            user_id=db_user.id,
            token=phone_otp,
            token_type="phone",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.add(db_phone_token)
        
        db.commit()
        
        # TODO: Send verification email and SMS
        # send_verification_email(db_user.email, email_token)
        # send_verification_sms(db_user.phone, phone_otp)
        
        return db_user
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/verify", status_code=status.HTTP_200_OK)
async def verify_account(verification: VerificationRequest, db: Session = Depends(get_db)):
    token_record = db.query(VerificationToken).filter(
        VerificationToken.token == verification.token,
        VerificationToken.status == VerificationStatus.PENDING
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired verification token"
        )
    
    if token_record.expires_at < datetime.utcnow():
        token_record.status = VerificationStatus.EXPIRED
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="Verification token has expired"
        )
    
    user = db.query(User).filter(User.id == token_record.user_id).first()
    
    if verification.verification_type == "email":
        user.email_verified = True
        token_record.status = VerificationStatus.VERIFIED
    elif verification.verification_type == "phone":
        user.phone_verified = True
        token_record.status = VerificationStatus.VERIFIED
    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid verification type"
        )
    
    db.commit()
    
    return {"message": f"{verification.verification_type} verified successfully"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset. Generates a reset token and stores it.
    In production, this token should be sent via email.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success (don't reveal if email exists)
    if not user:
        return {"message": "If an account with that email exists, password reset instructions have been sent."}
    
    # Invalidate any existing password reset tokens for this user
    existing_tokens = db.query(VerificationToken).filter(
        VerificationToken.user_id == user.id,
        VerificationToken.token_type == "password_reset",
        VerificationToken.status == VerificationStatus.PENDING
    ).all()
    
    for token in existing_tokens:
        token.status = VerificationStatus.EXPIRED
    db.commit()
    
    # Generate new password reset token
    reset_token = secrets.token_urlsafe(32)
    db_reset_token = VerificationToken(
        user_id=user.id,
        token=reset_token,
        token_type="password_reset",
        expires_at=datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
    )
    db.add(db_reset_token)
    db.commit()
    
    # TODO: Send password reset email with token
    # For now, in development, you can check the token in the database
    # In production, implement email sending:
    # send_password_reset_email(user.email, reset_token)
    
    return {
        "message": "If an account with that email exists, password reset instructions have been sent.",
        # Only include token in development - remove in production
        "reset_token": reset_token if settings.secret_key == "your-secret-key-change-in-production" else None
    }

@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid reset token.
    """
    # Find the reset token
    token_record = db.query(VerificationToken).filter(
        VerificationToken.token == request.token,
        VerificationToken.token_type == "password_reset",
        VerificationToken.status == VerificationStatus.PENDING
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired reset token"
        )
    
    # Check if token has expired
    if token_record.expires_at < datetime.utcnow():
        token_record.status = VerificationStatus.EXPIRED
        db.commit()
        raise HTTPException(
            status_code=400,
            detail="Reset token has expired. Please request a new one."
        )
    
    # Get the user
    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    
    # Mark token as used
    token_record.status = VerificationStatus.VERIFIED
    
    db.commit()
    
    return {"message": "Password has been reset successfully. You can now login with your new password."}