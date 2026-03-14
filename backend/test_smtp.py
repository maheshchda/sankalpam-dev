#!/usr/bin/env python3
"""
Test Brevo/SMTP email configuration.
Run from backend dir: python test_smtp.py
"""
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

def test_smtp():
    host = os.getenv("SMTP_HOST", "")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    email_from = os.getenv("EMAIL_FROM", user)

    print("SMTP Configuration:")
    print(f"  Host:     {host or '(not set)'}")
    print(f"  Port:     {port}")
    print(f"  User:     {user or '(not set)'}")
    print(f"  Password: {'***' if password else '(not set)'}")
    print(f"  From:     {email_from or '(not set)'}")
    print()

    if not all([host, user, password]):
        print("ERROR: SMTP_HOST, SMTP_USER, and SMTP_PASSWORD must be set in .env")
        return False

    # Test recipient - send to self
    to_email = user if user else email_from
    if not to_email:
        print("ERROR: Cannot determine test recipient. Set SMTP_USER or EMAIL_FROM.")
        return False

    print(f"Sending test email to {to_email}...")

    try:
        import smtplib
        import ssl
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["From"] = f"Pooja Sankalpam <{email_from or user}>"
        msg["To"] = to_email
        msg["Subject"] = "SMTP Test - Pooja Sankalpam"

        body = "This is a test email from Pooja Sankalpam. Your Brevo SMTP configuration is working correctly."
        msg.attach(MIMEText(body, "plain"))

        context = ssl.create_default_context()
        with smtplib.SMTP(host, port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(user, password)
            server.sendmail(user, to_email, msg.as_string())

        print("SUCCESS: Test email sent. Check your inbox (and spam folder).")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"FAILED: Authentication error - {e}")
        print("  For Brevo: Use SMTP key (Settings → SMTP & API → SMTP Keys), not API key.")
        return False
    except smtplib.SMTPException as e:
        print(f"FAILED: SMTP error - {e}")
        return False
    except Exception as e:
        print(f"FAILED: {type(e).__name__} - {e}")
        return False

if __name__ == "__main__":
    ok = test_smtp()
    sys.exit(0 if ok else 1)
