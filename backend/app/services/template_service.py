"""
Service to replace template variables with actual data from database and external sources
"""
from typing import Dict, Optional
from datetime import datetime, time
from app.models import User, FamilyMember, Language
from app.services.astronomical_service import get_astronomical_data
from app.services.location_service import get_nearby_geographical_features
import re


def template_is_telugu(template_language: Optional[str]) -> bool:
    """True when the sankalpam template language is Telugu (DB enum or ISO)."""
    tl = (template_language or "").strip().lower()
    if tl.startswith("language."):
        tl = tl.split(".")[-1]
    return tl in ("te", "telugu") or "telugu" in tl


def is_telugu_template_language(
    template_language: Optional[str],
    language_enum: Optional[Language] = None,
) -> bool:
    """
    Telugu template detection: prefer DB enum (handles str vs Enum from SQLAlchemy),
    then string codes, then template text is not needed here.
    """
    if language_enum is not None:
        if isinstance(language_enum, Language):
            if language_enum == Language.TELUGU:
                return True
        else:
            ev = str(language_enum).strip().lower()
            if ev == Language.TELUGU.value or ev.endswith("telugu"):
                return True
    return template_is_telugu(template_language)


# Zero-width / invisible chars inside pasted {{placeholders}} break dict lookup
_PLACEHOLDER_INNER_NORM = re.compile(r"[\u200b-\u200d\ufeff\u2060]+")


def replace_variables(text: str, variables: Dict[str, str]) -> str:
    """
    Replace every {{name}} in the template; missing keys substitute to empty string.
    """

    def _repl(m: re.Match) -> str:
        inner = _PLACEHOLDER_INNER_NORM.sub("", (m.group(1) or "")).strip()
        return str(variables.get(inner, ""))

    return re.sub(r"\{\{([^}]+)\}\}", _repl, text)

def identify_variables(text: str) -> list[str]:
    """
    Identify variables in the text.
    Variables should be in the format {{variable_name}} or {{variable.name}}.
    Returns a list of unique variable names found.
    """
    # Pattern to match {{variable_name}} or {{variable.name}}
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, text)
    
    # Remove duplicates and return unique variable names
    unique_variables = list(set(matches))
    return sorted(unique_variables)

