# -*- coding: utf-8 -*-
"""
Krishnamurti Paddhati (KP) core: Vimshottari-based sub-lords on the 13°20' nakshatra arc.

Swiss Ephemeris supplies sidereal longitudes (Krishnamurti ayanamsa). This module is pure math:
given a sidereal longitude in [0, 360), compute star lord, sub lord, and (optionally) cuspal sub-lords.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

# Vimshottari dasha years (Ketu … Mercury) — total 120
VIMSHOTTARI_YEARS: Tuple[int, ...] = (7, 20, 6, 10, 7, 18, 16, 19, 17)

# Standard Vimshottari order (same index as VIMSHOTTARI_YEARS)
VIMSHOTTARI_PLANETS: Tuple[str, ...] = (
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
)

NAKSHATRA_SPAN_DEG = 360.0 / 27.0  # 13°20'

# 27 nakshatras; lord of nakshatra i = VIMSHOTTARI_PLANETS[i % 9]
NAKSHATRA_NAMES: Tuple[str, ...] = (
    "Ashwini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashira",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Ashlesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishta",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
)

YOGA_NAMES: Tuple[str, ...] = (
    "Vishkambha",
    "Priti",
    "Ayushman",
    "Saubhagya",
    "Shobhana",
    "Atiganda",
    "Sukarma",
    "Dhriti",
    "Shoola",
    "Ganda",
    "Vriddhi",
    "Dhruva",
    "Vyaghata",
    "Harshana",
    "Vajra",
    "Siddhi",
    "Vyatipata",
    "Variyan",
    "Parigha",
    "Shiva",
    "Siddha",
    "Sadhya",
    "Shubha",
    "Shukla",
    "Brahma",
    "Indra",
    "Vaidhriti",
)


@dataclass(frozen=True)
class KpSubLordResult:
    sidereal_longitude: float
    nakshatra_index: int
    nakshatra_name: str
    star_lord: str
    sub_lord: str
    degree_within_nakshatra: float


def _norm360(x: float) -> float:
    y = x % 360.0
    return y + 360.0 if y < 0 else y


def nakshatra_index_and_offset(sidereal_longitude: float) -> Tuple[int, float]:
    lon = _norm360(sidereal_longitude)
    idx = int(lon // NAKSHATRA_SPAN_DEG) % 27
    offset = lon - idx * NAKSHATRA_SPAN_DEG
    if offset < 0:
        offset += NAKSHATRA_SPAN_DEG
    return idx, offset


def star_lord_for_nakshatra(nakshatra_index: int) -> str:
    return VIMSHOTTARI_PLANETS[nakshatra_index % 9]


def kp_sub_lord_from_sidereal_longitude(sidereal_longitude: float) -> KpSubLordResult:
    """
    KP sub-lord: divide the current nakshatra (13°20') into 9 unequal subs
    proportional to Vimshottari years, starting from the star lord and following
    Vimshottari order.
    """
    idx, within = nakshatra_index_and_offset(sidereal_longitude)
    nak_name = NAKSHATRA_NAMES[idx]
    star = star_lord_for_nakshatra(idx)
    start_order = idx % 9  # Ashwini → Ketu (0), Bharani → Venus (1), …

    cumulative = 0.0
    sub_lord = VIMSHOTTARI_PLANETS[(start_order + 8) % 9]
    for k in range(9):
        p_order = (start_order + k) % 9
        planet = VIMSHOTTARI_PLANETS[p_order]
        years = VIMSHOTTARI_YEARS[p_order]
        width = (years / 120.0) * NAKSHATRA_SPAN_DEG
        if within < cumulative + width:
            sub_lord = planet
            break
        cumulative += width

    return KpSubLordResult(
        sidereal_longitude=_norm360(sidereal_longitude),
        nakshatra_index=idx,
        nakshatra_name=nak_name,
        star_lord=star,
        sub_lord=sub_lord,
        degree_within_nakshatra=within,
    )


def cuspal_sub_lords_from_sidereal_cusps(cusp_longitudes: Sequence[float]) -> List[KpSubLordResult]:
    """House cusps 1..12 sidereal → KP sub-lord at each cusp start."""
    out: List[KpSubLordResult] = []
    for lon in cusp_longitudes:
        out.append(kp_sub_lord_from_sidereal_longitude(float(lon)))
    return out


def yoga_name_for_sum_longitude(sun_sidereal: float, moon_sidereal: float) -> str:
    s = _norm360(sun_sidereal + moon_sidereal)
    y_idx = int(s // NAKSHATRA_SPAN_DEG) % 27
    return YOGA_NAMES[y_idx]
