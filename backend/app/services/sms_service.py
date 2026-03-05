"""
SMS service for sending verification OTPs
Supports Twilio and console output for development
"""
import os
import re
from typing import Optional
from app.config import settings

# Try to import Twilio
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Twilio not available. Install with: pip install twilio")

def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to E.164 format for Twilio.
    Assumes Indian numbers if no country code is present.
    
    Args:
        phone: Phone number in any format
    
    Returns:
        Phone number in E.164 format (e.g., +919876543210)
    """
    # Remove all non-digit characters except +
    phone = re.sub(r'[^\d+]', '', phone)
    
    # If it already starts with +, return as is
    if phone.startswith('+'):
        return phone
    
    # If it starts with 0, remove it (common in Indian numbers)
    if phone.startswith('0'):
        phone = phone[1:]
    
    # If it doesn't start with country code, assume India (+91)
    if not phone.startswith('+') and len(phone) == 10:
        phone = '+91' + phone
    elif not phone.startswith('+') and len(phone) > 10:
        # Might already have country code without +
        phone = '+' + phone
    
    return phone

def send_verification_sms(to_phone: str, otp: str) -> bool:
    """
    Send SMS verification OTP to user.
    
    Args:
        to_phone: Recipient phone number (will be normalized to E.164 format)
        otp: 6-digit OTP code
    
    Returns:
        True if SMS sent successfully, False otherwise
    """
    try:
        # Get Twilio settings from environment
        twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        twilio_from_number = os.getenv("TWILIO_FROM_NUMBER", settings.sms_from)
        
        # If no Twilio credentials configured, use development mode (console output)
        if not twilio_account_sid or not twilio_auth_token or not TWILIO_AVAILABLE:
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - SMS Verification")
            print(f"To: {to_phone}")
            print(f"OTP Code: {otp}")
            print(f"Use this OTP on the verification page: http://localhost:3000/verify")
            print(f"{'='*60}\n")
            return True
        
        # Normalize phone number to E.164 format
        normalized_phone = normalize_phone_number(to_phone)
        
        # Send SMS via Twilio
        client = Client(twilio_account_sid, twilio_auth_token)
        
        message_body = f"Your Sankalpam verification code is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this code, please ignore this message."
        
        message = client.messages.create(
            body=message_body,
            from_=twilio_from_number,
            to=normalized_phone
        )
        
        print(f"✅ Verification SMS sent to {normalized_phone} (SID: {message.sid})")
        return True
        
    except Exception as e:
        print(f"❌ Error sending verification SMS to {to_phone}: {e}")
        # In development, still return True and print to console
        if settings.secret_key == "your-secret-key-change-in-production":
            print(f"\n{'='*60}")
            print(f"DEVELOPMENT MODE - SMS Verification (Twilio failed)")
            print(f"To: {to_phone}")
            print(f"OTP Code: {otp}")
            print(f"Use this OTP on the verification page: http://localhost:3000/verify")
            print(f"{'='*60}\n")
            return True
        return False
