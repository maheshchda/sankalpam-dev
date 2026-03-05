"""
Check if DivineAPI is configured and responding.
Run from backend dir: python check_divineapi.py
"""
import asyncio
import sys
from pathlib import Path

# Ensure backend app is on path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
import httpx


def print_section(title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def check_config() -> bool:
    """Print config status. Returns True if any DivineAPI key is set."""
    print_section("DivineAPI configuration")
    has_any = False
    print(f"  divine_api_key:      {'(set)' if settings.divine_api_key else '(not set)'}")
    if settings.divine_api_key:
        has_any = True
        print(f"    -> length {len(settings.divine_api_key)} chars")
    print(f"  divine_access_token: {'(set)' if settings.divine_access_token else '(not set)'}")
    if settings.divine_access_token:
        has_any = True
        print(f"    -> length {len(settings.divine_access_token)} chars")
    print(f"  divineapi_key:       {'(set)' if getattr(settings, 'divineapi_key', '') else '(not set)'}")
    if getattr(settings, 'divineapi_key', ''):
        has_any = True
    print(f"  divineapi_base_url:  {getattr(settings, 'divineapi_base_url', '') or '(not set)'}")
    return has_any


async def test_panchang() -> None:
    """Test DivineAPI find-panchang (used for tithi, nakshatra, etc.)."""
    print_section("Test: Panchang API (find-panchang)")
    if not settings.divine_api_key or not settings.divine_access_token:
        print("  Skipped: divine_api_key and divine_access_token are required for Panchang.")
        return
    url = "https://astroapi-1.divineapi.com/indian-api/v2/find-panchang"
    payload = {
        "api_key": settings.divine_api_key,
        "day": "10",
        "month": "2",
        "year": "2026",
        "Place": "Hyderabad, India",
        "lat": "17.3850",
        "lon": "78.4867",
        "tzone": "5.5",
        "lan": "en",
    }
    headers = {"Authorization": f"Bearer {settings.divine_access_token}"}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, headers=headers, data=payload)
            print(f"  Status: {response.status_code}")
            if response.status_code != 200:
                print(f"  Body:   {response.text[:500]}")
                return
            data = response.json()
            success = data.get("success", False)
            print(f"  success: {success}")
            if success and data.get("data"):
                d = data["data"]
                tithis = (d.get("tithis") or [])[:1]
                naks = (d.get("nakshatras") or {}).get("nakshatra_list") or []
                print(f"  tithi:    {tithis[0] if tithis else 'N/A'}")
                print(f"  nakshatra: {naks[0] if naks else 'N/A'}")
                print("  -> Panchang API is working.")
            else:
                print(f"  Response: {list(data.keys())}")
    except Exception as e:
        print(f"  Error: {e}")


async def test_sankalpam() -> None:
    """Test DivineAPI sankalpam/generate (if base URL and key are set)."""
    print_section("Test: Sankalpam API (sankalpam/generate)")
    key = getattr(settings, "divineapi_key", None) or settings.divine_api_key
    base = getattr(settings, "divineapi_base_url", None) or "https://api.divineapi.com"
    if not key:
        print("  Skipped: divineapi_key (or divine_api_key) is required for Sankalpam.")
        return
    # Try configured base first; if DNS/connection fails, try Panchang host (astroapi-1)
    bases_to_try = [base.rstrip("/"), "https://astroapi-1.divineapi.com"]
    # Minimal payload so we don't depend on full sankalpam_data shape
    payload = {
        "user_name": "Test User",
        "gotram": "Test Gotram",
        "birth_place": "Test City, State, Country",
        "birth_time": "12:00",
        "birth_date": "1990-01-01",
        "current_year": 2026,
        "current_location": "Test Location",
        "nearby_river": "Ganga",
        "family_members": [],
        "language_code": "sa",
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    last_error = None
    for base_url in bases_to_try:
        test_url = f"{base_url}/v1/sankalpam/generate"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(test_url, json=payload, headers=headers)
                print(f"  URL:    {test_url}")
                print(f"  Status: {response.status_code}")
                if response.status_code != 200:
                    print(f"  Body:   {response.text[:500]}")
                    last_error = f"HTTP {response.status_code}"
                    continue
                data = response.json()
                text = data.get("sankalpam_text") or data.get("text") or ""
                if text:
                    print(f"  sankalpam_text length: {len(text)} chars")
                    print("  -> Sankalpam API is working.")
                    return
                print(f"  Response keys: {list(data.keys())}")
                return
        except Exception as e:
            last_error = str(e)
            print(f"  URL:    {test_url}")
            print(f"  Error:  {e}")
    if last_error:
        print("  -> Sankalpam endpoint not reachable or not implemented at configured base.")
        print("     App falls back to local templates when Sankalpam API is unavailable.")


async def main() -> None:
    check_config()
    await test_panchang()
    await test_sankalpam()
    print()


if __name__ == "__main__":
    asyncio.run(main())
