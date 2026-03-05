"""
Test script: Generate Telugu sankalpam for user maheshc11@gmail.com
Location: United States, Texas, Richmond
Run from backend directory: python test_sankalpam_mahesh.py
"""
import asyncio
import sys
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import SessionLocal
from app.models import User, FamilyMember
from app.services.divineapi_service import generate_sankalpam


async def main():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "maheshc11@gmail.com").first()
        if not user:
            print("User maheshc11@gmail.com not found in database.")
            return

        family_members = db.query(FamilyMember).filter(FamilyMember.user_id == user.id).all()

        # Richmond, Texas, USA - coordinates
        lat, lon = "29.58", "-95.76"
        location_city = "Richmond"
        location_state = "Texas"
        location_country = "United States"
        # US Central time
        timezone_offset_hours = -6.0

        sankalpam_text = await generate_sankalpam(
            user=user,
            family_members=family_members,
            location_city=location_city,
            location_state=location_state,
            location_country=location_country,
            nearby_river="Sacred River",
            language="telugu",
            language_code="te",
            pooja_name="Ganesh Pooja",
            nearby_mountain=None,
            nearby_sea=None,
            nearby_ocean=None,
            primary_geographical_feature=None,
            latitude=lat,
            longitude=lon,
            timezone_offset_hours=timezone_offset_hours,
            force_telugu=True,
        )

        # Write to UTF-8 file (Windows console often can't display Telugu)
        out_path = Path(__file__).parent / "sankalpam_output_mahesh.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write("SANKALPAM OUTPUT (Telugu) – User: maheshc11@gmail.com\n")
            f.write("Location: United States, Texas, Richmond\n")
            f.write("=" * 60 + "\n\n")
            f.write(sankalpam_text)
            f.write("\n" + "=" * 60 + "\n")
        print("Output written to:", out_path)
        # Also print ASCII-safe summary
        print("Length:", len(sankalpam_text), "characters")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
