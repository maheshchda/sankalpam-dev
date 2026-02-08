# Start Frontend Server - Quick Guide

## The Problem
You're getting 404 errors because **the frontend server is not running**.

## Solution: Start the Frontend Server

### Method 1: I Just Started It For You
A new PowerShell window should have opened. Check it:
- Look for a new PowerShell window
- It should show "Starting Frontend Server..."
- Wait for it to say "✓ Ready in X seconds"
- Then refresh your browser (Ctrl+Shift+R)

### Method 2: Start It Manually

1. **Open PowerShell**
2. **Run these commands:**
   ```powershell
   cd "C:\Projects\sankalpam-dev\frontend"
   npm run dev
   ```
3. **Wait for "Ready" message**
4. **Refresh browser** (Ctrl+Shift+R)

---

## What You Should See

When the server starts, you'll see:
```
> sankalpam-frontend@0.1.0 dev
> next dev

  ▲ Next.js 14.0.4
  - Local:        http://localhost:3000
  - Ready in X seconds
```

**DO NOT close this terminal window!** Keep it open while using the app.

---

## Why You're Getting 404 Errors

- **Frontend server is not running**
- Browser tries to load the page
- Next.js static files (`_next/static/...`) don't exist because server hasn't built them
- Result: 404 errors for all static files

**Solution:** Start the server, it will build the files automatically.

---

## Verify It's Working

1. **Check the terminal** - should show "Ready"
2. **Open browser** - http://localhost:3000
3. **Check console** (F12) - no more 404 errors
4. **Page should load normally**

---

## Keep Both Servers Running

You need **TWO terminals** running:

**Terminal 1 - Backend:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd "C:\Projects\sankalpam-dev\frontend"
npm run dev
```

**Keep both open** while using the application!

---

## Quick Check

After starting, verify:
- Backend: http://localhost:8000/docs (should show API docs)
- Frontend: http://localhost:3000 (should show your app)

Both should work without errors.

