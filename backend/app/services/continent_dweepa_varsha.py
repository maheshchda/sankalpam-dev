# -*- coding: utf-8 -*-
"""
Continent-wise Dvīpa and Varṣa for sankalpa geography (Puranic names).

Canonical phrases are Sanskrit in **Harvard-Kyoto**, transliterated with
`indic_transliteration.sanscript` (same sources as `frontend/lib/continentWiseDweepaVarsha.ts`).

Nepal and Śrī Laṅkā use fixed Devanagari phrases, then script conversion.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional, Tuple

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

from app.models import Language


class ContinentDweepaKey(str, Enum):
    ASIA_INDIA = "ASIA_INDIA"
    NORTH_AMERICA = "NORTH_AMERICA"
    SOUTH_AMERICA = "SOUTH_AMERICA"
    AFRICA = "AFRICA"
    EUROPE = "EUROPE"
    AUSTRALIA = "AUSTRALIA"


# ISO 639-1 → indic_transliteration scheme (same coverage as frontend IndianLanguageCode + oriya).
_ISO_TO_SCHEME = {
    "sa": sanscript.DEVANAGARI,
    "hi": sanscript.DEVANAGARI,
    "mr": sanscript.DEVANAGARI,
    "te": sanscript.TELUGU,
    "ta": sanscript.TAMIL,
    "kn": sanscript.KANNADA,
    "ml": sanscript.MALAYALAM,
    "bn": sanscript.BENGALI,
    "gu": sanscript.GUJARATI,
    "pa": sanscript.GURMUKHI,
    "or": sanscript.ORIYA,
    "en": sanscript.DEVANAGARI,
}

# (dweepa HK, varsha HK) — locative, matches frontend CONTINENT_WISE_DWEEPA_VARSHA_SOURCE
_DWEEPA_VARSHA_HK: dict[ContinentDweepaKey, Tuple[str, str]] = {
    ContinentDweepaKey.ASIA_INDIA: ("jambudvIpe", "bhAratavarSe bhAratakhaNDe"),
    ContinentDweepaKey.NORTH_AMERICA: ("puSkaradvIpe", "ramyakavarSe"),
    ContinentDweepaKey.SOUTH_AMERICA: ("plakSadvIpe", "kuSavarSe"),
    ContinentDweepaKey.AFRICA: ("krauJcadvIpe", "rAmaNakavarSe"),
    ContinentDweepaKey.EUROPE: ("zakadvIpe", "zAvakavarSe"),
    ContinentDweepaKey.AUSTRALIA: ("zAlmalidvIpe", "arjunavarSe"),
}

_SPECIAL_NEPAL_DN = "जम्बूद्वीपे नेपालवर्षे"
_SPECIAL_LANKA_DN = "लङ्काद्वीपे"


def _norm_country(s: str) -> str:
    t = (s or "").strip().lower()
    t = re.sub(r"[\.,']", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def parse_coords(lat: Any, lon: Any) -> Tuple[Optional[float], Optional[float]]:
    """Parse latitude/longitude from request / DB (may be str or float)."""

    def _one(v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            x = float(str(v).strip())
        except (ValueError, TypeError):
            return None
        if x == 0.0 and v == "":
            return None
        return x

    return _one(lat), _one(lon)


def template_language_to_iso(
    template_language: Optional[str],
    template_language_enum: Optional[Language],
) -> str:
    if template_language_enum is not None:
        return template_language_enum.code
    s = (template_language or "").strip().lower()
    if len(s) == 2 and s.isalpha():
        return s
    for lang in Language:
        if lang.value == s or lang.code == s:
            return lang.code
    return "sa"


def _scheme_for_iso(lang_iso: str):
    return _ISO_TO_SCHEME.get((lang_iso or "sa").strip().lower(), sanscript.DEVANAGARI)


def _phrase_hk_to_scheme(dweepa_hk: str, varsha_hk: str, scheme: str) -> str:
    d = transliterate(dweepa_hk.strip(), sanscript.HK, scheme).strip()
    v = transliterate(varsha_hk.strip(), sanscript.HK, scheme).strip()
    return f"{d} {v}".strip()


def _phrase_devanagari_to_scheme(dn_phrase: str, scheme: str) -> str:
    return transliterate(dn_phrase.strip(), sanscript.DEVANAGARI, scheme).strip()


def _continent_from_latlon(lat: float, lon: float) -> ContinentDweepaKey:
    """Rough WGS84 regions when country string is missing or unmapped."""
    # Australia / Oceania (incl. NZ, much of Pacific)
    if -50 <= lat <= 5 and ((110 <= lon <= 180) or (-180 <= lon <= -110)):
        return ContinentDweepaKey.AUSTRALIA
    if -50 <= lat < 0 and 90 <= lon < 110:
        return ContinentDweepaKey.AUSTRALIA
    # South America
    if -56 <= lat < 15 and -85 <= lon <= -30:
        return ContinentDweepaKey.SOUTH_AMERICA
    # North America (incl. Caribbean latitudes)
    if 7 <= lat <= 72 and -168 <= lon <= -50:
        return ContinentDweepaKey.NORTH_AMERICA
    # Europe (excl. transcontinental handled by overlapping checks: SA first)
    if 35 <= lat <= 72 and -25 <= lon <= 45:
        return ContinentDweepaKey.EUROPE
    # Africa
    if -37 <= lat <= 38 and -25 <= lon <= 55:
        return ContinentDweepaKey.AFRICA
    # Default: Jambū / Bhārata-style bucket for remaining Asia & polar edge cases
    return ContinentDweepaKey.ASIA_INDIA


_NORTH_AMERICA = frozenset(
    {
        "united states",
        "united states of america",
        "usa",
        "us",
        "america",
        "canada",
        "mexico",
        "guatemala",
        "belize",
        "honduras",
        "el salvador",
        "nicaragua",
        "costa rica",
        "panama",
        "cuba",
        "jamaica",
        "haiti",
        "dominican republic",
        "puerto rico",
        "bahamas",
        "barbados",
        "trinidad and tobago",
        "saint lucia",
        "grenada",
        "antigua and barbuda",
        "dominica",
        "saint kitts and nevis",
        "saint vincent and the grenadines",
        "bermuda",
        "greenland",
        "aruba",
        "curacao",
        "cayman islands",
        "turks and caicos islands",
        "british virgin islands",
        "us virgin islands",
        "martinique",
        "guadeloupe",
    }
)

_SOUTH_AMERICA = frozenset(
    {
        "brazil",
        "argentina",
        "chile",
        "colombia",
        "peru",
        "venezuela",
        "ecuador",
        "bolivia",
        "paraguay",
        "uruguay",
        "guyana",
        "suriname",
        "french guiana",
        "falkland islands",
    }
)

_EUROPE = frozenset(
    {
        "united kingdom",
        "uk",
        "great britain",
        "england",
        "scotland",
        "wales",
        "northern ireland",
        "ireland",
        "france",
        "germany",
        "italy",
        "spain",
        "portugal",
        "netherlands",
        "belgium",
        "switzerland",
        "austria",
        "sweden",
        "norway",
        "denmark",
        "finland",
        "poland",
        "czech republic",
        "czechia",
        "slovakia",
        "hungary",
        "romania",
        "bulgaria",
        "greece",
        "croatia",
        "serbia",
        "slovenia",
        "bosnia and herzegovina",
        "north macedonia",
        "albania",
        "kosovo",
        "montenegro",
        "estonia",
        "latvia",
        "lithuania",
        "ukraine",
        "moldova",
        "belarus",
        "russia",
        "russian federation",
        "iceland",
        "malta",
        "cyprus",
        "luxembourg",
        "monaco",
        "liechtenstein",
        "andorra",
        "san marino",
        "vatican",
        "turkey",
        "faroe islands",
        "isle of man",
        "jersey",
        "guernsey",
        "gibraltar",
    }
)

_AFRICA = frozenset(
    {
        "algeria",
        "angola",
        "benin",
        "botswana",
        "burkina faso",
        "burundi",
        "cabo verde",
        "cameroon",
        "central african republic",
        "chad",
        "comoros",
        "congo",
        "democratic republic of the congo",
        "djibouti",
        "egypt",
        "equatorial guinea",
        "eritrea",
        "eswatini",
        "ethiopia",
        "gabon",
        "gambia",
        "ghana",
        "guinea",
        "guinea bissau",
        "ivory coast",
        "cote divoire",
        "kenya",
        "lesotho",
        "liberia",
        "libya",
        "madagascar",
        "malawi",
        "mali",
        "mauritania",
        "mauritius",
        "morocco",
        "mozambique",
        "namibia",
        "niger",
        "nigeria",
        "rwanda",
        "sao tome and principe",
        "senegal",
        "seychelles",
        "sierra leone",
        "somalia",
        "south africa",
        "south sudan",
        "sudan",
        "tanzania",
        "togo",
        "tunisia",
        "uganda",
        "zambia",
        "zimbabwe",
        "western sahara",
        "reunion",
        "mayotte",
    }
)

_AUSTRALASIA = frozenset(
    {
        "australia",
        "new zealand",
        "fiji",
        "papua new guinea",
        "solomon islands",
        "vanuatu",
        "new caledonia",
        "french polynesia",
        "samoa",
        "tonga",
        "kiribati",
        "micronesia",
        "marshall islands",
        "palau",
        "nauru",
        "tuvalu",
        "guam",
        "northern mariana islands",
        "american samoa",
        "cook islands",
        "niue",
        "tokelau",
        "wallis and futuna",
        "pitcairn",
    }
)

_ASIA_INDIA_BUCKET = frozenset(
    {
        "india",
        "bharat",
        "bangladesh",
        "pakistan",
        "bhutan",
        "maldives",
        "myanmar",
        "burma",
        "afghanistan",
        "china",
        "japan",
        "south korea",
        "north korea",
        "korea",
        "taiwan",
        "hong kong",
        "macau",
        "mongolia",
        "thailand",
        "vietnam",
        "laos",
        "cambodia",
        "malaysia",
        "singapore",
        "indonesia",
        "philippines",
        "brunei",
        "east timor",
        "timor leste",
        "uzbekistan",
        "kazakhstan",
        "kyrgyzstan",
        "tajikistan",
        "turkmenistan",
        "iran",
        "iraq",
        "saudi arabia",
        "yemen",
        "oman",
        "uae",
        "united arab emirates",
        "qatar",
        "kuwait",
        "bahrain",
        "jordan",
        "lebanon",
        "syria",
        "israel",
        "palestine",
        "georgia",
        "armenia",
        "azerbaijan",
    }
)


def infer_continent_dweepa_key(
    country: Optional[str],
    lat: Optional[float],
    lon: Optional[float],
) -> Optional[ContinentDweepaKey]:
    """
    Map location to continent bucket. None = caller should use generic country fallback.
    Nepal / Sri Lanka are handled separately in resolve_geographical_reference (not returned here).
    """
    n = _norm_country(country or "")
    if not n and lat is not None and lon is not None:
        return _continent_from_latlon(lat, lon)
    if not n:
        return None

    if "nepal" in n:
        return None
    if "sri lanka" in n or n == "ceylon":
        return None

    if "india" in n or "bharat" in n:
        return ContinentDweepaKey.ASIA_INDIA
    if n in _ASIA_INDIA_BUCKET:
        return ContinentDweepaKey.ASIA_INDIA
    if n in _NORTH_AMERICA:
        return ContinentDweepaKey.NORTH_AMERICA
    if n in _SOUTH_AMERICA:
        return ContinentDweepaKey.SOUTH_AMERICA
    if n in _EUROPE:
        return ContinentDweepaKey.EUROPE
    if n in _AFRICA:
        return ContinentDweepaKey.AFRICA
    if n in _AUSTRALASIA:
        return ContinentDweepaKey.AUSTRALIA

    if lat is not None and lon is not None:
        return _continent_from_latlon(lat, lon)
    return None


def resolve_geographical_reference(
    language_iso: str,
    country: Optional[str],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> str:
    """
    Full {{geographical_reference}} phrase for sankalpam in the given language (ISO 639-1).
    """
    iso = (language_iso or "sa").strip().lower()
    scheme = _scheme_for_iso(iso)
    n = _norm_country(country or "")

    if "nepal" in n:
        return _phrase_devanagari_to_scheme(_SPECIAL_NEPAL_DN, scheme)
    if "sri lanka" in n or n == "ceylon":
        return _phrase_devanagari_to_scheme(_SPECIAL_LANKA_DN, scheme)

    key = infer_continent_dweepa_key(country, latitude, longitude)
    if key is not None:
        d_hk, v_hk = _DWEEPA_VARSHA_HK[key]
        return _phrase_hk_to_scheme(d_hk, v_hk, scheme)

    # Legacy fallbacks (unknown country, no coords)
    if iso == "te":
        from app.services.telugu_sankalpam_output import force_telugu_place_segment

        raw = (country or "").strip()
        if not raw:
            return "దేశే"
        _cde = force_telugu_place_segment(raw)
        return f"{_cde} దేశే" if _cde else "దేశే"

    base = (country or "").strip() or ""
    if scheme == sanscript.DEVANAGARI:
        return f"{base} देशे" if base else "देशे"
    # Other Indic scripts: suffix देशे in Devanagari then convert whole phrase
    try:
        dn = f"{base} देशे" if base else "देशे"
        return transliterate(dn, sanscript.DEVANAGARI, scheme).strip()
    except Exception:
        return f"{base} देशे" if base else "देशे"
