import httpx
from typing import Optional, Dict
from app.config import settings

async def get_nearby_rivers(
    city: str,
    state: str,
    country: str,
    lat: Optional[str] = None,
    lon: Optional[str] = None
) -> str:
    """
    Get nearby river name using Google Places API or Geocoding API
    Falls back to a default river name based on location if API fails
    """
    
    if lat and lon:
        # Use Google Places API to find nearby rivers
        try:
            async with httpx.AsyncClient() as client:
                # Search for rivers near the location
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                params = {
                    "location": f"{lat},{lon}",
                    "radius": 50000,  # 50km radius
                    "keyword": "river",
                    "key": settings.google_maps_api_key
                }
                
                response = await client.get(url, params=params)
                data = response.json()
                
                if data.get("results"):
                    # Get the first river found
                    river_name = data["results"][0].get("name", "")
                    if river_name:
                        return river_name
        except Exception as e:
            print(f"Error fetching river from Google Places API: {e}")
    
    # Fallback: Return a common river name based on state/city
    # This is a simple mapping - in production, you'd want a comprehensive database
    river_mapping = {
        "india": {
            "ganga": ["uttar pradesh", "uttarakhand", "west bengal", "bihar"],
            "yamuna": ["delhi", "uttar pradesh", "haryana"],
            "godavari": ["maharashtra", "telangana", "andhra pradesh"],
            "krishna": ["karnataka", "andhra pradesh", "telangana"],
            "kaveri": ["karnataka", "tamil nadu"],
            "narmada": ["madhya pradesh", "gujarat"],
            "tapi": ["gujarat", "maharashtra"],
        },
        "united states": {
            "brazos": ["texas"],
            "rio grande": ["texas", "new mexico"],
            "mississippi": ["mississippi", "louisiana", "tennessee", "arkansas", "missouri", "illinois", "iowa", "wisconsin", "minnesota"],
            "colorado": ["colorado", "utah", "arizona", "nevada", "california"],
            "hudson": ["new york", "new jersey"],
            "potomac": ["maryland", "virginia", "west virginia"],
            "columbia": ["washington", "oregon"],
        }
    }
    
    # Try to match state to a river
    country_lower = country.lower()
    state_lower = state.lower()
    
    if country_lower in river_mapping:
        for river, states in river_mapping[country_lower].items():
            # Check if state matches (case-insensitive)
            if state_lower in [s.lower() for s in states]:
                return river.title()
    
    # Also check if country name contains "united states" or "usa"
    if "united states" in country_lower or "usa" in country_lower:
        for river, states in river_mapping.get("united states", {}).items():
            if state_lower in [s.lower() for s in states]:
                return river.title()
    
    # Default fallback
    return "Ganga" if country.lower() == "india" else "Sacred River"

