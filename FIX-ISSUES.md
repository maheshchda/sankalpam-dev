# Fix: Backend and Frontend Not Opening

## Current Issues Found:

1. ✅ **Backend:** A new PowerShell window should have opened - check if it's running
2. ❌ **Frontend:** Node.js version is too old (18.12.1, need >= 18.17.0)

---

## Quick Fix Steps:

### Step 1: Check Backend Window
Look for a new PowerShell window that opened. It should show:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

If you see errors in that window, share them.

### Step 2: Fix Frontend - Update Node.js

**Option A: Update Node.js (Easiest)**
1. Go to: https://nodejs.org/
2. Download the **LTS version** (currently 20.x or 18.x)
3. Install it (this will update your Node.js)
4. **Close and reopen PowerShell**
5. Verify: `node --version` (should show 18.17.0 or higher)
6. Run:
   ```powershell
   cd "C:\Projects\sankalpam-dev\frontend"
   npm run dev
   ```

**Option B: Manual Start (If Backend Window Didn't Open)**

**Terminal 1 - Backend:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend (After updating Node.js):**
```powershell
cd "C:\Projects\sankalpam-dev\frontend"
npm run dev
```

---

## Verify Everything Works:

1. **Backend:** Open browser to http://localhost:8000/docs
   - Should show API documentation
   
2. **Frontend:** Open browser to http://localhost:3000
   - Should show your application

---

## If Backend Still Won't Start:

Run these commands to check:
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
python -c "import uvicorn; print('uvicorn OK')"
python -c "import fastapi; print('fastapi OK')"
```

If you see errors, run:
```powershell
pip install --upgrade pip
pip install uvicorn fastapi
```

---

## Summary:

**Main Issue:** Frontend needs Node.js >= 18.17.0
**Solution:** Update Node.js from https://nodejs.org/

**Backend:** Should be running in a separate PowerShell window. If not, start it manually using the commands above.

