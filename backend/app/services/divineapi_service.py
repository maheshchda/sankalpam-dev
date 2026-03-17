import httpx
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from app.models import User, FamilyMember, Language
from app.config import settings

# Sankalpam templates: backend/templates/{language}/ e.g. telugu/Ganesh_Pooja_template_telugu.txt
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_BASE_DIR = _BACKEND_DIR / "templates"
# Explicit path to Ganesh Pooja Telugu template so it's always found when file exists
_GANESH_POOJA_TELUGU_TEMPLATE_PATH = _BACKEND_DIR / "templates" / "telugu" / "Ganesh_Pooja_template_telugu.txt"
# Fallback literal path (e.g. when running from different cwd)
_GANESH_POOJA_TELUGU_PATHS = [
    _GANESH_POOJA_TELUGU_TEMPLATE_PATH,
    Path(r"C:\Projects\sankalpam-dev\backend\templates\telugu\Ganesh_Pooja_template_telugu.txt"),
]

# ISO 639-1 code -> folder name under templates/
_LANGUAGE_CODE_TO_FOLDER = {
    "te": "telugu", "hi": "hindi", "sa": "sanskrit", "ta": "tamil", "kn": "kannada",
    "ml": "malayalam", "en": "english", "mr": "marathi", "gu": "gujarati",
    "bn": "bengali", "or": "oriya", "pa": "punjabi",
}

# Inline Telugu template fallback when file is missing (ensures we never return Sanskrit for Telugu requests)
_TELUGU_TEMPLATE_INLINE = """ఓం శ్రీమహాగణపతయే నమః ॥

మమ ఉపాత్త సమస్త దురితక్షయ ద్వారా
శ్రీపరమేశ్వర ప్రీత్యర్థమ్ ।

అద్య శ్రీమద్ బ్రహ్మణః ద్వితీయ పారార్ధే
శ్వేతవరాహ కల్పే
వైవస్వత మన్వంతరే
{{samvathsarE}} సంవత్సరే
అష్టావింశతితే కలియుగే
ప్రథమే పాదే

{{geographical_reference}}
{{current_location}} స్థానే
{{geographical_feature}}

అస్మిన్ శుభే శుద్ధే
{{rithou}} ఋతౌ
{{mAsE}} మాసే
{{pakshE}} పక్షే
{{thithou}} తిథౌ
{{vAsara}} వారే
{{nakshatra}} నక్షత్రే
{{yoga}} యోగే
{{karaNa}} కరణే
{{ayanam}} ॥

శుభే ముహూర్తే
అహం {{user_name}}
గోత్ర {{gotram}}
{{birth_nakshatra}} నక్షత్రే
{{birth_rashi}} రాశౌ

జన్మస్థానం: {{birth_place}}
జన్మసమయం: {{birth_time}}

{{birth_city}} స్థానే
{{birth_state}} రాష్ట్రే
{{birth_country}} దేశే
{{birth_date}} సంవత్సరే జన్మ ప్రాప్తవాన్

మమ పారివారిక సదస్యులు:
{{family_members}}

ఇత్యాది సకలపాపక్షయపూర్వకం
అఖండమండలాకారం వ్యాప్తం యేన చరాచరం
తత్పరమేశ్వరం ప్రణమ్య

అస్యాం శుభతిథౌ
{{pooja_name}} పూజనం కరిష్యే ।

తత్సిద్ధ్యర్థం
సంకల్పం కరోమి ॥

శుభం భవతు ॥
"""

# Telugu equivalents for English calendar/panchang terms (so Telugu template has no English script)
_TE_MONTHS = {
    "january": "జనవరి", "february": "ఫిబ్రవరి", "march": "మార్చి", "april": "ఏప్రిల్",
    "may": "మే", "june": "జూన్", "july": "జూలై", "august": "ఆగస్టు",
    "september": "సెప్టెంబర్", "october": "అక్టోబర్", "november": "నవంబర్", "december": "డిసెంబర్",
}
_TE_WEEKDAYS = {
    "monday": "సోమవారం", "tuesday": "మంగళవారం", "wednesday": "బుధవారం", "thursday": "గురువారం",
    "friday": "శుక్రవారం", "saturday": "శనివారం", "sunday": "ఆదివారం",
}
_TE_RITU = {
    1: "శిశిరం", 2: "శిశిరం", 3: "వసంతం", 4: "వసంతం", 5: "గ్రీష్మం", 6: "గ్రీష్మం",
    7: "వర్షం", 8: "వర్షం", 9: "శరదృతువు", 10: "శరదృతువు", 11: "హేమంతం", 12: "హేమంతం",
}
_TE_PAKSHA = {"shukla": "శుక్ల", "krishna": "కృష్ణ", "sukla": "శుక్ల", "krishna paksha": "కృష్ణ పక్షం", "shukla paksha": "శుక్ల పక్షం"}
_TE_TITHI = {
    "prathama": "ప్రథమ", "pratipada": "ప్రతిపద", "dvitiya": "ద్వితీయ", "tritiya": "తృతీయ", "chaturthi": "చతుర్థి", "panchami": "పంచమి",
    "shashthi": "షష్ఠి", "saptami": "సప్తమి", "ashtami": "అష్టమి", "navami": "నవమి", "dashami": "దశమి",
    "ekadashi": "ఏకాదశి", "dvadashi": "ద్వాదశి", "trayodashi": "త్రయోదశి", "chaturdashi": "చతుర్దశి", "purnima": "పౌర్ణమి",
    "amavasya": "అమావాస్య",
}
_TE_NAKSHATRA = {
    "ashwini": "అశ్విని", "bharani": "భరణి", "krittika": "కృత్తిక", "rohini": "రోహిణి", "mrigashira": "మృగశిర",
    "ardra": "ఆర్ద్ర", "punarvasu": "పునర్వసు", "pushya": "పుష్య", "ashlesha": "ఆశ్లేష", "magha": "మఖ",
    "purva phalguni": "పూర్వ ఫల్గుణి", "uttara phalguni": "ఉత్తర ఫల్గుణి", "hasta": "హస్త", "chitra": "చిత్ర",
    "swati": "స్వాతి", "vishakha": "విశాఖ", "anuradha": "అనురాధ", "jyestha": "జ్యేష్ఠ", "mula": "మూల",
    "purva ashadha": "పూర్వాషాఢ", "uttara ashadha": "ఉత్తరాషాఢ", "shravana": "శ్రవణం", "dhanishta": "ధనిష్ఠ",
    "shatabhisha": "శతభిషం", "purva bhadrapada": "పూర్వ భాద్రపద", "uttara bhadrapada": "ఉత్తర భాద్రపద", "revati": "రేవతి",
    # Alternate spellings (no space, or three words)
    "purvabhadrapada": "పూర్వ భాద్రపద", "uttarabhadrapada": "ఉత్తర భాద్రపద",
    "purva bhadra pada": "పూర్వ భాద్రపద", "uttara bhadra pada": "ఉత్తర భాద్రపద",
}
_TE_YOGA = {
    "vishkumbha": "విష్కుంభ", "preeti": "ప్రీతి", "ayushman": "ఆయుష్మాన్", "saubhagya": "సౌభాగ్య",
    "shobhana": "శోభన", "atiganda": "అతిగండ", "sukarma": "సుకర్మ", "dhriti": "ధృతి", "shula": "శూల",
    "ganda": "గండ", "vridhi": "వృద్ధి", "dhruva": "ధ్రువ", "vyaghata": "వ్యాఘాట", "harshana": "హర్షణ",
    "vajra": "వజ్ర", "siddhi": "సిద్ధి", "vyatipata": "వ్యతీపాత", "variyan": "వరియాన్", "parigha": "పరిఘ",
    "shiva": "శివ", "siddha": "సిద్ధ", "sadhya": "సాధ్య", "shubha": "శుభ", "shukla": "శుక్ల",
    "brahma": "బ్రహ్మ", "indra": "ఇంద్ర", "vaidhriti": "వైధృతి",
}
_TE_KARANA = {
    "bava": "బవ", "balava": "బాలవ", "kaulava": "కౌలవ", "taitila": "తైతిల", "gara": "గర",
    "vanija": "వణిజ", "vishti": "విష్టి", "bhadra": "భద్ర", "shakuni": "శకుని", "chatushpada": "చతుష్పాద",
    "naga": "నాగ", "kimstughna": "కింస్తుఘ్న",
}
_TE_POOJA_NAMES = {"ganesh pooja": "గణేశ పూజ", "ganesha pooja": "గణేశ పూజ", "lakshmi pooja": "శ్రీ లక్ష్మీ పూజ"}
_TE_RASHI = {
    "aries": "మేషం", "taurus": "వృషభం", "gemini": "మిథునం", "cancer": "కర్కాటకం",
    "leo": "సింహం", "virgo": "కన్య", "libra": "తులా", "scorpio": "వృశ్చికం",
    "sagittarius": "ధనుస్సు", "capricorn": "మకరం", "aquarius": "కుంభం", "pisces": "మీనం",
    "mesha": "మేషం", "vrishabha": "వృషభం", "mithuna": "మిథునం", "karkata": "కర్కాటకం",
    "simha": "సింహం", "kanya": "కన్య", "tula": "తులా", "vrishchika": "వృశ్చికం",
    "dhanu": "ధనుస్సు", "makara": "మకరం", "kumbha": "కుంభం", "mina": "మీనం",
    # Pooja convention: Meena Rasi in Telugu as మీన
    "meena": "మీన", "meenam": "మీన",
}

