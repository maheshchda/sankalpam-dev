from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, FamilyMember, _gen_uid
from app.schemas import FamilyMemberCreate, FamilyMemberResponse
from app.dependencies import get_current_user
from app.services.divineapi_service import fetch_death_panchang

router = APIRouter()

# Relations where only one member is allowed per user
UNIQUE_RELATIONS = {
    "Wife", "Father", "Mother",
    "Grand Paternal Father", "Grand Paternal Mother",
    "Great Grand Paternal Father", "Great Grand Paternal Mother",
    "Grand Maternal Father", "Grand Maternal Mother",
    "Great Grand Maternal Father", "Great Grand Maternal Mother",
}


async def _fill_death_panchang(member: FamilyMember, db: Session) -> None:
    """
    Call Divine API to get panchang for the death date and save to member.
    Safe to call as a background task — uses its own db operation.
    """
    if not member.is_deceased or not member.date_of_death:
        return
    try:
        result = await fetch_death_panchang(
            date_of_death=member.date_of_death,
            death_city=member.death_city or "",
            death_state=member.death_state or "",
            death_country=member.death_country or "",
            time_of_death=member.time_of_death,
        )
        if result:
            # Store plain tithi name only (e.g. "Ekadashi" not "Krishna Ekadashi")
            raw_tithi = result.get("tithi") or ""
            # Strip leading paksha word if present (e.g. "Krishna Ekadashi" -> "Ekadashi")
            tithi_parts = raw_tithi.strip().split()
            plain_tithi = (tithi_parts[-1] if len(tithi_parts) > 1
                           and tithi_parts[0].lower() in ("shukla", "krishna", "bahula", "sukla")
                           else raw_tithi) or None

            member.death_tithi     = plain_tithi
            member.death_paksha    = result.get("paksha")    or None
            member.death_nakshatra = result.get("nakshatra") or None
            member.death_vara      = result.get("vara")      or None
            member.death_yoga      = result.get("yoga")      or None
            member.death_karana    = result.get("karana")    or None
            db.commit()
            print(f"[Family] Death panchang saved for member {member.id}: {result}")
    except Exception as exc:
        print(f"[Family] Error fetching death panchang for member {member.id}: {exc}")


