from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import secrets
from app.database import Base

_UID_CHARS = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # 32 unambiguous chars

def _gen_uid(prefix: str) -> str:
    return prefix + '-' + ''.join(secrets.choice(_UID_CHARS) for _ in range(8))

class Language(str, enum.Enum):
    """Language enum: value is display name; use .code for ISO 639-1 (e.g. Telugu -> 'te')."""
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

    # ISO 639-1 two-letter codes for language selection / APIs
    @property
    def code(self) -> str:
        return _LANGUAGE_TO_ISO.get(self.value, "en")

    @classmethod
    def from_code(cls, code: str) -> "Language":
        """Return Language enum for ISO code (e.g. 'te' -> Language.TELUGU)."""
        c = (code or "").strip().lower()
        name = _ISO_TO_LANGUAGE.get(c, "sanskrit")
        return cls(name)


# Map language name -> ISO 639-1 code (used for selection and external APIs)
_LANGUAGE_TO_ISO = {
    "hindi": "hi",
    "telugu": "te",
    "tamil": "ta",
    "kannada": "kn",
    "malayalam": "ml",
    "sanskrit": "sa",
    "english": "en",
    "marathi": "mr",
    "gujarati": "gu",
    "bengali": "bn",
    "oriya": "or",
    "punjabi": "pa",
}
_ISO_TO_LANGUAGE = {v: k for k, v in _LANGUAGE_TO_ISO.items()}

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
    unique_id = Column(String(15), unique=True, index=True, nullable=True)
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
    birth_nakshatra = Column(String(50), nullable=True)  # Janma Nakshatra (Birth Star)
    birth_rashi = Column(String(50), nullable=True)  # Janma Raasi (Birth Zodiac Sign)
    birth_pada = Column(String(10), nullable=True)  # Janma Pada (1–4)
    
    # Current address (where user currently lives; used e.g. for Pooja location default)
    current_city = Column(String(100), nullable=True)
    current_state = Column(String(100), nullable=True)
    current_country = Column(String(100), nullable=True)

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
    admin_roles = relationship("UserAdminRole", foreign_keys="UserAdminRole.user_id", back_populates="user", cascade="all, delete-orphan")

class FamilyMember(Base):
    __tablename__ = "family_members"
    
    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String(15), unique=True, index=True, nullable=True)
    linked_user_id = Column(String(15), index=True, nullable=True)
    source_unique_id = Column(String(15), index=True, nullable=True)  # FM-xxx from another family when added by Unique ID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    relation = Column(String(50), nullable=False)  # father, mother, spouse, child, etc.
    gender = Column(SQLEnum(Gender), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    birth_time = Column(String(10), nullable=True)  # 24 hour format HH:MM
    birth_nakshatra = Column(String(50), nullable=True)  # Janma Nakshatra (Birth Star)
    birth_rashi = Column(String(50), nullable=True)  # Janma Raasi (Birth Zodiac Sign)
    birth_pada = Column(String(10), nullable=True)  # Janma Pada (1–4)
    
    # Place of Birth
    birth_city = Column(String(100), nullable=False)
    birth_state = Column(String(100), nullable=False)
    birth_country = Column(String(100), nullable=False)

    # Marital status (for RSVP: married sons/daughters excluded — they have their own households)
    is_married = Column(Boolean, default=False, nullable=False)

    # Deceased info
    is_deceased = Column(Boolean, default=False, nullable=False)
    date_of_death = Column(DateTime, nullable=True)
    time_of_death = Column(String(10), nullable=True)   # 24 hour format HH:MM
    death_city = Column(String(100), nullable=True)
    death_state = Column(String(100), nullable=True)
    death_country = Column(String(100), nullable=True)

    # Panchang on the day of death (auto-filled via Divine API)
    death_tithi    = Column(String(100), nullable=True)
    death_paksha   = Column(String(50),  nullable=True)
    death_nakshatra= Column(String(100), nullable=True)
    death_vara     = Column(String(50),  nullable=True)   # Weekday (Vara)
    death_yoga     = Column(String(100), nullable=True)
    death_karana   = Column(String(100), nullable=True)

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
    state_codes = Column(Text, nullable=True)  # JSON array e.g. ["IN-TN","IN-KA"]; null = all states
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

# ── Admin Roles ───────────────────────────────────────────────────────────────

# All available granular permissions
ALL_PERMISSIONS = [
    ("user_management",      "Activate / Deactivate users and view user list"),
    ("user_password_reset",  "Reset user passwords and send email notifications"),
    ("user_verification",    "Manually verify user emails and phone numbers"),
    ("template_management",  "Create, edit and delete Sankalpam templates"),
    ("pooja_management",     "Create, edit and delete Poojas"),
    ("view_stats",           "View dashboard statistics and reports"),
    ("role_management",      "Create, edit and delete admin roles"),
    ("admin_management",     "Grant or revoke admin access for users"),
]

PERMISSION_CODES = [p[0] for p in ALL_PERMISSIONS]


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=False, default="[]")   # JSON list of permission codes
    is_system_role = Column(Boolean, default=False)            # System roles cannot be deleted
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user_roles = relationship("UserAdminRole", back_populates="role", cascade="all, delete-orphan")


class UserAdminRole(Base):
    __tablename__ = "user_admin_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("admin_roles.id"), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id], back_populates="admin_roles")
    role = relationship("AdminRole", back_populates="user_roles")


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


class PoojaSchedule(Base):
    __tablename__ = "pooja_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pooja_id = Column(Integer, ForeignKey("poojas.id"), nullable=True)
    pooja_name = Column(String(200), nullable=True)        # snapshot / free-text fallback
    scheduled_date = Column(DateTime, nullable=False)
    invite_message = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=True)

    # Venue
    venue_place = Column(String(200), nullable=True)       # Event hall / temple name
    venue_street_number = Column(String(50), nullable=True)
    venue_street_name = Column(String(200), nullable=True)
    venue_city = Column(String(100), nullable=True)
    venue_state = Column(String(100), nullable=True)
    venue_country = Column(String(100), nullable=True)
    venue_coordinates = Column(String(150), nullable=True) # lat,lng or Google Maps URL

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    pooja = relationship("Pooja")
    invitees = relationship("PoojaScheduleInvitee", back_populates="schedule", cascade="all, delete-orphan")


class PoojaScheduleInvitee(Base):
    __tablename__ = "pooja_schedule_invitees"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("pooja_schedules.id"), nullable=False)
    name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=True)
    email = Column(String(200), nullable=False)

    # RSVP fields
    rsvp_token = Column(String(64), unique=True, index=True, nullable=True)
    rsvp_status = Column(String(20), default="pending")   # pending / attending / not_attending / maybe
    rsvp_unique_id = Column(String(15), nullable=True)     # Sankalpam Unique ID of the responder
    attending_members = Column(Text, nullable=True)        # JSON list of unique_ids attending
    rsvp_notes = Column(Text, nullable=True)
    rsvp_updated_at = Column(DateTime(timezone=True), nullable=True)

    # Cancel invite (host-initiated)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_reason = Column(Text, nullable=True)

    # Brevo delivery tracking (sent, delivered, hard_bounce, soft_bounce, etc.)
    last_email_message_id = Column(String(255), nullable=True)
    email_delivery_status = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    schedule = relationship("PoojaSchedule", back_populates="invitees")
