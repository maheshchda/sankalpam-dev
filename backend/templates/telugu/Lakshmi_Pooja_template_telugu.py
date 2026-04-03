"""
Telugu Sankalpam Template Generator for Lakshmi Pooja
This Python file generates the sankalpam text dynamically, calling Divine API for panchang variables.
Based on Ganesh Pooja template structure; adapted for Sri Mahalakshmi Pooja.
"""
from datetime import datetime
from typing import Dict, Optional
import httpx
import sys
from pathlib import Path

# Add backend directory to path for imports
_BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

try:
    from app.config import settings
except ImportError:
    # Fallback if running standalone
    class Settings:
        divine_api_key = None
        divine_access_token = None
    settings = Settings()


def _to_telugu_birth_nakshatra(raw: str) -> str:
    """Convert birth nakshatra to Telugu (e.g. Purva Bhadrapada -> పూర్వ భాద్రపద)."""
    if not raw or not raw.strip():
        return raw or ""
    try:
        from app.services.divineapi_service import _nakshatra_to_telugu
        return _nakshatra_to_telugu(raw.strip())
    except Exception:
        return raw.strip()


def _to_telugu_birth_rashi(raw: str) -> str:
    """Convert birth rashi to Telugu (e.g. Meena -> మీన)."""
    if not raw or not raw.strip():
        return raw or ""
    try:
        from app.services.divineapi_service import _english_to_telugu, _TE_RASHI
        return _english_to_telugu(raw.strip(), _TE_RASHI) or raw.strip()
    except Exception:
        return raw.strip()


async def generate_sankalpam_text(data: Dict) -> str:
    """
    Generate Telugu sankalpam text for Lakshmi Pooja.

    Args:
        data: Dictionary containing:
            - user_name, gotram, birth_nakshatra, birth_rashi, birth_place, birth_time, birth_city, birth_state, birth_country, birth_date
            - current_location, location_city, location_state, location_country
            - nearby_river, nearby_mountain, nearby_sea, nearby_ocean, primary_geographical_feature
            - family_members (list of dicts with name, relation)
            - pooja_name
            - latitude, longitude, timezone_offset_hours (for Divine API)
            - language_code (e.g. 'te')

    Returns:
        Complete sankalpam text in Telugu
    """
    lines = []

    # Lakshmi Pooja – opening invocations
    lines.append("ఓం శ్రీమహాలక్ష్మ్యై నమః ॥")
    lines.append("")
    lines.append("మమ ఉపాత్త సమస్త దురితక్షయ ద్వారా")
    lines.append("శ్రీపరమేశ్వర ప్రీత్యర్థమ్ ।")
    lines.append("")
    lines.append("అద్య శ్రీమద్ బ్రహ్మణః ద్వితీయ పారార్ధే")
    lines.append("శ్వేతవరాహ కల్పే")
    lines.append("వైవస్వత మన్వంతరే")

    # {{samvathsarE}} - Current year
    current_year = data.get("current_year", datetime.now().year)
    lines.append(f"{current_year} సంవత్సరే")
    lines.append("అష్టావింశతితే కలియుగే")
    lines.append("ప్రథమే పాదే")
    lines.append("")

    # {{geographical_reference}}
    geographical_reference = await _get_geographical_reference(data)
    lines.append(geographical_reference)

    # {{current_location}}
    current_location = data.get("current_location", "")
    lines.append(f"{current_location} స్థానే")

    # {{geographical_feature}}
    geographical_feature = await _get_geographical_feature(data)
    lines.append(geographical_feature)
    lines.append("")

    lines.append("అస్మిన్ శుభే శుద్ధే")

    # Panchang variables from Divine API
    panchang_data = await _get_panchang_from_divine_api(data)

    rithou = panchang_data.get("rithou", "")
    lines.append(f"{rithou} ఋతౌ")

    mAsE = panchang_data.get("mAsE", "")
    lines.append(f"{mAsE} మాసే")

    pakshE = panchang_data.get("pakshE", "")
    lines.append(f"{pakshE} పక్షే")

    thithou = panchang_data.get("thithou", "")
    lines.append(f"{thithou} తిథౌ")

    vAsara = panchang_data.get("vAsara", "")
    lines.append(f"{vAsara} వారే")

    nakshatra = panchang_data.get("nakshatra", "")
    lines.append(f"{nakshatra} నక్షత్రే")

    yoga = panchang_data.get("yoga", "")
    lines.append(f"{yoga} యోగే")

    karaNa = panchang_data.get("karaNa", "")
    lines.append(f"{karaNa} కరణే")

    ayanam = panchang_data.get("ayanam", "")
    lines.append(f"{ayanam} ॥")
    lines.append("")

    lines.append("శుభే ముహూర్తే")
    lines.append(f"అహం {data.get('user_name', '')}")
    lines.append(f"గోత్ర {data.get('gotram', '')}")

    birth_nakshatra_raw = data.get("birth_nakshatra", "") or ""
    birth_nakshatra = _to_telugu_birth_nakshatra(birth_nakshatra_raw)
    lines.append(f"{birth_nakshatra} నక్షత్రే")

    birth_rashi_raw = data.get("birth_rashi", "") or ""
    birth_rashi = _to_telugu_birth_rashi(birth_rashi_raw)
    lines.append(f"{birth_rashi} రాశౌ")
    lines.append("")

    lines.append("మమ పారివారిక సదస్యులు:")
    family_members = data.get("family_members", [])
    for member in family_members:
        name = member.get("name", "")
        relation = member.get("relation", "")
        lines.append(f"- {name} ({relation})")
    lines.append("")

    lines.append("ఇత్యాది సకలపాపక్షయపూర్వకం")
    lines.append("అఖండమండలాకారం వ్యాప్తం యేన చరాచరం")
    lines.append("తత్పరమేశ్వరం ప్రణమ్య")
    lines.append("")
    lines.append("అస్యాం శుభతిథౌ")

    # Show Telugu name for Lakshmi Pooja in closing line
    pooja_name = data.get("pooja_name", "")
    pooja_display = "శ్రీ లక్ష్మీ పూజ" if (pooja_name or "").strip().lower() == "lakshmi pooja" else (pooja_name or "")
    lines.append(f"{pooja_display} పూజనం కరిష్యే ।")
    lines.append("")
    lines.append("తత్సిద్ధ్యర్థం")
    lines.append("సంకల్పం కరోమి ॥")
    lines.append("")
    lines.append("శుభం భవతు ॥")
    lines.append("")

    return "\n".join(lines)


