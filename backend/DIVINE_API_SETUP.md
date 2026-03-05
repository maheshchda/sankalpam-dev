# Divine API Setup (Panchang only)

This app **does not use a separate "Sankalpam API"** from Divine. Sankalpam text is generated using **our own Telugu/Sanskrit templates** stored in `backend/templates/`.

## What we use Divine API for

We only call **one** Divine API:

- **Find Panchang** (Daily Panchang)  
  Used to fill **పక్షే, తిథౌ, నక్షత్రే, యోగే, కరణే** (paksha, tithi, nakshatra, yoga, karana) in the sankalpam.

So you do **not** need to find or enable any "Sankalpam API" in the Divine dashboard.

## What you need in the Divine dashboard

Divine’s docs ask for:

1. **API Key**
2. **Access Token** (Bearer token for the `Authorization` header)

In the dashboard you may only see something like **"Default Key"**. That is often the **API Key**. The **Access Token** might be:

- On the same page (e.g. "API Key" and "Access Token", or "Default Key" and another token), or  
- Under **Profile** / **API credentials** / **Profile Details**.

If Divine only gives you **one** value (e.g. "Default Key"):

- Set that as **API Key** in `.env` (see below).
- If there is a separate **Access Token**, set that too.  
- If there is no separate token, some accounts use the same value for both; in that case you can set the **same value** for both in `.env` and see if the Panchang test passes.

## .env configuration

In the backend `.env` file, set:

```env
# Use the same value for both if Divine only shows one "Default Key"
Divine_API_Key=your-api-key-here
Divine_Access_Token=your-access-token-here
```

Or:

```env
DIVINE_API_KEY=your-api-key-here
DIVINE_ACCESS_TOKEN=your-access-token-here
```

If you only have one credential (e.g. Default Key), try:

```env
Divine_API_Key=your-default-key
Divine_Access_Token=your-default-key
```

## Verify

From the backend folder:

```bash
python check_divineapi.py
```

If the **Panchang API (find-panchang)** section shows `Status: 200` and `-> Panchang API is working.`, you’re set. The "Sankalpam API" part of the script is optional; the app uses local templates for sankalpam text.
