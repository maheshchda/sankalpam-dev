"""
Hindi Sankalpam Template Generator for Ganesh Pooja (Devanagari).
Uses Divine API with lan=hi for panchang; static text in Hindi/Devanagari.
"""
from datetime import datetime
from typing import Dict, Optional
import httpx
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

try:
    from app.config import settings
except ImportError:
    class Settings:
        divine_api_key = None
        divine_access_token = None
    settings = Settings()

_HI_RITU = {
    1: "शिशिर", 2: "वसन्त", 3: "वसन्त", 4: "ग्रीष्म", 5: "ग्रीष्म", 6: "वर्षा",
    7: "वर्षा", 8: "शरद", 9: "शरद", 10: "हेमन्त", 11: "हेमन्त", 12: "शिशिर",
}
_HI_WEEKDAYS = {
    "monday": "सोमवार", "tuesday": "मंगलवार", "wednesday": "बुधवार",
    "thursday": "गुरुवार", "friday": "शुक्रवार", "saturday": "शनिवार", "sunday": "रविवार",
}


async def generate_sankalpam_text(data: Dict) -> str:
    """Generate Hindi (Devanagari) sankalpam text for Ganesh Pooja."""
    lines = []

    lines.append("ॐ श्रीमहागणपतये नमः ॥")
    lines.append("")
    lines.append("मम उपात्त समस्त दुरितक्षय द्वारा")
    lines.append("श्रीपरमेश्वर प्रीत्यर्थम् ।")
    lines.append("")
    lines.append("अद्य श्रीमद् ब्रह्मणः द्वितीय परार्धे")
    lines.append("श्वेतवराह कल्पे")
    lines.append("वैवस्वत मन्वन्तरे")

    current_year = data.get("current_year", datetime.now().year)
    lines.append(f"{current_year} संवत्सरे")
    lines.append("अष्टाविंशतिते कलियुगे")
    lines.append("प्रथमे पादे")
    lines.append("")

    geographical_reference = await _get_geographical_reference(data)
    lines.append(geographical_reference)

    current_location = data.get("current_location", "")
    lines.append(f"{current_location} स्थाने")

    geographical_feature = await _get_geographical_feature(data)
    lines.append(geographical_feature)
    lines.append("")

    lines.append("अस्मिन् शुभे शुद्धे")

    panchang_data = await _get_panchang_from_divine_api(data)

    rithou = panchang_data.get("rithou", "")
    lines.append(f"{rithou} ऋतौ")
    mAsE = panchang_data.get("mAsE", "")
    lines.append(f"{mAsE} मासे")
    pakshE = panchang_data.get("pakshE", "")
    lines.append(f"{pakshE} पक्षे")
    thithou = panchang_data.get("thithou", "")
    lines.append(f"{thithou} तिथौ")
    vAsara = panchang_data.get("vAsara", "")
    lines.append(f"{vAsara} वारे")
    nakshatra = panchang_data.get("nakshatra", "")
    lines.append(f"{nakshatra} नक्षत्रे")
    yoga = panchang_data.get("yoga", "")
    lines.append(f"{yoga} योगे")
    karaNa = panchang_data.get("karaNa", "")
    lines.append(f"{karaNa} करणे")
    ayanam = panchang_data.get("ayanam", "")
    lines.append(f"{ayanam} ॥")
    lines.append("")

    lines.append("शुभे मुहूर्ते")
    lines.append(f"अहं {data.get('user_name', '')}")
    lines.append(f"गोत्र {data.get('gotram', '')}")

    birth_nakshatra = (data.get("birth_nakshatra", "") or "").strip() or ""
    lines.append(f"{birth_nakshatra} नक्षत्रे")
    birth_rashi = (data.get("birth_rashi", "") or "").strip() or ""
    lines.append(f"{birth_rashi} राशौ")
    lines.append("")

    lines.append("मम पारिवारिक सदस्याः")
    family_members = data.get("family_members", [])
    for member in family_members:
        name = member.get("name", "")
        relation = member.get("relation", "")
        lines.append(f"- {name} ({relation})")
    lines.append("")

    lines.append("इत्यादि सकलपापक्षयपूर्वकं")
    lines.append("अखण्डमण्डलाकारं व्याप्तं येन चराचरं")
    lines.append("तत्परमेश्वरं प्रणम्य")
    lines.append("")
    lines.append("अस्यां शुभतिथौ")

    pooja_name = data.get("pooja_name", "")
    lines.append(f"{pooja_name} पूजनं करिष्ये ।")
    lines.append("")
    lines.append("तत्सिद्ध्यर्थं")
    lines.append("संकल्पं करोमि ॥")
    lines.append("")
    lines.append("शुभं भवतु ॥")
    lines.append("")

    return "\n".join(lines)


