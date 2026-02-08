"""
Translation service for geographical names and other text
Translates city, state, country, river, ocean names to user's preferred language
"""
from typing import Dict, Optional
from app.models import Language

# Translation dictionaries for common geographical names
GEOGRAPHICAL_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "telugu": {
        # Countries
        "america": "అమెరికా",
        "united states": "అమెరికా",
        "usa": "అమెరికా",
        "india": "భారతదేశం",
        "bharat": "భారతదేశం",
        
        # US States
        "texas": "టెక్సాస్",
        "florida": "ఫ్లోరిడా",
        "california": "కాలిఫోర్నియా",
        "new york": "న్యూయార్క్",
        
        # Rivers
        "brazos": "బ్రాజోస్",
        "gulf of mexico": "మెక్సికో గల్ఫ్",
        "pacific ocean": "పసిఫిక్ మహాసముద్రం",
        "atlantic ocean": "అట్లాంటిక్ మహాసముద్రం",
        "indian ocean": "భారత మహాసముద్రం",
        "ganga": "గంగా",
        "yamuna": "యమున",
        "godavari": "గోదావరి",
        "krishna": "కృష్ణ",
        "kaveri": "కావేరి",
        
        # Common terms
        "nadi": "నది",
        "samudra": "సముద్రం",
        "tere": "తీరే",
    },
    "hindi": {
        # Countries
        "america": "अमेरिका",
        "united states": "अमेरिका",
        "usa": "अमेरिका",
        "india": "भारत",
        "bharat": "भारत",
        
        # US States
        "texas": "टेक्सास",
        "florida": "फ्लोरिडा",
        "california": "कैलिफोर्निया",
        "new york": "न्यूयॉर्क",
        
        # Rivers
        "brazos": "ब्राजोस",
        "gulf of mexico": "मैक्सिको की खाड़ी",
        "pacific ocean": "प्रशांत महासागर",
        "atlantic ocean": "अटलांटिक महासागर",
        "indian ocean": "हिंद महासागर",
        "ganga": "गंगा",
        "yamuna": "यमुना",
        "godavari": "गोदावरी",
        "krishna": "कृष्ण",
        "kaveri": "कावेरी",
        
        # Common terms
        "nadi": "नदी",
        "samudra": "समुद्र",
        "tere": "तटे",
    },
    "sanskrit": {
        # Countries - keep in Devanagari script
        "america": "अमेरिका",
        "united states": "अमेरिका",
        "usa": "अमेरिका",
        "india": "भारत",
        "bharat": "भारत",
        
        # Rivers
        "ganga": "गङ्गा",
        "yamuna": "यमुना",
        "godavari": "गोदावरी",
        "krishna": "कृष्ण",
        "kaveri": "कावेरी",
        
        # Common terms
        "nadi": "नदी",
        "samudra": "समुद्र",
        "tere": "तटे",
    },
    # Add more languages as needed
}

def translate_geographical_name(name: str, language: str) -> str:
    """
    Translate a geographical name to the specified language.
    If translation not found, returns the original name.
    
    Args:
        name: The geographical name to translate (case-insensitive)
        language: Target language code (e.g., "telugu", "hindi")
    
    Returns:
        Translated name or original name if translation not available
    """
    if not name:
        return name
    
    language_lower = language.lower()
    name_lower = name.lower().strip()
    
    # Check if we have translations for this language
    if language_lower not in GEOGRAPHICAL_TRANSLATIONS:
        # Return original name if language not supported
        return name
    
    translations = GEOGRAPHICAL_TRANSLATIONS[language_lower]
    
    # Direct match
    if name_lower in translations:
        return translations[name_lower]
    
    # Try partial matches (e.g., "Gulf of Mexico" contains "mexico")
    for key, value in translations.items():
        if key in name_lower or name_lower in key:
            # Replace the matched part
            return name.replace(name_lower, value)
    
    # No translation found, return original
    return name

def translate_location(
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    language: str = "sanskrit"
) -> Dict[str, str]:
    """
    Translate location components (city, state, country) to specified language.
    
    Returns:
        Dictionary with translated city, state, country
    """
    result = {}
    
    if city:
        result["city"] = translate_geographical_name(city, language)
    else:
        result["city"] = ""
    
    if state:
        result["state"] = translate_geographical_name(state, language)
    else:
        result["state"] = ""
    
    if country:
        result["country"] = translate_geographical_name(country, language)
    else:
        result["country"] = ""
    
    return result

def translate_geographical_feature(feature_name: str, feature_type: str, language: str) -> str:
    """
    Translate geographical feature name (river, ocean, sea, mountain) to specified language.
    
    Args:
        feature_name: Name of the feature (e.g., "Gulf of Mexico", "Brazos")
        feature_type: Type of feature ("river", "ocean", "sea", "mountain")
        language: Target language
    
    Returns:
        Translated feature name
    """
    translated_name = translate_geographical_name(feature_name, language)
    
    # For certain languages, we might want to append native terms
    # For now, just return the translated name
    # The template will add "nadi", "samudra", etc.
    
    return translated_name

