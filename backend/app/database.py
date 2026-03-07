import os
import re
import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

logger = logging.getLogger(__name__)

_SUPABASE_PROJECT_REF = "ywdbaxurlxvoqzdkaqik"
_SUPABASE_POOLER_HOST = "aws-1-us-east-1.pooler.supabase.com"


def _mask_url(url: str) -> str:
    return re.sub(r"(://[^:@]+:)[^@]+(@)", r"\1***\2", url)


def _resolve_db_url() -> str:
    """
    Build the correct Supabase session-pooler DATABASE_URL.

    Priority order:
    1. SUPABASE_DB_PASSWORD env var  → build URL from scratch (always correct)
    2. DB_CONNECTION_STRING env var  → use as-is
    3. DATABASE_URL already points to pooler with correct username → use as-is
    4. DATABASE_URL points to pooler but username is missing project ref → fix username
    5. DATABASE_URL is a direct Supabase URL (db.PROJECT.supabase.co) → convert to pooler
    6. DATABASE_URL as-is (local dev / non-Supabase)
    """
    raw_url = settings.db_connection_string or settings.database_url

    # ── Priority 1: explicit password ─────────────────────────────────────────
    supabase_pw = os.environ.get("SUPABASE_DB_PASSWORD", "").strip()
    if supabase_pw:
        url = (
            f"postgresql://postgres.{_SUPABASE_PROJECT_REF}:{supabase_pw}"
            f"@{_SUPABASE_POOLER_HOST}:5432/postgres?sslmode=require"
        )
        print(f"[DB] Built URL from SUPABASE_DB_PASSWORD: {_mask_url(url)}", file=sys.stderr)
        return url

    # ── Priority 2: explicit DB_CONNECTION_STRING ─────────────────────────────
    conn_str = os.environ.get("DB_CONNECTION_STRING", "").strip()
    if conn_str:
        print(f"[DB] Using DB_CONNECTION_STRING: {_mask_url(conn_str)}", file=sys.stderr)
        return conn_str

    # ── Priority 3 & 4: URL already points to the pooler ─────────────────────
    if "pooler.supabase.com" in raw_url:
        # Parse out the username to check if it already has the project ref
        pooler_match = re.match(
            r"(postgresql(?:\+\w+)?|postgres)://([^:@]+):([^@]*)@([^/]+)/([^?]*)(.*)",
            raw_url,
        )
        if pooler_match:
            scheme, user, password, host, dbname, rest = pooler_match.groups()
            # If username is plain "postgres" (no project ref), inject the project ref
            if "." not in user:
                url = (
                    f"{scheme}://postgres.{_SUPABASE_PROJECT_REF}:{password}"
                    f"@{_SUPABASE_POOLER_HOST}:5432/{dbname}?sslmode=require"
                )
                print(f"[DB] Fixed pooler URL (added project ref to username): {_mask_url(url)}", file=sys.stderr)
                return url
        print(f"[DB] Using existing pooler URL: {_mask_url(raw_url)}", file=sys.stderr)
        return raw_url

    # ── Priority 4: direct Supabase connection URL → convert to pooler ────────
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
        print(f"[DB] Rewrote direct→pooler URL: {_mask_url(url)}", file=sys.stderr)
        return url

    # ── Priority 5: local / non-Supabase URL ──────────────────────────────────
    print(f"[DB] Using DATABASE_URL as-is: {_mask_url(raw_url)}", file=sys.stderr)
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

