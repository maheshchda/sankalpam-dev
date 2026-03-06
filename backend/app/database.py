import re
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)


def _mask_url(url: str) -> str:
    """Return URL with password replaced by ***"""
    return re.sub(r"(://[^:@]+:)[^@]+(@)", r"\1***\2", url)


def _resolve_db_url(url: str) -> str:
    """
    Rewrites a Supabase direct-connection URL to the session-pooler URL.
    This is required on Railway (and any IPv4-only host) because the direct
    Supabase host resolves to an IPv6 address that those platforms cannot reach.

    Direct:  postgresql://postgres:PASS@db.PROJECT.supabase.co:5432/postgres
    Pooler:  postgresql://postgres.PROJECT:PASS@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
    """
    # Already using the pooler — leave unchanged
    if "pooler.supabase.com" in url:
        logger.info("DATABASE_URL: already using Supabase pooler → %s", _mask_url(url))
        return url

    match = re.match(
        r"(postgresql(?:\+\w+)?|postgres)://([^:@]+):([^@]*)@db\.([^.]+)\.supabase\.co(?::\d+)?/(.+)",
        url,
    )
    if not match:
        logger.info("DATABASE_URL: not a direct Supabase URL, using as-is → %s", _mask_url(url))
        return url

    scheme, _user, password, project_ref, dbname = match.groups()
    dbname = dbname.split("?")[0]  # strip any existing query params

    pooler_url = (
        f"{scheme}://postgres.{project_ref}:{password}"
        f"@aws-0-us-east-1.pooler.supabase.com:5432/{dbname}?sslmode=require"
    )
    logger.info(
        "DATABASE_URL: rewrote direct Supabase URL to pooler → %s",
        _mask_url(pooler_url),
    )
    return pooler_url


_db_url = _resolve_db_url(settings.database_url)

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

