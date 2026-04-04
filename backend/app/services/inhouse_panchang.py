# -*- coding: utf-8 -*-
"""
In-house panchang from Swiss Ephemeris (Krishnamurti sidereal Sun/Moon).

Replaces DivineAPI find-panchang for tithi / nakshatra / yoga / karana when enabled.
Chandramasa is a rough solar-based lunar month label (see docstring on limitations).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from app.services.kp_core import (
    NAKSHATRA_SPAN_DEG,
    yoga_name_for_sum_longitude,
)
from app.services.swiss_ephemeris_engine import julian_day_ut_from_local, sidereal_sun_moon

_TITHI_NAMES = [
    "Prathama",
    "Dvitiya",
    "Tritiya",
    "Chaturthi",
    "Panchami",
    "Shashthi",
    "Saptami",
    "Ashtami",
    "Navami",
    "Dashami",
    "Ekadashi",
    "Dvadashi",
    "Trayodashi",
    "Chaturdashi",
    "Purnima",
]

# Simplified karana: 6° steps cycling 11 names (not full movable/fixed BPHS table).
_KARANAS_11 = [
    "Bava",
    "Balava",
    "Kaulava",
    "Taitila",
    "Gara",
    "Vanija",
    "Vishti",
    "Shakuni",
    "Chatushpada",
    "Naga",
    "Kimstughna",
]

# Rough solar-month names: Mesha (Sun 0–30° sidereal) labelled Chaitra-style cycle for templates.
_LUNAR_MONTH_SANSKRIT = [
    "Chaitra",
    "Vaishakha",
    "Jyaishtha",
    "Ashadha",
    "Shravana",
    "Bhadrapada",
    "Ashvina",
    "Kartika",
    "Margashirsha",
    "Pausha",
    "Magha",
    "Phalguna",
]


def _lunar_month_english(sun_sidereal: float) -> str:
    idx = int((sun_sidereal % 360.0) // 30.0) % 12
    return _LUNAR_MONTH_SANSKRIT[idx]


def _tithi_paksha(elongation: float) -> Tuple[str, str, str]:
    """Elongation = (Moon - Sun) sidereal, degrees [0,360)."""
    d = elongation % 360.0
    t_index = int(d / 12.0)
    if t_index > 29:
        t_index = 29
    if t_index < 15:
        paksha = "Shukla"
        name = _TITHI_NAMES[t_index]
    else:
        paksha = "Krishna"
        lk = t_index - 15
        if lk == 14:
            name = "Amavasya"
        else:
            name = _TITHI_NAMES[lk]
    full = f"{paksha} {name}".strip()
    return paksha, name, full


def _nakshatra_name(moon_sidereal: float) -> str:
    from app.services.kp_core import NAKSHATRA_NAMES

    idx = int((moon_sidereal % 360.0) // NAKSHATRA_SPAN_DEG) % 27
    return NAKSHATRA_NAMES[idx]


def _karana_simple(elongation: float) -> str:
    d = elongation % 360.0
    return _KARANAS_11[int(d / 6.0) % 11]


def compute_panchang_dict(
    now: datetime,
    timezone_offset_hours: float,
    latitude: float,
    longitude: float,
) -> Optional[Dict[str, Any]]:
    """
    Returns the same keys as DivineAPI parsing in divineapi_service._fetch_panchang_for_today.
    Uses local date/time interpreted with timezone_offset_hours at the given place for JD.
    """
    try:
        import swisseph  # noqa: F401
    except ImportError:
        print("[Panchang] pyswisseph not installed; pip install pyswisseph")
        return None
    try:
        jd = julian_day_ut_from_local(now, timezone_offset_hours)
        sun, moon = sidereal_sun_moon(jd)
    except Exception as e:
        print(f"[Panchang] Swiss Ephemeris compute failed: {e}")
        return None

    elong = (moon - sun) % 360.0
    paksha, _tname, tithi_full = _tithi_paksha(elong)
    nak = _nakshatra_name(moon)
    yoga = yoga_name_for_sum_longitude(sun, moon)
    karana = _karana_simple(elong)

    return {
        "tithi": tithi_full,
        "paksha": paksha,
        "tithi_end_time": "",
        "nakshatra": nak,
        "nakshatra_end_time": "",
        "yoga": yoga,
        "karana": karana,
        "_source": "swiss_ephemeris_kp",
        "_sun_sidereal_deg": sun,
        "_moon_sidereal_deg": moon,
    }


def compute_chandramasa_english(
    now: datetime,
    timezone_offset_hours: float,
    latitude: float,
    longitude: float,
) -> Optional[str]:
    """Rough lunar month label from solar sidereal sign (not full amanta/purnimanta)."""
    try:
        import swisseph  # noqa: F401
    except ImportError:
        return None
    try:
        jd = julian_day_ut_from_local(now, timezone_offset_hours)
        sun, _ = sidereal_sun_moon(jd)
    except Exception:
        return None
    return _lunar_month_english(sun)