async def _get_panchang_from_divine_api(data: Dict) -> Dict[str, str]:
    """Fetch panchang from Divine API with lan=hi (Devanagari)."""
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
    place = location_city or location_state or location_country or "Unknown"
    latitude = data.get("latitude")
    longitude = data.get("longitude")
    timezone_offset_hours = data.get("timezone_offset_hours", 0.0)

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
                "tzone": str(timezone_offset_hours), "lan": "hi",
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

                    result["pakshE"] = paksha_name or ""
                    tithi_parts = (tithi_name or "").split(maxsplit=1)
                    result["thithou"] = tithi_parts[1] if len(tithi_parts) > 1 else (tithi_parts[0] if tithi_parts else "")
                    result["nakshatra"] = nakshatra_name or ""
                    result["yoga"] = (yoga_name or "").strip()
                    result["karaNa"] = (karana_name or "").strip()

            chandramasa_url = "https://astroapi-3.divineapi.com/indian-api/v2/chandramasa"
            chandramasa_data = {
                "api_key": settings.divine_api_key,
                "day": str(now.day), "month": str(now.month), "year": str(now.year),
                "Place": place, "lat": str(lat_num), "lon": str(lon_num),
                "tzone": str(timezone_offset_hours), "lan": "hi",
            }
            chandramasa_response = await client.post(chandramasa_url, headers=headers, data=chandramasa_data)
            if chandramasa_response.status_code == 200:
                chandramasa_payload = chandramasa_response.json()
                if chandramasa_payload.get("success"):
                    cdata = chandramasa_payload.get("data") or {}
                    if cdata.get("chandramasa"):
                        result["mAsE"] = str(cdata["chandramasa"]).strip()

            result["rithou"] = _HI_RITU.get(now.month, "")
            result["vAsara"] = _HI_WEEKDAYS.get(now.strftime("%A").lower(), now.strftime("%A"))
            result["ayanam"] = "उत्तरायणे" if 1 <= now.month <= 6 else "दक्षिणायणे"

    except Exception as e:
        print(f"[Ganesh Hindi Template] Error fetching from Divine API: {e}")
        return _get_fallback_panchang(data)

    return result


def _get_fallback_panchang(data: Dict) -> Dict[str, str]:
    """Fallback panchang in Devanagari when API unavailable."""
    now = datetime.now()
    try:
        from app.services.divineapi_service import _fallback_panchang_for_today
        fallback = _fallback_panchang_for_today(now)
    except ImportError:
        fallback = {"paksha": "", "tithi": "", "nakshatra": "", "yoga": "", "karana": ""}

    return {
        "rithou": _HI_RITU.get(now.month, ""),
        "mAsE": now.strftime("%B"),
        "pakshE": fallback.get("paksha", ""),
        "thithou": fallback.get("tithi", ""),
        "vAsara": _HI_WEEKDAYS.get(now.strftime("%A").lower(), now.strftime("%A")),
        "nakshatra": fallback.get("nakshatra", ""),
        "yoga": fallback.get("yoga", ""),
        "karaNa": fallback.get("karana", ""),
        "ayanam": "उत्तरायणे" if 1 <= now.month <= 6 else "दक्षिणायणे",
    }


async def _get_geographical_reference(data: Dict) -> str:
    """Geographical reference in Devanagari."""
    location_country = (data.get("location_country") or "").strip()
    if not location_country or "india" in location_country.lower():
        return "जम्बूद्वीपे भारतवर्षे भारतखण्डे"
    return f"{location_country} देशे"


async def _get_geographical_feature(data: Dict) -> str:
    """Geographical feature phrase in Devanagari."""
    nearby_river = data.get("nearby_river", "")
    if nearby_river:
        return f"{nearby_river} नदी तटे"
    nearby_sea = data.get("nearby_sea", "")
    if nearby_sea:
        return f"{nearby_sea} समुद्र तटे"
    nearby_ocean = data.get("nearby_ocean", "")
    if nearby_ocean:
        return f"{nearby_ocean} महासागर तटे"
    nearby_mountain = data.get("nearby_mountain", "")
    if nearby_mountain:
        return f"{nearby_mountain} पर्वत समीपे"
    return "गंगा नदी तटे"
