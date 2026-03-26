# Railway Environment Variables & Deployment

## Fix: Backend build fails with "Could not read package.json"

**Cause:** Railway is building from the **repo root** instead of the `backend` folder. Railpack detects both Python and Node, then runs `npm run build` from `/app` where `package.json` doesn't exist.

**Fix:** In Railway → **backend** service → **Settings** → set **Root Directory** to `backend`.

---

## Fix: Live site calling localhost instead of production API

If your live site (https://www.poojasankalp.org) shows CORS errors or tries to call `localhost:8000`, the frontend was built without the production API URL.

### Frontend service (Railway)

Add this variable to your **frontend** service in Railway:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-BACKEND-URL.up.railway.app` |

Replace `YOUR-BACKEND-URL` with your actual backend Railway URL (e.g. if backend is at `sankalpam-backend-production-xxxx.up.railway.app`, use that).

**Important:** After adding the variable, **redeploy** the frontend. `NEXT_PUBLIC_*` vars are baked in at build time.

### Backend service (Railway)

If using a custom domain, ensure CORS allows it. The backend already allows `poojasankalp.org`. For other domains, add:

| Variable | Value |
|----------|-------|
| `ALLOWED_ORIGINS` | `https://www.poojasankalp.org,https://poojasankalp.org` |

### Email (Brevo) — for invitations & verification

For schedule-pooja invitations and auth emails to work in production, add these to your **backend** service. **Brevo API is preferred** (enables delivery tracking):

| Variable | Value |
|----------|-------|
| `BREVO_API_KEY` | Your Brevo API key (Settings → SMTP & API → API Keys) |
| `SMTP_HOST` | `smtp-relay.brevo.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Brevo SMTP login |
| `SMTP_PASSWORD` | Your Brevo SMTP key (Settings → SMTP & API → SMTP Keys) |
| `EMAIL_FROM` | `poojasankalpam@gmail.com` |
| `FRONTEND_URL` | `https://www.poojasankalp.org` (no trailing slash) |
| `BACKEND_URL` | `https://api.poojasankalp.org` |

### SMS & WhatsApp (Brevo) — phone OTP on register / resend

See **`backend/EMAIL_SMS_SETUP.md`** for full steps. Minimal Railway vars:

| Variable | Notes |
|----------|--------|
| `BREVO_API_KEY` | Same API key as email (required for SMS/WhatsApp API) |
| `SMS_SENDER` | Alphanumeric sender, max 11 chars (e.g. `Sankalpam`) |
| `PHONE_VERIFICATION_CHANNEL` | Optional: `sms` (default), `whatsapp`, or `both` |
| `BREVO_WHATSAPP_SENDER_NUMBER` | Digits + country code, e.g. `919876543210` |
| `BREVO_WHATSAPP_OTP_TEMPLATE_ID` | Integer; Meta-approved OTP template in Brevo |
| `BREVO_WHATSAPP_OTP_PARAM` | Optional; template variable name (default `OTP`) |

### Checklist

1. [ ] Backend deployed on Railway (or elsewhere)
2. [ ] `NEXT_PUBLIC_API_URL` set in frontend service = backend URL
3. [ ] Redeploy frontend after adding env var
4. [ ] Backend CORS allows your domain (poojasankalp.org is already in code)
5. [ ] SMTP env vars set for invitation emails

### Email not sending? Debug steps

1. **Check the error in the UI** — When you click "Send invitations", if it fails, the toast now shows the Brevo API error (e.g. "Invalid sender", "Domain not verified").

2. **Use the debug endpoints:**
   - **No login:** Set `EMAIL_TEST_SECRET` in Railway (e.g. a random string), then:
     ```
     GET https://api.poojasankalp.org/api/email/test?email=you@example.com&token=YOUR_SECRET
     ```
     Sends a real test email via Brevo API. Check your inbox (and spam).
   - **With login:** `GET /api/email/config` — Shows if `BREVO_API_KEY`, `EMAIL_FROM` are loaded. `POST /api/email/test-send` with body `{"to": "your@email.com"}` — Same test, requires JWT.

3. **Common Brevo issues:**
   - **Sender domain not verified** — `EMAIL_FROM` must use a domain you verified in Brevo (Senders & IP). Use `noreply@yourdomain.com` or a verified address.
   - **Wrong API key** — Use the key from Brevo → Settings → SMTP & API → API Keys (not SMTP key).
   - **Redeploy** — After changing env vars in Railway, redeploy the backend service.

### Invitation shows "sent" but recipient doesn't receive it

1. **Check spam folder** — Ask the recipient to check Spam/Junk. Gmail and Yahoo often filter emails from unverified senders.
2. **Verify sender domain in Brevo** — Brevo → Senders & IP → add and verify your domain (e.g. `poojasankalp.org`). Add the DKIM/SPF records Brevo provides to your DNS. Without this, emails are more likely to land in spam.
3. **Use "Check delivery"** — In the schedule page, expand RSVP and click "📬 Check delivery". If it shows "delivered", the email reached the recipient's server (may still be in spam). If "bounced", the address may be invalid.
4. **Share the RSVP link manually** — Use the "🔗 Link" button to copy the invite link and send it via WhatsApp, SMS, or another channel.

### RSVP link shows wrong domain (e.g. placeholder.com)

1. **FRONTEND_URL must be in the backend service** — Railway → backend → Variables. Set `FRONTEND_URL` = `https://www.poojasankalp.org` (no trailing slash).
2. **Verify:** After redeploying, open `https://api.poojasankalp.org/config-check` — it should show `"frontend_url": "https://www.poojasankalp.org"`.
3. **Resend invitations** — Old emails have the old URL baked in. Changing FRONTEND_URL only affects NEW invitations. Use "📨 Resend" or "Send invitations" again to get emails with the correct link.