async def get_all_variables(
    user: User,
    family_members: list[FamilyMember],
    location_city: str,
    location_state: str,
    location_country: str,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    date: Optional[datetime] = None,
    pooja_name: Optional[str] = None,
    template_language: str = "sanskrit",
    template_language_enum: Optional[Language] = None,
    override_gotram: Optional[str] = None,
    override_birth_nakshatra: Optional[str] = None,
    override_birth_rashi: Optional[str] = None,
    sankalpa_intent: Optional[str] = None,
    output_telugu_preference: Optional[bool] = None,
) -> Dict[str, str]:
    """
    Gather all variables needed for Sankalpam template replacement.
    Returns a dictionary mapping variable names to their values.
    
    Supported variables:
    - User variables: {{user_name}}, {{gotram}}, {{birth_place}}, {{birth_time}}, etc.
    - Astronomical variables: {{samvathsarE}}, {{ayanam}}, {{rithou}}, {{mAsE}}, {{thithou}}, {{vAsara}}, {{nakshatra}}, etc.
    - Location variables: {{current_location}}, {{nearby_river}}, {{nearby_mountain}}, {{nearby_sea}}, {{geographical_feature}}
    - Family variables: {{family_members}}
    - Pooja variables: {{pooja_name}}
    """
    
    if date is None:
        date = datetime.now()
    
    variables: Dict[str, str] = {}
    
    # User variables — prefer DB Language enum so SQLAlchemy str/enum quirks do not skip Telugu path
    is_telugu = is_telugu_template_language(template_language, template_language_enum)
    astro_lang = "telugu" if is_telugu else (template_language or "sanskrit")
    if is_telugu:
        from app.services.divineapi_service import (
            _latin_name_to_telugu,
            _english_to_telugu,
            _TE_RELATION as _TE_REL,
            _TE_POOJA_NAMES,
            _nakshatra_to_telugu,
            _TE_RASHI,
        )
        from app.services.telugu_sankalpam_output import (
            format_birth_date_telugu,
            format_birth_time_telugu,
            force_telugu_place_segment,
        )

        variables["user_first_name"] = _latin_name_to_telugu(user.first_name or "")
        variables["user_last_name"] = _latin_name_to_telugu(user.last_name or "")
        variables["user_name"] = f"{variables['user_first_name']} {variables['user_last_name']}".strip()
        gotra_raw = ((override_gotram if override_gotram is not None else user.gotram) or "").strip()
        variables["gotram"] = _latin_name_to_telugu(gotra_raw) if gotra_raw else ""

        variables["birth_city"] = force_telugu_place_segment(user.birth_city or "")
        variables["birth_state"] = force_telugu_place_segment(user.birth_state or "")
        variables["birth_country"] = force_telugu_place_segment(user.birth_country or "")
        _bp_parts = [variables["birth_city"], variables["birth_state"], variables["birth_country"]]
        variables["birth_place"] = ", ".join(p for p in _bp_parts if p)
        variables["birth_time"] = format_birth_time_telugu(user.birth_time or "")
        variables["birth_date"] = format_birth_date_telugu(user.birth_date)
    else:
        variables["user_first_name"] = user.first_name
        variables["user_last_name"] = user.last_name
        variables["user_name"] = f"{user.first_name} {user.last_name}"
        variables["gotram"] = ((override_gotram if override_gotram is not None else user.gotram) or "").strip()
        variables["birth_place"] = f"{user.birth_city}, {user.birth_state}, {user.birth_country}"
        variables["birth_city"] = user.birth_city
        variables["birth_state"] = user.birth_state
        variables["birth_country"] = user.birth_country
        variables["birth_time"] = user.birth_time
        variables["birth_date"] = user.birth_date.strftime("%Y-%m-%d") if user.birth_date else ""

    # Translate location names based on template language
    from app.services.translation_service import translate_location

    _tr_lang = "telugu" if is_telugu else ("hindi" if "hindi" in (template_language or "").lower() else "sanskrit")
    translated_location = translate_location(
        city=location_city,
        state=location_state,
        country=location_country,
        language=_tr_lang,
    )
    
    # Current location variables (translated; Telugu forces no Latin in place names)
    if is_telugu:
        _cc = force_telugu_place_segment(translated_location["city"] or location_city or "")
        _cs = force_telugu_place_segment(translated_location["state"] or location_state or "")
        _cco = force_telugu_place_segment(translated_location["country"] or location_country or "")
        variables["current_location"] = ", ".join(x for x in (_cc, _cs) if x)
        variables["location_city"] = _cc
        variables["location_state"] = _cs
        variables["location_country"] = _cco
    else:
        variables["current_location"] = f"{translated_location['city']}, {translated_location['state']}"
        variables["location_city"] = translated_location["city"]
        variables["location_state"] = translated_location["state"]
        variables["location_country"] = translated_location["country"]
    
    # Keep original English names for internal use (if needed)
    variables["location_city_en"] = location_city
    variables["location_state_en"] = location_state
    variables["location_country_en"] = location_country
    
    # Astronomical data for current date at selected location (Divine API when configured)
    astronomical_data = await get_astronomical_data(
        date,
        latitude,
        longitude,
        location_city=location_city,
        location_state=location_state,
        location_country=location_country,
        template_language=astro_lang,
    )
    variables.update(astronomical_data)
    
    # Birth nakshatra / rashi: profile + ritual overrides first (same as pooja flow); else compute from birth time
    bn_profile = ((override_birth_nakshatra if override_birth_nakshatra is not None else user.birth_nakshatra) or "").strip()
    br_profile = ((override_birth_rashi if override_birth_rashi is not None else user.birth_rashi) or "").strip()
    variables["birth_nakshatra"] = ""
    variables["birth_rashi"] = ""
    if bn_profile:
        if is_telugu:
            bn_clean = re.sub(r"\s*nakshatra\s*$", "", bn_profile, flags=re.I).strip()
            variables["birth_nakshatra"] = _nakshatra_to_telugu(bn_clean) or _latin_name_to_telugu(bn_clean)
            if br_profile:
                br_clean = re.sub(r"\s*(rAshi|rashi|raśi)\s*$", "", br_profile, flags=re.I).strip()
                _br = _english_to_telugu(br_clean, _TE_RASHI)
                if not _br or _br.strip().lower() == br_clean.lower():
                    variables["birth_rashi"] = _latin_name_to_telugu(br_clean)
                else:
                    variables["birth_rashi"] = _br
            else:
                variables["birth_rashi"] = ""
        else:
            variables["birth_nakshatra"] = bn_profile
            variables["birth_rashi"] = br_profile
    else:
        try:
            birth_time_parts = (user.birth_time or "0:0").split(":")
            birth_hour = int(birth_time_parts[0])
            birth_minute = int(birth_time_parts[1]) if len(birth_time_parts) > 1 else 0
            if isinstance(user.birth_date, datetime):
                birth_datetime = datetime.combine(user.birth_date.date(), time(hour=birth_hour, minute=birth_minute))
            else:
                from datetime import date as date_type
                if isinstance(user.birth_date, date_type):
                    birth_datetime = datetime.combine(user.birth_date, time(hour=birth_hour, minute=birth_minute))
                else:
                    birth_datetime = datetime.now()
            birth_astronomical_data = await get_astronomical_data(
                birth_datetime,
                None,
                None,
                template_language=astro_lang,
            )
            nak = birth_astronomical_data.get("nakshatra", "") or ""
            rash = birth_astronomical_data.get("rashi", "") or ""
            if is_telugu:
                nak2 = re.sub(r"\s*nakshatra\s*$", "", nak, flags=re.I).strip()
                variables["birth_nakshatra"] = (
                    _nakshatra_to_telugu(nak2) or _latin_name_to_telugu(nak2) if nak2 else ""
                )
                if rash:
                    r2 = re.sub(r"\s*(rAshi|rashi|raśi)\s*$", "", rash, flags=re.I).strip()
                    _rz = _english_to_telugu(r2, _TE_RASHI)
                    variables["birth_rashi"] = _rz if _rz.lower() != r2.lower() else _latin_name_to_telugu(r2)
                else:
                    variables["birth_rashi"] = ""
            else:
                variables["birth_nakshatra"] = nak
                variables["birth_rashi"] = rash
        except Exception as e:
            print(f"Error calculating birth astronomical data: {e}")
    
    # Geographical features
    geo_features = await get_nearby_geographical_features(
        lat=str(latitude) if latitude else None,
        lon=str(longitude) if longitude else None,
        city=location_city,
        state=location_state,
        country=location_country
    )
    
    # Handle None values properly - use empty string as default
    variables["nearby_river"] = geo_features.get("river") or ""
    variables["nearby_mountain"] = geo_features.get("mountain") or ""
    variables["nearby_sea"] = geo_features.get("sea") or ""
    variables["nearby_ocean"] = geo_features.get("ocean") or ""
    
    # Translate geographical feature names based on language
    from app.services.translation_service import translate_geographical_feature
    
    # Geographical feature line: full Telugu script when template is Telugu
    if is_telugu:
        if geo_features.get("river"):
            tr = translate_geographical_feature(geo_features["river"], "river", "telugu")
            tr = force_telugu_place_segment(tr)
            variables["geographical_feature"] = f"{tr} నదీ తీరం"
        elif geo_features.get("sea"):
            tr = translate_geographical_feature(geo_features["sea"], "sea", "telugu")
            tr = force_telugu_place_segment(tr)
            variables["geographical_feature"] = f"{tr} సముద్ర తీరం"
        elif geo_features.get("ocean"):
            tr = translate_geographical_feature(geo_features["ocean"], "ocean", "telugu")
            tr = force_telugu_place_segment(tr)
            variables["geographical_feature"] = f"{tr} సముద్ర తీరం"
        elif geo_features.get("mountain"):
            tr = translate_geographical_feature(geo_features["mountain"], "mountain", "telugu")
            tr = force_telugu_place_segment(tr)
            variables["geographical_feature"] = f"{tr} పర్వత సమీపం"
        elif geo_features.get("primary_feature"):
            variables["geographical_feature"] = force_telugu_place_segment(geo_features.get("primary_feature") or "")
        else:
            variables["geographical_feature"] = ""
    elif geo_features.get("river"):
        translated_river = translate_geographical_feature(geo_features["river"], "river", template_language)
        variables["geographical_feature"] = f"{translated_river} nadi tere"
    elif geo_features.get("sea"):
        translated_sea = translate_geographical_feature(geo_features["sea"], "sea", template_language)
        variables["geographical_feature"] = f"{translated_sea} samudra tere"
    elif geo_features.get("ocean"):
        translated_ocean = translate_geographical_feature(geo_features["ocean"], "ocean", template_language)
        variables["geographical_feature"] = f"{translated_ocean} samudra tere"
    elif geo_features.get("mountain"):
        translated_mountain = translate_geographical_feature(geo_features["mountain"], "mountain", template_language)
        variables["geographical_feature"] = f"{translated_mountain} parvata pArshvE"
    elif geo_features.get("primary_feature"):
        variables["geographical_feature"] = geo_features.get("primary_feature")
    else:
        variables["geographical_feature"] = ""
    
    # Family members (names and relations in selected language when Telugu)
    family_list = []
    for member in family_members:
        if is_telugu:
            # Keep names exactly as stored; per-letter Latin→Telugu mangles many personal names.
            name_disp = (member.name or "").strip()
            rel_raw = (member.relation or "").strip()
            rel_te = _english_to_telugu(rel_raw, _TE_REL)
            if not rel_te or rel_te.strip().lower() == rel_raw.lower():
                rel_te = rel_raw
            if rel_te:
                family_list.append(f"{name_disp} ({rel_te})")
            else:
                family_list.append(name_disp)
        else:
            family_list.append(f"{member.name} ({member.relation})")
    variables["family_members"] = ", ".join(family_list) if family_list else ("" if is_telugu else "None")
    variables["family_members_count"] = str(len(family_members))
    
    # Pooja / generic sankalpam title
    if pooja_name:
        if is_telugu:
            _pn = pooja_name.strip()
            _mapped = _english_to_telugu(_pn, _TE_POOJA_NAMES)
            if _mapped.strip().lower() == _pn.lower():
                variables["pooja_name"] = _latin_name_to_telugu(_pn)
            else:
                variables["pooja_name"] = _mapped
        else:
            variables["pooja_name"] = pooja_name
    else:
        variables["pooja_name"] = "సాధారణ సంకల్పం" if is_telugu else "Pooja"

    # Date and time variables (Telugu month names; digits stay 0–9 when template is Telugu)
    if is_telugu:
        variables["date"] = format_birth_date_telugu(date)
        variables["time"] = format_birth_time_telugu(date.strftime("%H:%M"))
        variables["date_formatted"] = format_birth_date_telugu(date)
    else:
        variables["date"] = date.strftime("%Y-%m-%d")
        variables["time"] = date.strftime("%H:%M")
        variables["date_formatted"] = date.strftime("%B %d, %Y")

    # Location-based geographical references (language-aware)
    country_lower = (location_country or "").lower().strip()

    if is_telugu:
        if "india" in country_lower or "bharat" in country_lower:
            variables["geographical_reference"] = "జంబూద్వీపే భారతవర్షే భారతఖండే"
        elif "nepal" in country_lower:
            variables["geographical_reference"] = "జంబూద్వీపే నేపాలవర్షే"
        elif "sri lanka" in country_lower or "ceylon" in country_lower:
            variables["geographical_reference"] = "లంకాద్వీపే"
        elif "united states" in country_lower or "usa" in country_lower:
            variables["geographical_reference"] = "అమెరికా దేశే"
        else:
            _cde = force_telugu_place_segment(location_country or "")
            variables["geographical_reference"] = f"{_cde} దేశే" if _cde else "దేశే"
    else:
        # Sanskrit/Devanagari script (default)
        if "india" in country_lower or "bharat" in country_lower:
            variables["geographical_reference"] = "भारतवर्षे भरतखण्डे जम्बूद्वीपे"
        elif "nepal" in country_lower:
            variables["geographical_reference"] = "नेपालवर्षे जम्बूद्वीपे"
        elif "sri lanka" in country_lower or "ceylon" in country_lower:
            variables["geographical_reference"] = "लङ्काद्वीपे"
        elif "united states" in country_lower or "usa" in country_lower:
            variables["geographical_reference"] = "अमेरिका देशे"
        else:
            variables["geographical_reference"] = f"{location_country} देशे"

    # Telugu sankalpa purpose phrase (matches /api/sankalpam/generate intent options)
    if is_telugu:
        from app.services.sankalpa_family_builder import sankalpa_intent_phrase_te
        variables["sankalpa_intent"] = sankalpa_intent_phrase_te(sankalpa_intent or "general")
    else:
        variables["sankalpa_intent"] = ""

    return variables

async def replace_template_variables(
    template_text: str,
    variables: Dict[str, str]
) -> str:
    """
    Replace all variables in template text with actual values.
    
    Args:
        template_text: Text with variables in {{variable_name}} format
        variables: Dictionary of variable names and their values
    
    Returns:
        Text with all variables replaced
    """
    return replace_variables(template_text, variables)