# Relation labels in Telugu for family members
_TE_RELATION = {
    "father": "తండ్రి", "mother": "తల్లి", "spouse": "భార్య/భర్త", "husband": "భర్త", "wife": "భార్య",
    "son": "కుమారుడు", "daughter": "కుమార్తె", "child": "సంతానం", "brother": "సోదరుడు",
    "sister": "సోదరి", "grandfather": "తాత", "grandmother": "అమ్మమ్మ", "grandson": "మనుమడు",
    "granddaughter": "మనుమరాలు", "uncle": "మామ/చెల్లెలు భర్త", "aunt": "అత్త/పిన్ని",
    "nephew": "అన్నయ్య/చెల్లెలు కుమారుడు", "niece": "అన్నయ్య/చెల్లెలు కుమార్తె",
}


# Curated Latin -> Telugu for common names (finer forms: మహేష్ not మఅహఎసహ)
_COMMON_NAME_TO_TELUGU = {
    "mahesh": "మహేష్", "chada": "చాద", "polisetla": "పోలిసేట్ల", "polishetla": "పోలిసేట్ల",
    "datta": "దత్త", "mahita": "మహిత", "radha": "రాధ", "madhavi": "మాధవి", "putnala": "పుట్నాల",
    "rama": "రామ", "sita": "సీత", "lakshmi": "లక్ష్మి", "krishna": "కృష్ణ", "venkata": "వెంకట",
    "srinivas": "శ్రీనివాస", "rao": "రావు", "reddy": "రెడ్డి", "naidu": "నాయుడు",
    "karimnagar": "కరీంనగర్", "hyderabad": "హైదరాబాద్", "telangana": "తెలంగాణ",
    "richmond": "రిచ్మండ్", "india": "భారతదేశం",
}
# Fallback when indic_transliteration is unavailable: simple Latin letter -> Telugu
_LATIN_TO_TELUGU_FALLBACK = {
    "a": "అ", "b": "బ", "c": "క", "d": "డ", "e": "ఎ", "f": "ఫ", "g": "గ", "h": "హ",
    "i": "ఇ", "j": "జ", "k": "క", "l": "ల", "m": "మ", "n": "న", "o": "ఓ", "p": "ప",
    "q": "క", "r": "ర", "s": "స", "t": "ట", "u": "ఉ", "v": "వ", "w": "వ", "x": "క్స",
    "y": "య", "z": "జ",
}


def _latin_name_to_telugu(text: str) -> str:
    """Transliterate to Telugu: curated names first, then indic_transliteration (HK with sh->S), then letter fallback."""
    if not text or not isinstance(text, str):
        return text or ""
    text = text.strip()
    if not text:
        return text
    normal = text.lower()
    # 1) Check curated dict for full phrase and for each word
    if normal in _COMMON_NAME_TO_TELUGU:
        return _COMMON_NAME_TO_TELUGU[normal]
    words = normal.split()
    if len(words) == 1 and words[0] in _COMMON_NAME_TO_TELUGU:
        return _COMMON_NAME_TO_TELUGU[words[0]]
    # 2) Per-word: curated first, else library with HK (normalize trailing 'sh' -> 'S' for మహేష్-style)
    result_parts = []
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
        for word in words:
            if not word:
                continue
            if word in _COMMON_NAME_TO_TELUGU:
                result_parts.append(_COMMON_NAME_TO_TELUGU[word])
                continue
            # HK: word-final "sh" -> "S" gives ష్ (e.g. mahesh -> maheS -> మహేష్)
            hk_word = word[:-2] + "S" if len(word) > 2 and word.endswith("sh") else word
            out = transliterate(hk_word, sanscript.HK, sanscript.TELUGU)
            if out and out.strip() and any("\u0c00" <= c <= "\u0c7f" for c in out):
                result_parts.append(out.strip())
            else:
                out = transliterate(word, sanscript.IAST, sanscript.TELUGU)
                if out and out.strip() and any("\u0c00" <= c <= "\u0c7f" for c in out):
                    result_parts.append(out.strip())
                else:
                    result_parts.append("".join(_LATIN_TO_TELUGU_FALLBACK.get(c, c) for c in word))
        if result_parts:
            return " ".join(result_parts)
    except Exception:
        result_parts = []
    # 3) Fallback when library unavailable: curated per-word then letter-by-letter
    for word in words:
        if word in _COMMON_NAME_TO_TELUGU:
            result_parts.append(_COMMON_NAME_TO_TELUGU[word])
        else:
            result_parts.append("".join(_LATIN_TO_TELUGU_FALLBACK.get(c, c) for c in word))
    return " ".join(result_parts) if result_parts else "".join(_LATIN_TO_TELUGU_FALLBACK.get(c, c) for c in normal)


def _english_to_telugu(text: str, mapping: dict) -> str:
    """Return Telugu for English key (case-insensitive); else return original text."""
    if not text or not isinstance(text, str):
        return text or ""
    key = text.strip().lower()
    return mapping.get(key) or text


def _tithi_to_telugu(tithi: str) -> str:
    """Convert tithi string (e.g. 'Krishna Chaturdashi') to Telugu."""
    if not tithi or not isinstance(tithi, str):
        return tithi or ""
    parts = tithi.strip().split()
    out = []
    for p in parts:
        low = p.lower()
        if low in _TE_PAKSHA:
            out.append(_TE_PAKSHA[low])
        elif low in _TE_TITHI:
            out.append(_TE_TITHI[low])
        else:
            # Try multi-word nakshatra-style (e.g. purva phalguni)
            out.append(p)
    return " ".join(out) if out else tithi


def _nakshatra_to_telugu(nak: str) -> str:
    if not nak:
        return ""
    s = nak.strip()
    if not s:
        return ""
    # Try exact key (lowercase), then key with spaces collapsed (e.g. "Purva Bhadrapada" -> "purvabhadrapada")
    out = _english_to_telugu(s, _TE_NAKSHATRA)
    if out and out != s:
        return out
    key_no_spaces = s.lower().replace(" ", "")
    out = _TE_NAKSHATRA.get(key_no_spaces)
    if out:
        return out
    return s


# ISO 639-1 codes for language selection (e.g. Telugu/telugu -> 'te')
_LANG_NAME_OR_CODE_TO_ISO = {
    "hindi": "hi", "hi": "hi",
    "telugu": "te", "te": "te",
    "tamil": "ta", "ta": "ta",
    "kannada": "kn", "kn": "kn",
    "malayalam": "ml", "ml": "ml",
    "sanskrit": "sa", "sa": "sa",
    "english": "en", "en": "en",
    "marathi": "mr", "mr": "mr",
    "gujarati": "gu", "gu": "gu",
    "bengali": "bn", "bn": "bn",
    "oriya": "or", "or": "or",
    "punjabi": "pa", "pa": "pa",
}


def _language_to_iso(user_or_lang) -> str:
    """Normalize Language enum or string (name or code) to ISO 639-1 code (e.g. 'te')."""
    if user_or_lang is None:
        return "sa"
    if isinstance(user_or_lang, Language):
        return user_or_lang.code
    s = (user_or_lang if isinstance(user_or_lang, str) else str(user_or_lang)).strip().lower()
    return _LANG_NAME_OR_CODE_TO_ISO.get(s, "sa")


