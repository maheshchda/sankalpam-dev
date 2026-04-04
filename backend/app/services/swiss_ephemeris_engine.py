# -*- coding: utf-8 -*-
"""
Swiss Ephemeris engine for KP-style work:
- Krishnamurti ayanamsa (pyswisseph: SIDM_KRISHNAMURTI)
- Sidereal planet longitudes
- Placidus house cusps ('P') in sidereal
- Cuspal sub-lords via kp_core

Ephemeris files: set env SWISSEPH_EPHE_PATH to a folder with .se1 files for full precision;
empty path uses built-in / Moshier fallback where available.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from app.services.kp_core import KpSubLordResult, cuspal_sub_lords_from_sidereal_cusps, kp_sub_lord_from_sidereal_longitude

_swe_initialized = False


def _ensure_swiss() -> Any:
    global _swe_initialized
    import swisseph as swe

    if not _swe_initialized:
        path = (os.environ.get("SWISSEPH_EPHE_PATH") or "").strip()
        swe.set_ephe_path(path)
        swe.set_sid_mode(swe.SIDM_KRISHNAMURTI, 0, 0)
        _swe_initialized = True
    return swe


def julian_day_ut_from_local(
    dt_local_naive: datetime,
    timezone_offset_hours: float,
) -> float:
    """Interpret naive datetime as civil time in a zone UTC+offset, return Julian day UT."""
    swe = _ensure_swiss()
    tz = timezone(timedelta(hours=timezone_offset_hours))
    if dt_local_naive.tzinfo is not None:
        dt_local_naive = dt_local_naive.replace(tzinfo=None)
    aware = dt_local_naive.replace(tzinfo=tz)
    u = aware.astimezone(timezone.utc)
    hour = (
        u.hour
        + u.minute / 60.0
        + u.second / 3600.0
        + u.microsecond / 3600e6
    )
    return swe.julday(u.year, u.month, u.day, hour, swe.GREG_CAL)


def sidereal_planet_longitude(jd_ut: float, planet: int) -> float:
    swe = _ensure_swiss()
    xx, ret = swe.calc_ut(jd_ut, planet, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)
    if ret < 0:
        raise RuntimeError(swe.get_planet_name(planet) + ": Swiss Ephemeris calc_ut error")
    lon = xx[0] % 360.0
    return lon + 360.0 if lon < 0 else lon


def sidereal_sun_moon(jd_ut: float) -> Tuple[float, float]:
    swe = _ensure_swiss()
    sun = sidereal_planet_longitude(jd_ut, swe.SUN)
    moon = sidereal_planet_longitude(jd_ut, swe.MOON)
    return sun, moon


def placidus_house_cusps_sidereal(jd_ut: float, lat: float, lon: float) -> Tuple[List[float], float, float]:
    """
    Placidus cusps in sidereal (Krishnamurti ayanamsa already set).
    Returns (twelve cusp longitudes for houses 1..12, ascendant, MC).
    """
    swe = _ensure_swiss()
    cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"P", swe.FLG_SIDEREAL)
    # pyswisseph: cusps length 12 → indices 0..11 = houses 1..12
    twelve = [float(cusps[i]) % 360.0 for i in range(12)]
    asc = float(ascmc[0]) % 360.0
    mc = float(ascmc[1]) % 360.0
    return twelve, asc, mc


@dataclass
class KpChartSnapshot:
    jd_ut: float
    sun_sidereal: float
    moon_sidereal: float
    moon_kp: KpSubLordResult
    house_cusps_sidereal: List[float]
    cuspal_sub_lords: List[KpSubLordResult]
    asc_sidereal: float
    mc_sidereal: float


def compute_kp_chart(
    jd_ut: float,
    lat: float,
    lon: float,
) -> KpChartSnapshot:
    sun, moon = sidereal_sun_moon(jd_ut)
    moon_kp = kp_sub_lord_from_sidereal_longitude(moon)
    cusps, asc, mc = placidus_house_cusps_sidereal(jd_ut, lat, lon)
    csl = cuspal_sub_lords_from_sidereal_cusps(cusps)
    return KpChartSnapshot(
        jd_ut=jd_ut,
        sun_sidereal=sun,
        moon_sidereal=moon,
        moon_kp=moon_kp,
        house_cusps_sidereal=cusps,
        cuspal_sub_lords=csl,
        asc_sidereal=asc,
        mc_sidereal=mc,
    )


def kp_chart_to_dict(chart: KpChartSnapshot) -> Dict[str, Any]:
    """JSON-friendly summary for APIs / debugging."""

    def _sub(r: KpSubLordResult) -> Dict[str, Any]:
        return {
            "nakshatra": r.nakshatra_name,
            "star_lord": r.star_lord,
            "sub_lord": r.sub_lord,
            "longitude": round(r.sidereal_longitude, 6),
        }

    return {
        "jd_ut": chart.jd_ut,
        "sun_sidereal_deg": round(chart.sun_sidereal, 6),
        "moon_sidereal_deg": round(chart.moon_sidereal, 6),
        "moon": _sub(chart.moon_kp),
        "asc_sidereal_deg": round(chart.asc_sidereal, 6),
        "mc_sidereal_deg": round(chart.mc_sidereal, 6),
        "houses": [
            {
                "house": i + 1,
                "cusp_deg": round(chart.house_cusps_sidereal[i], 6),
                "cuspal_sub_lord": chart.cuspal_sub_lords[i].sub_lord,
                "cuspal_star_lord": chart.cuspal_sub_lords[i].star_lord,
                "cuspal_nakshatra": chart.cuspal_sub_lords[i].nakshatra_name,
            }
            for i in range(12)
        ],
    }
