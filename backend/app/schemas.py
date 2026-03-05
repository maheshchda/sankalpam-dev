from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Union
from datetime import datetime, date
from app.models import Language, Gender

# User Schemas
class UserBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    gotram: str = Field(..., min_length=1, max_length=100)
    birth_city: str = Field(..., min_length=1, max_length=100)
    birth_state: str = Field(..., min_length=1, max_length=100)
    birth_country: str = Field(..., min_length=1, max_length=100)
    birth_time: str = Field(..., pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')  # 24 hour format
    birth_date: date
    birth_nakshatra: Optional[str] = Field(None, max_length=50)  # Janma Nakshatra (Birth Star)
    birth_rashi: Optional[str] = Field(None, max_length=50)  # Janma Raasi (Birth Zodiac Sign)
    birth_pada: Optional[str] = Field(None, max_length=10)  # Janma Pada (1–4)
    preferred_language: Language = Language.SANSKRIT
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    # Current address (optional; where user currently lives)
    current_city: Optional[str] = Field(None, max_length=100)
    current_state: Optional[str] = Field(None, max_length=100)
    current_country: Optional[str] = Field(None, max_length=100)

class UserCreate(UserBase):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)  # bcrypt limit is 72 bytes

class UserUpdate(BaseModel):
    """Schema for updating user profile - all fields optional"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    gotram: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_city: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_state: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_country: Optional[str] = Field(None, min_length=1, max_length=100)
    birth_time: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')  # 24 hour format
    birth_date: Optional[date] = None
    birth_nakshatra: Optional[str] = Field(None, max_length=50)  # Janma Nakshatra (Birth Star)
    birth_rashi: Optional[str] = Field(None, max_length=50)  # Janma Raasi (Birth Zodiac Sign)
    birth_pada: Optional[str] = Field(None, max_length=10)  # Janma Pada (1–4)
    preferred_language: Optional[Union[Language, str]] = None  # Accept enum or ISO code (e.g. 'te') or name ('telugu')
    password: Optional[str] = Field(None, min_length=8, max_length=72)  # Optional password update
    current_city: Optional[str] = Field(None, max_length=100)
    current_state: Optional[str] = Field(None, max_length=100)
    current_country: Optional[str] = Field(None, max_length=100)

    @field_validator("preferred_language", mode="before")
    @classmethod
    def normalize_preferred_language(cls, v):
        if v is None:
            return None
        if isinstance(v, Language):
            return v
        s = (v if isinstance(v, str) else str(v)).strip().lower()
        if not s:
            return None
        # Accept ISO 639-1 code (e.g. 'te') or full name (e.g. 'telugu')
        return Language.from_code(s) if len(s) == 2 else Language(s) if s in [e.value for e in Language] else None

class UserResponse(UserBase):
    id: int
    username: str
    email_verified: bool
    phone_verified: bool
    is_active: bool
    is_admin: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}

# Family Member Schemas
class FamilyMemberBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    relation: str = Field(..., min_length=1, max_length=50)
    gender: Gender
    date_of_birth: Optional[date] = None
    birth_time: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')  # 24 hour format HH:MM
    birth_nakshatra: Optional[str] = Field(None, max_length=50)  # Janma Nakshatra (Birth Star)
    birth_rashi: Optional[str] = Field(None, max_length=50)  # Janma Raasi (Birth Zodiac Sign)
    birth_pada: Optional[str] = Field(None, max_length=10)  # Janma Pada (1–4)
    birth_city: str = Field(..., min_length=1, max_length=100)
    birth_state: str = Field(..., min_length=1, max_length=100)
    birth_country: str = Field(..., min_length=1, max_length=100)
    is_deceased: bool = False
    date_of_death: Optional[date] = None
    time_of_death: Optional[str] = Field(None, pattern=r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$')
    death_city: Optional[str] = Field(None, max_length=100)
    death_state: Optional[str] = Field(None, max_length=100)
    death_country: Optional[str] = Field(None, max_length=100)
    # Panchang on the day of death (read-only from API; user can override)
    death_tithi: Optional[str] = Field(None, max_length=100)
    death_paksha: Optional[str] = Field(None, max_length=50)
    death_nakshatra: Optional[str] = Field(None, max_length=100)
    death_vara: Optional[str] = Field(None, max_length=50)
    death_yoga: Optional[str] = Field(None, max_length=100)
    death_karana: Optional[str] = Field(None, max_length=100)

class FamilyMemberCreate(FamilyMemberBase):
    pass

class FamilyMemberResponse(FamilyMemberBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}

# Pooja Schemas
class PoojaBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    duration_minutes: Optional[int] = None

class PoojaCreate(PoojaBase):
    pass

class PoojaResponse(PoojaBase):
    id: int
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}

# Pooja Session Schemas
class PoojaSessionCreate(BaseModel):
    pooja_id: int
    location_city: Optional[str] = None
    location_state: Optional[str] = None
    location_country: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None

class PoojaSessionResponse(BaseModel):
    id: int
    user_id: int
    pooja_id: int
    location_city: Optional[str]
    location_state: Optional[str]
    location_country: Optional[str]
    nearby_river: Optional[str]
    sankalpam_text: Optional[str]
    status: str
    started_at: datetime
    
    model_config = {"from_attributes": True}

# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class VerificationRequest(BaseModel):
    token: str
    verification_type: str  # email or phone

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=72)

# Sankalpam Schemas
class SankalpamRequest(BaseModel):
    session_id: int
    location_city: str
    location_state: str
    location_country: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    timezone_offset_hours: Optional[float] = None  # e.g. -6 for US Central; from browser when possible
    language_code: Optional[str] = None  # e.g. 'te', 'sa', 'hi' — overrides user profile for this request

class SankalpamResponse(BaseModel):
    sankalpam_text: str
    nearby_river: str
    session_id: int
    sankalpam_audio_url: Optional[str] = None  # e.g. /audio/uuid.mp3 when TTS succeeds

# Template Schemas
class SankalpamTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    language: Language = Language.SANSKRIT

class SankalpamTemplateCreate(SankalpamTemplateBase):
    template_text: str = Field(..., min_length=1)  # Direct text input

class SankalpamTemplateResponse(SankalpamTemplateBase):
    id: int
    template_text: str
    variables: Optional[str] = None  # JSON string
    created_by: int
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}

class TemplateGenerateRequest(BaseModel):
    template_id: int
    session_id: Optional[int] = None
    location_city: str
    location_state: str
    location_country: str
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    date: Optional[datetime] = None
    pooja_name: Optional[str] = None

class TemplateGenerateResponse(BaseModel):
    text: str
    audio_url: str
    variables_used: Dict[str, str]
    session_id: Optional[int] = None

