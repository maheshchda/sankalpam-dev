"""
Email service for Sankalpam — Brevo API (with delivery tracking) or SMTP fallback.
Configure: BREVO_API_KEY for API (recommended), or SMTP_* for SMTP.
"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple

from app.config import settings

# Brevo API
BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"


def _smtp_configured() -> bool:
    return bool(settings.smtp_user and settings.smtp_password)


def _brevo_configured() -> bool:
    return bool(getattr(settings, "brevo_api_key", "") or "")


def send_email_via_brevo(to: str, to_name: str, subject: str, html_body: str, text_body: str = "", tags: Optional[list] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Send via Brevo Transactional API. Returns (success, message_id, error_message).
    message_id can be used for delivery tracking via webhooks.
    """
    api_key = getattr(settings, "brevo_api_key", "") or ""
    if not api_key:
        return False, None, "BREVO_API_KEY not configured"
    sender_email = settings.email_from or settings.smtp_user or "noreply@sankalpam.com"
    sender_name = "Pooja Sankalpam"
    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to, "name": to_name or to}],
        "subject": subject,
        "htmlContent": html_body,
        "textContent": text_body or None,
    }
    if tags:
        payload["tags"] = tags
    try:
        import httpx
        r = httpx.post(
            BREVO_API_URL,
            json=payload,
            headers={"api-key": api_key, "accept": "application/json", "content-type": "application/json"},
            timeout=30.0,
        )
        if r.status_code in (200, 201):
            data = r.json()
            msg_id = data.get("messageId")
            print(f"[EMAIL] Brevo API sent to {to}: {subject} (messageId={msg_id})")
            return True, msg_id, None
        err = f"Brevo API {r.status_code}: {r.text}"
        print(f"[EMAIL] {err}")
        return False, None, err
    except Exception as exc:
        err = str(exc)
        print(f"[EMAIL] Brevo API error to {to}: {err}")
        return False, None, err


def get_brevo_delivery_status(message_id: str) -> Optional[str]:
    """
    Fetch delivery status from Brevo for a given message_id.
    Returns 'delivered', 'bounces', 'requests', etc. or None if not found/error.
    """
    api_key = getattr(settings, "brevo_api_key", "") or ""
    if not api_key or not message_id:
        return None
    try:
        import httpx
        from datetime import datetime, timedelta
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        r = httpx.get(
            "https://api.brevo.com/v3/smtp/statistics/events",
            params={"messageId": message_id, "startDate": start_date.strftime("%Y-%m-%d"), "endDate": end_date.strftime("%Y-%m-%d")},
            headers={"api-key": api_key, "accept": "application/json"},
            timeout=10.0,
        )
        if r.status_code != 200:
            return None
        data = r.json()
        events = data.get("events") or []
        # Prefer 'delivered' if present, else most recent event
        for ev in events:
            if ev.get("event") == "delivered":
                return "delivered"
        for ev in events:
            if ev.get("event") in ("hardBounces", "softBounces", "bounces"):
                return "bounced"
        for ev in events:
            if ev.get("event") == "requests":
                return "sent"
        return events[0].get("event") if events else None
    except Exception:
        return None


def send_email(to: str, subject: str, html_body: str, text_body: str = "", tags: Optional[list] = None) -> bool:
    """Send a single email. Returns True on success. Uses Brevo API if configured, else SMTP."""
    # Try Brevo API first (no message_id return for simple send_email interface)
    if _brevo_configured():
        ok, _, _ = send_email_via_brevo(to, "", subject, html_body, text_body, tags)
        if ok:
            return True
        # Fall through to SMTP if Brevo fails
    if not _smtp_configured():
        print(f"[EMAIL] Neither Brevo nor SMTP configured — would have sent to {to}: {subject}")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Pooja Sankalpam <{settings.email_from or settings.smtp_user}>"
    msg["To"] = to
    msg["Subject"] = subject

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to, msg.as_string())
        print(f"[EMAIL] SMTP sent to {to}: {subject}")
        return True
    except Exception as exc:
        print(f"[EMAIL] Failed to send to {to}: {exc}")
        return False


# ─── Invitation email template ────────────────────────────────────────────────

