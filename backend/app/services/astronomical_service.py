"""
Service to fetch astronomical data for Sankalpam (year, ayanam, rithu, tithi, nakshatra, etc.)
Uses external APIs or calculations based on date/time/location
"""
import httpx
from datetime import datetime
from typing import Dict, Optional
from app.config import settings

async def get_astronomical_data(
    date: datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timezone: Optional[str] = None
) -> Dict[str, str]:
    """
    Fetch astronomical data for a given date and location.
    Returns a dictionary with all astronomical variables needed for Sankalpam.
    
    Priority:
    1. Try DivineAPI Panchang API (if configured)
    2. Fallback to approximate calculations
    
    Based on the ahobilamutt.org format:
    - samvathsarE (year name like "viSvAvasu nAma")
    - ayanam (dakshiNAyaNE or uttarAyaNE)
    - rithou (season like "hEmantha rithou")
    - mAsE (month like "dhanur mAsE")
    - pakshE (lunar phase like "shukla pakshE" or "krishna pakshE")
    - thithou (day of month like "prathamyAm shubha thithou")
    - vAsara (day of week like "bhrugu vAsara")
    - nakshatra (star constellation like "moolA nakshatra")
    """
    
    # Try DivineAPI Panchang API first (if configured and coordinates available)
    if latitude and longitude:
        try:
            from app.services.divineapi_panchang import get_panchang_from_divineapi
            panchang_data = await get_panchang_from_divineapi(date, latitude, longitude, timezone)
            
            if panchang_data:
                # Merge with calculated data (panchang API might not have everything)
                calculated_data = calculate_astronomical_data_fallback(date, latitude, longitude)
                
                # Override with API data where available
                if panchang_data.get("tithi"):
                    calculated_data["thithou"] = panchang_data["tithi"]
                if panchang_data.get("nakshatra"):
                    calculated_data["nakshatra"] = panchang_data["nakshatra"]
                if panchang_data.get("yoga"):
                    calculated_data["yoga"] = panchang_data["yoga"]
                if panchang_data.get("karana"):
                    calculated_data["karaNa"] = panchang_data["karana"]
                if panchang_data.get("pakshE"):
                    calculated_data["pakshE"] = panchang_data["pakshE"]
                
                return calculated_data
        except ImportError:
            print("DivineAPI panchang service not available")
        except Exception as e:
            print(f"Error fetching from DivineAPI Panchang: {e}")
            # Continue to fallback
    
    # Fallback: Calculate basic values (this is a simplified version)
    # In production, use proper panchangam calculation libraries
    return calculate_astronomical_data_fallback(date, latitude, longitude)