# Fallback coordinates when lat/lon not sent (so Panchang API gets valid place)
_PLACE_COORDS_FALLBACK = {
    ("richmond", "tx", "usa"): (29.58, -95.76),
    ("richmond", "texas", "united states"): (29.58, -95.76),
    ("houston", "tx", "usa"): (29.76, -95.37),
    ("hyderabad", "telangana", "india"): (17.39, 78.49),
    ("delhi", "delhi", "india"): (28.61, 77.21),
}


def _is_us_location(country: Optional[str]) -> bool:
    if not country:
        return False
    c = country.lower().strip()
    return c in ("usa", "us", "united states", "united states of america")


def _us_state_timezone_offset(state: Optional[str]) -> float:
    """Rough UTC offset in hours for US states (for Panchang when browser TZ not sent)."""
    if not state:
        return -6.0
    s = state.upper().strip()
    # Central
    if s in ("TX", "IL", "WI", "MN", "IA", "MO", "AR", "LA", "MS", "AL", "OK", "KS", "NE", "SD", "ND", "TN", "IN", "KY", "FL", "MI", "IL"):
        # FL/KY/TN/IN/MI are split; use Central for TX and central states
        central = ("TX", "OK", "KS", "NE", "SD", "ND", "MN", "IA", "MO", "AR", "LA", "MS", "AL", "WI", "IL")
        if s in central:
            return -6.0
    if s in ("NY", "NJ", "PA", "CT", "MA", "VT", "NH", "ME", "RI", "OH", "VA", "NC", "SC", "GA", "WV", "DE", "MD", "DC"):
        return -5.0
    if s in ("CO", "NM", "WY", "MT", "UT", "AZ"):
        return -7.0
    if s in ("CA", "NV", "WA", "OR", "ID"):
        return -8.0
    return -6.0


async def _resolve_coords_for_panchang(
    city: str, state: str, country: str
) -> Tuple[Optional[str], Optional[str]]:
    """Return (lat, lon) for Panchang when request did not send coords. Tries fallback dict then Nominatim."""
    c = (city or "").strip().lower()
    s = (state or "").strip().lower()
    co = (country or "").strip().lower()
    key = (c, s, co)
    if key in _PLACE_COORDS_FALLBACK:
        lat, lon = _PLACE_COORDS_FALLBACK[key]
        return str(lat), str(lon)
    for (fc, fs, fco), (lat, lon) in _PLACE_COORDS_FALLBACK.items():
        if (c == fc or c in fc) and (s == fs or s in fs) and (co == fco or co in fco):
            return str(lat), str(lon)
    # Try Nominatim forward geocode (free)
    try:
        query = f"{city}, {state}, {country}".strip(", ")
        async with httpx.AsyncClient(timeout=8.0) as client:
            r = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={"q": query, "format": "json", "limit": "1"},
                headers={"User-Agent": "SankalpamApp/1.0"},
            )
        if r.status_code != 200:
            return None, None
        data = r.json()
        if data and isinstance(data, list) and len(data) > 0:
            first = data[0]
            lat = first.get("lat")
            lon = first.get("lon")
            if lat is not None and lon is not None:
                return str(lat), str(lon)
    except Exception:
        pass
    return None, None


def _fallback_panchang_for_today(now: datetime) -> dict:
    """
    Return approximate panchang (tithi, paksha, nakshatra, yoga, karana) when Divine API
    is not configured or fails. Uses date-based approximation so template fields are never empty.
    """
    day = now.day
    month = now.month
    # Approximate paksha: first half of month -> Shukla, second half -> Krishna
    paksha = "Shukla" if day <= 15 else "Krishna"
    tithi_day = min(day, 15) if day <= 15 else min(day - 15, 15)
    shukla_tithis = [
        "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
        "Ashtami", "Navami", "Dashami", "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima"
    ]
    krishna_tithis = [
        "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
        "Ashtami", "Navami", "Dashami", "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Amavasya"
    ]
    tithi_names = shukla_tithis if day <= 15 else krishna_tithis
    tithi_name = tithi_names[tithi_day - 1] if 1 <= tithi_day <= 15 else tithi_names[0]
    tithi = f"{paksha} {tithi_name}"
    nakshatra_list = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
        "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
        "Vishakha", "Anuradha", "Jyestha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
        "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]
    yoga_list = [
        "Vishkumbha", "Preeti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma", "Dhriti",
        "Shula", "Ganda", "Vridhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi",
        "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla",
        "Brahma", "Indra", "Vaidhriti"
    ]
    karana_list = [
        "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti", "Shakuni",
        "Chatushpada", "Naga", "Kimstughna"
    ]
    idx = ((month - 1) * 30 + day) % len(nakshatra_list)
    return {
        "tithi": tithi,
        "paksha": paksha,
        "nakshatra": nakshatra_list[idx],
        "yoga": yoga_list[idx % len(yoga_list)],
        "karana": karana_list[idx % len(karana_list)],
    }


async def _fetch_panchang_for_today(
    now: datetime,
    location_city: str,
    location_state: str,
    location_country: str,
    latitude: Optional[str],
    longitude: Optional[str],
    timezone_offset_hours: float,
    language: str,
) -> Optional[dict]:
    """
    Call Divine API Daily Panchang endpoint to get tithi, nakshatra, yoga, karana, etc.
    Returns a small dict with the key fields we need, or None on failure.
    """
    if not settings.divine_api_key or not settings.divine_access_token:
        print("[Panchang] Divine API key or token not set. Set Divine_API_Key and Divine_Access_Token in .env")
        return None

    day = now.day
    month = now.month
    year = now.year
    city = (location_city or "").strip()
    state = (location_state or "").strip()
    country = (location_country or "").strip()
    place = ", ".join(p for p in [city, state, country] if p) or "Unknown"

    # API requires lat/lon; use 0,0 when missing so request is valid (send as numbers)
    try:
        lat_num = float(latitude) if latitude not in (None, "") else 0.0
    except (TypeError, ValueError):
        lat_num = 0.0
    try:
        lon_num = float(longitude) if longitude not in (None, "") else 0.0
    except (TypeError, ValueError):
        lon_num = 0.0

    tzone = timezone_offset_hours
    api_language = _language_to_iso(language) if language else "en"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = "https://astroapi-1.divineapi.com/indian-api/v2/find-panchang"
            headers = {
                "Authorization": f"Bearer {settings.divine_access_token}",
            }
            # Divine API: place, lat, lon, tzone, lan (some implementations expect string lat/lon)
            data = {
                "api_key": settings.divine_api_key,
                "day": str(day),
                "month": str(month),
                "year": str(year),
                "place": place,
                "Place": place,
                "lat": str(lat_num),
                "lon": str(lon_num),
                "tzone": str(tzone),
                "lan": api_language,
            }

            response = await client.post(url, headers=headers, data=data)
            if response.status_code != 200:
                print(f"DivineAPI find-panchang error: {response.status_code} - {response.text[:500]}")
                return None

            payload = response.json()
            if not payload.get("success"):
                print(f"DivineAPI find-panchang success=false: {payload.get('message', payload)[:200]}")
                return None

            pdata = payload.get("data") or payload
            if not isinstance(pdata, dict):
                pdata = {}

            # Tithi: try tithis[0] (paksha + tithi) or top-level tithi/paksha
            tithi_name = None
            paksha_name = None
            tithi_end_time = None
            tithis = pdata.get("tithis") or []
            if tithis and isinstance(tithis, list):
                t0 = tithis[0] if isinstance(tithis[0], dict) else {}
                if t0.get("tithi"):
                    paksha_name = t0.get("paksha") or ""
                    tithi_name = f"{paksha_name} {t0['tithi']}".strip() or t0["tithi"]
                    tithi_end_time = (
                        t0.get("end_time") or t0.get("tithi_end_time") or
                        t0.get("tithi_end") or t0.get("endtime") or None
                    )
            if not tithi_name and (pdata.get("tithi") or pdata.get("tithi_name")):
                paksha_name = pdata.get("paksha") or ""
                tithi_name = f"{paksha_name} {pdata.get('tithi') or pdata.get('tithi_name')}".strip()
                tithi_end_time = tithi_end_time or pdata.get("tithi_end_time") or pdata.get("tithi_end")

            # Nakshatra: nakshatras.nakshatra_list[0] or nakshatra_list or current_nakshatra or nakshatra (object)
            nakshatra_name = None
            nakshatra_end_time = None
            nak_block = pdata.get("nakshatras") or {}
            nak_list = nak_block.get("nakshatra_list") if isinstance(nak_block, dict) else (pdata.get("nakshatra_list") or [])
            if nak_list and isinstance(nak_list, list) and len(nak_list) > 0:
                first = nak_list[0]
                if isinstance(first, dict):
                    nakshatra_name = first.get("nak_name") or first.get("nakshatra_name") or first.get("name")
                    nakshatra_end_time = (
                        first.get("end_time") or first.get("nak_end_time") or
                        first.get("nakshatra_end_time") or first.get("endtime") or None
                    )
                elif isinstance(first, str):
                    nakshatra_name = first
            if not nakshatra_name and pdata.get("nakshatra_name"):
                nakshatra_name = pdata.get("nakshatra_name")
            if not nakshatra_name and pdata.get("current_nakshatra"):
                nakshatra_name = pdata.get("current_nakshatra")
            if not nakshatra_name:
                nk = pdata.get("nakshatra")
                if isinstance(nk, dict):
                    nakshatra_name = nk.get("name") or nk.get("nak_name") or nk.get("nakshatra_name")
                    nakshatra_end_time = nakshatra_end_time or nk.get("end_time") or nk.get("nak_end_time")
                elif isinstance(nk, str):
                    nakshatra_name = nk

            # Yoga: yogas[0] or yoga_name or yoga (object)
            yoga_name = None
            yogas = pdata.get("yogas") or []
            if yogas and isinstance(yogas, list) and len(yogas) > 0:
                y0 = yogas[0]
                if isinstance(y0, dict):
                    yoga_name = y0.get("yoga_name") or y0.get("yoga") or y0.get("name")
                elif isinstance(y0, str):
                    yoga_name = y0
            if not yoga_name and pdata.get("yoga_name"):
                yoga_name = pdata.get("yoga_name")
            if not yoga_name and isinstance(pdata.get("yoga"), str):
                yoga_name = pdata.get("yoga")

            # Karana: karnas[0] or karana_name or karana (object)
            karana_name = None
            karnas = pdata.get("karnas") or []
            if karnas and isinstance(karnas, list) and len(karnas) > 0:
                k0 = karnas[0]
                if isinstance(k0, dict):
                    karana_name = k0.get("karana_name") or k0.get("karana") or k0.get("name")
                elif isinstance(k0, str):
                    karana_name = k0
            if not karana_name and pdata.get("karana_name"):
                karana_name = pdata.get("karana_name")
            if not karana_name and isinstance(pdata.get("karana"), str):
                karana_name = pdata.get("karana")

            result = {
                "tithi":             tithi_name or "",
                "paksha":            paksha_name or "",
                "tithi_end_time":    tithi_end_time or "",
                "nakshatra":         nakshatra_name or "",
                "nakshatra_end_time": nakshatra_end_time or "",
                "yoga":              yoga_name or "",
                "karana":            karana_name or "",
            }
            print("[Panchang] Fetched from Divine API:", result.get("nakshatra"), result.get("tithi_end_time"), result.get("nakshatra_end_time"))
            return result
    except Exception as e:
        print(f"[Panchang] Error calling DivineAPI find-panchang: {e}")
        import traceback
        traceback.print_exc()
        return None


