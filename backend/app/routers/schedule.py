import json
import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Pooja, PoojaSchedule, PoojaScheduleInvitee, User
from app.schemas import PoojaScheduleResponse, PoojaScheduleUpdate

router = APIRouter()

UPLOAD_DIR = "uploads/schedule_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("", response_model=PoojaScheduleResponse, status_code=status.HTTP_201_CREATED)
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
    return schedule


@router.get("", response_model=List[PoojaScheduleResponse])
async def list_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all scheduled poojas for the current user."""
    return (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.user_id == current_user.id)
        .order_by(PoojaSchedule.scheduled_date.desc())
        .all()
    )


@router.get("/{schedule_id}", response_model=PoojaScheduleResponse)
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
    return schedule


@router.patch("/{schedule_id}", response_model=PoojaScheduleResponse)
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
    return schedule


@router.patch("/{schedule_id}/invitees", response_model=PoojaScheduleResponse)
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
    return schedule


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
