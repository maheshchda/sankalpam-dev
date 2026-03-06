import re
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings


def _resolve_db_url(url: str) -> str:
    """
    Rewrites a Supabase direct-connection URL to the session-pooler URL.
    This is required on Railway (and any IPv4-only host) because the direct
    Supabase host resolves to an IPv6 address that those platforms cannot reach.

    Direct:  postgresql://postgres:PASS@db.PROJECT.supabase.co:5432/postgres
    Pooler:  postgresql://postgres.PROJECT:PASS@aws-0-us-east-1.pooler.supabase.com:5432/postgres?sslmode=require
    """
    match = re.match(
        r"(postgresql(?:\+\w+)?|postgres)://([^:@]+):([^@]*)@db\.([^.]+)\.supabase\.co(?::\d+)?/(.+)",
        url,
    )
    if not match:
        return url  # not a direct Supabase URL — leave unchanged

    scheme, _user, password, project_ref, dbname = match.groups()
    dbname = dbname.split("?")[0]  # strip any existing query params

    pooler_url = (
        f"{scheme}://postgres.{project_ref}:{password}"
        f"@aws-0-us-east-1.pooler.supabase.com:5432/{dbname}?sslmode=require"
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

