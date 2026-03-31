"""
Service to fetch astronomical data for Sankalpam (year, ayanam, rithu, tithi, nakshatra, etc.)
Uses Divine API (find-panchang + chandramasa) for the selected location when keys are configured,
with fallbacks when the API is unavailable.
"""
import re
from datetime import datetime
from typing import Dict, Optional

from app.services.divineapi_service import (
    _resolve_coords_for_panchang,
    _fetch_panchang_for_today,
    _fetch_chandramasa_for_today,
    _estimate_timezone_offset,
    _fallback_panchang_for_today,
    _language_to_iso,
    _latin_name_to_telugu,
    _english_to_telugu,
    _tithi_to_telugu,
    _nakshatra_to_telugu,
    _TE_RITU,
    _TE_WEEKDAYS,
    _TE_PAKSHA,
    _TE_YOGA,
    _TE_KARANA,
)


def _normalize_template_lang(lang: Optional[str]) -> str:
    if not lang:
        return "sanskrit"
    s = str(lang).strip().lower()
    if s.startswith("language."):
        s = s.split(".")[-1]
    return s


def _is_telugu_template(template_language: str) -> bool:
    tl = _normalize_template_lang(template_language)
    return tl in ("te", "telugu") or "telugu" in tl


def _telugu_scrub_latin(s: str) -> str:
    """If any Latin letters remain, transliterate to Telugu script."""
    if not s or not str(s).strip():
        return s or ""
    t = str(s).strip()
    if re.search(r"[A-Za-z]", t):
        return _latin_name_to_telugu(t)
    return t


def _bad_coords(lat_s: Optional[str], lon_s: Optional[str]) -> bool:
    if not lat_s or not lon_s:
        return True
    try:
        return abs(float(lat_s)) < 1e-9 and abs(float(lon_s)) < 1e-9
    except (TypeError, ValueError):
        return True


