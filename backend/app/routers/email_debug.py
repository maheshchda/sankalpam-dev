"""
Email debug endpoints — diagnose Brevo/SMTP config and test sending.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.config import settings
from app.dependencies import get_current_user
from app.email_service import send_email_via_brevo, _brevo_configured, _smtp_configured
from app.models import User

router = APIRouter()


class TestSendBody(BaseModel):
    to: str


@router.get("/test")
async def test_email_public(
    email: str = Query(..., description="Email address to send test to"),
    token: str = Query(..., description="Must match EMAIL_TEST_SECRET env var"),
):
    """
    Send a test email via Brevo API (no login required).
    Set EMAIL_TEST_SECRET in Railway, then call:
    GET /api/email/test?email=you@example.com&token=YOUR_SECRET
    """
    secret = getattr(settings, "email_test_secret", "") or ""
    if not secret or token != secret:
        return {"ok": False, "error": "Invalid or missing token. Set EMAIL_TEST_SECRET in Railway."}

    if not email or "@" not in email:
        return {"ok": False, "error": "Invalid email address"}

    if not _brevo_configured():
        return {"ok": False, "error": "Brevo not configured. Set BREVO_API_KEY in Railway."}

    ok, msg_id, err = send_email_via_brevo(
        to=email.strip(),
        to_name="Test Recipient",
        subject="[Sankalpam] Brevo API Test",
        html_body="<p>This test email confirms Brevo API works on Railway.</p>",
        text_body="This test email confirms Brevo API works on Railway.",
    )

    if ok:
        return {"ok": True, "message_id": msg_id, "message": "Test email sent via Brevo API."}
    return {"ok": False, "error": err or "Unknown error"}


@router.get("/config")
async def email_config(current_user: User = Depends(get_current_user)):
    """
    Returns email configuration status (no secrets).
    Use this to verify env vars are loaded on Railway.
    """
    brevo_key = getattr(settings, "brevo_api_key", "") or ""
    return {
        "brevo_configured": bool(brevo_key),
        "brevo_key_length": len(brevo_key) if brevo_key else 0,
        "email_from": settings.email_from or "(not set)",
        "smtp_configured": _smtp_configured(),
        "frontend_url": settings.frontend_url or "(not set)",
    }


@router.post("/test-send")
async def test_send(body: TestSendBody, current_user: User = Depends(get_current_user)):
    """
    Send a test email to the given address.
    Returns the full Brevo/SMTP result for debugging.
    """
    to = body.to.strip()
    if not to or "@" not in to:
        return {"ok": False, "error": "Invalid email address"}

    if not _brevo_configured():
        return {
            "ok": False,
            "error": "Brevo not configured. Set BREVO_API_KEY in Railway.",
            "brevo_configured": False,
        }

    ok, msg_id, err = send_email_via_brevo(
        to=to,
        to_name="Test Recipient",
        subject="[Sankalpam] Test Email",
        html_body="<p>This is a test email from Pooja Sankalpam.</p>",
        text_body="This is a test email from Pooja Sankalpam.",
    )

    if ok:
        return {"ok": True, "message_id": msg_id}
    return {"ok": False, "error": err or "Unknown error"}
