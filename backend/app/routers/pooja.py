from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User, Pooja, PoojaSession
from app.schemas import PoojaResponse, PoojaSessionCreate, PoojaSessionResponse
from app.dependencies import get_current_user, get_current_active_user
from app.services.divineapi_service import get_poojas_available_for_language

router = APIRouter()

def _filter_poojas_by_state(poojas, state_code: Optional[str]) -> list:
    """Filter poojas by state. state_code e.g. IN-TN. None/empty = return all."""
    if not state_code or not state_code.strip():
        return poojas
    sc = state_code.strip().upper()
    result = []
    for p in poojas:
        if not p.state_codes:
            result.append(p)  # Pan-India
        else:
            try:
                import json
                codes = json.loads(p.state_codes)
                if sc in (c.upper() for c in codes):
                    result.append(p)
            except (json.JSONDecodeError, TypeError):
                result.append(p)
    return result


@router.get("", response_model=List[PoojaResponse])
@router.get("/list", response_model=List[PoojaResponse])
async def get_poojas(
    language_code: Optional[str] = None,
    state: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List active poojas. Optional: state (e.g. IN-TN) filters by region; language_code
    filters by sankalpam template availability.
    """
    poojas = db.query(Pooja).filter(Pooja.is_active == True).order_by(Pooja.name).all()
    poojas = _filter_poojas_by_state(poojas, state)
    if language_code and language_code.strip():
        poojas = get_poojas_available_for_language(language_code.strip(), poojas)
    return poojas

@router.get("/{pooja_id}", response_model=PoojaResponse)
async def get_pooja(
    pooja_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pooja = db.query(Pooja).filter(
        Pooja.id == pooja_id,
        Pooja.is_active == True
    ).first()
    
    if not pooja:
        raise HTTPException(
            status_code=404,
            detail="Pooja not found"
        )
    
    return pooja

@router.post("/session", response_model=PoojaSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_pooja_session(
    session_data: PoojaSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verify pooja exists
    pooja = db.query(Pooja).filter(
        Pooja.id == session_data.pooja_id,
        Pooja.is_active == True
    ).first()
    
    if not pooja:
        raise HTTPException(
            status_code=404,
            detail="Pooja not found"
        )
    
    db_session = PoojaSession(
        user_id=current_user.id,
        pooja_id=session_data.pooja_id,
        location_city=session_data.location_city,
        location_state=session_data.location_state,
        location_country=session_data.location_country,
        latitude=session_data.latitude,
        longitude=session_data.longitude
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

@router.get("/session/{session_id}", response_model=PoojaSessionResponse)
async def get_pooja_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    session = db.query(PoojaSession).filter(
        PoojaSession.id == session_id,
        PoojaSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Pooja session not found"
        )
    
    return session