async def get_astronomical_data(
    date: datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_city: str = "",
    location_state: str = "",
    location_country: str = "",
    template_language: str = "sanskrit",
) -> Dict[str, str]:
    """
    Fetch astronomical data for a given date and location.
    Uses Divine API find-panchang + chandramasa for the selected place (lat/lon + timezone),
    resolving coordinates via geocoding when missing.

    Template variables: samvathsarE, ayanam, rithou, mAsE, pakshE, thithou, vAsara,
    nakshatra, yoga, karaNa, rashi

    {{samvathsarE}} is only the year-name phrase (e.g. "prabhava nAma"); templates append సంవత్సరే / samvatsara.
    """
    is_te = _is_telugu_template(template_language)
    lang_for_api = "te" if is_te else "en"

    lat_s = str(latitude) if latitude is not None else None
    lon_s = str(longitude) if longitude is not None else None
    if _bad_coords(lat_s, lon_s):
        rl, rr = await _resolve_coords_for_panchang(location_city, location_state, location_country)
        if rl and rr:
            lat_s, lon_s = rl, rr
            try:
                latitude = float(rl)
                longitude = float(rr)
            except (TypeError, ValueError):
                pass

    tz = _estimate_timezone_offset(location_country, location_state)
    iso = _language_to_iso(template_language)

    panchang = await _fetch_panchang_for_today(
        now=date,
        location_city=location_city,
        location_state=location_state,
        location_country=location_country,
        latitude=lat_s,
        longitude=lon_s,
        timezone_offset_hours=tz,
        language=lang_for_api,
    )
    if not panchang:
        fb = _fallback_panchang_for_today(date)
        panchang = {
            "tithi": fb.get("tithi") or "",
            "paksha": fb.get("paksha") or "",
            "nakshatra": fb.get("nakshatra") or "",
            "yoga": fb.get("yoga") or "",
            "karana": fb.get("karana") or "",
        }

    place = ", ".join(p for p in [location_city, location_state, location_country] if p) or "Unknown"
    lunar_month = await _fetch_chandramasa_for_today(
        now=date,
        place=place,
        latitude=lat_s or "0",
        longitude=lon_s or "0",
        timezone_offset_hours=tz,
        lan=iso or "en",
    )

    base = calculate_astronomical_data_fallback(date, latitude, longitude)
    # samvathsarE in base must not duplicate "samvathsarE" / సంవత్సరే (template adds it)
    if lunar_month:
        base["mAsE"] = lunar_month

    tithi_raw = (panchang.get("tithi") or "").strip()
    paksha_en = (panchang.get("paksha") or "").strip()
    tithi_parts = tithi_raw.split(maxsplit=1) if tithi_raw else []
    if not paksha_en and len(tithi_parts) > 1:
        paksha_en = tithi_parts[0]
    tithi_only = tithi_parts[1] if len(tithi_parts) > 1 else (tithi_parts[0] if tithi_parts else "")

    nak_raw = (panchang.get("nakshatra") or "").strip()
    nak_raw = re.sub(r"\s*nakshatra\s*$", "", nak_raw, flags=re.I).strip()
    yoga_raw = (panchang.get("yoga") or "").strip()
    yoga_raw = re.sub(r"\s*yoga\s*$", "", yoga_raw, flags=re.I).strip()
    karana_raw = (panchang.get("karana") or "").strip()
    karana_raw = re.sub(r"\s*karana\s*$", "", karana_raw, flags=re.I).strip()

    if is_te:
        paksha_te = _english_to_telugu(paksha_en, _TE_PAKSHA) or paksha_en
        thithou_te = _tithi_to_telugu(tithi_only) if tithi_only else _tithi_to_telugu(tithi_raw)
        nak_te = _nakshatra_to_telugu(nak_raw) or nak_raw
        yoga_te = _english_to_telugu(yoga_raw, _TE_YOGA) or yoga_raw
        kara_te = _english_to_telugu(karana_raw, _TE_KARANA) or karana_raw
        paksha_te = _telugu_scrub_latin(paksha_te)
        thithou_te = _telugu_scrub_latin(thithou_te)
        nak_te = _telugu_scrub_latin(nak_te)
        yoga_te = _telugu_scrub_latin(yoga_te)
        kara_te = _telugu_scrub_latin(kara_te)
        rithou_te = _TE_RITU.get(date.month, "")
        weekday_en = date.strftime("%A")
        vasara_te = _english_to_telugu(weekday_en, _TE_WEEKDAYS) or weekday_en
        vasara_te = _telugu_scrub_latin(vasara_te)
        ayanam_te = "ఉత్తరాయణే" if 1 <= date.month <= 6 else "దక్షిణాయణే"
        year_names = [
            "prabhava", "vibhava", "shukla", "pramoda", "prajApati",
            "A~Ngirasa", "shrImukha", "bhAva", "yuvan", "dhAtR",
        ]
        year_index = (date.year - 1987) % len(year_names)
        sam_te = f"{_latin_name_to_telugu(year_names[year_index])} నామ"
        mase_val = (lunar_month or base.get("mAsE") or "").strip()
        if mase_val:
            mase_val = _telugu_scrub_latin(mase_val)
        rashi_raw = (base.get("rashi") or "").strip()
        rashi_raw = re.sub(r"\s*rAshi\s*$", "", rashi_raw, flags=re.I).strip()
        rashi_raw = re.sub(r"\s*rashi\s*$", "", rashi_raw, flags=re.I).strip()
        rashi_te = _telugu_scrub_latin(rashi_raw) if rashi_raw else ""
        return {
            "samvathsarE": sam_te,
            "ayanam": ayanam_te,
            "rithou": rithou_te,
            "mAsE": mase_val,
            "pakshE": paksha_te,
            "thithou": thithou_te,
            "vAsara": vasara_te,
            "nakshatra": nak_te,
            "yoga": yoga_te,
            "karaNa": kara_te,
            "rashi": rashi_te,
        }

    # Non-Telugu: Sanskrit/IAST-style strings from API or fallback
    paksh_out = f"{paksha_en} pakshE".strip() if paksha_en else base.get("pakshE", "")
    thith_out = tithi_raw if tithi_raw else base.get("thithou", "")
    nak_out = f"{nak_raw} nakshatra" if nak_raw and "nakshatra" not in nak_raw.lower() else (nak_raw or base.get("nakshatra", ""))
    yoga_out = f"{yoga_raw} yoga" if yoga_raw and "yoga" not in yoga_raw.lower() else (yoga_raw or base.get("yoga", ""))
    kara_out = f"{karana_raw} karaNa" if karana_raw and "kara" not in karana_raw.lower() else (karana_raw or base.get("karaNa", ""))

    return {
        "samvathsarE": base.get("samvathsarE", ""),
        "ayanam": base.get("ayanam", ""),
        "rithou": base.get("rithou", ""),
        "mAsE": base.get("mAsE", ""),
        "pakshE": paksh_out,
        "thithou": thith_out,
        "vAsara": base.get("vAsara", ""),
        "nakshatra": nak_out,
        "yoga": yoga_out,
        "karaNa": kara_out,
        "rashi": base.get("rashi", ""),
    }