def build_invitation_html(
    *,
    invitee_name: str,
    pooja_name: str,
    scheduled_date: str,
    host_name: str,
    invite_message: str,
    rsvp_url: str,
    image_url: Optional[str] = None,
    frontend_url: str,
    venue_place: Optional[str] = None,
    venue_street_number: Optional[str] = None,
    venue_street_name: Optional[str] = None,
    venue_city: Optional[str] = None,
    venue_state: Optional[str] = None,
    venue_country: Optional[str] = None,
    venue_coordinates: Optional[str] = None,
) -> str:
    image_block = ""
    if image_url:
        image_block = f"""
        <tr>
          <td align="center" style="padding:0 0 24px 0;">
            <img src="{image_url}" alt="Pooja" style="max-width:480px;width:100%;border-radius:12px;border:3px solid #c9a227;"/>
          </td>
        </tr>
        """

    # Build venue block
    venue_lines = []
    if venue_place:
        venue_lines.append(f"<strong>{venue_place}</strong>")
    street = " ".join(filter(None, [venue_street_number, venue_street_name]))
    if street:
        venue_lines.append(street)
    city_line = ", ".join(filter(None, [venue_city, venue_state, venue_country]))
    if city_line:
        venue_lines.append(city_line)

    venue_block = ""
    if venue_lines:
        maps_href = ""
        if venue_coordinates:
            if venue_coordinates.startswith("http"):
                maps_href = venue_coordinates
            else:
                import urllib.parse
                maps_href = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(venue_coordinates)}"
        elif city_line:
            import urllib.parse
            maps_href = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(city_line)}"

        maps_link = f' &nbsp;<a href="{maps_href}" style="color:#c9a227;font-size:11px;">Open in Maps →</a>' if maps_href else ""
        venue_html = "<br/>".join(venue_lines)
        venue_block = f"""
        <tr>
          <td style="padding:0 0 24px 0;">
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td style="background:#fdf8f0;border:1px solid #e8d5a8;border-radius:8px;padding:14px 18px;">
                  <p style="margin:0 0 4px 0;font-size:11px;color:#8a7060;letter-spacing:1px;text-transform:uppercase;">📍 Venue</p>
                  <p style="margin:0;color:#4a3728;font-size:14px;line-height:1.6;">{venue_html}{maps_link}</p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
        """

    message_block = ""
    if invite_message:
        paragraphs = "".join(
            f'<p style="margin:0 0 12px 0;color:#4a3728;line-height:1.7;">{line}</p>'
            for line in invite_message.split("\n") if line.strip()
        )
        message_block = f"""
        <tr>
          <td style="padding:0 0 28px 0;">
            <div style="background:#fdf8f0;border-left:4px solid #c9a227;border-radius:4px;padding:20px 24px;">
              {paragraphs}
            </div>
          </td>
        </tr>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>You're Invited — {pooja_name}</title>
</head>
<body style="margin:0;padding:0;background-color:#f5f0e8;font-family:'Georgia',serif;">
  <!-- Outer wrapper -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f5f0e8;padding:40px 0;">
    <tr>
      <td align="center">
        <!-- Card -->
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:#fff9ef;border-radius:16px;border:2px solid #c9a227;
                      box-shadow:0 4px 24px rgba(0,0,0,0.10);max-width:600px;width:100%;">

          <!-- Gold header band -->
          <tr>
            <td style="background:linear-gradient(135deg,#2d1b0e 0%,#4a2c0a 100%);
                       border-radius:14px 14px 0 0;padding:32px 40px;text-align:center;">
              <p style="margin:0 0 6px 0;color:#c9a227;font-size:13px;letter-spacing:3px;text-transform:uppercase;">
                Pooja Sankalpam
              </p>
              <h1 style="margin:0;color:#f5e6c8;font-size:30px;font-family:'Georgia',serif;font-weight:bold;">
                🪔 {pooja_name}
              </h1>
              <p style="margin:12px 0 0 0;color:#e8d5a8;font-size:16px;">{scheduled_date}</p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:36px 40px 0 40px;">
              <table width="100%" cellpadding="0" cellspacing="0">

                <!-- Greeting -->
                <tr>
                  <td style="padding:0 0 24px 0;">
                    <p style="margin:0;font-size:17px;color:#2d1b0e;">
                      Dear <strong>{invitee_name}</strong>,
                    </p>
                    <p style="margin:8px 0 0 0;font-size:15px;color:#6b4f3a;">
                      <strong>{host_name}</strong> has invited you to join in a sacred Pooja ceremony.
                    </p>
                  </td>
                </tr>

                <!-- Image -->
                {image_block}

                <!-- Venue -->
                {venue_block}

                <!-- Message -->
                {message_block}

                <!-- RSVP button section -->
                <tr>
                  <td align="center" style="padding:0 0 36px 0;">
                    <div style="background:#fdf8f0;border:1px solid #e8d5a8;border-radius:12px;padding:28px 32px;text-align:center;">
                      <p style="margin:0 0 6px 0;font-size:13px;color:#8a7060;letter-spacing:1px;text-transform:uppercase;">
                        Will you be joining us?
                      </p>
                      <p style="margin:0 0 24px 0;font-size:15px;color:#4a3728;">
                        Please let us know by clicking the button below
                      </p>
                      <a href="{rsvp_url}"
                         style="display:inline-block;background:linear-gradient(135deg,#c9a227,#e8c547);
                                color:#2d1b0e;font-size:16px;font-weight:bold;text-decoration:none;
                                padding:14px 40px;border-radius:8px;letter-spacing:0.5px;">
                        ✓ &nbsp; View Invitation &amp; RSVP
                      </a>
                      <p style="margin:20px 0 0 0;font-size:12px;color:#a09080;">
                        Or copy this link: <a href="{rsvp_url}" style="color:#c9a227;">{rsvp_url}</a>
                      </p>
                    </div>
                  </td>
                </tr>

              </table>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#2d1b0e;border-radius:0 0 14px 14px;padding:20px 40px;text-align:center;">
              <p style="margin:0;color:#c9a227;font-size:12px;letter-spacing:1px;">
                POOJA SANKALPAM &nbsp;·&nbsp; Sacred Family Traditions
              </p>
              <p style="margin:6px 0 0 0;font-size:11px;color:#8a7060;">
                This invitation was sent via
                <a href="{frontend_url}" style="color:#c9a227;text-decoration:none;">Pooja Sankalpam</a>.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def build_invitation_text(
    *,
    invitee_name: str,
    pooja_name: str,
    scheduled_date: str,
    host_name: str,
    invite_message: str,
    rsvp_url: str,
) -> str:
    return f"""You're invited to {pooja_name}!

