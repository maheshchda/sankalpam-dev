"""
Router for generating Sankalpam audio from templates.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pathlib import Path
import json

from app.database import get_db
from app.models import User, SankalpamTemplate, PoojaSession, FamilyMember, Language
from app.schemas import TemplateGenerateRequest, TemplateGenerateResponse
from app.dependencies import get_current_active_user, get_current_user
from app.services.template_service import (
    get_all_variables,
    replace_template_variables,
    is_telugu_template_language,
)
from app.services.sankalpa_family_builder import filter_family_participants
from app.services.tts_service import text_to_speech
from app.services.location_service import get_location_from_coordinates, get_coordinates_from_place
from app.services.divineapi_service import _resolve_coords_for_panchang
from app.services.geonames_service import (
    GeoNamesError,
    find_nearby_features,
    find_nearby_place_name,
    ocean,
    search_natural_features,
)
from app.config import settings
router = APIRouter()

@router.get("/reverse-geocode")
async def reverse_geocode_location(
    latitude: str,
    longitude: str,
    current_user: User = Depends(get_current_user)
):
    """
    Reverse geocode coordinates to get city, state, country
    Uses OpenStreetMap Nominatim (FREE, no API key needed)
    """
    try:
        location_data = await get_location_from_coordinates(latitude, longitude)
        # Always return the data, even if empty - let frontend handle empty values
        return location_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reverse geocoding: {str(e)}"
        )


@router.get("/forward-geocode")
async def forward_geocode_location(
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    Forward geocode: get latitude and longitude for a place (city, state, country).
    Query params: city, state, country. Returns { latitude, longitude }.
    """
    result = await get_coordinates_from_place(city=city, state=state, country=country)
    return result


@router.get("/geonames-test")
async def geonames_test(
    latitude: str,
    longitude: str,
    current_user: User = Depends(get_current_user),
):
    """
    Test endpoint to verify GeoNames is reachable and your GEONAMES_USERNAME works.
    Returns:
      - nearest place (findNearbyPlaceName)
      - ocean (oceanJSON) when applicable
      - nearby raw features (findNearbyJSON)
    """
    try:
        lat = float(latitude)
        lon = float(longitude)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid latitude/longitude.")

    try:
        place = await find_nearby_place_name(lat, lon)
        try:
            oc = await ocean(lat, lon)
        except GeoNamesError:
            # Inland coords often have no ocean; keep response usable.
            oc = None

        # Raw nearby (often buildings/hotels). Kept for debugging.
        features_raw = await find_nearby_features(lat, lon, radius_km=30.0, max_rows=20)

        # Natural-only nearby results suitable for Sankalpam geography lines.
        natural = await search_natural_features(lat, lon, radius_km=60.0, max_rows=20)

        return {
            "username_configured": bool((settings.geonames_username or "").strip()),
            "place": place,
            "ocean": oc,
            "features_raw": features_raw,
            "natural_features": natural,
        }
    except GeoNamesError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/generate", response_model=TemplateGenerateResponse)
