# Email and SMS Verification Setup

This guide explains how to configure email and SMS verification for the Sankalpam application.

## Email Configuration (SMTP)

The application uses SMTP to send verification emails. You can use Gmail, Outlook, or any SMTP server.

### Gmail Setup

1. **Enable 2-Step Verification** on your Google account
2. **Generate an App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "Sankalpam" as the name
   - Copy the generated 16-character password

3. **Add to `.env` file**:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
EMAIL_FROM=your-email@gmail.com
FRONTEND_URL=http://localhost:3000
```

### Outlook/Hotmail Setup

```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
EMAIL_FROM=your-email@outlook.com
FRONTEND_URL=http://localhost:3000
```

### Custom SMTP Server

```env
SMTP_HOST=your-smtp-server.com
SMTP_PORT=587
SMTP_USER=your-username
SMTP_PASSWORD=your-password
EMAIL_FROM=noreply@yourdomain.com
FRONTEND_URL=http://localhost:3000
```

## SMS configuration (Brevo transactional SMS)

The app sends **phone OTPs** with Brevo’s **Transactional SMS** API (`POST /v3/transactionalSMS/send`). Same **API key** as email (REST), not the SMTP password.

### In the Brevo dashboard

1. Log in at [brevo.com](https://www.brevo.com).
2. **API key:** **Settings → SMTP & API → API Keys** → create/copy a key with permission to send SMS (v3 APIs).
3. **Enable SMS:** **Marketing → SMS** (or **Transactional SMS** in your plan). Complete any **sender registration** / compliance steps Brevo requires for your country (India: DLT/template rules may apply—follow Brevo’s wizard).
4. **Credits:** **Settings → Plan & Billing** (or SMS section)—ensure you have **SMS credits**.
5. **Sender name:** Alphanumeric label (max **11** characters), e.g. `Sankalpam`. Must be allowed in your Brevo SMS settings.

### Environment variables

```env
BREVO_API_KEY=your-brevo-api-key
SMS_SENDER=Sankalpam
# Optional: default is sms. Use whatsapp or both after WhatsApp is configured (below).
# PHONE_VERIFICATION_CHANNEL=sms
```

| Variable | Purpose |
|----------|---------|
| `BREVO_API_KEY` | REST API key (Settings → API Keys) |
| `SMS_SENDER` | SMS originator name (≤11 chars) |
| `PHONE_VERIFICATION_CHANNEL` | `sms` (default) \| `whatsapp` \| `both` |

### Verify SMS

- Register or use **Resend phone OTP** and watch the **backend logs**: success prints `Verification SMS sent ... via Brevo`; errors print `Brevo SMS API error` with status/body.
- Numbers are normalized to **digits + country code** (10-digit India → `91` prefix). Use a real handset for testing.

---

## WhatsApp configuration (Brevo + Meta)

OTP over **WhatsApp** uses Brevo’s **transactional WhatsApp** API (`POST /v3/whatsapp/sendMessage`). This is **not** plain SMS; you need a **WhatsApp Business** number connected in Brevo and a **Meta-approved message template** that includes a variable for the OTP.

### In Brevo (high level)

1. **Connect WhatsApp:** Brevo docs: [Activating WhatsApp](https://developers.brevo.com/docs/whatsapp-campaigns-1) / in-app **Conversations → WhatsApp** (wording may vary). Complete **Meta Business** verification if prompted.
2. **Note your WhatsApp number** as Brevo shows it (with country code, digits only for the API), e.g. `919876543210`.
3. **Create a template** in Brevo/Meta for OTP (category typically **Authentication** or **Utility**, per Meta rules). Example body:  
   `Your Sankalpam code is {{OTP}}. Valid 10 minutes.`  
   Use **one** variable whose name you will map in env (below). Wait until Meta **approves** the template.
4. Copy the **template ID** Brevo exposes for API use (integer).

### In this app

Map the template variable name **exactly** to `BREVO_WHATSAPP_OTP_PARAM` (default `OTP`). The app sends:

`params: { "<BREVO_WHATSAPP_OTP_PARAM>": "<6-digit otp>" }`

```env
BREVO_API_KEY=your-brevo-api-key
PHONE_VERIFICATION_CHANNEL=whatsapp
# or both — sends SMS + WhatsApp when both are configured

BREVO_WHATSAPP_SENDER_NUMBER=919876543210
BREVO_WHATSAPP_OTP_TEMPLATE_ID=123456
BREVO_WHATSAPP_OTP_PARAM=OTP
```

| Variable | Purpose |
|----------|---------|
| `BREVO_WHATSAPP_SENDER_NUMBER` | Your Brevo-connected WA number, digits only (with country code) |
| `BREVO_WHATSAPP_OTP_TEMPLATE_ID` | Integer template ID from Brevo |
| `BREVO_WHATSAPP_OTP_PARAM` | Template variable name for the OTP (default `OTP`) |

If `PHONE_VERIFICATION_CHANNEL` is `whatsapp` or `both` but WhatsApp env is incomplete, the app **logs a fallback** and uses **SMS only** (if SMS is configured).

### Verify WhatsApp

- Trigger OTP; check logs for `Verification WhatsApp sent ... via Brevo` or `Brevo WhatsApp API error` with response body.
- **First message** to a user must be **template-based** (this flow always uses a template).

### Official references

- [Transactional SMS](https://developers.brevo.com/docs/transactional-sms-endpoints)  
- [Send WhatsApp message](https://developers.brevo.com/reference/send-whatsapp-message)

## Development Mode

If you don't configure SMTP or Brevo credentials, the application will run in **development mode**:
- Email tokens and SMS OTPs will be printed to the console
- No actual emails or SMS will be sent
- You can copy the tokens/OTPs from the console to verify accounts

This is useful for local development and testing.

## Testing

1. **Test Email**:
   - Register a new user or click "Resend Email" on the profile page
   - Check your email inbox (or console in dev mode)
   - Use the verification token on `/verify` page

2. **Test SMS**:
   - Click "Resend OTP" on the profile page
   - Check your phone (or console in dev mode)
   - Use the OTP on `/verify` page

## Troubleshooting

### Email not sending:
- Check SMTP credentials are correct
- For Gmail, ensure you're using an App Password, not your regular password
- Check firewall/network allows SMTP connections
- Check spam folder

### SMS not sending:
- Verify BREVO_API_KEY is correct (from Brevo Settings → API Keys)
- Ensure Transactional SMS is enabled in your Brevo account
- Check Brevo SMS credits/balance
- Phone number should include country code (e.g. 919876543210 for India)

### Development mode not working:
- Ensure `SECRET_KEY` in `.env` is set to `"your-secret-key-change-in-production"`
- Check backend console output for tokens/OTPs
