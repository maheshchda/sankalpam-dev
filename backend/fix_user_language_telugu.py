#!/usr/bin/env python
"""
Utility script to inspect and (optionally) fix the preferred_language
for a specific user in the Sankalpam database.

This is intended for local debugging only.
"""

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import User, Language


def main() -> None:
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        identifier = "maheshc11@gmail.com"
        user = (
            db.query(User)
            .filter(or_(User.email == identifier, User.username == identifier))
            .first()
        )

        if not user:
            print("User not found for email/username:", identifier)
            return

        print("Current user record:")
        print("  id:", user.id)
        print("  username:", user.username)
        print("  email:", user.email)
        print("  preferred_language:", user.preferred_language)

        # If not already Telugu, set to Telugu
        if user.preferred_language != Language.TELUGU:
            print("Updating preferred_language to TELUGU...")
            user.preferred_language = Language.TELUGU
            db.commit()
            db.refresh(user)
            print("Updated preferred_language:", user.preferred_language)
        else:
            print("preferred_language is already TELUGU; no change made.")

    finally:
        db.close()


if __name__ == "__main__":
    main()

