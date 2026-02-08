"""
Router for generating Sankalpam audio from templates
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pathlib import Path
import json

from app.database import get_db
from app.models import User, SankalpamTemplate, PoojaSession, FamilyMember
from app.schemas import TemplateGenerateRequest, TemplateGenerateResponse
from app.dependencies import get_current_active_user, get_current_user
from app.services.template_service import get_all_variables, replace_template_variables
from app.services.tts_service import text_to_speech
from app.services.location_service import get_location_from_coordinates
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
        
        # Get user's family members
        family_members = db.query(FamilyMember).filter(
            FamilyMember.user_id == current_user.id
        ).all()
        
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
            
            variables = await get_all_variables(
                user=current_user,
                family_members=family_members,
                location_city=location_city,
                location_state=location_state,
                location_country=location_country,
                latitude=latitude,
                longitude=longitude,
                date=date,
                pooja_name=pooja_name or "Ganesha Pooja",
                template_language=template_lang
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
            audio_path = await text_to_speech(
                text=final_text,
                language=template.language.value,
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
        # Handle language - it might be an enum or string
        language_value = t.language
        if hasattr(language_value, 'value'):
            language_value = language_value.value
        elif hasattr(language_value, '__str__'):
            language_value = str(language_value)
        
        result.append({
            "id": t.id,
            "name": t.name,
            "description": t.description,
            "language": language_value,
            "variables": t.variables if isinstance(t.variables, str) else json.dumps(t.variables) if t.variables else "[]"
        })
    
    return result

