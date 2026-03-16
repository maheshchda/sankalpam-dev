from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User, FamilyMember, _gen_uid
from app.schemas import FamilyMemberCreate, FamilyMemberResponse, UniqueIdLookupResult, ExtendedFamilyMemberResponse
from app.dependencies import get_current_user
from app.services.divineapi_service import fetch_death_panchang

router = APIRouter()

# Map relation to in-law equivalent when viewing linked family (e.g. spouse's family)
RELATION_TO_INLAW: dict[str, str] = {
    "Father": "Father-in-law",
    "Mother": "Mother-in-law",
    "Brother": "Brother-in-law",
    "Sister": "Sister-in-law",
    "Married Brother": "Brother-in-law",
    "Married Sister": "Sister-in-law",
    "Grand Paternal Father": "Grand Paternal Father-in-law",
    "Grand Paternal Mother": "Grand Paternal Mother-in-law",
    "Grand Maternal Father": "Grand Maternal Father-in-law",
    "Grand Maternal Mother": "Grand Maternal Mother-in-law",
    "Great Grand Paternal Father": "Great Grand Paternal Father-in-law",
    "Great Grand Paternal Mother": "Great Grand Paternal Mother-in-law",
    "Great Grand Maternal Father": "Great Grand Maternal Father-in-law",
    "Great Grand Maternal Mother": "Great Grand Maternal Mother-in-law",
    "Son": "Spouse's Son",
    "Daughter": "Spouse's Daughter",
    "Grand Son": "Spouse's Grand Son",
    "Grand Daughter": "Spouse's Grand Daughter",
    "Great Grand Son": "Spouse's Great Grand Son",
    "Great Grand Daughter": "Spouse's Great Grand Daughter",
}

# Relations where only one member is allowed per user
UNIQUE_RELATIONS = {
    "Wife", "Father", "Mother",
    "Grand Paternal Father", "Grand Paternal Mother",
    "Great Grand Paternal Father", "Great Grand Paternal Mother",
    "Grand Maternal Father", "Grand Maternal Mother",
    "Great Grand Maternal Father", "Great Grand Maternal Mother",
}