def calculate_astronomical_data_fallback(
    date: datetime,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None
) -> Dict[str, str]:
    """
    Fallback calculation for astronomical data.
    This is a simplified version - for production, use proper panchangam libraries.
    """
    
    # Day of week mapping
    weekdays = {
        0: "bhAnu vAsara",  # Sunday
        1: "sOma vAsara",   # Monday
        2: "ma~Ngala vAsara",  # Tuesday
        3: "budha vAsara",  # Wednesday
        4: "guru vAsara",   # Thursday
        5: "shukra vAsara", # Friday
        6: "shaNi vAsara",  # Saturday
    }
    
    # Month names (simplified - actual calculation is more complex)
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
    
    # Seasons (rithu) - simplified
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
    
    # Determine ayanam (solstice direction)
    month = date.month
    day = date.day
    # Rough calculation: uttarAyaNE (Dec 21 - Jun 20), dakshiNAyaNE (Jun 21 - Dec 20)
    if (month == 12 and day >= 21) or month in [1, 2, 3, 4, 5] or (month == 6 and day < 21):
        ayanam = "uttarAyaNE"
    else:
        ayanam = "dakshiNAyaNE"
    
    # Year names cycle (60-year cycle - simplified to current year)
    # Note: This is a partial list. For full implementation, add all 60 names
    year_names = [
        "prabhava", "vibhava", "shukla", "pramoda", "prajApati",
        "A~Ngirasa", "shrImukha", "bhAva", "yuvan", "dhAtR",
        # ... (60 names total - for now using modulo on available names)
    ]
    # Use modulo with the actual list length to prevent index errors
    year_index = (date.year - 1987) % len(year_names)  # Starting from a known reference year
    samvathsarE = f"{year_names[year_index]} nAma samvathsarE"
    
    # Rashi (Zodiac sign) calculation - approximate based on month
    # Note: This is simplified. Accurate rashi requires Sun's exact position
    rashi_map = {
        1: "makara rAshi",  # Capricorn (Jan)
        2: "kumbha rAshi",  # Aquarius (Feb)
        3: "mIna rAshi",    # Pisces (Mar)
        4: "mEsha rAshi",   # Aries (Apr)
        5: "vRishabha rAshi",  # Taurus (May)
        6: "mithuna rAshi",    # Gemini (Jun)
        7: "karkaTa rAshi",    # Cancer (Jul)
        8: "simha rAshi",      # Leo (Aug)
        9: "kanyA rAshi",      # Virgo (Sep)
        10: "tulA rAshi",      # Libra (Oct)
        11: "vRishchika rAshi", # Scorpio (Nov)
        12: "dhanu rAshi",     # Sagittarius (Dec)
    }
    # Rough approximation - actual rashi depends on exact date within month
    rashi = rashi_map.get(month, "rAshi")
    
    # Simplified Nakshatra calculation (placeholder for now)
    # In a real application, this would involve complex astronomical calculations
    nakshatra_names = [
        "ashvini", "bharaNi", "krittika", "rOhiNi", "mrugashIrsha", "Ardra",
        "punarvasu", "pushyA", "AshlEsha", "maghA", "pUrva phalguni", "uttara phalguni",
        "hasta", "chitra", "svAti", "vishAkha", "anurAdha", "jyEshTha",
        "moola", "pUrvAshADha", "uttarAshADha", "shrAvaNa", "dhaniSTha", "shatabhisha",
        "pUrva bhAdrapada", "uttara bhAdrapada", "rEvati"
    ]
    # Use month and day as a very rough proxy for nakshatra (not astronomically accurate)
    # This cycles through nakshatras approximately based on date
    nakshatra_index = ((month - 1) * 30 + day) % len(nakshatra_names)
    nakshatra = f"{nakshatra_names[nakshatra_index]} nakshatra"
    
    # Calculate weekday
    # Python's weekday() returns: 0=Monday, 1=Tuesday, ..., 6=Sunday
    # Our mapping uses: 0=Sunday, 1=Monday, ..., 6=Saturday
    # So we convert: (weekday() + 1) % 7 to map Monday->1, Sunday->0
    weekday_python = date.weekday()  # Python: 0=Monday, 6=Sunday
    weekday_num = (weekday_python + 1) % 7  # Convert: Monday(0)->1, Sunday(6)->0
    
    # Get actual weekday name
    vAsara = weekdays.get(weekday_num, "vAsara")
    
    # Simplified yoga and karana (placeholders - need panchangam API for accurate values)
    yoga_names = ["vishkambha", "prIti", "AyushmAn", "saubhAgya", "shobhana", "atiganda",
                  "sukarma", "dhRiti", "shUla", "ganda", "vRiddhi", "dhruva",
                  "vyAghAta", "harshaNa", "vajra", "siddhi", "vyatIpAta", "varIyas",
                  "parigha", "shiva", "siddha", "sAdhya", "shubha", "shukla",
                  "brahma", "indrA", "vaidhRiti"]
    yoga_index = ((month - 1) * 30 + day) % len(yoga_names)
    yoga = f"{yoga_names[yoga_index]} yoga"
    
    karana_names = ["bava", "bAlava", "kaulava", "taitila", "garaja", "vaNija",
                    "visti", "shakuni", "chatushpAda", "nAga", "kiMstughna"]
    karana_index = ((month - 1) * 30 + day) % len(karana_names)
    karaNa = f"{karana_names[karana_index]} karaNa"
    
    return {
        "samvathsarE": samvathsarE,
        "ayanam": ayanam,
        "rithou": month_to_season.get(month, "rithou"),
        "mAsE": months.get(month, "mAsE"),
        "pakshE": "shukla pakshE",  # Would need lunar calculation - TODO: integrate panchangam API
        "thithou": "shubha thithou",  # Would need lunar calculation - TODO: integrate panchangam API
        "vAsara": vAsara,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "karaNa": karaNa,
        "rashi": rashi,  # Zodiac sign
    }