async def generate_audio_from_template(
    request: TemplateGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate audio file from a Sankalpam template.
    
    Steps:
    1. Load the template text from database
    2. Gather all variables (user data, astronomical data, location data)
    3. Replace variables in template text
    4. Convert text to speech audio
    5. Return audio URL and generated text
    """
    try:
        print(f"=== GENERATE SANKKALPAM REQUEST ===")
        print(f"User: {current_user.username}")
        print(f"Template ID: {request.template_id}")
        print(f"Location: {request.location_city}, {request.location_state}, {request.location_country}")
        
        # Get template
        template = db.query(SankalpamTemplate).filter(
            SankalpamTemplate.id == request.template_id,
            SankalpamTemplate.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail="Template not found or inactive"
            )
        
        # Get session if provided
        session = None
        if request.session_id:
            session = db.query(PoojaSession).filter(
                PoojaSession.id == request.session_id,
                PoojaSession.user_id == current_user.id
            ).first()
            
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail="Pooja session not found"
                )
        
        # Get template text directly (stored in database)
        template_text = template.template_text
        
        # Family members: optional participant list (omit = all); never include deceased
        _all_family = db.query(FamilyMember).filter(
            FamilyMember.user_id == current_user.id
        ).all()
        family_members = filter_family_participants(
            _all_family, request.participant_member_ids
        )
        
        # Get pooja name if session exists
        pooja_name = None
        if session and session.pooja:
            pooja_name = session.pooja.name
        elif request.pooja_name:
            pooja_name = request.pooja_name
        
        # Parse latitude/longitude
        latitude = float(request.latitude) if request.latitude else None
        longitude = float(request.longitude) if request.longitude else None
        
        # If coordinates are provided, automatically get location from them
        location_city = request.location_city
        location_state = request.location_state
        location_country = request.location_country
        
        if latitude and longitude:
            try:
                location_data = await get_location_from_coordinates(str(latitude), str(longitude))
                # Use coordinates-based location if available, otherwise fall back to provided location
                if location_data.get("city"):
                    location_city = location_data["city"]
                if location_data.get("state"):
                    location_state = location_data["state"]
                if location_data.get("country"):
                    location_country = location_data["country"]
            except Exception as e:
                print(f"Error getting location from coordinates: {e}")
                # Fall back to provided location if geocoding fails

        # Panchang (Divine API) needs coordinates: geocode from city when browser did not send GPS
        if (latitude is None or longitude is None) and (location_city or "").strip() and (location_country or "").strip():
            try:
                rl, rr = await _resolve_coords_for_panchang(
                    (location_city or "").strip(),
                    (location_state or "").strip(),
                    (location_country or "").strip(),
                )
                if rl and rr:
                    latitude = float(rl)
                    longitude = float(rr)
            except (ValueError, TypeError) as e:
                print(f"Could not resolve coordinates for panchang: {e}")

        # Use provided date or current date
        # For Sankalpam, we want the local date at the location, not UTC
        # So we use naive datetime which represents local time
        if request.date:
            date = request.date
        else:
            # Use naive datetime (represents local system time)
            # This ensures weekday calculation is correct for the user's location
            date = datetime.now()
        
        # Gather all variables (pass template language for proper script generation)
        try:
            template_lang = template.language.value if hasattr(template.language, 'value') else str(template.language)
            print(f"Gathering variables for template language: {template_lang}")

            _slc = (request.sankalpam_language_code or "").strip().lower()
            output_telugu_preference: Optional[bool] = None
            if _slc in ("te", "telugu") or "telugu" in _slc:
                output_telugu_preference = True

            variables = await get_all_variables(
                user=current_user,
                family_members=family_members,
                location_city=location_city,
                location_state=location_state,
                location_country=location_country,
                latitude=latitude,
                longitude=longitude,
                date=date,
                pooja_name=pooja_name,
                template_language=template_lang,
                template_language_enum=template.language,
                override_gotram=request.override_gotram,
                override_birth_nakshatra=request.override_birth_nakshatra,
                override_birth_rashi=request.override_birth_rashi,
                sankalpa_intent=request.sankalpa_intent,
                output_telugu_preference=output_telugu_preference,
            )
            print(f"Variables gathered successfully. Count: {len(variables)}")
        except Exception as e:
            print(f"Error gathering variables: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Error gathering variables: {str(e)}"
            )
        
        # Replace variables in template text
        try:
            print(f"Replacing variables in template text (length: {len(template_text)})")
            final_text = await replace_template_variables(template_text, variables)
            print(f"Variables replaced. Final text length: {len(final_text)}")
        except Exception as e:
            print(f"Error replacing variables: {e}")
            import traceback
            traceback.print_exc()
            raise HTTPException(
                status_code=500,
                detail=f"Error replacing variables in template: {str(e)}"
            )
        
        # Generate audio file
        try:
            _tl = template.language.value if isinstance(template.language, Language) else str(template.language)
            _effective_te = output_telugu_preference is True or is_telugu_template_language(
                template_lang, template.language
            )
            tts_language = Language.TELUGU.value if _effective_te else _tl
            audio_path = await text_to_speech(
                text=final_text,
                language=tts_language,
                slow=False  # Set to True for slower speech if needed
            )
            
            # Generate URL for audio file (relative to static files or full URL)
            # In production, you might upload to S3 or CDN and return full URL
            audio_url = f"/audio/{Path(audio_path).name}"
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating audio: {str(e)}"
            )
        
        # Update session if provided
        if session:
            session.sankalpam_text = final_text
            session.sankalpam_audio_url = audio_url
            db.commit()
        
        return TemplateGenerateResponse(
            text=final_text,
            audio_url=audio_url,
            variables_used=variables,
            session_id=request.session_id
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"=== UNEXPECTED ERROR IN GENERATE ===")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/templates", response_model=list)
async def get_active_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of active templates available for users
    """
    templates = db.query(SankalpamTemplate).filter(
        SankalpamTemplate.is_active == True
    ).all()
    
    # Return simplified template info (without file paths)
    result = []
    for t in templates:
        # Always expose enum .value (e.g. telugu), never str(Language.TELUGU) repr
        language_value = t.language
        if isinstance(language_value, Language):
            language_value = language_value.value
        elif isinstance(language_value, str):
            language_value = language_value.strip().lower()
        elif hasattr(language_value, 'value'):
            language_value = language_value.value
        else:
            language_value = str(language_value).lower()
        
        result.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "language": language_value,
            "variables": t.variables if isinstance(t.variables, str) else json.dumps(t.variables) if t.variables else "[]"
        })
    
    return result