# When adding a Brother/Sister by Unique ID, we auto-include shared ancestors and siblings (no in-law mapping)
SIBLING_FAMILY_RELATIONS = {
    "Father", "Mother",
    "Brother", "Sister",
    "Married Brother", "Married Sister",
    "Grand Paternal Father", "Grand Paternal Mother",
    "Grand Maternal Father", "Grand Maternal Mother",
    "Great Grand Paternal Father", "Great Grand Paternal Mother",
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


@router.get("/lookup/{unique_id}", response_model=UniqueIdLookupResult)
async def lookup_by_unique_id(
    unique_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Look up by Unique ID to pre-fill family member form.
    PS-xxx: returns User info (linked_user_id set).
    FM-xxx: returns FamilyMember info (source_unique_id set) — their whole family can be pulled into your tree.
    """
    uid = (unique_id or "").strip().upper()
    if not uid:
        raise HTTPException(status_code=400, detail="Unique ID is required.")

    # Try User first (PS-xxx)
    user = db.query(User).filter(User.unique_id == uid).first()
    if user:
        if user.id == current_user.id:
            raise HTTPException(status_code=400, detail="You cannot link yourself as a family member.")
        return UniqueIdLookupResult(
            type="user",
            unique_id=uid,
            first_name=user.first_name,
            last_name=user.last_name or None,
            birth_city=user.birth_city or "",
            birth_state=user.birth_state or "",
            birth_country=user.birth_country or "",
            birth_date=user.birth_date.date() if user.birth_date else None,
            birth_time=user.birth_time,
            birth_nakshatra=user.birth_nakshatra,
            birth_rashi=user.birth_rashi,
            birth_pada=user.birth_pada,
            linked_user_id=uid,
        )

    # Try FamilyMember (FM-xxx)
    fm = db.query(FamilyMember).filter(FamilyMember.unique_id == uid).first()
    if fm:
        # Don't allow linking if they're already in the current user's tree
        if fm.user_id == current_user.id:
            raise HTTPException(status_code=400, detail="This person is already in your family tree.")
        return UniqueIdLookupResult(
            type="family_member",
            unique_id=uid,
            first_name=fm.name,
            last_name=fm.last_name or None,
            birth_city=fm.birth_city or "",
            birth_state=fm.birth_state or "",
            birth_country=fm.birth_country or "",
            birth_date=fm.date_of_birth.date() if fm.date_of_birth else None,
            birth_time=fm.birth_time,
            birth_nakshatra=fm.birth_nakshatra,
            birth_rashi=fm.birth_rashi,
            birth_pada=fm.birth_pada,
            source_unique_id=uid,
        )

    raise HTTPException(status_code=404, detail="No account or family member found with that Unique ID.")


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

    # Resolve unique_id: when adding by Unique ID (linked_user_id or source_unique_id), always generate FM-xxx.
    # Otherwise use caller-supplied value or auto-generate.
    has_link = bool((member_data.linked_user_id or "").strip()) or bool((member_data.source_unique_id or "").strip())
    if has_link:
        fmid = _gen_uid('FM')
        while db.query(FamilyMember).filter(FamilyMember.unique_id == fmid).first():
            fmid = _gen_uid('FM')
    else:
        supplied_uid = (member_data.unique_id or "").strip().upper() or None
        if supplied_uid:
            if db.query(FamilyMember).filter(FamilyMember.unique_id == supplied_uid).first():
                raise HTTPException(status_code=400, detail=f"Unique ID '{supplied_uid}' is already in use.")
            fmid = supplied_uid
        else:
            fmid = _gen_uid('FM')
            while db.query(FamilyMember).filter(FamilyMember.unique_id == fmid).first():
                fmid = _gen_uid('FM')

    # When adding by Unique ID: store only reference (no data copy). Display always fetches from source.
    if has_link:
        link_name, link_last, link_city, link_state, link_country = "—", None, "—", "—", "—"
    else:
        link_name = member_data.name
        link_last = member_data.last_name or None
        link_city = member_data.birth_city
        link_state = member_data.birth_state
        link_country = member_data.birth_country

    db_member = FamilyMember(
        unique_id=fmid,
        linked_user_id=(member_data.linked_user_id or "").strip().upper() or None,
        source_unique_id=(member_data.source_unique_id or "").strip().upper() or None,
        user_id=current_user.id,
        name=link_name,
        last_name=link_last,
        relation=member_data.relation,
        gender=member_data.gender,
        date_of_birth=None if has_link else member_data.date_of_birth,
        birth_time=None if has_link else member_data.birth_time,
        birth_nakshatra=None if has_link else member_data.birth_nakshatra,
        birth_rashi=None if has_link else member_data.birth_rashi,
        birth_pada=None if has_link else getattr(member_data, "birth_pada", None),
        birth_city=link_city,
        birth_state=link_state,
        birth_country=link_country,
        is_deceased=False if has_link else member_data.is_deceased,
        date_of_death=None if has_link else (member_data.date_of_death if member_data.is_deceased else None),
        time_of_death=None if has_link else (member_data.time_of_death if member_data.is_deceased else None),
        death_city=None if has_link else (member_data.death_city if member_data.is_deceased else None),
        death_state=None if has_link else (member_data.death_state if member_data.is_deceased else None),
        death_country=None if has_link else (member_data.death_country if member_data.is_deceased else None),
    )

    db.add(db_member)
    db.commit()
    db.refresh(db_member)

    if db_member.is_deceased and db_member.date_of_death:
        background_tasks.add_task(_fill_death_panchang, db_member, db)

    resolved = _resolve_linked_member(db_member, db)
    return resolved


def _resolve_linked_member(m: FamilyMember, db: Session) -> FamilyMember:
    """
    For members with linked_user_id or source_unique_id, return a copy with display data
    resolved from the source (no data copy in DB — we fetch live when displaying).
    """
    if not m.linked_user_id and not m.source_unique_id:
        return m
    if m.linked_user_id:
        u = db.query(User).filter(User.unique_id == m.linked_user_id).first()
        if u:
            # Build a display copy from User source (don't mutate m)
            m2 = FamilyMember(
                id=m.id, unique_id=m.unique_id, linked_user_id=m.linked_user_id,
                source_unique_id=m.source_unique_id, user_id=m.user_id,
                name=u.first_name, last_name=u.last_name or None,
                relation=m.relation, gender=m.gender,
                date_of_birth=u.birth_date, birth_time=u.birth_time,
                birth_nakshatra=u.birth_nakshatra, birth_rashi=u.birth_rashi, birth_pada=u.birth_pada,
                birth_city=u.birth_city or "—", birth_state=u.birth_state or "—", birth_country=u.birth_country or "—",
                is_deceased=False, date_of_death=None, time_of_death=None,
                death_city=None, death_state=None, death_country=None,
                death_tithi=None, death_paksha=None, death_nakshatra=None,
                death_vara=None, death_yoga=None, death_karana=None,
                created_at=m.created_at, updated_at=m.updated_at,
            )
            return m2
    if m.source_unique_id:
        src = db.query(FamilyMember).filter(FamilyMember.unique_id == m.source_unique_id).first()
        if src:
            src = _resolve_linked_member(src, db)  # resolve chain (e.g. FM -> User)
            m2 = FamilyMember(
                id=m.id, unique_id=m.unique_id, linked_user_id=m.linked_user_id,
                source_unique_id=m.source_unique_id, user_id=m.user_id,
                name=src.name, last_name=src.last_name,
                relation=m.relation, gender=m.gender,
                date_of_birth=src.date_of_birth, birth_time=src.birth_time,
                birth_nakshatra=src.birth_nakshatra, birth_rashi=src.birth_rashi, birth_pada=src.birth_pada,
                birth_city=src.birth_city or "—", birth_state=src.birth_state or "—", birth_country=src.birth_country or "—",
                is_deceased=src.is_deceased, date_of_death=src.date_of_death, time_of_death=src.time_of_death,
                death_city=src.death_city, death_state=src.death_state, death_country=src.death_country,
                death_tithi=src.death_tithi, death_paksha=src.death_paksha, death_nakshatra=src.death_nakshatra,
                death_vara=src.death_vara, death_yoga=src.death_yoga, death_karana=src.death_karana,
                created_at=m.created_at, updated_at=m.updated_at,
            )
            return m2
    return m


def _member_to_extended(m: FamilyMember, source: str = "own", linked_via: Optional[str] = None, db: Optional[Session] = None) -> ExtendedFamilyMemberResponse:
    display = _resolve_linked_member(m, db) if db and (m.linked_user_id or m.source_unique_id) else m
    d = ExtendedFamilyMemberResponse.model_validate(display)
    d.source = source
    d.linked_via = linked_via
    return d


def _fetch_and_add_linked_family(
    db: Session,
    current_user_id: int,
    current_user_unique_id: Optional[str],
    target_user_id: int,
    linked_via: str,
    exclude_unique_id: Optional[str],
    is_sibling: bool,
    seen_ids: set[str],
    owned_relations: set[str],
    result: list,
    fetched_user_ids: Optional[set[int]] = None,
) -> None:
    """
    Fetch target_user's family and append to result. Recursively fetches nested links
    (e.g. Brother's Wife's family) so that when your brother adds you, your wife's
    family shows up in his tree.
    """
    fetched = fetched_user_ids or set()
    if target_user_id in fetched:
        return  # avoid cycles (e.g. Wife -> Husband -> Wife)
    fetched.add(target_user_id)

    others = db.query(FamilyMember).filter(FamilyMember.user_id == target_user_id).all()

    for o in others:
        if o.linked_user_id == current_user_unique_id:
            continue  # skip — that's us
        if exclude_unique_id and o.unique_id == exclude_unique_id:
            continue  # skip — the person we're linking from (avoid duplicate)
        uid = o.unique_id or f"fm-{o.id}"
        if uid in seen_ids:
            continue

        if is_sibling:
            if o.relation not in SIBLING_FAMILY_RELATIONS:
                continue
            mapped_rel = o.relation
            if o.relation in UNIQUE_RELATIONS and o.relation in owned_relations:
                continue
        else:
            mapped_rel = RELATION_TO_INLAW.get(o.relation, o.relation)

        seen_ids.add(uid)
        ext = _member_to_extended(o, source="linked", linked_via=linked_via, db=db_session)
        ext.relation = mapped_rel
        result.append(ext)

        # Recursively fetch this person's family if they have a link (e.g. Brother's Wife → Wife's family)
        if o.linked_user_id or o.source_unique_id:
            nested_user_id: Optional[int] = None
            if o.linked_user_id:
                u = db.query(User).filter(User.unique_id == o.linked_user_id).first()
                if u:
                    nested_user_id = u.id
            elif o.source_unique_id:
                src_fm = db.query(FamilyMember).filter(FamilyMember.unique_id == o.source_unique_id).first()
                if src_fm:
                    nested_user_id = src_fm.user_id

            if nested_user_id and nested_user_id != current_user_id:
                _fetch_and_add_linked_family(
                    db=db,
                    current_user_id=current_user_id,
                    current_user_unique_id=current_user_unique_id,
                    target_user_id=nested_user_id,
                    linked_via=o.relation,
                    exclude_unique_id=None,
                    is_sibling=False,  # nested (e.g. Wife's family) always uses in-law mapping
                    seen_ids=seen_ids,
                    owned_relations=owned_relations,
                    result=result,
                    fetched_user_ids=fetched,
                    db_session=db_session,
                )


@router.get("/extended-tree", response_model=List[ExtendedFamilyMemberResponse])
async def get_extended_family_tree(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the full family tree including linked families.
    When you add someone by Unique ID (PS-xxx or FM-xxx), their whole family is included.
    Recursively includes nested links: e.g. when your brother adds you, your wife's family
    shows up in his tree (pulled from your data).
    """
    seen_ids: set[str] = set()
    result: list[ExtendedFamilyMemberResponse] = []

    # 1. Add own members
    own = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()
    owned_relations: set[str] = set()
    for m in own:
        result.append(_member_to_extended(m, source="own", db=db))
        if m.unique_id:
            seen_ids.add(m.unique_id)
        owned_relations.add(m.relation)

    # 2. For each member with linked_user_id or source_unique_id, fetch their family (recursively)
    for m in own:
        target_user_id: Optional[int] = None
        linked_via = m.relation

        if m.linked_user_id:
            u = db.query(User).filter(User.unique_id == m.linked_user_id).first()
            if u:
                target_user_id = u.id
        elif m.source_unique_id:
            src_fm = db.query(FamilyMember).filter(FamilyMember.unique_id == m.source_unique_id).first()
            if src_fm:
                target_user_id = src_fm.user_id

        if not target_user_id or target_user_id == current_user.id:
            continue

        is_sibling = linked_via in ("Brother", "Sister", "Married Brother", "Married Sister")
        exclude_uid = m.source_unique_id if m.source_unique_id else None

        _fetch_and_add_linked_family(
            db=db,
            current_user_id=current_user.id,
            current_user_unique_id=current_user.unique_id,
            target_user_id=target_user_id,
            linked_via=linked_via,
            exclude_unique_id=exclude_uid,
            is_sibling=is_sibling,
            seen_ids=seen_ids,
            owned_relations=owned_relations,
            result=result,
            fetched_user_ids=set(),
            db_session=db,
        )

    return result


@router.get("/members", response_model=List[FamilyMemberResponse])
async def get_family_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all family members for the current user. Linked members show data from source (no copy)."""
    members = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()
    resolved = [_resolve_linked_member(m, db) for m in members]
    return resolved


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

    resolved = _resolve_linked_member(member, db)
    return resolved


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

    member.linked_user_id = (member_data.linked_user_id or "").strip().upper() or None
    member.source_unique_id = (member_data.source_unique_id or "").strip().upper() or None
    member.relation = member_data.relation
    member.gender = member_data.gender

    # Linked members: don't overwrite name/birth/death — display always from source
    has_link = bool(member.linked_user_id or member.source_unique_id)
    if not has_link:
        member.name = member_data.name
        member.last_name = member_data.last_name or None
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

        if not member_data.is_deceased:
            member.death_tithi = member.death_paksha = member.death_nakshatra = None
            member.death_vara = member.death_yoga = member.death_karana = None

    db.commit()
    db.refresh(member)

    if member.is_deceased and member.date_of_death:
        background_tasks.add_task(_fill_death_panchang, member, db)

    resolved = _resolve_linked_member(member, db)
    return resolved


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

