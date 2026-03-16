import json
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional, Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Pooja, PoojaSchedule, PoojaScheduleInvitee, User
from app.schemas import PoojaScheduleUpdate

router = APIRouter()


def _to_date(v: Any) -> str:
    """Convert datetime/date to YYYY-MM-DD string."""
    if v is None:
        return None
    if hasattr(v, "date"):
        return v.date().isoformat()
    if hasattr(v, "isoformat"):
        return v.isoformat()[:10]
    return str(v)[:10]


def _to_datetime(v: Any) -> Optional[str]:
    """Convert datetime to ISO string."""
    if v is None:
        return None
    if hasattr(v, "isoformat"):
        return v.isoformat()
    return str(v)


def _schedule_to_dict(s: PoojaSchedule) -> dict:
    """Manually serialize schedule to avoid Pydantic/datetime validation issues."""
    invitees = []
    for i in s.invitees:
        invitees.append({
            "id": i.id,
            "name": i.name,
            "last_name": i.last_name,
            "email": i.email,
            "rsvp_token": i.rsvp_token,
            "rsvp_status": i.rsvp_status or "pending",
            "rsvp_unique_id": i.rsvp_unique_id,
            "attending_members": i.attending_members,
            "rsvp_notes": i.rsvp_notes,
            "rsvp_updated_at": _to_datetime(i.rsvp_updated_at),
            "cancelled_at": _to_datetime(i.cancelled_at),
            "cancelled_reason": i.cancelled_reason,
        })
    return {
        "id": s.id,
        "user_id": s.user_id,
        "pooja_id": s.pooja_id,
        "pooja_name": s.pooja_name,
        "scheduled_date": _to_date(s.scheduled_date),
        "invite_message": s.invite_message,
        "image_path": s.image_path,
        "venue_place": s.venue_place,
        "venue_street_number": s.venue_street_number,
        "venue_street_name": s.venue_street_name,
        "venue_city": s.venue_city,
        "venue_state": s.venue_state,
        "venue_country": s.venue_country,
        "venue_coordinates": s.venue_coordinates,
        "invitees": invitees,
        "created_at": _to_datetime(s.created_at),
    }

UPLOAD_DIR = "uploads/schedule_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_schedule(
    pooja_id: Optional[int] = Form(None),
    pooja_name: Optional[str] = Form(None),
    scheduled_date: str = Form(...),
    invite_message: Optional[str] = Form(None),
    invitees_json: str = Form(default="[]"),
    image: Optional[UploadFile] = File(None),
    # Venue
    venue_place: Optional[str] = Form(None),
    venue_street_number: Optional[str] = Form(None),
    venue_street_name: Optional[str] = Form(None),
    venue_city: Optional[str] = Form(None),
    venue_state: Optional[str] = Form(None),
    venue_country: Optional[str] = Form(None),
    venue_coordinates: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new scheduled pooja with optional image and invitees."""

    # Validate date
    try:
        sched_dt = datetime.strptime(scheduled_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")
    today = datetime.now().date()
    if sched_dt.date() < today:
        raise HTTPException(status_code=422, detail="Pooja date cannot be in the past.")

    # Resolve pooja name
    resolved_name = pooja_name
    if pooja_id:
        pooja = db.query(Pooja).filter(Pooja.id == pooja_id).first()
        if pooja:
            resolved_name = pooja.name

    # Handle image upload
    image_path: Optional[str] = None
    if image and image.filename:
        if image.content_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP or GIF images are allowed.")
        ext = image.filename.rsplit(".", 1)[-1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        dest = os.path.join(UPLOAD_DIR, filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_path = f"/uploads/schedule_images/{filename}"

    # Parse invitees
    try:
        raw_invitees = json.loads(invitees_json)
    except json.JSONDecodeError:
        raw_invitees = []

    # Create schedule
    schedule = PoojaSchedule(
        user_id=current_user.id,
        pooja_id=pooja_id,
        pooja_name=resolved_name,
        scheduled_date=sched_dt,
        invite_message=invite_message,
        image_path=image_path,
        venue_place=venue_place or None,
        venue_street_number=venue_street_number or None,
        venue_street_name=venue_street_name or None,
        venue_city=venue_city or None,
        venue_state=venue_state or None,
        venue_country=venue_country or None,
        venue_coordinates=venue_coordinates or None,
    )
    db.add(schedule)
    db.flush()  # get schedule.id before adding invitees

    for inv in raw_invitees:
        name = (inv.get("name") or "").strip()
        email = (inv.get("email") or "").strip()
        if not name or not email:
            continue
        db.add(PoojaScheduleInvitee(
            schedule_id=schedule.id,
            name=name,
            last_name=(inv.get("last_name") or "").strip() or None,
            email=email,
        ))

    db.commit()
    db.refresh(schedule)
    return _schedule_to_dict(schedule)


@router.get("")
async def list_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all scheduled poojas for the current user."""
    schedules = (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.user_id == current_user.id)
        .order_by(PoojaSchedule.scheduled_date.desc())
        .all()
    )
    return [_schedule_to_dict(s) for s in schedules]


@router.get("/{schedule_id}")
async def get_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.id == schedule_id, PoojaSchedule.user_id == current_user.id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    return _schedule_to_dict(schedule)


@router.patch("/{schedule_id}")
async def update_schedule(
    schedule_id: int,
    data: PoojaScheduleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update schedule details (pooja name, date, venue, message). Invitees are managed separately."""
    schedule = (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.id == schedule_id, PoojaSchedule.user_id == current_user.id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")

    update_data = data.model_dump(exclude_unset=True)
    if "scheduled_date" in update_data:
        d = update_data["scheduled_date"]
        if hasattr(d, "strftime"):  # date object from pydantic
            sched_dt = datetime.combine(d, datetime.min.time())
        else:
            try:
                sched_dt = datetime.strptime(str(d), "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")
        if sched_dt.date() < datetime.now().date():
            raise HTTPException(status_code=422, detail="Pooja date cannot be in the past.")
        update_data["scheduled_date"] = sched_dt

    for key, value in update_data.items():
        setattr(schedule, key, value)

    db.commit()
    db.refresh(schedule)
    return _schedule_to_dict(schedule)


@router.patch("/{schedule_id}/invitees")
async def add_invitees(
    schedule_id: int,
    invitees_json: str = Form(default="[]"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add more invitees to an existing schedule (e.g. after invitations were sent)."""
    schedule = (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.id == schedule_id, PoojaSchedule.user_id == current_user.id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")

    try:
        raw_invitees = json.loads(invitees_json)
    except json.JSONDecodeError:
        raw_invitees = []

    for inv in raw_invitees:
        name = (inv.get("name") or "").strip()
        email = (inv.get("email") or "").strip()
        if not name or not email:
            continue
        db.add(PoojaScheduleInvitee(
            schedule_id=schedule.id,
            name=name,
            last_name=(inv.get("last_name") or "").strip() or None,
            email=email,
        ))

    db.commit()
    db.refresh(schedule)
    return _schedule_to_dict(schedule)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    schedule = (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.id == schedule_id, PoojaSchedule.user_id == current_user.id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")
    # Remove image file if exists
    if schedule.image_path:
        local_path = schedule.image_path.lstrip("/")
        if os.path.exists(local_path):
            os.remove(local_path)
    db.delete(schedule)
    db.commit()
