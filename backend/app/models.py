from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from app.database import Base

class Language(str, enum.Enum):
    HINDI = "hindi"
    TELUGU = "telugu"
    TAMIL = "tamil"
    KANNADA = "kannada"
    MALAYALAM = "malayalam"
    SANSKRIT = "sanskrit"
    ENGLISH = "english"
    MARATHI = "marathi"
    GUJARATI = "gujarati"
    BENGALI = "bengali"
    ORIYA = "oriya"
    PUNJABI = "punjabi"

class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gotram = Column(String(100), nullable=False)
    
    # Birth Information
    birth_city = Column(String(100), nullable=False)
    birth_state = Column(String(100), nullable=False)
    birth_country = Column(String(100), nullable=False)
    birth_time = Column(String(10), nullable=False)  # 24 hour format HH:MM
    birth_date = Column(DateTime, nullable=False)
    
    # Preferences
    preferred_language = Column(SQLEnum(Language), default=Language.SANSKRIT, nullable=False)
    
    # Verification Status
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    family_members = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    verification_tokens = relationship("VerificationToken", back_populates="user", cascade="all, delete-orphan")

class FamilyMember(Base):
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    relation = Column(String(50), nullable=False)  # father, mother, spouse, child, etc.
    gender = Column(SQLEnum(Gender), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    birth_time = Column(String(10), nullable=False)  # 24 hour format HH:MM
    
    # Place of Birth
    birth_city = Column(String(100), nullable=False)
    birth_state = Column(String(100), nullable=False)
    birth_country = Column(String(100), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="family_members")

class VerificationToken(Base):
    __tablename__ = "verification_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    token_type = Column(String(20), nullable=False)  # email or phone
    status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="verification_tokens")

class Pooja(Base):
    __tablename__ = "poojas"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    duration_minutes = Column(Integer)  # Estimated duration
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))  # Admin user
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class PoojaSession(Base):
    __tablename__ = "pooja_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pooja_id = Column(Integer, ForeignKey("poojas.id"), nullable=False)
    
    # Location for Sankalpam
    location_city = Column(String(100))
    location_state = Column(String(100))
    location_country = Column(String(100))
    latitude = Column(String(20))
    longitude = Column(String(20))
    nearby_river = Column(String(200))
    
    # Generated Sankalpam
    sankalpam_text = Column(Text)
    sankalpam_audio_url = Column(String(500))
    
    status = Column(String(20), default="pending")  # pending, in_progress, completed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User")
    pooja = relationship("Pooja")

class SankalpamTemplate(Base):
    __tablename__ = "sankalpam_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # Template content stored directly in database (supports text, markdown, etc.)
    template_text = Column(Text, nullable=False)
    
    # Template metadata
    language = Column(SQLEnum(Language), default=Language.SANSKRIT, nullable=False)
    variables = Column(Text)  # JSON string of available variables in the template
    
    # Admin metadata
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
