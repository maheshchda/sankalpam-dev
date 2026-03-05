"""
Service to replace template variables with actual data from database and external sources
"""
from typing import Dict, Optional
from datetime import datetime, time
from app.models import User, FamilyMember
from app.services.astronomical_service import get_astronomical_data
from app.services.location_service import get_nearby_geographical_features
import re

def replace_variables(text: str, variables: Dict[str, str]) -> str:
    """
    Replace variables in text with actual values.
    Variables in format {{variable_name}} will be replaced with values from the dictionary.
    
    Args:
        text: Text with variables in {{variable_name}} format
        variables: Dictionary mapping variable names to their values
    
    Returns:
        Text with all variables replaced
    """
    result = text
    
    for var_name, var_value in variables.items():
        # Replace {{variable_name}} with the value
        pattern = r'\{\{' + re.escape(var_name) + r'\}\}'
        result = re.sub(pattern, str(var_value), result)
    
    return result

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
    template_language: str = "sanskrit"  # Default to sanskrit for backward compatibility
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
    
    # User variables
    template_lang_lower = (template_language or "").strip().lower()
    is_telugu = template_lang_lower in ("te", "telugu")
    if is_telugu:
        from app.services.divineapi_service import _latin_name_to_telugu, _english_to_telugu, _TE_RELATION as _TE_REL
        variables["user_first_name"] = _latin_name_to_telugu(user.first_name)
        variables["user_last_name"] = _latin_name_to_telugu(user.last_name)
        variables["user_name"] = f"{variables['user_first_name']} {variables['user_last_name']}"
        variables["gotram"] = _latin_name_to_telugu(user.gotram or "")
    else:
        variables["user_first_name"] = user.first_name
        variables["user_last_name"] = user.last_name
        variables["user_name"] = f"{user.first_name} {user.last_name}"
        variables["gotram"] = user.gotram
    variables["birth_place"] = f"{user.birth_city}, {user.birth_state}, {user.birth_country}"
    variables["birth_city"] = user.birth_city
    variables["birth_state"] = user.birth_state
    variables["birth_country"] = user.birth_country
    variables["birth_time"] = user.birth_time
    variables["birth_date"] = user.birth_date.strftime("%Y-%m-%d")
    
    # Translate location names based on user's preferred language
    from app.services.translation_service import translate_location
    translated_location = translate_location(
        city=location_city,
        state=location_state,
        country=location_country,
        language=template_language if template_language else "sanskrit"
    )
    
    # Current location variables (without country to avoid duplication, translated)
    variables["current_location"] = f"{translated_location['city']}, {translated_location['state']}"
    variables["location_city"] = translated_location["city"]
    variables["location_state"] = translated_location["state"]
    variables["location_country"] = translated_location["country"]
    
    # Keep original English names for internal use (if needed)
    variables["location_city_en"] = location_city
    variables["location_state_en"] = location_state
    variables["location_country_en"] = location_country
    
    # Astronomical data for current date (when Sankalpam is performed)
    astronomical_data = await get_astronomical_data(date, latitude, longitude)
    variables.update(astronomical_data)
    
    # User's birth astronomical data (nakshatra, rashi, etc.)
    # Parse birth date and time to calculate birth nakshatra
    try:
        # Combine birth_date and birth_time
        birth_time_parts = user.birth_time.split(':')
        birth_hour = int(birth_time_parts[0])
        birth_minute = int(birth_time_parts[1]) if len(birth_time_parts) > 1 else 0
        
        # Create birth datetime - user.birth_date is already a datetime, so get date part and combine with time
        if isinstance(user.birth_date, datetime):
            birth_datetime = datetime.combine(user.birth_date.date(), time(hour=birth_hour, minute=birth_minute))
        else:
            # If it's already a date object, combine directly
            from datetime import date as date_type
            if isinstance(user.birth_date, date_type):
                birth_datetime = datetime.combine(user.birth_date, time(hour=birth_hour, minute=birth_minute))
            else:
                # Fallback: use current date
                birth_datetime = datetime.now()
        
        # Get user's birth location coordinates if available (for now, use None or default)
        # In production, you might want to store lat/long for birth location
        birth_latitude = None
        birth_longitude = None
        
        # Calculate birth astronomical data
        birth_astronomical_data = await get_astronomical_data(
            birth_datetime, 
            birth_latitude, 
            birth_longitude
        )
        
        # Add birth-specific variables
        variables["birth_nakshatra"] = birth_astronomical_data.get("nakshatra", "")
        variables["birth_rashi"] = birth_astronomical_data.get("rashi", "")  # Zodiac sign
    except Exception as e:
        # If there's an error calculating birth data, set empty strings
        print(f"Error calculating birth astronomical data: {e}")
        variables["birth_nakshatra"] = ""
        variables["birth_rashi"] = ""
    
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
    
    # Set geographical_feature with priority: river > sea > ocean > mountain
    # This ensures we use river first, then sea, then ocean, then mountain
    # All names are translated to user's preferred language
    if geo_features.get("river"):
        translated_river = translate_geographical_feature(geo_features["river"], "river", template_language)
        variables["geographical_feature"] = f"{translated_river} nadi tere"  # "river shore"
    elif geo_features.get("sea"):
        translated_sea = translate_geographical_feature(geo_features["sea"], "sea", template_language)
        variables["geographical_feature"] = f"{translated_sea} samudra tere"  # "sea shore"
    elif geo_features.get("ocean"):
        translated_ocean = translate_geographical_feature(geo_features["ocean"], "ocean", template_language)
        variables["geographical_feature"] = f"{translated_ocean} samudra tere"  # "ocean shore"
    elif geo_features.get("mountain"):
        translated_mountain = translate_geographical_feature(geo_features["mountain"], "mountain", template_language)
        variables["geographical_feature"] = f"{translated_mountain} parvata pArshvE"  # "near mountain"
    elif geo_features.get("primary_feature"):
        # primary_feature already contains translated text, so use as is
        variables["geographical_feature"] = geo_features.get("primary_feature")
    else:
        # Final fallback
        variables["geographical_feature"] = ""
    
    # Family members (names and relations in selected language when Telugu)
    family_list = []
    for member in family_members:
        if is_telugu:
            name_te = _latin_name_to_telugu(member.name)
            rel_te = _english_to_telugu((member.relation or "").strip(), _TE_REL) or (member.relation or "")
            family_list.append(f"{name_te} ({rel_te})")
        else:
            family_list.append(f"{member.name} ({member.relation})")
    variables["family_members"] = ", ".join(family_list) if family_list else "None"
    variables["family_members_count"] = str(len(family_members))
    
    # Pooja name
    if pooja_name:
        variables["pooja_name"] = pooja_name
    else:
        variables["pooja_name"] = "Pooja"
    
    # Date and time variables
    variables["date"] = date.strftime("%Y-%m-%d")
    variables["time"] = date.strftime("%H:%M")
    variables["date_formatted"] = date.strftime("%B %d, %Y")
    
    # Location-based geographical references (language-aware)
    # Generate in appropriate script based on template language
    country_lower = location_country.lower().strip()
    template_lang_lower = template_language.lower() if template_language else "sanskrit"
    
    if "telugu" in template_lang_lower:
        # Telugu script
        if "india" in country_lower or "bharat" in country_lower:
            variables["geographical_reference"] = "జంబూద్వీపే భారతవర్షే భారతఖండే"
        elif "nepal" in country_lower:
            variables["geographical_reference"] = "జంబూద్వీపే నేపాలవర్షే"
        elif "sri lanka" in country_lower or "ceylon" in country_lower:
            variables["geographical_reference"] = "లంకాద్వీపే"
        elif "united states" in country_lower or "usa" in country_lower:
            variables["geographical_reference"] = "అమెరికా దేశే"
        else:
            variables["geographical_reference"] = f"{location_country} దేశే"
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
