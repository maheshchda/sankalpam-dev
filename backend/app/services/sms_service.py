"""
Phone verification OTPs via Brevo: transactional SMS and/or WhatsApp (Meta templates).
See backend/EMAIL_SMS_SETUP.md for Brevo dashboard setup.
"""
import os
import re
from typing import Optional

import httpx
from app.config import settings

BREVO_WHATSAPP_URL = "https://api.brevo.com/v3/whatsapp/sendMessage"


def normalize_phone_for_brevo(phone: str) -> str:
    """
    Normalize phone number for Brevo SMS API (digits only, with country code).
    Supports explicit international numbers and applies a fallback for local 10-digit input.

    Returns:
        Phone number as digits only, e.g. 919876543210
    """
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = phone[1:]
    # Already has country code (E.164 digits-only length is usually 11-15)
    if len(phone) >= 11:
        return phone

    if len(phone) == 10:
        # Heuristic for local input without +country code:
        # - Indian mobiles typically start 6-9 -> prefix 91
        # - Otherwise treat as NANP/US -> prefix 1
        if phone[0] in ("6", "7", "8", "9"):
            phone = "91" + phone
        else:
            phone = "1" + phone
    return phone


def _whatsapp_otp_configured() -> bool:
    tid: Optional[int] = getattr(settings, "brevo_whatsapp_otp_template_id", None)
    sender = (getattr(settings, "brevo_whatsapp_sender_number", "") or "").strip()
    return bool(sender and tid)


def send_verification_whatsapp(to_phone: str, otp: str) -> bool:
    """
    Send OTP using Brevo WhatsApp API (approved Meta template required).
    Template must expose a transactional variable matching brevo_whatsapp_otp_param (default OTP).
    """
    api_key = os.getenv("BREVO_API_KEY", "") or getattr(settings, "brevo_api_key", "")
    sender = (getattr(settings, "brevo_whatsapp_sender_number", "") or "").strip()
    tid = getattr(settings, "brevo_whatsapp_otp_template_id", None)
    param_name = (getattr(settings, "brevo_whatsapp_otp_param", None) or "OTP").strip() or "OTP"

    if not api_key or not api_key.strip():
        print(f"\n{'='*60}")
        print("DEVELOPMENT MODE - WhatsApp Verification (Brevo API key not set)")
        print(f"To: {to_phone}")
        print(f"OTP Code: {otp}")
        print(f"{'='*60}\n")
        return True

    if not sender or not tid:
        print(
            "WhatsApp OTP skipped: set BREVO_WHATSAPP_SENDER_NUMBER and "
            "BREVO_WHATSAPP_OTP_TEMPLATE_ID (see EMAIL_SMS_SETUP.md)."
        )
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"DEVELOPMENT MODE - OTP: {otp}")
            return True
        return False

    recipient = normalize_phone_for_brevo(to_phone)
    payload = {
        "contactNumbers": [recipient],
        "senderNumber": sender,
        "templateId": int(tid),
        "params": {param_name: otp},
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(
                BREVO_WHATSAPP_URL,
                headers={"api-key": api_key.strip(), "Content-Type": "application/json"},
                json=payload,
            )
        if r.status_code in (200, 201):
            print(f"✅ Verification WhatsApp sent to {recipient} via Brevo (template {tid})")
            return True
        print(f"❌ Brevo WhatsApp API error {r.status_code}: {r.text}")
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"DEVELOPMENT MODE - OTP: {otp}")
            return True
        return False
    except Exception as e:
        print(f"❌ Error sending verification WhatsApp to {to_phone}: {e}")
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"DEVELOPMENT MODE - OTP: {otp}")
            return True
        return False


def dispatch_phone_verification_otp(to_phone: str, otp: str) -> bool:
    """
    Send OTP per PHONE_VERIFICATION_CHANNEL: sms | whatsapp | both.
    Falls back to SMS if channel asks for WhatsApp but WhatsApp env is incomplete.
    """
    ch = (
        os.getenv("PHONE_VERIFICATION_CHANNEL", "").strip()
        or getattr(settings, "phone_verification_channel", "sms")
        or "sms"
    ).lower()
    if ch not in ("sms", "whatsapp", "both"):
        ch = "sms"

    if ch == "whatsapp" and not _whatsapp_otp_configured():
        print("[phone verification] WhatsApp not fully configured; falling back to SMS.")
        ch = "sms"
    elif ch == "both" and not _whatsapp_otp_configured():
        print("[phone verification] WhatsApp not fully configured; sending SMS only.")
        ch = "sms"

    ok = False
    if ch in ("sms", "both"):
        ok = send_verification_sms(to_phone, otp) or ok
    if ch in ("whatsapp", "both"):
        ok = send_verification_whatsapp(to_phone, otp) or ok
    return ok


def send_verification_sms(to_phone: str, otp: str) -> bool:
    """
    Send SMS verification OTP via Brevo Transactional SMS API.

    Args:
        to_phone: Recipient phone number
        otp: 6-digit OTP code

    Returns:
        True if SMS sent successfully or in dev mode, False otherwise
    """
    api_key = os.getenv("BREVO_API_KEY", "") or getattr(settings, "brevo_api_key", "")

    if not api_key or not api_key.strip():
        print(f"\n{'='*60}")
        print(f"DEVELOPMENT MODE - SMS Verification (Brevo not configured)")
        print(f"To: {to_phone}")
        print(f"OTP Code: {otp}")
        print(f"Use this OTP on the verification page: http://localhost:3000/verify")
        print(f"{'='*60}\n")
        return True

    try:
        recipient = normalize_phone_for_brevo(to_phone)
        sender = (os.getenv("SMS_SENDER", "") or getattr(settings, "sms_sender", "Sankalpam") or "Sankalpam")[:11]
        content = f"Your Sankalpam verification code is: {otp}. Valid for 10 minutes. If you did not request this, please ignore."

        with httpx.Client(timeout=15.0) as client:
            r = client.post(
                "https://api.brevo.com/v3/transactionalSMS/send",
                headers={"api-key": api_key.strip(), "Content-Type": "application/json"},
                json={
                    "sender": sender,
                    "recipient": recipient,
                    "content": content,
                    "type": "transactional",
                },
            )

        if r.status_code in (200, 201):
            print(f"✅ Verification SMS sent to {recipient} via Brevo")
            return True

        print(f"❌ Brevo SMS API error {r.status_code}: {r.text}")
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"DEVELOPMENT MODE - OTP: {otp}")
            return True
        return False

    except Exception as e:
        print(f"❌ Error sending verification SMS to {to_phone}: {e}")
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - SMS Verification (Brevo failed)")
            print(f"To: {to_phone}")
            print(f"OTP Code: {otp}")
            print(f"{'='*60}\n")
            return True
        return False
