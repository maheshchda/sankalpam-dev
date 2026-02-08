# Fix: Generate Sankalpam Not Working

## Issue
The "Generate Sankalpam" button on http://localhost:3000/sankalpam is not working even after entering required data.

## Common Causes & Solutions

### 1. Backend Server Not Running
**Check:**
- Is the backend server running on http://localhost:8000?
- Check the backend terminal for errors

**Solution:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

### 2. Missing Required Data
**Check:**
- Template selected?
- City, State, Country filled in?
- User logged in?

**The form requires:**
- ✅ A template must be selected
- ✅ City (required)
- ✅ State (required)  
- ✅ Country (required)
- ✅ User must be logged in

---

### 3. Browser Console Errors
**Check:**
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for red error messages
4. Go to Network tab
5. Try generating again
6. Check the `/api/templates/generate` request:
   - Status code (should be 200)
   - Response body (check for error messages)

---

### 4. API Endpoint Issues
**Test the API directly:**
```powershell
# Check if templates endpoint works
Invoke-RestMethod -Uri "http://localhost:8000/api/templates/templates" -Method Get

# Test generate endpoint (replace with actual data)
$body = @{
    template_id = 1
    location_city = "Hyderabad"
    location_state = "Telangana"
    location_country = "India"
    date = (Get-Date).ToISOString()
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/templates/generate" -Method Post -Body $body -ContentType "application/json"
```

---

### 5. Database Issues
**Check:**
- Are templates in the database?
- Is the database connected?

**Verify:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
python -c "from app.database import SessionLocal; from app.models import Template; db = SessionLocal(); templates = db.query(Template).all(); print(f'Found {len(templates)} templates'); db.close()"
```

---

### 6. CORS Issues
**Check backend logs for CORS errors**

**Solution:** CORS is already configured in main.py, but verify:
- Frontend URL is in allowed origins
- Backend is running on port 8000

---

### 7. Authentication Token Issues
**Check:**
- Is user logged in?
- Is auth token valid?

**Solution:**
- Logout and login again
- Check browser localStorage for token

---

## Step-by-Step Debugging

### Step 1: Check Browser Console
1. Open http://localhost:3000/sankalpam
2. Press F12 to open DevTools
3. Go to Console tab
4. Try to generate Sankalpam
5. Note any errors

### Step 2: Check Network Tab
1. In DevTools, go to Network tab
2. Try generating again
3. Find the `/api/templates/generate` request
4. Check:
   - Status code
   - Request payload
   - Response body

### Step 3: Check Backend Logs
1. Look at the backend terminal
2. Check for error messages when you click Generate
3. Note any stack traces

### Step 4: Verify Data
1. Make sure all required fields are filled:
   - Template selected
   - City entered
   - State entered
   - Country entered

---

## Quick Test

Run this in browser console (F12) to test the API:

```javascript
// Test if templates endpoint works
fetch('http://localhost:8000/api/templates/templates')
  .then(r => r.json())
  .then(data => console.log('Templates:', data))
  .catch(err => console.error('Error:', err))

// Test generate endpoint (replace with your data)
fetch('http://localhost:8000/api/templates/generate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN_HERE'
  },
  body: JSON.stringify({
    template_id: 1,
    location_city: 'Hyderabad',
    location_state: 'Telangana',
    location_country: 'India',
    date: new Date().toISOString()
  })
})
  .then(r => r.json())
  .then(data => console.log('Generated:', data))
  .catch(err => console.error('Error:', err))
```

---

## Most Common Issues

1. **Backend not running** - Start the backend server
2. **Missing required fields** - Fill in all required location fields
3. **No templates in database** - Contact admin to add templates
4. **Authentication expired** - Logout and login again
5. **CORS error** - Check backend CORS configuration

---

## Still Not Working?

1. **Share the error message** from browser console
2. **Share the backend error** from terminal
3. **Share the network request details** from DevTools Network tab

