"""
DivineAPI Panchang Service
Integrates with DivineAPI Panchang API to get accurate astronomical data

Based on DivineAPI documentation:
- Documentation: https://developers.divineapi.com/divine-api
- Support: support@divineapi.com
"""
import httpx
from datetime import datetime
from typing import Dict, Optional
from app.config import settings

async def get_panchang_from_divineapi(
    date: datetime,
    latitude: float,
    longitude: float,
    timezone: Optional[str] = None
) -> Optional[Dict[str, str]]:
    """
    Fetch panchangam data from DivineAPI Panchang API
    
    Returns dictionary with:
    - tithi (lunar day)
    - nakshatra (star constellation)
    - yoga (auspicious combination)
    - karana (half tithi)
    - paksha (shukla/krishna)
    - sunrise, sunset
    - And other panchang details
    
    Returns None if API call fails or not configured
    
    NOTE: Update endpoint URL, authentication method, and response parsing
    based on actual DivineAPI documentation at https://developers.divineapi.com/divine-api
    """
    
    # Use API Key or Access Token (check which one DivineAPI requires)
    api_key = settings.divine_api_key or settings.divineapi_key
    access_token = settings.divine_access_token
    
    if not api_key and not access_token:
        print("DivineAPI credentials not configured")
        return None
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # TODO: Update endpoint based on actual DivineAPI documentation
            # Check: https://developers.divineapi.com/divine-api for exact endpoint
            # Typical format might be: /v1/panchang or /v1/indian-astrology/panchang
            base_url = settings.divineapi_base_url
            url = f"{base_url}/v1/panchang"  # UPDATE THIS based on documentation
            
            # Prepare request parameters
            # TODO: Adjust parameter format based on actual API documentation
            params = {
                "date": date.strftime("%Y-%m-%d"),  # Format: YYYY-MM-DD or check docs
                "latitude": latitude,
                "longitude": longitude,
            }
            
            if timezone:
                params["timezone"] = timezone
            else:
                # Default to UTC if not provided
                params["timezone"] = "UTC"
            
            # Headers - TODO: Check actual authentication method from documentation
            # Usually Bearer token or API key in header
            headers = {
                "Content-Type": "application/json",
            }
            
            # Authentication - try Access Token first, then API Key
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
            elif api_key:
                headers["Authorization"] = f"Bearer {api_key}"
                # Alternative: headers["X-API-Key"] = api_key
                # Check documentation for exact format!
            
            print(f"Calling DivineAPI Panchang: {url} with params: {params}")
            response = await client.get(url, params=params, headers=headers)
            
            print(f"DivineAPI Panchang response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"DivineAPI Panchang response: {data}")
                # Parse DivineAPI response and return formatted data
                return parse_panchang_response(data)
            else:
                print(f"DivineAPI Panchang API error: {response.status_code} - {response.text}")
                return None
                
    except Exception as e:
        print(f"Error calling DivineAPI Panchang API: {e}")
        import traceback
        traceback.print_exc()
        return None

def parse_panchang_response(data: dict) -> Dict[str, str]:
    """
    Parse DivineAPI Panchang response and convert to our format
    
    TODO: Adjust field names based on actual API response structure
    Typical response might have:
    - tithi, nakshatra, yoga, karana
    - paksha (shukla/krishna)
    - sunrise, sunset
    - etc.
    
    Common field name variations to check:
    - tithi / tithi_name / lunar_day
    - nakshatra / nakshatra_name / star
    - yoga / yoga_name
    - karana / karana_name
    - paksha / paksh / lunar_phase
    """
    # This is a template - adjust field names based on actual API response
    # Print the response first to see the structure
    print(f"Parsing DivineAPI response structure: {list(data.keys())}")
    
    return {
        "tithi": data.get("tithi") or data.get("tithi_name") or data.get("lunar_day", ""),
        "nakshatra": data.get("nakshatra") or data.get("nakshatra_name") or data.get("star", ""),
        "yoga": data.get("yoga") or data.get("yoga_name", ""),
        "karana": data.get("karana") or data.get("karana_name", ""),
        "pakshE": data.get("paksha") or data.get("paksh") or data.get("lunar_phase", ""),
        "sunrise": data.get("sunrise") or data.get("sunrise_time", ""),
        "sunset": data.get("sunset") or data.get("sunset_time", ""),
        # Add other fields as needed based on API response
    }
