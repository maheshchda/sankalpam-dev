"""
RSVP Router — all endpoints are either:
  - Public (no auth) identified by unique rsvp_token
  - Protected by standard JWT (send-invitations, host view)
"""

import json
import secrets
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.email_service import (
    build_invitation_html,
    build_invitation_text,
    send_email,
)
from app.models import FamilyMember, PoojaSchedule, PoojaScheduleInvitee, User
from app.schemas import AttendingMemberInfo, RsvpInvitationView, RsvpSubmit
from app.config import settings

router = APIRouter()


# ─── Helper ───────────────────────────────────────────────────────────────────

def _make_token() -> str:
    return secrets.token_urlsafe(40)


def _format_date(d) -> str:
    try:
        return d.strftime("%A, %B %-d, %Y")
    except Exception:
        return str(d)


# ─── HOST: Send invitations ───────────────────────────────────────────────────

@router.post("/{schedule_id}/send", status_code=200)
async def send_invitations(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate a unique RSVP token for each invitee (if not already set)
    and send a beautiful HTML invitation email.
    """
    schedule = (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.id == schedule_id, PoojaSchedule.user_id == current_user.id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")

    if not schedule.invitees:
        raise HTTPException(status_code=400, detail="No invitees to send to.")

    host_name = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.username
    pooja_name = schedule.pooja_name or "Pooja Ceremony"
    date_str = _format_date(schedule.scheduled_date)
    invite_message = schedule.invite_message or ""

    # Build image URL if available
    image_url: Optional[str] = None
    if schedule.image_path:
        base = (settings.frontend_url or "http://localhost:8000").rstrip("/")
        # Image is served from backend, construct full URL using backend port
        import os
        backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
        image_url = backend_url.rstrip("/") + schedule.image_path

    sent_count = 0
    skipped = []
    for inv in schedule.invitees:
        # Assign token if missing
        if not inv.rsvp_token:
            tok = _make_token()
            while db.query(PoojaScheduleInvitee).filter(PoojaScheduleInvitee.rsvp_token == tok).first():
                tok = _make_token()
            inv.rsvp_token = tok
            db.flush()

        rsvp_url = f"{settings.frontend_url.rstrip('/')}/rsvp/{inv.rsvp_token}"
        invitee_name = f"{inv.name}{' ' + inv.last_name if inv.last_name else ''}"

        html = build_invitation_html(
            invitee_name=invitee_name,
            pooja_name=pooja_name,
            scheduled_date=date_str,
            host_name=host_name,
            invite_message=invite_message,
            rsvp_url=rsvp_url,
            image_url=image_url,
            frontend_url=settings.frontend_url,
        )
        text = build_invitation_text(
            invitee_name=invitee_name,
            pooja_name=pooja_name,
            scheduled_date=date_str,
            host_name=host_name,
            invite_message=invite_message,
            rsvp_url=rsvp_url,
        )

        subject = f"🪔 You're invited to {pooja_name} — {date_str}"
        ok = send_email(to=inv.email, subject=subject, html_body=html, text_body=text)
        if ok:
            sent_count += 1
        else:
            skipped.append(inv.email)

    db.commit()

    return {
        "sent": sent_count,
        "skipped": skipped,
        "total": len(schedule.invitees),
        "message": f"Invitations sent to {sent_count} of {len(schedule.invitees)} invitees.",
    }


# ─── PUBLIC: View invitation ──────────────────────────────────────────────────

@router.get("/view/{token}", response_model=RsvpInvitationView)
async def view_invitation(token: str, db: Session = Depends(get_db)):
    """Public endpoint — returns invitation details for the RSVP page."""
    inv = (
        db.query(PoojaScheduleInvitee)
        .filter(PoojaScheduleInvitee.rsvp_token == token)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    schedule = inv.schedule
    host = db.query(User).filter(User.id == schedule.user_id).first()
    host_name = (
        f"{host.first_name} {host.last_name}".strip() if host else "Your host"
    )

    return RsvpInvitationView(
        schedule_id=schedule.id,
        invitee_id=inv.id,
        invitee_name=inv.name,
        invitee_last_name=inv.last_name,
        pooja_name=schedule.pooja_name or "Pooja Ceremony",
        scheduled_date=schedule.scheduled_date,
        invite_message=schedule.invite_message,
        image_path=schedule.image_path,
        host_name=host_name,
        rsvp_status=inv.rsvp_status or "pending",
        rsvp_notes=inv.rsvp_notes,
        attending_members=inv.attending_members,
    )


# ─── PUBLIC: Submit RSVP ─────────────────────────────────────────────────────

@router.post("/view/{token}", status_code=200)
async def submit_rsvp(token: str, data: RsvpSubmit, db: Session = Depends(get_db)):
    """Public endpoint — submit an RSVP response."""
    inv = (
        db.query(PoojaScheduleInvitee)
        .filter(PoojaScheduleInvitee.rsvp_token == token)
        .first()
    )
    if not inv:
        raise HTTPException(status_code=404, detail="Invitation not found.")

    inv.rsvp_status = data.status
    inv.rsvp_notes = data.notes
    inv.rsvp_updated_at = datetime.now(timezone.utc)

    if data.unique_id:
        uid = data.unique_id.strip().upper()
        # Verify the unique_id exists
        user = db.query(User).filter(User.unique_id == uid).first()
        if user:
            inv.rsvp_unique_id = uid
        else:
            raise HTTPException(status_code=404, detail=f"No Sankalpam account found with Unique ID {uid}.")

    if data.attending_member_ids is not None:
        inv.attending_members = json.dumps(data.attending_member_ids)

    db.commit()

    return {"status": inv.rsvp_status, "message": "RSVP recorded successfully."}


# ─── PUBLIC: Lookup family members by Unique ID (for RSVP "who's attending") ─

@router.get("/members/{unique_id}", response_model=List[AttendingMemberInfo])
async def get_members_for_rsvp(unique_id: str, db: Session = Depends(get_db)):
    """
    Public endpoint: given a PS-XXXXXXXX Unique ID, return the user + their
    family members so the RSVP page can display a checklist.
    """
    uid = unique_id.strip().upper()
    user = db.query(User).filter(User.unique_id == uid).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"No account found with Unique ID {uid}.")

    result: List[AttendingMemberInfo] = []

    # Account holder themselves
    result.append(AttendingMemberInfo(
        unique_id=uid,
        display_name=f"{user.first_name} {user.last_name}".strip() or user.username,
        relation="Self",
    ))

    # Family members
    members = db.query(FamilyMember).filter(FamilyMember.user_id == user.id).all()
    for m in members:
        display = m.name
        if m.last_name:
            display = f"{m.name} {m.last_name}"
        result.append(AttendingMemberInfo(
            unique_id=m.unique_id or f"fm-{m.id}",
            display_name=display,
            relation=m.relation,
        ))

    return result


# ─── HOST: Get RSVP summary for a schedule ───────────────────────────────────

@router.get("/summary/{schedule_id}")
async def rsvp_summary(
    schedule_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return RSVP status counts and detail for a schedule (host only)."""
    schedule = (
        db.query(PoojaSchedule)
        .filter(PoojaSchedule.id == schedule_id, PoojaSchedule.user_id == current_user.id)
        .first()
    )
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found.")

    summary = {"attending": 0, "not_attending": 0, "maybe": 0, "pending": 0, "invitees": []}
    for inv in schedule.invitees:
        st = inv.rsvp_status or "pending"
        summary[st] = summary.get(st, 0) + 1
        summary["invitees"].append({
            "id": inv.id,
            "name": f"{inv.name}{' ' + inv.last_name if inv.last_name else ''}",
            "email": inv.email,
            "status": st,
            "notes": inv.rsvp_notes,
            "unique_id": inv.rsvp_unique_id,
            "attending_members": json.loads(inv.attending_members or "[]"),
            "rsvp_token": inv.rsvp_token,
        })

    return summary
