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

## SMS Configuration (Brevo)

The application uses Brevo Transactional SMS (same account as email) to send verification OTPs.

### Brevo SMS Setup

1. **Use your existing Brevo account** (same as email)
2. **Get your API key** from Brevo: Settings → SMTP & API → API Keys
3. **Enable Transactional SMS** in your Brevo account (may require activation)
4. **Add to `.env` file**:
```env
BREVO_API_KEY=your-brevo-api-key
SMS_SENDER=Sankalpam
```

- `BREVO_API_KEY`: Your Brevo API key (same key used for other Brevo API features)
- `SMS_SENDER`: Sender name shown in SMS (max 11 alphanumeric chars, e.g. "Sankalpam")

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
