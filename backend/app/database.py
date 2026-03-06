import os
import re
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

# Known Supabase project details (confirmed via MCP)
_SUPABASE_PROJECT_REF = "ywdbaxurlxvoqzdkaqik"
_SUPABASE_POOLER_HOST = "aws-0-us-east-1.pooler.supabase.com"


def _mask_url(url: str) -> str:
    return re.sub(r"(://[^:@]+:)[^@]+(@)", r"\1***\2", url)


def _resolve_db_url() -> str:
    """
    Build the correct Supabase session-pooler DATABASE_URL.

    Priority order:
    1. SUPABASE_DB_PASSWORD env var  → build URL from scratch using known project ref
    2. DATABASE_URL env var that is already a pooler URL → use as-is
    3. DATABASE_URL env var that is a direct Supabase URL → convert to pooler
    4. DATABASE_URL as-is (local dev, non-Supabase)
    """
    raw_url = settings.database_url

    # ── Priority 1: explicit password override ────────────────────────────────
    # If SUPABASE_DB_PASSWORD is set in Railway, we build the correct URL
    # with the known project ref, bypassing any URL-parsing issues entirely.
    supabase_pw = os.environ.get("SUPABASE_DB_PASSWORD", "").strip()
    if supabase_pw:
        url = (
            f"postgresql://postgres.{_SUPABASE_PROJECT_REF}:{supabase_pw}"
            f"@{_SUPABASE_POOLER_HOST}:5432/postgres?sslmode=require"
        )
        logger.info("DATABASE_URL: built from SUPABASE_DB_PASSWORD → %s", _mask_url(url))
        return url

    # ── Priority 2: URL already points to pooler ─────────────────────────────
    if "pooler.supabase.com" in raw_url:
        logger.info("DATABASE_URL: already using Supabase pooler → %s", _mask_url(raw_url))
        return raw_url

    # ── Priority 3: direct Supabase connection URL → convert ─────────────────
    match = re.match(
        r"(postgresql(?:\+\w+)?|postgres)://([^:@]+):([^@]*)@db\.([^.]+)\.supabase\.co(?::\d+)?/([^?]+)",
        raw_url,
    )
    if match:
        scheme, _user, password, project_ref, dbname = match.groups()
        url = (
            f"{scheme}://postgres.{project_ref}:{password}"
            f"@{_SUPABASE_POOLER_HOST}:5432/{dbname}?sslmode=require"
        )
        logger.info("DATABASE_URL: rewrote direct→pooler → %s", _mask_url(url))
        return url

    # ── Priority 4: local / non-Supabase URL ─────────────────────────────────
    logger.info("DATABASE_URL: using as-is → %s", _mask_url(raw_url))
    return raw_url


_db_url = _resolve_db_url()

engine = create_engine(
    _db_url,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

