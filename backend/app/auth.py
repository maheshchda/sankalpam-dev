from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.config import settings

# Use bcrypt directly to avoid passlib's internal bug detection issues
# Bcrypt has a 72-byte limit - we'll handle truncation manually

def _truncate_password_to_72_bytes(password: str) -> bytes:
    """
    Truncate password to exactly 72 bytes (bcrypt limit).
    Returns bytes representation of the truncated password.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        # Truncate to 72 bytes
        password_bytes = password_bytes[:72]
        # Remove any incomplete UTF-8 sequences at the end
        while password_bytes and (password_bytes[-1] & 0x80) and not (password_bytes[-1] & 0x40):
            password_bytes = password_bytes[:-1]
    return password_bytes

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash using bcrypt directly.
    Apply same truncation as get_password_hash for consistency.
    """
    if not plain_password or not hashed_password:
        return False
    
    try:
        # Truncate password to 72 bytes
        password_bytes = _truncate_password_to_72_bytes(plain_password)
        # Verify using bcrypt directly
        return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt directly.
    Bcrypt has a 72-byte limit. We truncate to ensure the password fits.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    
    # Truncate password to 72 bytes (bcrypt limit)
    password_bytes = _truncate_password_to_72_bytes(password)
    
    # Generate salt and hash using bcrypt directly
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string (bcrypt returns bytes)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None