async def get_nearby_geographical_features(
    lat: Optional[str] = None,
    lon: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None
) -> Dict[str, Optional[str]]:
    """
    Get nearby geographical features: river, mountain, sea, ocean.
    Returns a dictionary with river, mountain, sea, ocean names.
    
    Priority (FIXED):
    1. Sea/Ocean (if available) - for coastal areas
    2. River (if no sea/ocean)
    3. Mountain (if no sea/ocean or river)
    """
    result = {
        "river": None,
        "mountain": None,
        "sea": None,
        "ocean": None,
        "primary_feature": None,  # The primary geographical feature to use
    }
    
    if lat and lon and settings.google_maps_api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
                
                # PRIORITY 1: Check for sea/ocean first (for coastal cities)
                params_water = {
                    "location": f"{lat},{lon}",
                    "radius": 50000,  # 50km - coastal areas should be within this
                    "keyword": "beach OR ocean OR sea OR gulf OR bay",
                    "key": settings.google_maps_api_key
                }
                
                response = await client.get(url, params=params_water)
                data = response.json()
                
                if data.get("results"):
                    # Look for ocean/sea/gulf/bay in results
                    for place in data.get("results", []):
                        name = place.get("name", "").lower()
                        types = place.get("types", [])
                        
                        # Check if it's a water body
                        if any(t in ["beach", "natural_feature", "point_of_interest"] for t in types):
                            # Determine ocean vs sea vs gulf based on name or location
                            name_lower = name
                            if any(word in name_lower for word in ["ocean", "atlantic", "pacific", "indian ocean", "arctic"]):
                                result["ocean"] = place.get("name", "")
                                # Don't set primary_feature here - let template_service handle translation
                                break
                            elif any(word in name_lower for word in ["gulf", "bay", "sea", "mediterranean", "caribbean"]):
                                result["sea"] = place.get("name", "")
                                # Don't set primary_feature here - let template_service handle translation
                                break
                    
                    # If no specific name found but we're near water, use generic
                    # Note: This is a fallback only when Google Places API doesn't return a specific water body name
                    # For Gulf Coast states, we use "Gulf of Mexico" as a reasonable default
                    if not result["primary_feature"] and data.get("results"):
                        # Check country/region to determine ocean name
                        if country and ("united states" in country.lower() or "usa" in country.lower()):
                            if state and ("texas" in state.lower() or "florida" in state.lower() or "louisiana" in state.lower() or 
                                         "mississippi" in state.lower() or "alabama" in state.lower()):
                                # Gulf Coast states - fallback to Gulf of Mexico if API doesn't return specific name
                                # Note: This will be translated later based on language preference
                                result["ocean"] = "Gulf of Mexico"
                                # Don't set primary_feature here - let template_service handle translation
                            elif state and any(s in state.lower() for s in ["california", "oregon", "washington"]):
                                # Pacific Coast states - fallback to Pacific Ocean
                                # Note: This will be translated later based on language preference
                                # Pacific Coast states - fallback to Pacific Ocean
                                # Note: This will be translated later based on language preference
                                result["ocean"] = "Pacific Ocean"
                                # Don't set primary_feature here - let template_service handle translation
                            else:
                                result["ocean"] = "Ocean"
                                result["primary_feature"] = "samudra tere"
                        else:
                            result["sea"] = "Sea"
                            result["primary_feature"] = "samudra tere"
                
                # PRIORITY 2: If no sea/ocean, try to find a river
                if not result["primary_feature"]:
                    params_river = {
                        "location": f"{lat},{lon}",
                        "radius": 100000,  # 100km radius for better coverage
                        "keyword": "river",
                        "key": settings.google_maps_api_key
                    }
                    
                    response = await client.get(url, params=params_river)
                    data = response.json()
                    
                    river_name = None
                    if data.get("results"):
                        # Look through results to find a river (not just any water feature)
                        for place in data.get("results", []):
                            name = place.get("name", "").lower()
                            types = place.get("types", [])
                            # Prioritize actual rivers, not beaches or other water features
                            if "river" in name or any("river" in t for t in types):
                                river_name = place.get("name", "")
                                break
                        # If no clear river found, use first result
                        if not river_name and data["results"]:
                            river_name = data["results"][0].get("name", "")
                    
                    if river_name:
                        result["river"] = river_name
                        # Don't set primary_feature here - let template_service handle translation
                
                # PRIORITY 3: If no river or sea/ocean, try mountains
                if not result["primary_feature"]:
                    params_mountain = {
                        "location": f"{lat},{lon}",
                        "radius": 100000,  # 100km (mountains are larger features)
                        "keyword": "mountain",
                        "key": settings.google_maps_api_key
                    }
                    
                    response = await client.get(url, params=params_mountain)
                    data = response.json()
                    
                    if data.get("results"):
                        mountain_name = data["results"][0].get("name", "")
                        if mountain_name:
                            result["mountain"] = mountain_name
                            result["primary_feature"] = f"{mountain_name} parvata pArshvE"  # "near mountain"
        
        except Exception as e:
            print(f"Error fetching geographical features from Google Places API: {e}")
    
    # Fallback: Use river mapping ONLY if we have location info and NO feature found yet
    # IMPORTANT: Skip river fallback for coastal cities - they should have sea/ocean
    # Check if city is known to be coastal before using river fallback
    if not result["primary_feature"] and city and state and country:
        # List of known coastal cities (where we should prioritize sea/ocean over river)
        coastal_cities = [
            "corpus christi", "houston", "galveston", "miami", "tampa", "jacksonville",
            "new orleans", "mobile", "birmingham", "san diego", "los angeles", "san francisco",
            "seattle", "portland", "boston", "new york", "philadelphia", "baltimore",
            "norfolk", "charleston", "savannah", "jacksonville"
        ]
        
        city_lower = city.lower()
        is_coastal = any(coastal in city_lower for coastal in coastal_cities)
        
        # Only use river fallback if NOT a coastal city
        if not is_coastal:
            river = await get_nearby_rivers(city, state, country, lat, lon)
            # Only use fallback river if it's not "Sacred River" (generic fallback)
            if river and river.lower() != "sacred river":
                result["river"] = river
                # Don't set primary_feature here - let template_service handle translation
        else:
            # For coastal cities without detected sea/ocean, use generic coastal reference
            if country and ("united states" in country.lower() or "usa" in country.lower()):
                if state and ("texas" in state.lower() or "florida" in state.lower() or 
                             "louisiana" in state.lower() or "mississippi" in state.lower() or 
                             "alabama" in state.lower()):
                    # For coastal cities, set ocean but let template_service handle translation
                    result["ocean"] = "Gulf of Mexico"
                    # Don't set primary_feature here - let template_service handle translation
                elif state and any(s in state.lower() for s in ["california", "oregon", "washington"]):
                    # For coastal cities, set ocean but let template_service handle translation
                    result["ocean"] = "Pacific Ocean"
                    # Don't set primary_feature here - let template_service handle translation
    
    # Final fallback - only if nothing was found
    if not result["primary_feature"]:
        if country and country.lower() == "india":
            result["primary_feature"] = "Ganga nadi tere"
        else:
            result["primary_feature"] = "sacred tIrtha"  # "sacred place"
    
    return result

