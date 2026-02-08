# How to Set Google Maps API Key

## Step 1: Get Your Google Maps API Key

If you don't have a Google Maps API key yet:

1. Go to: https://console.cloud.google.com/
2. Sign in with your Google account
3. Create a new project (or select existing one)
4. Enable these APIs:
   - Maps JavaScript API
   - Geocoding API (for reverse geocoding)
   - Places API (if needed)
5. Go to "Credentials" → "Create Credentials" → "API Key"
6. Copy your API key
7. (Optional) Restrict the API key to your domain for security

## Step 2: Set the API Key in Your Application

### Option A: Edit .env.local File Directly

1. Open: `C:\Projects\sankalpam-dev\frontend\.env.local`
2. Replace `your-google-maps-api-key` with your actual API key
3. Save the file
4. **Restart your frontend server** (important!)

### Option B: Use PowerShell Command

Run this command (replace YOUR_API_KEY with your actual key):

```powershell
cd "C:\Projects\sankalpam-dev\frontend"
$apiKey = "YOUR_API_KEY_HERE"
(Get-Content .env.local) -replace 'your-google-maps-api-key', $apiKey | Set-Content .env.local
```

## Step 3: Restart Frontend Server

After updating the API key, you MUST restart the frontend server:

1. Stop the current frontend server (Ctrl+C in the terminal)
2. Start it again:
   ```powershell
   cd "C:\Projects\sankalpam-dev\frontend"
   npm run dev
   ```

## Step 4: Verify It Works

1. Open http://localhost:3000
2. Check browser console (F12) for any Google Maps errors
3. If you see "Google Maps API key" errors, double-check the key is correct

## Important Notes

- The `.env.local` file is in the `frontend` folder
- The variable name is: `NEXT_PUBLIC_GOOGLE_MAPS_API_KEY`
- After changing `.env.local`, you MUST restart the frontend server
- The API key should start with something like: `AIza...`

## Troubleshooting

### "Google Maps API key" error in browser
- Check the API key is correct in `.env.local`
- Make sure you restarted the frontend server
- Verify the API key is enabled in Google Cloud Console

### "API key not valid" error
- Check you enabled the correct APIs (Maps JavaScript API, Geocoding API)
- Verify the API key hasn't been restricted too much
- Check billing is enabled in Google Cloud Console (free tier available)

### Changes not taking effect
- Make sure you restarted the frontend server
- Clear browser cache (Ctrl+Shift+R)
- Check `.env.local` file is in the `frontend` folder

