"""
SMS service for sending verification OTPs
Uses Brevo Transactional SMS API (same account as email)
"""
import os
import re
import httpx
from app.config import settings


def normalize_phone_for_brevo(phone: str) -> str:
    """
    Normalize phone number for Brevo SMS API (digits only, with country code).
    Assumes Indian numbers if no country code is present.

    Returns:
        Phone number as digits only, e.g. 919876543210
    """
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = phone[1:]
    if len(phone) == 10:
        phone = '91' + phone
    return phone


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