async def get_location_from_coordinates(lat: str, lon: str) -> dict:
    """
    Reverse geocode coordinates to get city, state, country
    Uses OpenStreetMap Nominatim (FREE, no API key needed) as primary method
    Falls back to Google Maps if API key is configured
    """
    # Try OpenStreetMap Nominatim first (FREE, no API key needed)
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # OpenStreetMap Nominatim - FREE and doesn't require API key
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json",
                "addressdetails": "1",
                "accept-language": "en"
            }
            headers = {
                "User-Agent": "SankalpamApp/1.0"  # Required by Nominatim
            }
            
            response = await client.get(url, params=params, headers=headers)
            data = response.json()
            
            if data.get("address"):
                address = data["address"]
                
                # Extract city (try multiple fields)
                city = (
                    address.get("city") or
                    address.get("town") or
                    address.get("village") or
                    address.get("municipality") or
                    address.get("suburb") or
                    address.get("county") or
                    ""
                )
                
                # Extract state
                state = (
                    address.get("state") or
                    address.get("region") or
                    address.get("province") or
                    ""
                )
                
                # Extract country
                country = address.get("country", "")
                
                if city or state or country:
                    return {
                        "city": city,
                        "state": state,
                        "country": country
                    }
    except Exception as e:
        print(f"Error with OpenStreetMap geocoding: {e}")
    
    # Fallback to Google Maps if API key is configured
    try:
        if settings.google_maps_api_key:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = "https://maps.googleapis.com/maps/api/geocode/json"
                params = {
                    "latlng": f"{lat},{lon}",
                    "key": settings.google_maps_api_key
                }
                
                response = await client.get(url, params=params)
                data = response.json()
                
                if data.get("status") != "OK":
                    print(f"Geocoding API error: {data.get('status')} - {data.get('error_message', '')}")
                    return {"city": "", "state": "", "country": ""}
                
                if data.get("results"):
                    result = data["results"][0]
                    address_components = result.get("address_components", [])
                    
                    # Build a comprehensive mapping of all types to values
                    components_map = {}
                    for component in address_components:
                        types = component.get("types", [])
                        long_name = component.get("long_name", "")
                        
                        # Map all types to the long_name
                        for comp_type in types:
                            if comp_type not in components_map:
                                components_map[comp_type] = long_name
                    
                    # Extract city (try multiple possible types)
                    city = (
                        components_map.get("locality") or
                        components_map.get("sublocality") or
                        components_map.get("sublocality_level_1") or
                        components_map.get("administrative_area_level_3") or
                        components_map.get("administrative_area_level_2") or
                        ""
                    )
                    
                    # Extract state (administrative_area_level_1)
                    state = components_map.get("administrative_area_level_1", "")
                    
                    # Extract country
                    country = components_map.get("country", "")
                    
                    return {
                        "city": city,
                        "state": state,
                        "country": country
                    }
    except Exception as e:
        print(f"Error with Google Maps geocoding: {e}")
        import traceback
        traceback.print_exc()
    
    return {"city": "", "state": "", "country": ""}


async def get_coordinates_from_place(
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """
    Forward geocode: get latitude and longitude for a place (city, state, country).
    Uses Nominatim (OpenStreetMap). Returns {"latitude": str or None, "longitude": str or None}.
    """
    result: Dict[str, Optional[str]] = {"latitude": None, "longitude": None}
    city = (city or "").strip()
    state = (state or "").strip()
    country = (country or "").strip()
    if not city and not state and not country:
        return result
    query = ", ".join(filter(None, [city, state, country]))
    if not query:
        return result
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = "https://nominatim.openstreetmap.org/search"
            params = {"q": query, "format": "json", "limit": "1"}
            headers = {"User-Agent": "SankalpamApp/1.0"}
            response = await client.get(url, params=params, headers=headers)
        if response.status_code != 200:
            return result
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            first = data[0]
            lat = first.get("lat")
            lon = first.get("lon")
            if lat is not None and lon is not None:
                result["latitude"] = str(lat)
                result["longitude"] = str(lon)
    except Exception as e:
        print(f"Forward geocode error: {e}")
    return result