# Divine API Chandramasa uses different lan codes: tl=Telugu, tm=Tamil, ma=Marathi, etc.
_DIVINE_LAN_FOR_CHANDRAMASA = {
    "te": "tl", "hi": "hi", "sa": "hi", "ta": "tm", "ml": "ml", "kn": "kn",
    "mr": "ma", "bn": "bn", "en": "en", "gu": "en", "or": "en", "pa": "en",
}


async def _fetch_chandramasa_for_today(
    now: datetime,
    place: str,
    latitude: Optional[str],
    longitude: Optional[str],
    timezone_offset_hours: float,
    lan: str,
) -> Optional[str]:
    """
    Call Divine API Find Chandramasa to get the current Indian lunar month name in the requested language.
    Returns e.g. Telugu month name when lan='tl', Hindi when lan='hi'. Used for {{mAsE}} in templates.
    """
    if not settings.divine_api_key or not settings.divine_access_token:
        return None
    # Default to English if lan not supported by Chandramasa
    divine_lan = _DIVINE_LAN_FOR_CHANDRAMASA.get(lan, "en") if lan else "en"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            url = "https://astroapi-3.divineapi.com/indian-api/v2/chandramasa"
            headers = {"Authorization": f"Bearer {settings.divine_access_token}"}
            data = {
                "api_key": settings.divine_api_key,
                "day": str(now.day),
                "month": str(now.month),
                "year": str(now.year),
                "Place": place or "Unknown",
                "lat": latitude or "0",
                "lon": longitude or "0",
                "tzone": str(timezone_offset_hours),
                "lan": divine_lan,
            }
            response = await client.post(url, headers=headers, data=data)
            if response.status_code != 200:
                return None
            payload = response.json()
            if not payload.get("success"):
                return None
            cdata = payload.get("data") or {}
            chandramasa = cdata.get("chandramasa")
            return str(chandramasa).strip() if chandramasa else None
    except Exception as e:
        print(f"Error calling DivineAPI chandramasa: {e}")
        return None


# For Telugu, Ganesh Pooja always uses Ganesh_Pooja_template_telugu.txt (handles "Ganesh Pooja" / "Ganesha Pooja")
_POOJA_TO_TELUGU_TEMPLATE = {
    "ganesh_pooja",
    "ganesha_pooja",
}


def get_poojas_available_for_language(language_code: str, pooja_list: list) -> list:
    """
    Return only poojas that have a sankalpam template file for the given language.
    Same rule for all languages (including Sanskrit and Hindi): only poojas with a
    template in templates/{language}/ are returned. Empty folder -> no poojas.
    """
    code = (language_code or "").strip().lower()
    if not code:
        return list(pooja_list)
    result = []
    for pooja in pooja_list:
        name = getattr(pooja, "name", None) or str(pooja)
        if _get_sankalpam_template_path(code, name):
            result.append(pooja)
    return result


def _get_sankalpam_template_path(language_code: str, pooja_name: Optional[str] = None, prefer_python: bool = True) -> Optional[Path]:
    """
    Resolve path to sankalpam template under backend/templates/{language}/.
    For Telugu + Ganesh Pooja: prefer full Ganesha_Sankalpam_template_telugu.py (play full sankalpam on Pooja page).
    Else use Ganesh_Pooja_template_telugu.txt/.py; for other poojas use pooja-specific or generic.
    If prefer_python=True, checks for .py files first, then .txt.
    """
    folder_name = _LANGUAGE_CODE_TO_FOLDER.get((language_code or "").strip().lower())
    if not folder_name:
        return None
    lang_dir = TEMPLATES_BASE_DIR / folder_name
    if not lang_dir.exists():
        return None
    # Pooja-specific: for Telugu Ganesh Pooja use full Ganesha Sankalpam template first (full mantras + variables)
    if pooja_name and pooja_name.strip():
        normalized = pooja_name.strip().replace(" ", "_").lower()
        if (language_code or "").strip().lower() == "te" and normalized in _POOJA_TO_TELUGU_TEMPLATE:
            # Full sankalpam file (all mantras, aachamana, sankalpam paragraph, etc.)
            full_sankalpam_py = lang_dir / "Ganesha_Sankalpam_template_telugu.py"
            if full_sankalpam_py.exists():
                return full_sankalpam_py
            safe_name = "Ganesh_Pooja"
        else:
            safe_name = pooja_name.strip().replace(" ", "_")
        # Try Python first if preferred
        if prefer_python:
            pooja_file_py = lang_dir / f"{safe_name}_template_{folder_name}.py"
            if pooja_file_py.exists():
                return pooja_file_py
        pooja_file_txt = lang_dir / f"{safe_name}_template_{folder_name}.txt"
        if pooja_file_txt.exists():
            return pooja_file_txt
        # If prefer_python and .py not found, don't return .txt yet (will try generic)
        if prefer_python:
            pass
    # Generic fallback
    if prefer_python:
        generic_file_py = lang_dir / f"sankalpam_template_{folder_name}.py"
        if generic_file_py.exists():
            return generic_file_py
    generic_file_txt = lang_dir / f"sankalpam_template_{folder_name}.txt"
    return generic_file_txt if generic_file_txt.exists() else None