async def _get_panchang_from_divine_api(data: Dict) -> Dict[str, str]:
    """
    Fetch panchang data from Divine API. Returns dict with Telugu values.
    """
    try:
        from app.services.divineapi_service import (
            _english_to_telugu, _tithi_to_telugu, _nakshatra_to_telugu,
            _TE_PAKSHA, _TE_YOGA, _TE_KARANA, _TE_RITU, _TE_WEEKDAYS
        )
    except ImportError:
        def _english_to_telugu(text, mapping):
            return mapping.get(text.lower(), text) if text else ""
        def _tithi_to_telugu(text):
            return text or ""
        def _nakshatra_to_telugu(text):
            return text or ""
        _TE_PAKSHA = {}
        _TE_YOGA = {}
        _TE_KARANA = {}
        _TE_RITU = {}
        _TE_WEEKDAYS = {}

    result = {
        "rithou": "", "mAsE": "", "pakshE": "", "thithou": "", "vAsara": "",
        "nakshatra": "", "yoga": "", "karaNa": "", "ayanam": "",
    }

    if not settings.divine_api_key or not settings.divine_access_token:
        return _get_fallback_panchang(data)

    now = datetime.now()
    location_city = data.get("location_city", "")
    location_state = data.get("location_state", "")
    location_country = data.get("location_country", "")
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timezone_offset_hours = data.get("timezone_offset_hours", 0.0)
    place = location_city or location_state or location_country or "Unknown"

    try:
        lat_num = float(latitude) if latitude not in (None, "") else 0.0
    except (TypeError, ValueError):
        lat_num = 0.0
    try:
        lon_num = float(longitude) if longitude not in (None, "") else 0.0
    except (TypeError, ValueError):
        lon_num = 0.0

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://astroapi-1.divineapi.com/indian-api/v2/find-panchang"
            headers = {"Authorization": f"Bearer {settings.divine_access_token}"}
            panchang_data = {
                "api_key": settings.divine_api_key,
                "day": str(now.day), "month": str(now.month), "year": str(now.year),
                "place": place, "Place": place, "lat": str(lat_num), "lon": str(lon_num),
                "tzone": str(timezone_offset_hours), "lan": "tl",
            }
            response = await client.post(url, headers=headers, data=panchang_data)
            if response.status_code == 200:
                payload = response.json()
                if payload.get("success"):
                    pdata = payload.get("data") or {}
                    tithi_name = None
                    paksha_name = None
                    tithis = pdata.get("tithis") or []
                    if tithis and isinstance(tithis, list):
                        t0 = tithis[0] if isinstance(tithis[0], dict) else {}
                        if t0.get("tithi"):
                            paksha_name = t0.get("paksha") or ""
                            tithi_name = f"{paksha_name} {t0['tithi']}".strip() or t0["tithi"]
                    if not tithi_name and (pdata.get("tithi") or pdata.get("tithi_name")):
                        paksha_name = pdata.get("paksha") or ""
                        tithi_name = f"{paksha_name} {pdata.get('tithi') or pdata.get('tithi_name')}".strip()

                    nakshatra_name = None
                    nak_block = pdata.get("nakshatras") or {}
                    nak_list = nak_block.get("nakshatra_list") if isinstance(nak_block, dict) else (pdata.get("nakshatra_list") or [])
                    if nak_list and isinstance(nak_list, list) and len(nak_list) > 0:
                        first = nak_list[0]
                        nakshatra_name = first.get("nak_name") or first.get("nakshatra_name") or first.get("name") if isinstance(first, dict) else first
                    if not nakshatra_name and pdata.get("nakshatra_name"):
                        nakshatra_name = pdata.get("nakshatra_name")

                    yoga_name = None
                    yogas = pdata.get("yogas") or []
                    if yogas and isinstance(yogas, list) and len(yogas) > 0:
                        y0 = yogas[0]
                        yoga_name = y0.get("yoga_name") or y0.get("yoga") or y0.get("name") if isinstance(y0, dict) else y0
                    if not yoga_name and pdata.get("yoga_name"):
                        yoga_name = pdata.get("yoga_name")

                    karana_name = None
                    karnas = pdata.get("karnas") or []
                    if karnas and isinstance(karnas, list) and len(karnas) > 0:
                        k0 = karnas[0]
                        karana_name = k0.get("karana_name") or k0.get("karana") or k0.get("name") if isinstance(k0, dict) else k0
                    if not karana_name and pdata.get("karana_name"):
                        karana_name = pdata.get("karana_name")

                    paksha_te = _english_to_telugu(paksha_name or "", _TE_PAKSHA) or paksha_name or ""
                    tithi_parts = (tithi_name or "").split(maxsplit=1)
                    tithi_only = tithi_parts[1] if len(tithi_parts) > 1 else (tithi_parts[0] if tithi_parts else "")
                    result["pakshE"] = paksha_te
                    result["thithou"] = _tithi_to_telugu(tithi_only) if tithi_only else ""
                    result["nakshatra"] = _nakshatra_to_telugu(nakshatra_name or "")
                    result["yoga"] = _english_to_telugu((yoga_name or "").strip(), _TE_YOGA) or (yoga_name or "")
                    result["karaNa"] = _english_to_telugu((karana_name or "").strip(), _TE_KARANA) or (karana_name or "")

            chandramasa_url = "https://astroapi-3.divineapi.com/indian-api/v2/chandramasa"
            chandramasa_data = {
                "api_key": settings.divine_api_key,
                "day": str(now.day), "month": str(now.month), "year": str(now.year),
                "Place": place, "lat": str(lat_num), "lon": str(lon_num),
                "tzone": str(timezone_offset_hours), "lan": "tl",
            }
            chandramasa_response = await client.post(chandramasa_url, headers=headers, data=chandramasa_data)
            if chandramasa_response.status_code == 200:
                chandramasa_payload = chandramasa_response.json()
                if chandramasa_payload.get("success"):
                    cdata = chandramasa_payload.get("data") or {}
                    if cdata.get("chandramasa"):
                        result["mAsE"] = str(cdata["chandramasa"]).strip()

            result["rithou"] = _TE_RITU.get(now.month, "")
            result["vAsara"] = _english_to_telugu(now.strftime("%A"), _TE_WEEKDAYS) or now.strftime("%A")
            result["ayanam"] = "ఉత్తరాయణే" if 1 <= now.month <= 6 else "దక్షిణాయణే"

    except Exception as e:
        print(f"[Lakshmi Template] Error fetching from Divine API: {e}")
        return _get_fallback_panchang(data)

    return result


