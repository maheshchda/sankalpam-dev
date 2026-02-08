from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx
from typing import Optional

from app.database import get_db
from app.models import User, PoojaSession, FamilyMember
from app.schemas import SankalpamRequest, SankalpamResponse
from app.dependencies import get_current_active_user
from app.config import settings
from app.services.location_service import get_nearby_rivers
from app.services.divineapi_service import generate_sankalpam

router = APIRouter()

@router.post("/generate", response_model=SankalpamResponse)
async def generate_sankalpam_for_pooja(
    request: SankalpamRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify session exists
    session = db.query(PoojaSession).filter(
        PoojaSession.id == request.session_id,
        PoojaSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Pooja session not found"
        )
    
    # Get nearby river using location services
    nearby_river = await get_nearby_rivers(
        city=request.location_city,
        state=request.location_state,
        country=request.location_country,
        lat=request.latitude,
        lon=request.longitude
    )
    
    # Get user's family members for sankalpam
    family_members = db.query(FamilyMember).filter(
        FamilyMember.user_id == current_user.id
    ).all()
    
    # Generate sankalpam using DivineAPI
    sankalpam_text = await generate_sankalpam(
        user=current_user,
        family_members=family_members,
        location_city=request.location_city,
        location_state=request.location_state,
        location_country=request.location_country,
        nearby_river=nearby_river,
        language=current_user.preferred_language.value
    )
    
    # Update session with sankalpam data
    session.nearby_river = nearby_river
    session.sankalpam_text = sankalpam_text
    session.status = "ready"
    
    db.commit()
    
    return SankalpamResponse(
        sankalpam_text=sankalpam_text,
        nearby_river=nearby_river,
        session_id=session.id
    )