async def _load_python_template(language_code: str, pooja_name: Optional[str] = None, data: Optional[dict] = None) -> Optional[str]:
    """
    Load and execute Python template if available. Returns generated text or None.
    """
    # Check for Python template file
    path = _get_sankalpam_template_path(language_code, pooja_name, prefer_python=True)
    if not path or not path.suffix == ".py":
        return None
    
    try:
        import importlib.util
        import sys
        from pathlib import Path
        
        # Ensure backend directory is in sys.path for app imports
        backend_dir = path.parent.parent.parent
        if str(backend_dir) not in sys.path:
            sys.path.insert(0, str(backend_dir))
        
        # Generate unique module name to avoid conflicts
        module_name = f"template_{language_code}_{pooja_name or 'generic'}_{id(path)}"
        module_name = module_name.replace("-", "_").replace(" ", "_")
        
        # Load the Python module
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Call generate_sankalpam_text if it exists
        if hasattr(module, "generate_sankalpam_text") and data:
            if callable(module.generate_sankalpam_text):
                result = await module.generate_sankalpam_text(data)
                return result if result else None
    except Exception as e:
        print(f"[Template] Error loading Python template {path}: {e}")
        import traceback
        traceback.print_exc()
    
    return None


def _load_sankalpam_template(language_code: str, pooja_name: Optional[str] = None) -> str:
    """
    Load sankalpam template for the given language (and optional pooja).
    For Telugu + Ganesh Pooja, tries explicit path first so file is always found when present.
    Note: Python templates (.py) are handled separately via _load_python_template.
    """
    # Telugu + Ganesh Pooja: try explicit paths first (ensures we load the file when it exists)
    if (language_code or "").strip().lower() == "te" and pooja_name and pooja_name.strip():
        normalized = pooja_name.strip().replace(" ", "_").lower()
        if normalized in _POOJA_TO_TELUGU_TEMPLATE:
            # Try Python first
            py_path = _BACKEND_DIR / "templates" / "telugu" / "Ganesh_Pooja_template_telugu.py"
            if py_path.exists():
                return ""  # Python templates handled separately
            # Then try text files
            for p in _GANESH_POOJA_TELUGU_PATHS:
                if p.exists():
                    try:
                        return p.read_text(encoding="utf-8")
                    except Exception:
                        continue
    path = _get_sankalpam_template_path(language_code, pooja_name, prefer_python=False)
    if path and path.suffix == ".txt":
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            pass
    # Try alternate base (e.g. cwd): for Telugu Ganesh Pooja try Ganesh_Pooja_template_telugu.txt first
    folder = _LANGUAGE_CODE_TO_FOLDER.get((language_code or "").strip().lower()) or "telugu"
    alt_dir = Path.cwd() / "templates" / folder
    if (language_code or "").strip().lower() == "te" and pooja_name and pooja_name.strip():
        normalized = pooja_name.strip().replace(" ", "_").lower()
        if normalized in _POOJA_TO_TELUGU_TEMPLATE:
            path2 = alt_dir / "Ganesh_Pooja_template_telugu.txt"
            if path2.exists():
                try:
                    return path2.read_text(encoding="utf-8")
                except Exception:
                    pass
    path2 = alt_dir / f"sankalpam_template_{folder}.txt"
    if path2.exists():
        try:
            return path2.read_text(encoding="utf-8")
        except Exception:
            pass
    # Telugu inline fallback so we never return Sanskrit for Telugu requests
    if (language_code or "").strip().lower() == "te":
        return _TELUGU_TEMPLATE_INLINE
    return ""


def _is_sanskrit_or_hindi(text: str) -> bool:
    """True if text is in Sanskrit or Hindi (Devanagari script). User who chose Telugu must not get this."""
    if not (text and isinstance(text, str)):
        return False
    # Devanagari Unicode block (used for both Sanskrit and Hindi)
    if any("\u0900" <= c <= "\u097f" for c in text):
        return True
    # Common Sanskrit/Hindi markers
    if "ॐ" in text or "विष्णु" in text or "[पूजा का नाम यहाँ]" in text:
        return True
    return False


async def _ensure_telugu_for_user(
    text: str,
    sankalpam_data: dict,
    pooja_name: Optional[str],
    effective_code: str = "sa",
) -> str:
    """If user selected Telugu and text is Sanskrit/Hindi, return Telugu instead."""
    if effective_code != "te":
        return text
    if _is_sanskrit_or_hindi(text):
        return await _generate_telugu_sankalpam(sankalpam_data, pooja_name)
    return text


def _telugu_geographical_reference_from_country(location_country: Optional[str]) -> str:
    """Return Telugu geographical reference phrase based on current location country (for {{geographical_reference}})."""
    if not location_country or not location_country.strip():
        return "భారతవర్షే భరతఖండే జంబూద్వీపే"
    country_lower = location_country.strip().lower()
    if "india" in country_lower or "bharat" in country_lower:
        return "జంబూద్వీపే భారతవర్షే భారతఖండే"
    if "nepal" in country_lower:
        return "జంబూద్వీపే నేపాలవర్షే"
    if "sri lanka" in country_lower or "ceylon" in country_lower:
        return "లంకాద్వీపే"
    if "united states" in country_lower or "usa" in country_lower or "america" in country_lower:
        return "అమెరికా దేశే"
    return f"{location_country.strip()} దేశే"


# English geographical fallbacks -> Telugu (so Telugu template never shows "sacred tIrtha" etc.)
_TE_GEO_FALLBACKS = {
    "sacred tirtha": "పవిత్ర తీర్థం",
    "sacred river": "పవిత్ర నదీ తటం",
    "sacred place": "పవిత్ర స్థలం",
}


def _telugu_geographical_feature_from_data(data: dict) -> str:
    """Build Telugu geographical feature phrase from location-based data (for {{geographical_feature}})."""
    primary = (data.get("primary_geographical_feature") or "").strip()
    if primary:
        # Translate known English fallbacks to Telugu
        low = primary.lower()
        if low in _TE_GEO_FALLBACKS:
            return _TE_GEO_FALLBACKS[low]
        return primary
    # Build from nearby features (priority: ocean > sea > river > mountain), with Telugu suffixes
    ocean = data.get("nearby_ocean") or ""
    sea = data.get("nearby_sea") or ""
    river = data.get("nearby_river") or ""
    mountain = data.get("nearby_mountain") or ""
    if ocean and str(ocean).strip():
        return f"{str(ocean).strip()} సముద్ర తీరే"
    if sea and str(sea).strip():
        return f"{str(sea).strip()} సముద్ర తీరే"
    if river and str(river).strip():
        return f"{str(river).strip()} నదీ తటే"
    if mountain and str(mountain).strip():
        return f"{str(mountain).strip()} పర్వత పార్శ్వే"
    return (data.get("nearby_river") or "గంగా") + " నదీ తటే"