def _get_fallback_panchang(data: Dict) -> Dict[str, str]:
    """Fallback panchang when Divine API is not available."""
    try:
        from app.services.divineapi_service import _fallback_panchang_for_today, _TE_RITU, _TE_WEEKDAYS
        from app.services.divineapi_service import (
            _english_to_telugu, _tithi_to_telugu, _nakshatra_to_telugu,
            _TE_PAKSHA, _TE_YOGA, _TE_KARANA
        )
    except ImportError:
        def _fallback_panchang_for_today(now):
            return {"paksha": "", "tithi": "", "nakshatra": "", "yoga": "", "karana": ""}
        _TE_RITU = {}
        _TE_WEEKDAYS = {}
        def _english_to_telugu(text, mapping):
            return mapping.get(text.lower(), text)
        def _tithi_to_telugu(text):
            return text
        def _nakshatra_to_telugu(text):
            return text
        _TE_PAKSHA = {}
        _TE_YOGA = {}
        _TE_KARANA = {}

    from datetime import datetime
    now = datetime.now()
    fallback = _fallback_panchang_for_today(now)
    paksha_te = _english_to_telugu(fallback.get("paksha", ""), _TE_PAKSHA) or fallback.get("paksha", "")
    tithi_parts = (fallback.get("tithi", "") or "").split(maxsplit=1)
    tithi_only = tithi_parts[1] if len(tithi_parts) > 1 else (tithi_parts[0] if tithi_parts else "")
    return {
        "rithou": _TE_RITU.get(now.month, ""),
        "mAsE": now.strftime("%B"),
        "pakshE": paksha_te,
        "thithou": _tithi_to_telugu(tithi_only) if tithi_only else "",
        "vAsara": _english_to_telugu(now.strftime("%A"), _TE_WEEKDAYS) or now.strftime("%A"),
        "nakshatra": _nakshatra_to_telugu(fallback.get("nakshatra", "")),
        "yoga": _english_to_telugu((fallback.get("yoga") or "").strip(), _TE_YOGA) or fallback.get("yoga", ""),
        "karaNa": _english_to_telugu((fallback.get("karana") or "").strip(), _TE_KARANA) or fallback.get("karana", ""),
        "ayanam": "ఉత్తరాయణే" if 1 <= now.month <= 6 else "దక్షిణాయణే",
    }


async def _get_geographical_reference(data: Dict) -> str:
    try:
        from app.services.divineapi_service import _telugu_geographical_reference_from_country
        return _telugu_geographical_reference_from_country(
            data.get("location_country", ""),
            data.get("latitude"),
            data.get("longitude"),
        )
    except ImportError:
        if not data.get("location_country") or "india" in (data.get("location_country") or "").lower():
            return "జంబూద్వీపే భారతవర్షే భారతఖండే"
        return f"{data.get('location_country', '')} దేశే"


async def _get_geographical_feature(data: Dict) -> str:
    try:
        from app.services.divineapi_service import _telugu_geographical_feature_from_data
        return _telugu_geographical_feature_from_data(data)
    except ImportError:
        nearby_river = data.get("nearby_river", "")
        if nearby_river:
            return f"{nearby_river} నదీ తటే"
        return "గంగా నదీ తటే"
