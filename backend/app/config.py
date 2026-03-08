from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # Database (reads DB_CONNECTION_STRING or DATABASE_URL)
    db_connection_string: str = ""
    database_url: str = "postgresql://user:password@localhost:5432/sankalpam_db"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # DivineAPI (Indian API - Daily Panchang only; no separate Sankalpam API used)
    # We use Find Panchang for tithi, nakshatra, yoga, karana. Sankalpam text is from our own templates.
    # In Divine dashboard you may only see "Default Key" - use it for both key and token if only one is shown.
    divine_api_key: str = ""  # .env: Divine_API_Key or DIVINE_API_KEY
    divine_access_token: str = ""  # .env: Divine_Access_Token or DIVINE_ACCESS_TOKEN (Bearer token)
    divineapi_key: str = ""  # Legacy - will be set to divine_api_key if empty
    divineapi_base_url: str = "https://api.divineapi.com"
    
    # Google Maps
    google_maps_api_key: str = ""
    
    # Google Cloud TTS (optional, for professional priest-like voice)
    google_cloud_tts_credentials_path: str = ""
    
    # ElevenLabs Voice Cloning (optional, for custom voice - paid)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""  # Voice ID of cloned voice for Sankalpam
    
    # XTTS-v2 Voice Cloning (optional, for custom voice - FREE & OPEN SOURCE)
    xtts_reference_audio_path: str = ""  # Path to reference voice audio file (6+ seconds)
    xtts_language: str = "hi"  # Language code: hi (Hindi/Sanskrit), en, etc.
    use_xtts: bool = False  # Set to True to use XTTS-v2 instead of other TTS services
    
    # Email Service (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""  # SMTP username (usually your email)
    smtp_password: str = ""  # SMTP password or app password
    email_from: str = "noreply@sankalpam.com"
    frontend_url: str = "http://localhost:3000"  # Frontend URL for verification links
    
    # SMS Service (Brevo Transactional SMS - same account as email)
    brevo_api_key: str = ""  # Brevo API key (Settings -> SMTP & API -> API Keys)
    sms_sender: str = "Sankalpam"  # Sender name (max 11 alphanumeric chars)
    
    # File Storage
    upload_path: str = "uploads"
    audio_storage_path: str = "uploads/audio"
    pdf_storage_path: str = "uploads/templates"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields from .env that aren't in this model
    )

# Initialize settings
settings = Settings()

# Map .env variable names to our settings (supports multiple name formats)
# Divine_API_Key -> divine_api_key
# Divine_Access_Token -> divine_access_token
import os
env_divine_key = os.getenv("Divine_API_Key") or os.getenv("DIVINE_API_KEY") or os.getenv("divine_api_key")
env_divine_token = os.getenv("Divine_Access_Token") or os.getenv("DIVINE_ACCESS_TOKEN") or os.getenv("divine_access_token")

if env_divine_key and not settings.divine_api_key:
    settings.divine_api_key = env_divine_key
if env_divine_token and not settings.divine_access_token:
    settings.divine_access_token = env_divine_token

# If only API key is set (e.g. Divine dashboard shows only "Default Key"), use it as token too
if settings.divine_api_key and not settings.divine_access_token:
    settings.divine_access_token = settings.divine_api_key

# Set legacy divineapi_key for backward compatibility
if settings.divine_api_key and not settings.divineapi_key:
    settings.divineapi_key = settings.divine_api_key

