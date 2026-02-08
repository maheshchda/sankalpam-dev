# Debug: Generate Sankalpam Not Working

## Quick Checks

### 1. Did you restart the frontend server after adding the API key?
**This is CRITICAL!** Environment variables are only loaded when the server starts.

**Solution:**
```powershell
# Stop the frontend server (Ctrl+C in the terminal)
# Then restart:
cd "C:\Projects\sankalpam-dev\frontend"
npm run dev
```

### 2. Is the backend server running?
The Generate button needs the backend API to work.

**Check:**
- Open http://localhost:8000/docs in browser
- If you see API documentation, backend is running
- If you get an error, backend is NOT running

**Start backend:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Check Browser Console for Errors

1. Open http://localhost:3000/sankalpam
2. Press **F12** to open DevTools
3. Go to **Console** tab
4. Click "Generate Sankalpam" button
5. Look for **red error messages**
6. **Share the error message** you see

### 4. Check Network Tab

1. In DevTools, go to **Network** tab
2. Click "Generate Sankalpam" button
3. Look for the `/api/templates/generate` request
4. Click on it to see:
   - **Status code** (should be 200)
   - **Request payload** (what data was sent)
   - **Response** (what the server returned)
5. If status is not 200, check the response for error details

### 5. Verify API Key is Set Correctly

**Check the .env.local file:**
```powershell
cd "C:\Projects\sankalpam-dev\frontend"
Get-Content .env.local
```

**Should show:**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Common mistakes:**
- ❌ Still says `your-google-maps-api-key` (not replaced)
- ❌ Has extra spaces or quotes
- ❌ Missing the `NEXT_PUBLIC_` prefix
- ❌ File is in wrong location (should be in `frontend` folder)

---

## Common Error Messages & Solutions

### Error: "Failed to generate Sankalpam"
- **Check:** Backend terminal for detailed error
- **Common causes:**
  - Backend not running
  - Database connection issue
  - TTS service error
  - Missing template

### Error: "Template not found"
- **Solution:** Add templates via http://localhost:3000/admin

### Error: "Please provide location information"
- **Solution:** Fill in City, State, and Country fields

### Error: "Please select a template"
- **Solution:** Click on a template to select it

### Error: CORS error
- **Check:** Backend is running on port 8000
- **Check:** Frontend is running on port 3000

### Error: 401 Unauthorized
- **Solution:** You're not logged in - login again

### Error: 500 Internal Server Error
- **Check:** Backend terminal for detailed error message
- **Common causes:**
  - Database issue
  - TTS service not working
  - Missing dependencies

---

## Step-by-Step Debugging

### Step 1: Verify Environment
```powershell
# Check backend is running
Invoke-WebRequest -Uri "http://localhost:8000/health"

# Check frontend is running  
Invoke-WebRequest -Uri "http://localhost:3000"
```

### Step 2: Check Browser Console
1. Open http://localhost:3000/sankalpam
2. F12 → Console tab
3. Try generating
4. Note any errors

### Step 3: Check Network Request
1. F12 → Network tab
2. Try generating
3. Find `/api/templates/generate` request
4. Check status and response

### Step 4: Check Backend Logs
1. Look at backend terminal
2. Check for error messages when you click Generate
3. Note any stack traces

---

## Most Likely Issues

1. **Frontend server not restarted** after adding API key (90% of cases)
2. **Backend server not running**
3. **Missing required fields** (template, location)
4. **Not logged in** (authentication expired)

---

## Quick Fix Checklist

- [ ] Restarted frontend server after adding API key?
- [ ] Backend server is running?
- [ ] Logged in to the application?
- [ ] Selected a template?
- [ ] Filled in City, State, Country?
- [ ] Checked browser console for errors?
- [ ] Checked backend terminal for errors?

---

## Still Not Working?

**Please share:**
1. Error message from browser console (F12 → Console)
2. Error message from backend terminal
3. Network request details (F12 → Network → click on the request)
4. What happens when you click Generate? (nothing? error message? loading forever?)