@router.post("/members", response_model=FamilyMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_family_member(
    member_data: FamilyMemberCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new family member for the current user."""
    if member_data.relation in UNIQUE_RELATIONS:
        existing = (
            db.query(FamilyMember)
            .filter(
                FamilyMember.user_id == current_user.id,
                FamilyMember.relation == member_data.relation,
            )
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"You already have a '{member_data.relation}' in your family. Only one is allowed.",
            )

    # Resolve unique_id: use caller-supplied value, or auto-generate FM-XXXXXXXX
    supplied_uid = (member_data.unique_id or "").strip().upper() or None
    if supplied_uid:
        if db.query(FamilyMember).filter(FamilyMember.unique_id == supplied_uid).first():
            raise HTTPException(status_code=400, detail=f"Unique ID '{supplied_uid}' is already in use.")
        fmid = supplied_uid
    else:
        fmid = _gen_uid('FM')
        while db.query(FamilyMember).filter(FamilyMember.unique_id == fmid).first():
            fmid = _gen_uid('FM')

    db_member = FamilyMember(
        unique_id=fmid,
        linked_user_id=(member_data.linked_user_id or "").strip().upper() or None,
        user_id=current_user.id,
        name=member_data.name,
        last_name=member_data.last_name or None,
        relation=member_data.relation,
        gender=member_data.gender,
        date_of_birth=member_data.date_of_birth,
        birth_time=member_data.birth_time,
        birth_nakshatra=member_data.birth_nakshatra,
        birth_rashi=member_data.birth_rashi,
        birth_pada=getattr(member_data, "birth_pada", None),
        birth_city=member_data.birth_city,
        birth_state=member_data.birth_state,
        birth_country=member_data.birth_country,
        is_deceased=member_data.is_deceased,
        date_of_death=member_data.date_of_death if member_data.is_deceased else None,
        time_of_death=member_data.time_of_death if member_data.is_deceased else None,
        death_city=member_data.death_city if member_data.is_deceased else None,
        death_state=member_data.death_state if member_data.is_deceased else None,
        death_country=member_data.death_country if member_data.is_deceased else None,
    )

    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    if db_member.is_deceased and db_member.date_of_death:
        background_tasks.add_task(_fill_death_panchang, db_member, db)

    return db_member


@router.get("/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all family members for the current user."""
    members = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()
    return members


@router.get("/members/{member_id}", response_model=FamilyMemberResponse)
async def get_family_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single family member by id (must belong to current user)."""
    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.user_id == current_user.id)
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Family member not found",
        )

    return member


@router.put("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_family_member(
    member_id: int,
    member_data: FamilyMemberCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing family member.

    For simplicity we reuse FamilyMemberCreate schema and expect all fields.
    """
    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.user_id == current_user.id)
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Family member not found",
        )

    member.name = member_data.name
    member.last_name = member_data.last_name or None
    member.linked_user_id = (member_data.linked_user_id or "").strip().upper() or None
    member.relation = member_data.relation
    member.gender = member_data.gender
    member.date_of_birth = member_data.date_of_birth
    member.birth_time = member_data.birth_time
    member.birth_nakshatra = member_data.birth_nakshatra
    member.birth_rashi = member_data.birth_rashi
    if hasattr(member_data, "birth_pada"):
        member.birth_pada = member_data.birth_pada
    member.birth_city = member_data.birth_city
    member.birth_state = member_data.birth_state
    member.birth_country = member_data.birth_country
    member.is_deceased = member_data.is_deceased
    member.date_of_death = member_data.date_of_death if member_data.is_deceased else None
    member.time_of_death = member_data.time_of_death if member_data.is_deceased else None
    member.death_city = member_data.death_city if member_data.is_deceased else None
    member.death_state = member_data.death_state if member_data.is_deceased else None
    member.death_country = member_data.death_country if member_data.is_deceased else None

    # Clear old panchang if deceased status removed or date changed
    if not member_data.is_deceased:
        member.death_tithi = member.death_paksha = member.death_nakshatra = None
        member.death_vara  = member.death_yoga   = member.death_karana    = None

    db.commit()
    db.refresh(member)

    if member.is_deceased and member.date_of_death:
        background_tasks.add_task(_fill_death_panchang, member, db)

    return member


@router.post("/members/{member_id}/update", response_model=FamilyMemberResponse)
async def update_family_member_post(
    member_id: int,
    member_data: FamilyMemberCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """POST alias for PUT update (compatibility)."""
    return await update_family_member(
        member_id=member_id,
        member_data=member_data,
        background_tasks=background_tasks,
        current_user=current_user,
        db=db,
    )


@router.post("/members/backfill-death-panchang", status_code=200)
async def backfill_death_panchang(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    For all deceased family members of the current user that have a date_of_death
    but are missing death panchang fields, call Divine API to fill them in.
    """
    members = (
        db.query(FamilyMember)
        .filter(
            FamilyMember.user_id == current_user.id,
            FamilyMember.is_deceased == True,
            FamilyMember.date_of_death != None,
        )
        .all()
    )
    filled = 0
    skipped = 0
    for member in members:
        # Skip if already has panchang data
        if member.death_tithi and member.death_nakshatra and member.death_vara:
            skipped += 1
            continue
        await _fill_death_panchang(member, db)
        filled += 1

    return {"filled": filled, "skipped": skipped, "total": len(members)}


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_family_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a family member belonging to the current user."""
    member = (
        db.query(FamilyMember)
        .filter(FamilyMember.id == member_id, FamilyMember.user_id == current_user.id)
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Family member not found",
        )

    db.delete(member)
    db.commit()

    return None