def calculate_astronomical_data_fallback(
    date: datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> Dict[str, str]:
    """
    Fallback calculation for astronomical data when Divine API is unavailable.
    """
    weekdays = {
        0: "bhAnu vAsara",
        1: "sOma vAsara",
        2: "ma~Ngala vAsara",
        3: "budha vAsara",
        4: "guru vAsara",
        5: "shukra vAsara",
        6: "shaNi vAsara",
    }

    months = {
        1: "mAgA mAsE",
        2: "phAlguna mAsE",
        3: "chaitra mAsE",
        4: "vaishAkha mAsE",
        5: "jyEshTha mAsE",
        6: "AshADha mAsE",
        7: "shrAvaNa mAsE",
        8: "bhAdrapada mAsE",
        9: "Ashvina mAsE",
        10: "kArtika mAsE",
        11: "mArgashIrsha mAsE",
        12: "pausha mAsE",
    }

    month_to_season = {
        1: "shishira rithou",
        2: "vAsanta rithou",
        3: "vAsanta rithou",
        4: "grIshma rithou",
        5: "grIshma rithou",
        6: "varshA rithou",
        7: "varshA rithou",
        8: "sharad rithou",
        9: "sharad rithou",
        10: "hEmantha rithou",
        11: "hEmantha rithou",
        12: "shishira rithou",
    }

    month = date.month
    day = date.day
    if (month == 12 and day >= 21) or month in [1, 2, 3, 4, 5] or (month == 6 and day < 21):
        ayanam = "uttarAyaNE"
    else:
        ayanam = "dakshiNAyaNE"

    year_names = [
        "prabhava", "vibhava", "shukla", "pramoda", "prajApati",
        "A~Ngirasa", "shrImukha", "bhAva", "yuvan", "dhAtR",
    ]
    year_index = (date.year - 1987) % len(year_names)
    # Template lines append "సంవత్సరే" / "saMvatsare" — value is only name + nAma
    samvathsarE = f"{year_names[year_index]} nAma"

    rashi_map = {
        1: "makara rAshi",
        2: "kumbha rAshi",
        3: "mIna rAshi",
        4: "mEsha rAshi",
        5: "vRishabha rAshi",
        6: "mithuna rAshi",
        7: "karkaTa rAshi",
        8: "simha rAshi",
        9: "kanyA rAshi",
        10: "tulA rAshi",
        11: "vRishchika rAshi",
        12: "dhanu rAshi",
    }
    rashi = rashi_map.get(month, "rAshi")

    nakshatra_names = [
        "ashvini", "bharaNi", "krittika", "rOhiNi", "mrugashIrsha", "Ardra",
        "punarvasu", "pushyA", "AshlEsha", "maghA", "pUrva phalguni", "uttara phalguni",
        "hasta", "chitra", "svAti", "vishAkha", "anurAdha", "jyEshTha",
        "moola", "pUrvAshADha", "uttarAshADha", "shrAvaNa", "dhaniSTha", "shatabhisha",
        "pUrva bhAdrapada", "uttara bhAdrapada", "rEvati",
    ]
    nakshatra_index = ((month - 1) * 30 + day) % len(nakshatra_names)
    nakshatra = f"{nakshatra_names[nakshatra_index]} nakshatra"

    weekday_python = date.weekday()
    weekday_num = (weekday_python + 1) % 7
    vAsara = weekdays.get(weekday_num, "vAsara")

    yoga_names = [
        "vishkumbha", "prIti", "AyushmAn", "saubhAgya", "shobhana", "atiganda",
        "sukarma", "dhRiti", "shUla", "ganda", "vRiddhi", "dhruva",
        "vyAghAta", "harshaNa", "vajra", "siddhi", "vyatIpAta", "varIyas",
        "parigha", "shiva", "siddha", "sAdhya", "shubha", "shukla",
        "brahma", "indrA", "vaidhRiti",
    ]
    yoga_index = ((month - 1) * 30 + day) % len(yoga_names)
    yoga = f"{yoga_names[yoga_index]} yoga"

    karana_names = [
        "bava", "bAlava", "kaulava", "taitila", "garaja", "vaNija",
        "visti", "shakuni", "chatushpAda", "nAga", "kiMstughna",
    ]
    karana_index = ((month - 1) * 30 + day) % len(karana_names)
    karaNa = f"{karana_names[karana_index]} karaNa"

    return {
        "samvathsarE": samvathsarE,
        "ayanam": ayanam,
        "rithou": month_to_season.get(month, "rithou"),
        "mAsE": months.get(month, "mAsE"),
        "pakshE": "shukla pakshE",
        "thithou": "shubha thithou",
        "vAsara": vAsara,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "karaNa": karaNa,
        "rashi": rashi,
    }