async def _generate_telugu_sankalpam(data: dict, pooja_name: Optional[str] = None) -> str:
    """
    Fill the Telugu sankalpam template from templates/telugu/ (pooja-specific or generic) with data.
    Prefers Python templates (.py) which call Divine API directly; falls back to text templates (.txt).
    Never returns Sanskrit: if file is missing, uses inline Telugu template.
    {{geographical_reference}}, {{current_location}}, {{geographical_feature}} come from current location / geo data.
    """
    # Try Python template first (calls Divine API for panchang variables)
    python_result = await _load_python_template("te", pooja_name, data)
    if python_result:
        return python_result
    
    # Fall back to text template with variable replacement
    template = _load_sankalpam_template("te", pooja_name)
    if not template:
        template = _TELUGU_TEMPLATE_INLINE

    # Map data to template variables; convert all English calendar/panchang terms to Telugu
    geographical_reference = _telugu_geographical_reference_from_country(data.get("location_country"))
    current_location = data.get("current_location") or ""
    primary_geo = _telugu_geographical_feature_from_data(data)
    now = datetime.now()
    # Ritu (season) in Telugu from month
    rithou_te = _TE_RITU.get(now.month, "")
    # Month and weekday in Telugu
    month_en = data.get("month_name") or ""
    month_te = _english_to_telugu(month_en, _TE_MONTHS) or month_en
    weekday_en = data.get("weekday_name") or ""
    vasara_te = _english_to_telugu(weekday_en, _TE_WEEKDAYS) or weekday_en
    # Paksha and tithi in Telugu (పక్షే = paksha only, తిథౌ = tithi only)
    tithi_raw = (data.get("tithi") or "").strip()
    tithi_parts = tithi_raw.split(maxsplit=1) if tithi_raw else []
    paksha_en = data.get("paksha") or ""
    if not paksha_en and len(tithi_parts) > 1:
        paksha_en = tithi_parts[0]
    paksha_te = _english_to_telugu(paksha_en, _TE_PAKSHA) or paksha_en
    # {{thithou}} = tithi part only (e.g. Ekadashi -> ఏకాదశి), not "Krishna Ekadashi"
    tithi_only = tithi_parts[1] if len(tithi_parts) > 1 else (tithi_parts[0] if tithi_parts else "")
    thithou_te = _tithi_to_telugu(tithi_only) if tithi_only else _tithi_to_telugu(tithi_raw)
    nakshatra_te = _nakshatra_to_telugu(data.get("nakshatra") or "")
    yoga_te = _english_to_telugu((data.get("yoga") or "").strip(), _TE_YOGA) or (data.get("yoga") or "")
    karana_te = _english_to_telugu((data.get("karana") or "").strip(), _TE_KARANA) or (data.get("karana") or "")
    # "Uttarayane" / "Dakshinayane" in Telugu (single phrase, not "Uttarayanam Ayane")
    ayanam = "ఉత్తరాయణే" if 1 <= now.month <= 6 else "దక్షిణాయణే"
    # Pooja name in Telugu
    pooja_display = (pooja_name or "").strip()
    pooja_te = _english_to_telugu(pooja_display, _TE_POOJA_NAMES) or pooja_display

    family_lines = []
    for m in data.get("family_members", []):
        family_lines.append(f"- {m.get('name', '')} ({m.get('relation', '')})")
    family_members = "\n".join(family_lines) if family_lines else ""

    birth_date_str = ""
    if data.get("birth_date"):
        birth_date_str = data["birth_date"] if isinstance(data["birth_date"], str) else str(data["birth_date"])

    # Birth nakshatra/rashi in Telugu if present
    birth_nak_te = _nakshatra_to_telugu(data.get("birth_nakshatra") or "") or (data.get("birth_nakshatra") or "")
    birth_rashi_en = (data.get("birth_rashi") or "").strip()
    birth_rashi_te = _english_to_telugu(birth_rashi_en, _TE_RASHI) or birth_rashi_en

    replacements = {
        "{{samvathsarE}}": str(data.get("current_year", "")),
        "{{geographical_reference}}": geographical_reference,
        "{{current_location}}": current_location,
        "{{geographical_feature}}": primary_geo,
        "{{rithou}}": rithou_te,
        "{{mAsE}}": month_te,
        "{{pakshE}}": paksha_te,
        "{{thithou}}": thithou_te,
        "{{vAsara}}": vasara_te,
        "{{nakshatra}}": nakshatra_te,
        "{{yoga}}": yoga_te,
        "{{karaNa}}": karana_te,
        "{{ayanam}}": ayanam,
        "{{user_name}}": data.get("user_name", ""),
        "{{gotram}}": data.get("gotram", ""),
        "{{birth_nakshatra}}": birth_nak_te,
        "{{birth_rashi}}": birth_rashi_te,
        "{{birth_place}}": data.get("birth_place", ""),
        "{{birth_time}}": data.get("birth_time", ""),
        "{{birth_city}}": data.get("birth_city", ""),
        "{{birth_state}}": data.get("birth_state", ""),
        "{{birth_country}}": data.get("birth_country", ""),
        "{{birth_date}}": birth_date_str,
        "{{family_members}}": family_members,
        "{{pooja_name}}": pooja_te,
    }
    out = template
    for k, v in replacements.items():
        out = out.replace(k, str(v))
    return out.strip()


_VARA_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# IST offset used as the canonical reference for all Indian panchang
# (Krishnamurti Paddhati and all South-Indian / Telugu panchangam books are published in IST)
_IST_OFFSET = 5.5


def _estimate_timezone_offset(country: str, state: str) -> float:
    """Estimate UTC offset in hours from country/state for historical panchang lookups."""
    co = (country or "").strip().lower()
    if "india" in co or "bharat" in co:
        return 5.5
    if "nepal" in co:
        return 5.75
    if "sri lanka" in co:
        return 5.5
    if "united states" in co or "usa" in co or co == "us":
        return _us_state_timezone_offset(state)
    if "united kingdom" in co or co in ("uk", "gb", "great britain"):
        return 0.0
    if "australia" in co:
        s = (state or "").strip().upper()
        if s in ("NSW", "VIC", "QLD", "TAS", "ACT"):
            return 10.0
        if s in ("SA", "NT"):
            return 9.5
        return 8.0
    if "germany" in co or "france" in co or "italy" in co or "spain" in co or "europe" in co:
        return 1.0
    if "singapore" in co or "malaysia" in co:
        return 8.0
    if "china" in co:
        return 8.0
    if "japan" in co:
        return 9.0
    if "canada" in co:
        return _us_state_timezone_offset(state)   # rough match for provinces
    return 0.0


_TITHI_NAMES_LIST = [
    "Prathama", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Purnima",
]


def _compute_tithi_ephem(dt) -> tuple:
    """
    Compute Hindu Tithi and Paksha for a given datetime (naive, treated as IST)
    using the pyephem library.  Returns (tithi_name, paksha) e.g. ("Ekadashi", "Krishna").
    Falls back to ("", "") if ephem is not installed.
    The 15th Krishna tithi is correctly labelled "Amavasya".
    """
    try:
        import ephem, math
        from datetime import timedelta

        # Convert IST to UTC for ephem
        utc_dt = dt - timedelta(hours=5.5)
        moon = ephem.Moon()
        sun  = ephem.Sun()
        obs  = ephem.Observer()
        obs.date = utc_dt.strftime("%Y/%m/%d %H:%M:%S")
        moon.compute(obs)
        sun.compute(obs)
        elong   = (math.degrees(moon.hlong) - math.degrees(sun.hlong)) % 360
        n       = int(elong / 12)          # 0 – 29
        paksha  = "Shukla" if n < 15 else "Krishna"
        idx     = n % 15                   # 0 – 14
        if paksha == "Krishna" and idx == 14:
            tithi_name = "Amavasya"
        elif paksha == "Shukla" and idx == 14:
            tithi_name = "Purnima"
        else:
            tithi_name = _TITHI_NAMES_LIST[idx]
        return tithi_name, paksha
    except Exception:
        return "", ""


async def fetch_death_panchang(
    date_of_death,            # datetime.date or datetime.datetime
    death_city: str,
    death_state: str,
    death_country: str,
    time_of_death: Optional[str] = None,  # "HH:MM" 24hr local time at place of death
) -> Optional[dict]:
    """
    Fetch the Hindu panchang for the day of death using the Krishnamurti Paddhati
    standard followed in Telangana / South India.

    Key rule: all South-Indian panchangam books (including Krishnamurti Paddhati)
    are published in IST (+5:30).  If the death occurred outside India, the local
    death date+time is first converted to IST, and the panchang is looked up for
    that IST moment — ensuring the nakshatra/tithi/vara match what the family's
    local panchangam would show.

    Vara (weekday) is always derived from the IST date for reliability.
    """
    if date_of_death is None:
        return None

    from datetime import datetime as _dt, date as _date, timedelta as _td

    # Build a naive datetime from whatever was stored
    if isinstance(date_of_death, _date) and not isinstance(date_of_death, _dt):
        hour, minute = 0, 0
        if time_of_death:
            try:
                parts = time_of_death.split(":")
                hour, minute = int(parts[0]), int(parts[1])
            except Exception:
                pass
        death_dt_local = _dt(date_of_death.year, date_of_death.month, date_of_death.day, hour, minute)
    else:
        # Strip timezone info so arithmetic is straightforward
        death_dt_local = date_of_death.replace(tzinfo=None) if getattr(date_of_death, "tzinfo", None) else date_of_death

    # ── Convert local death time → IST (Krishnamurti Paddhati / Telugu panchangam reference) ──
    local_tz_offset = _estimate_timezone_offset(death_country, death_state)
    # Shift: IST = local + (IST_OFFSET − local_offset) hours
    ist_dt = death_dt_local + _td(hours=(_IST_OFFSET - local_tz_offset))

    print(
        f"[DeathPanchang] Local: {death_dt_local} ({local_tz_offset:+.1f}h) "
        f"-> IST: {ist_dt}  (Krishnamurti Paddhati / Telugu panchangam reference)"
    )

    # Vara is determined from the IST date (what day it was in India / Telangana panchangam)
    vara = _VARA_NAMES[ist_dt.weekday()]

    # Resolve coordinates for the death location (needed for accurate sunrise/Moon position)
    lat, lon = await _resolve_coords_for_panchang(death_city, death_state, death_country)

    # Always pass IST offset (+5.5) to the panchang API — this matches the Telangana panchangam
    panchang = await _fetch_panchang_for_today(
        now=ist_dt,
        location_city=death_city or "",
        location_state=death_state or "",
        location_country=death_country or "",
        latitude=lat,
        longitude=lon,
        timezone_offset_hours=_IST_OFFSET,   # ← Krishnamurti Paddhati / IST always
        language="en",
    )

    # Augment with ephem-based tithi/paksha when API leaves them blank (common for historical dates)
    tithi_str, paksha_str = _compute_tithi_ephem(ist_dt)

    if panchang:
        return {
            "tithi":     panchang.get("tithi")     or tithi_str,
            "paksha":    panchang.get("paksha")    or paksha_str,
            "nakshatra": panchang.get("nakshatra") or "",
            "yoga":      panchang.get("yoga")      or "",
            "karana":    panchang.get("karana")    or "",
            "vara":      vara,
        }

    # Divine API unavailable: use ephem for tithi, approximate fallback for rest
    fallback = _fallback_panchang_for_today(ist_dt)
    return {
        "tithi":     tithi_str  or fallback.get("tithi")     or "",
        "paksha":    paksha_str or fallback.get("paksha")    or "",
        "nakshatra": fallback.get("nakshatra") or "",
        "yoga":      fallback.get("yoga")      or "",
        "karana":    fallback.get("karana")    or "",
        "vara":      vara,
    }


