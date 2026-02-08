# Fix: Generate Sankalpam Button Not Working

## Root Cause
**Backend server is NOT running** - This is why the generate button doesn't work.

## Solution

### Step 1: Start the Backend Server

Open PowerShell and run:

```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Keep this terminal open** - the backend must be running for the app to work.

### Step 2: Verify Backend is Running

Open in browser: http://localhost:8000/docs

You should see the API documentation page. If you see it, the backend is running.

### Step 3: Try Generating Sankalpam Again

1. Go to http://localhost:3000/sankalpam
2. Select a template (or add one via http://localhost:3000/admin if none exist)
3. Fill in location: City, State, Country
4. Click "Generate Sankalpam"

---

## If It Still Doesn't Work

### Check Browser Console (F12)
1. Open DevTools (F12)
2. Go to Console tab
3. Try generating again
4. Look for red error messages
5. Share the error message

### Check Network Tab
1. In DevTools, go to Network tab
2. Try generating again
3. Find the `/api/templates/generate` request
4. Check:
   - Status code (should be 200)
   - Request payload
   - Response body (click on the request to see details)

### Check Backend Terminal
1. Look at the backend terminal window
2. Check for error messages when you click Generate
3. Share any error messages you see

---

## Common Errors After Backend Starts

### Error: "Template not found"
- **Cause:** No templates in database or template is inactive
- **Solution:** Add templates via http://localhost:3000/admin

### Error: "Error generating audio"
- **Cause:** TTS service issue
- **Solution:** Check backend logs for TTS errors

### Error: "Authentication required"
- **Cause:** Not logged in or token expired
- **Solution:** Logout and login again

### Error: CORS error
- **Cause:** Backend CORS configuration
- **Solution:** Already configured, but verify backend is on port 8000

---

## Quick Test

After starting backend, test the API directly:

```powershell
# Test if backend is responding
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Test templates endpoint (requires auth token)
# Get token from browser localStorage after login
```

---

## Summary

**Main Issue:** Backend server not running
**Fix:** Start backend with `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

Once backend is running, the generate button should work!

