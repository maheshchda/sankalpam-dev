from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from pathlib import Path
from typing import Optional

from app.database import get_db
from app.models import User, PoojaSession, FamilyMember, Language
from app.schemas import SankalpamRequest, SankalpamResponse
from app.dependencies import get_current_active_user
from app.config import settings
from app.services.location_service import get_nearby_geographical_features
from app.services.divineapi_service import generate_sankalpam
from app.services.tts_service import text_to_speech

router = APIRouter()

@router.post("/generate", response_model=SankalpamResponse)
async def generate_sankalpam_for_pooja(
    request: SankalpamRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Ensure we have the latest user profile (including preferred_language) from the DB
    db.refresh(current_user)

    # Verify session exists and load pooja for name (Telugu template uses pooja_name)
    session = db.query(PoojaSession).filter(
        PoojaSession.id == request.session_id,
        PoojaSession.user_id == current_user.id
    ).options(joinedload(PoojaSession.pooja)).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Pooja session not found"
        )
    pooja_name = session.pooja.name if session.pooja else None
    
    # Get nearby geographical features (river, mountain, sea, ocean)
    geo_features = await get_nearby_geographical_features(
        lat=request.latitude,
        lon=request.longitude,
        city=request.location_city,
        state=request.location_state,
        country=request.location_country,
    )

    nearby_river = geo_features.get("river") or (
        "Ganga" if request.location_country.lower() == "india" else "Sacred River"
    )
    
    # Get user's family members for sankalpam
    family_members = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()

    # Language: request (pooja page dropdown) overrides user profile
    if request.language_code and request.language_code.strip():
        try:
            lang_enum = Language.from_code(request.language_code.strip())
            lang_value = lang_enum.value
            lang_code = lang_enum.code
        except (ValueError, KeyError):
            pref = getattr(current_user, "preferred_language", None)
            if pref is not None:
                lang_value = pref.value
                lang_code = pref.code
            else:
                lang_value = "sanskrit"
                lang_code = "sa"
    else:
        pref = getattr(current_user, "preferred_language", None)
        if pref is not None:
            lang_value = pref.value
            lang_code = pref.code
        else:
            lang_value = "sanskrit"
            lang_code = "sa"
    force_telugu = lang_code == "te"

    sankalpam_text = await generate_sankalpam(
        user=current_user,
        family_members=family_members,
        location_city=request.location_city,
        location_state=request.location_state,
        location_country=request.location_country,
        nearby_river=nearby_river,
        language=lang_value,
        language_code=lang_code,
        pooja_name=pooja_name,
        nearby_mountain=geo_features.get("mountain"),
        nearby_sea=geo_features.get("sea"),
        nearby_ocean=geo_features.get("ocean"),
        primary_geographical_feature=geo_features.get("primary_feature"),
        latitude=request.latitude,
        longitude=request.longitude,
        timezone_offset_hours=request.timezone_offset_hours,
        force_telugu=force_telugu,
    )

    # If user selected Telugu but got Sanskrit/Hindi (e.g. Divine API returned wrong language), retry with force_telugu
    def is_sanskrit_or_hindi(t: str) -> bool:
        if not t:
            return False
        return (
            any("\u0900" <= c <= "\u097f" for c in t)
            or "ॐ" in t
            or "[पूजा का नाम यहाँ]" in t
        )
    if lang_code == "te" and sankalpam_text and is_sanskrit_or_hindi(sankalpam_text):
        sankalpam_text = await generate_sankalpam(
            user=current_user,
            family_members=family_members,
            location_city=request.location_city,
            location_state=request.location_state,
            location_country=request.location_country,
            nearby_river=nearby_river,
            language="telugu",
            language_code="te",
            pooja_name=pooja_name,
            nearby_mountain=geo_features.get("mountain"),
            nearby_sea=geo_features.get("sea"),
            nearby_ocean=geo_features.get("ocean"),
            primary_geographical_feature=geo_features.get("primary_feature"),
            latitude=request.latitude,
            longitude=request.longitude,
            timezone_offset_hours=request.timezone_offset_hours,
            force_telugu=True,
        )

    # Update session with sankalpam data
    session.nearby_river = nearby_river
    session.sankalpam_text = sankalpam_text
    session.status = "ready"

    # Generate audio (TTS) so playback is hearable; skip on failure so text still works
    sankalpam_audio_url = None
    try:
        audio_path = await text_to_speech(
            text=sankalpam_text,
            language=lang_value,
            slow=False,
        )
        if audio_path:
            sankalpam_audio_url = f"/audio/{Path(audio_path).name}"
            session.sankalpam_audio_url = sankalpam_audio_url
    except Exception as e:
        print(f"[Sankalpam] TTS failed (audio will be unavailable): {e}")

    db.commit()

    return SankalpamResponse(
        sankalpam_text=sankalpam_text,
        nearby_river=nearby_river,
        session_id=session.id,
        sankalpam_audio_url=sankalpam_audio_url,
    )

