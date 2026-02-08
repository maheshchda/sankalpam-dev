# How to Get Google Maps API Key - Step by Step Guide

## Step 1: Go to Google Cloud Console

1. Open your web browser
2. Go to: **https://console.cloud.google.com/**
3. Sign in with your Google account

---

## Step 2: Create or Select a Project

1. At the top of the page, click on the **project dropdown** (next to "Google Cloud")
2. If you have an existing project, select it
3. If you don't have a project, click **"New Project"**:
   - Enter a project name (e.g., "Sankalpam App")
   - Click **"Create"**
   - Wait a few seconds for the project to be created
   - Select the new project from the dropdown

---

## Step 3: Enable Required APIs

You need to enable these APIs for your project:

### Enable Maps JavaScript API:
1. In the left sidebar, click **"APIs & Services"** → **"Library"**
2. Search for **"Maps JavaScript API"**
3. Click on it
4. Click **"Enable"** button
5. Wait for it to enable

### Enable Geocoding API:
1. Go back to **"APIs & Services"** → **"Library"**
2. Search for **"Geocoding API"**
3. Click on it
4. Click **"Enable"** button
5. Wait for it to enable

**Note:** You might see a billing warning. Google provides $200 free credit per month, which is usually enough for development and small applications.

---

## Step 4: Create API Key

1. Go to **"APIs & Services"** → **"Credentials"** (in the left sidebar)
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"API key"** from the dropdown
4. Your API key will be created and displayed in a popup
5. **Copy the API key** - it will look like: `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
6. Click **"Close"** (don't restrict it yet if you're just testing)

---

## Step 5: (Optional) Set Up Billing

Google requires billing to be enabled, but you get $200 free credit monthly:

1. Go to **"Billing"** in the left sidebar
2. Click **"Link a billing account"**
3. Follow the prompts to add a payment method
4. **Don't worry** - you won't be charged unless you exceed the free tier
5. The free tier covers most small to medium applications

---

## Step 6: (Recommended) Restrict Your API Key

For security, restrict your API key:

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click on your API key to edit it
3. Under **"API restrictions"**:
   - Select **"Restrict key"**
   - Check only: **"Maps JavaScript API"** and **"Geocoding API"**
4. Under **"Application restrictions"** (optional but recommended):
   - Select **"HTTP referrers (web sites)"**
   - Add: `http://localhost:3000/*` (for development)
   - Add: `http://127.0.0.1:3000/*` (for development)
   - Add your production domain when you deploy (e.g., `https://yourdomain.com/*`)
5. Click **"Save"**

---

## Step 7: Use Your API Key

1. Copy your API key (it starts with `AIza...`)
2. Open: `C:\Projects\sankalpam-dev\frontend\.env.local`
3. Replace `your-google-maps-api-key` with your actual key:
   ```
   NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
4. Save the file
5. **Restart your frontend server** (important!)

---

## Quick Reference

- **Google Cloud Console:** https://console.cloud.google.com/
- **Maps JavaScript API:** Used for displaying maps
- **Geocoding API:** Used for converting addresses to coordinates and vice versa
- **Free Tier:** $200 credit per month (usually enough for development)

---

## Troubleshooting

### "API key not valid" error
- Make sure you enabled both Maps JavaScript API and Geocoding API
- Check that billing is enabled (even if you're using free tier)
- Verify the API key is correct (no extra spaces)

### "This API project is not authorized" error
- Go back to APIs & Services → Library
- Make sure both APIs are enabled (should show "Enabled" status)

### Billing required warning
- You need to add a payment method, but won't be charged for free tier usage
- The $200 monthly credit covers most development needs

### API key restrictions too strict
- If you restricted the key and it's not working, temporarily remove restrictions to test
- Then add restrictions back once you confirm it works

---

## Cost Information

- **Free Tier:** $200 credit per month
- **Maps JavaScript API:** Free for first 28,000 loads per month
- **Geocoding API:** Free for first 40,000 requests per month
- For development and small apps, you'll likely stay within the free tier

---

## Security Best Practices

1. **Never commit your API key to Git** - it's already in `.env.local` which should be in `.gitignore`
2. **Restrict your API key** to only the APIs you need
3. **Add HTTP referrer restrictions** to limit which websites can use your key
4. **Monitor usage** in Google Cloud Console to detect any unauthorized use

---

## Next Steps

After getting your API key:
1. Add it to `.env.local` file
2. Restart frontend server
3. Test the application - maps and location features should work!