async def generate_sankalpam(
    user: User,
    family_members: List[FamilyMember],
    location_city: str,
    location_state: str,
    location_country: str,
    nearby_river: str,
    language: str = "sanskrit",
    language_code: Optional[str] = None,
    pooja_name: Optional[str] = None,
    nearby_mountain: Optional[str] = None,
    nearby_sea: Optional[str] = None,
    nearby_ocean: Optional[str] = None,
    primary_geographical_feature: Optional[str] = None,
    latitude: Optional[str] = None,
    longitude: Optional[str] = None,
    timezone_offset_hours: Optional[float] = None,
    force_telugu: bool = False,
) -> str:
    """
    Generate sankalpam using DivineAPI or generate a standard template.
    For Telugu (code 'te'), uses backend/templates/telugu/ or sample_sankalpam_template_telugu.txt.
    Language is determined by language_code, language param, then user.preferred_language (no hardcoded identities).
    """
    # Respect explicit request language (e.g. from pooja page dropdown); only fall back to user profile when none given
    explicit_code = (language_code or "").strip().lower() or (language and _language_to_iso(language))
    if explicit_code:
        effective_code = _language_to_iso(explicit_code) or "sa"
    else:
        effective_code = "sa"
        try:
            pref = getattr(user, "preferred_language", None)
            if pref is not None:
                effective_code = _language_to_iso(pref)
            if effective_code == "sa" and (language or "").strip():
                effective_code = _language_to_iso(language)
        except Exception:
            pass

    # Prepare sankalpam data (use effective code so downstream never sees wrong language)
    now = datetime.now().astimezone()
    current_date_str = now.strftime("%Y-%m-%d")
    current_year = now.year
    client_sent_timezone = timezone_offset_hours is not None
    server_tz = (now.utcoffset().total_seconds() / 3600.0) if now.utcoffset() else 0.0
    if timezone_offset_hours is None:
        timezone_offset_hours = server_tz
    # Resolve lat/lon when missing so Divine API returns correct Panchang for the place
    panchang_lat = latitude
    panchang_lon = longitude
    if not panchang_lat or not panchang_lon or (str(panchang_lat).strip() == "0" and str(panchang_lon).strip() == "0"):
        panchang_lat, panchang_lon = await _resolve_coords_for_panchang(location_city, location_state, location_country)
    # Timezone for Panchang: prefer request (browser); else server; for US when client didn't send TZ, estimate by state
    tz_for_panchang = timezone_offset_hours if client_sent_timezone else server_tz
    if not client_sent_timezone and _is_us_location(location_country):
        tz_for_panchang = _us_state_timezone_offset(location_state)
    # Base sankalpam data (user + location)
    sankalpam_data = {
        "user_name": f"{user.first_name} {user.last_name}",
        "gotram": user.gotram,
        "birth_place": f"{user.birth_city}, {user.birth_state}, {user.birth_country}",
        "birth_time": user.birth_time,
        "birth_date": user.birth_date.strftime("%Y-%m-%d"),
        "birth_city": user.birth_city,
        "birth_state": user.birth_state,
        "birth_country": user.birth_country,
        "birth_nakshatra": getattr(user, "birth_nakshatra", None) or "",
        "birth_rashi": getattr(user, "birth_rashi", None) or "",
        # Current date/time for DivineAPI to compute tithi/nakshatra/etc
        "current_date": current_date_str,
        "current_year": current_year,
        "current_location": f"{location_city}, {location_state}, {location_country}",
        "location_city": location_city,
        "location_state": location_state,
        "location_country": location_country,
        "nearby_river": nearby_river,
        "nearby_mountain": nearby_mountain,
        "nearby_sea": nearby_sea,
        "nearby_ocean": nearby_ocean,
        "primary_geographical_feature": primary_geographical_feature,
        "timezone_offset_hours": timezone_offset_hours,
        "latitude": panchang_lat,
        "longitude": panchang_lon,
        "language": language,
        "family_members": [
            {
                "name": member.name,
                "relation": member.relation,
                "gotram": user.gotram  # Usually same gotram
            }
            for member in family_members
        ]
    }
    # When output language is Telugu, show names, relations, and locations in Telugu (no English)
    if effective_code == "te":
        from app.services.translation_service import translate_location
        sankalpam_data["user_name"] = _latin_name_to_telugu(sankalpam_data["user_name"])
        sankalpam_data["gotram"] = _latin_name_to_telugu(sankalpam_data["gotram"])
        for m in sankalpam_data["family_members"]:
            m["name"] = _latin_name_to_telugu(m.get("name") or "")
            rel = (m.get("relation") or "").strip()
            m["relation"] = _english_to_telugu(rel, _TE_RELATION) if rel else ""
        # Current location: translate known names (e.g. United States, Texas) to Telugu; transliterate rest
        loc_te = translate_location(
            city=location_city, state=location_state, country=location_country, language="telugu"
        )
        def _place_to_telugu(raw: str, translated: str) -> str:
            if not raw or not raw.strip():
                return raw or ""
            # Use translated only if it actually changed (known place); else transliterate to Telugu script
            if translated and translated.strip() and translated.strip() != raw.strip():
                return translated.strip()
            return _latin_name_to_telugu(raw)
        sankalpam_data["location_city"] = _place_to_telugu(location_city, loc_te.get("city", ""))
        sankalpam_data["location_state"] = _place_to_telugu(location_state, loc_te.get("state", ""))
        sankalpam_data["location_country"] = _place_to_telugu(location_country, loc_te.get("country", ""))
        sankalpam_data["current_location"] = ", ".join(
            filter(None, [
                sankalpam_data["location_city"],
                sankalpam_data["location_state"],
                sankalpam_data["location_country"],
            ])
        )
        # Birth place: same treatment
        birth_loc_te = translate_location(
            city=user.birth_city, state=user.birth_state, country=user.birth_country, language="telugu"
        )
        sankalpam_data["birth_city"] = _place_to_telugu(user.birth_city, birth_loc_te.get("city", ""))
        sankalpam_data["birth_state"] = _place_to_telugu(user.birth_state, birth_loc_te.get("state", ""))
        sankalpam_data["birth_country"] = _place_to_telugu(user.birth_country, birth_loc_te.get("country", ""))
        sankalpam_data["birth_place"] = ", ".join(
            filter(None, [
                sankalpam_data["birth_city"],
                sankalpam_data["birth_state"],
                sankalpam_data["birth_country"],
            ])
        )
        # Birth nakshatra and rashi in Telugu script (so Python and text templates both get Telugu)
        sankalpam_data["birth_nakshatra"] = _nakshatra_to_telugu(sankalpam_data.get("birth_nakshatra") or "") or (sankalpam_data.get("birth_nakshatra") or "")
        birth_rashi_en = (sankalpam_data.get("birth_rashi") or "").strip()
        sankalpam_data["birth_rashi"] = _english_to_telugu(birth_rashi_en, _TE_RASHI) or birth_rashi_en
    # Include pooja_name for templates that need it
    if pooja_name:
        sankalpam_data["pooja_name"] = pooja_name
    # Try to enrich with Panchang data first (tithi, nakshatra, yoga, karana)
    panchang_info = await _fetch_panchang_for_today(
        now=now,
        location_city=location_city,
        location_state=location_state,
        location_country=location_country,
        latitude=panchang_lat,
        longitude=panchang_lon,
        timezone_offset_hours=tz_for_panchang,
        language=language,
    )

    if panchang_info:
        sankalpam_data.update(
            {
                "tithi": panchang_info.get("tithi") or "",
                "paksha": panchang_info.get("paksha") or "",
                "nakshatra": panchang_info.get("nakshatra") or "",
                "yoga": panchang_info.get("yoga") or "",
                "karana": panchang_info.get("karana") or "",
            }
        )
    else:
        # Divine API not configured or failed: use date-based fallback so పక్షే, తిథౌ, నక్షత్రే, యోగే, కరణే are never empty
        fallback = _fallback_panchang_for_today(now)
        sankalpam_data.update(
            {
                "tithi": fallback.get("tithi", ""),
                "paksha": fallback.get("paksha", ""),
                "nakshatra": fallback.get("nakshatra", ""),
                "yoga": fallback.get("yoga", ""),
                "karana": fallback.get("karana", ""),
            }
        )
        print("[Panchang] Using fallback (approximate) panchang data for today.")

    # Month: use DivineAPI Chandramasa (Indian lunar month) in the selected language when available
    sankalpam_data["month_name"] = now.strftime("%B")  # Gregorian fallback
    if effective_code:
        place = f"{location_city}, {location_state}, {location_country}".strip(", ")
        lunar_month = await _fetch_chandramasa_for_today(
            now=now,
            place=place or "Unknown",
            latitude=latitude,
            longitude=longitude,
            timezone_offset_hours=timezone_offset_hours,
            lan=effective_code,
        )
        if lunar_month:
            sankalpam_data["month_name"] = lunar_month
    # Weekday: keep Gregorian for now (template can convert to local script if needed)
    sankalpam_data["weekday_name"] = now.strftime("%A")
    # Store effective language code so downstream never overrides with default
    sankalpam_data["language"] = effective_code if effective_code in ("te", "hi", "sa", "ta", "kn", "ml", "en", "mr", "gu", "bn", "or", "pa") else language
    sankalpam_data["language_code"] = effective_code

    # Final safeguard: if router sent Telugu, never return Sanskrit
    if (language_code or "").strip().lower() == "te" or (language or "").strip().lower() == "telugu":
        effective_code = "te"

    # Router can force Telugu (for any user) so we never hit Divine API or Sanskrit path
    if force_telugu:
        sankalpam_data["language_code"] = "te"
        sankalpam_data["language"] = "telugu"
        telugu_text = await _generate_telugu_sankalpam(sankalpam_data, pooja_name)
        return await _ensure_telugu_for_user(telugu_text, sankalpam_data, pooja_name, "te")

    # Telugu (code 'te'): use our template only; do not call Divine API (it may return Sanskrit)
    if effective_code == "te":
        telugu_text = await _generate_telugu_sankalpam(sankalpam_data, pooja_name)
        return await _ensure_telugu_for_user(telugu_text, sankalpam_data, pooja_name, "te")

    # Hindi / Sanskrit: use Python templates under templates/hindi/ and templates/sanskrit/ when available
    if effective_code in ("hi", "sa"):
        python_text = await _load_python_template(effective_code, pooja_name, sankalpam_data)
        if python_text and python_text.strip():
            return await _ensure_telugu_for_user(python_text, sankalpam_data, pooja_name, effective_code)

    # Optional: DivineAPI Sankalpam "generate" endpoint. Not required for app to work.
    # DivineAPI provides Panchang (tithi/nakshatra etc.) but may not expose sankalpam/generate;
    # if the call fails or endpoint is missing, we fall back to local templates (Sanskrit/Telugu/etc).
    if settings.divineapi_key:
        try:
            async with httpx.AsyncClient() as client:
                url = f"{settings.divineapi_base_url}/v1/sankalpam/generate"
                headers = {
                    "Authorization": f"Bearer {settings.divineapi_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.post(url, json=sankalpam_data, headers=headers, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    api_text = data.get("sankalpam_text") or ""
                    if api_text:
                        return await _ensure_telugu_for_user(api_text, sankalpam_data, pooja_name, effective_code)
                    result = await generate_standard_sankalpam(sankalpam_data)
                    return await _ensure_telugu_for_user(result, sankalpam_data, pooja_name, effective_code)
                else:
                    print(f"DivineAPI error: {response.status_code} - {response.text}")
                    # Fall back to standard template
        except Exception as e:
            print(f"Error calling DivineAPI: {e}")
            # Fall back to standard template

    # Generate standard sankalpam template; verify we don't return Sanskrit to Telugu user
    result = await generate_standard_sankalpam(sankalpam_data)
    return await _ensure_telugu_for_user(result, sankalpam_data, pooja_name, effective_code)

# Language code -> display name for "not available" messages
_LANGUAGE_CODE_TO_NAME = {
    "ta": "Tamil", "te": "Telugu", "hi": "Hindi", "sa": "Sanskrit",
    "kn": "Kannada", "ml": "Malayalam", "en": "English", "mr": "Marathi",
    "gu": "Gujarati", "bn": "Bengali", "or": "Oriya", "pa": "Punjabi",
}


async def generate_standard_sankalpam(data: dict) -> str:
    """
    Generate a standard sankalpam text with all the provided information.
    Uses language_code or language from data (no default override).
    Never returns Sanskrit when user chose another language (e.g. Tamil).
    """
    # Prefer explicit language_code so user selection is never overridden
    code = str(data.get("language_code") or data.get("language") or "").strip().lower()
    if code in ("te", "telugu") or _language_to_iso(code) == "te":
        return await _generate_telugu_sankalpam(data, data.get("pooja_name"))

    # Only Hindi uses the inline Devanagari template. Sanskrit (sa) and all others need a template file.
    if code not in ("hi", "hindi"):
        lang_name = _LANGUAGE_CODE_TO_NAME.get(code) or code
        return (
            f"Sankalpam in {lang_name} is not available in this version. "
            f"Add a template file under backend/templates/ for the selected language (e.g. backend/templates/sanskrit/)."
        )

    # Standard sankalpam template (Devanagari / Hindi)
    # Decide primary geographical phrase
    primary_geo = data.get("primary_geographical_feature")
    if not primary_geo:
        # Fallback to river-based phrase
        river_name = data.get("nearby_river") or "Ganga"
        primary_geo = f"{river_name} नदी तटे"

    # Use current date (not birth date) for the "today" / Panchang lines
    current_year = data.get("current_year")
    month_name = data.get("month_name")
    tithi = data.get("tithi")
    nakshatra = data.get("nakshatra")
    yoga = data.get("yoga")
    karana = data.get("karana")
    weekday = data.get("weekday_name")

    sankalpam = f"""
श्री गणेशाय नमः

ॐ विष्णुर्विष्णुर्विष्णुः

अद्य श्रीमद्भगवतो महापुरुषस्य विष्णोराज्ञया प्रवर्तमानस्य
अद्य ब्रह्मणो द्वितीयपरार्धे श्री श्वेतवाराहकल्पे
वैवस्वतमन्वन्तरे अष्टाविंशतितमे कलियुगे
प्रथमचरणे

भारतवर्षे भरतखण्डे जम्बूद्वीपे
{data['current_location']} नगरे
{primary_geo}

    अस्मिन् वर्तमाने व्यावहारिके
{current_year} सम्वत्सरे
{month_name or ''} मासे
{tithi or ''} तिथौ
{weekday or ''} वासरे
{nakshatra or ''} नक्षत्रे
{yoga or ''} योगे
{karana or ''} करणे

शुभे मुहूर्ते
अहं {data['user_name']}
गोत्र {data['gotram']}
शर्मा/वर्मा/दास/देव (अपना उपनाम)
जन्मस्थान: {data['birth_place']}
जन्मसमय: {data['birth_time']}

मम पारिवारिक सदस्याः:
"""
    
    for member in data.get('family_members', []):
        sankalpam += f"- {member['name']} ({member['relation']})\n"
    
    sankalpam += f"""
इत्यादि सकलपापक्षयपूर्वकं
अखण्डमण्डलाकारं व्याप्तं येन चराचरं
तत्परमेश्वरं प्रणम्य

अस्यां शुभतिथौ
[पूजा का नाम यहाँ]
पूजनं करिष्यामि

तत्सिद्धयर्थं
संकल्पं करोमि ॥
"""
    
    return sankalpam.strip()

