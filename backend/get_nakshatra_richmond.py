"""
Get current Panchang (Paksha, Tithi, Nakshatra, Yoga, Karana) for Richmond, Texas, USA using Divine API Find Panchang.
Run from backend dir: python get_nakshatra_richmond.py
"""
import asyncio
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
import httpx


async def main():
    if not settings.divine_api_key or not settings.divine_access_token:
        print("Error: Set Divine_API_Key and Divine_Access_Token in .env")
        return

    now = datetime.now()
    # Richmond, Texas, USA - approx coordinates; Central Time UTC-6
    place = "Richmond, TX, USA"
    lat = 29.58
    lon = -95.76
    tzone = -6.0  # Central Time

    url = "https://astroapi-1.divineapi.com/indian-api/v2/find-panchang"
    headers = {"Authorization": f"Bearer {settings.divine_access_token}"}
    data = {
        "api_key": settings.divine_api_key,
        "day": str(now.day),
        "month": str(now.month),
        "year": str(now.year),
        "place": place,
        "Place": place,
        "lat": lat,
        "lon": lon,
        "tzone": str(tzone),
        "lan": "en",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, headers=headers, data=data)

    if response.status_code != 200:
        print(f"API error: {response.status_code}")
        print(response.text[:600])
        return

    payload = response.json()
    if not payload.get("success"):
        print("API returned success=false:", payload.get("message", payload)[:300])
        return

    pdata = payload.get("data") or {}

    # Paksha & Tithi from tithis[0]
    tithis = pdata.get("tithis") or []
    paksha = None
    tithi = None
    if tithis and isinstance(tithis[0], dict):
        t0 = tithis[0]
        paksha = t0.get("paksha")
        tithi = t0.get("tithi")
    tithi_str = f"{paksha or ''} {tithi or ''}".strip()

    # Nakshatra
    nak_block = pdata.get("nakshatras") or {}
    nak_list = nak_block.get("nakshatra_list") if isinstance(nak_block, dict) else []
    nakshatra = None
    if nak_list and isinstance(nak_list, list):
        first = nak_list[0]
        nakshatra = first.get("nak_name") or first.get("nakshatra_name") if isinstance(first, dict) else None
    if not nakshatra and pdata.get("nakshatra_name"):
        nakshatra = pdata.get("nakshatra_name")

    # Yoga
    yogas = pdata.get("yogas") or []
    yoga = None
    if yogas and isinstance(yogas, list) and isinstance(yogas[0], dict):
        yoga = yogas[0].get("yoga_name") or yogas[0].get("yoga")
    if not yoga and pdata.get("yoga_name"):
        yoga = pdata.get("yoga_name")

    # Karana
    karnas = pdata.get("karnas") or []
    karana = None
    if karnas and isinstance(karnas, list) and isinstance(karnas[0], dict):
        karana = karnas[0].get("karana_name") or karnas[0].get("karana")
    if not karana and pdata.get("karana_name"):
        karana = pdata.get("karana_name")

    print(f"Place:     {place}")
    print(f"Date:      {now.strftime('%Y-%m-%d %H:%M')} (server time)")
    print(f"Paksha:    {paksha or 'N/A'}")
    print(f"Tithi:     {tithi or 'N/A'}")
    print(f"Tithi (full): {tithi_str or 'N/A'}")
    print(f"Nakshatra: {nakshatra or 'N/A'}")
    print(f"Yoga:      {yoga or 'N/A'}")
    print(f"Karana:    {karana or 'N/A'}")


if __name__ == "__main__":
    asyncio.run(main())