Dear {invitee_name},

{host_name} has invited you to a sacred Pooja ceremony.

Pooja: {pooja_name}
Date:  {scheduled_date}

{invite_message}

Please RSVP here:
{rsvp_url}

With blessings,
Pooja Sankalpam
"""


def build_cancellation_html(
    *,
    invitee_name: str,
    pooja_name: str,
    scheduled_date: str,
    host_name: str,
    reason: str,
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><title>Invitation Cancelled</title></head>
<body style="margin:0;padding:0;background:#f5f0e8;font-family:Georgia,serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff9ef;border-radius:16px;border:2px solid #c9a227;padding:32px 40px;">
        <tr><td style="text-align:center;padding-bottom:24px;">
          <p style="margin:0;color:#c9a227;font-size:13px;letter-spacing:3px;">Pooja Sankalpam</p>
          <h1 style="margin:12px 0 0 0;color:#2d1b0e;font-size:24px;">Invitation Cancelled</h1>
        </td></tr>
        <tr><td style="color:#4a3728;font-size:15px;line-height:1.7;">
          <p>Dear <strong>{invitee_name}</strong>,</p>
          <p>We regret to inform you that your invitation to <strong>{pooja_name}</strong> on <strong>{scheduled_date}</strong> has been cancelled by {host_name}.</p>
          {f'<p style="background:#fdf8f0;border-left:4px solid #c9a227;padding:16px 20px;border-radius:4px;margin:20px 0;"><strong>Reason:</strong> {reason}</p>' if reason else ''}
          <p>If you have any questions, please contact the host directly.</p>
          <p style="margin-top:28px;">With regards,<br/>Pooja Sankalpam</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def build_cancellation_text(
    *,
    invitee_name: str,
    pooja_name: str,
    scheduled_date: str,
    host_name: str,
    reason: str,
) -> str:
    lines = [
        f"Dear {invitee_name},",
        f"Your invitation to {pooja_name} on {scheduled_date} has been cancelled by {host_name}.",
    ]
    if reason:
        lines.append(f"Reason: {reason}")
    lines.extend(["", "If you have questions, please contact the host directly.", "", "Pooja Sankalpam"])
    return "\n".join(lines)
