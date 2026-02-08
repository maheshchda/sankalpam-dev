# Troubleshooting Guide

## Issue 1: Frontend - Node.js Version Too Old

**Problem:** Node.js 18.12.1 is installed, but Next.js requires >= 18.17.0

**Solution Options:**

### Option A: Update Node.js (Recommended)
1. Download the latest LTS version from: https://nodejs.org/
2. Install it (this will update your Node.js)
3. Restart PowerShell
4. Verify: `node --version` (should show 18.17.0 or higher)
5. Run: `cd "C:\Projects\sankalpam-dev\frontend" && npm run dev`

### Option B: Use NVM (Node Version Manager)
1. Install nvm-windows from: https://github.com/coreybutler/nvm-windows
2. Run: `nvm install 18.17.0`
3. Run: `nvm use 18.17.0`
4. Run: `cd "C:\Projects\sankalpam-dev\frontend" && npm run dev`

### Option C: Downgrade Next.js (Not Recommended)
Edit `frontend/package.json` and change Next.js to a version compatible with Node 18.12.1

---

## Issue 2: Backend Dependencies

**Problem:** Some packages may not have installed completely

**Solution:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv
```

---

## Issue 3: Port Already in Use

**Problem:** Port 8000 or 3000 is already in use

**Solution:**

**Backend - Use different port:**
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```
Then update `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

**Frontend - Use different port:**
```powershell
npm run dev -- -p 3001
```

---

## Issue 4: Backend Won't Start

**Check:**
1. Virtual environment is activated: `.\venv\Scripts\Activate.ps1`
2. Dependencies are installed: `pip list | findstr uvicorn`
3. main.py exists: `Test-Path main.py`
4. No syntax errors: `python -m py_compile main.py`

---

## Issue 5: Frontend Won't Start

**Check:**
1. Node modules installed: `Test-Path node_modules`
2. package.json exists: `Test-Path package.json`
3. Node version: `node --version` (should be >= 18.17.0)

**Reinstall if needed:**
```powershell
cd "C:\Projects\sankalpam-dev\frontend"
Remove-Item -Recurse -Force node_modules
npm install
npm run dev
```

---

## Quick Fix Commands

**Reinstall Backend Dependencies:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

**Reinstall Frontend Dependencies:**
```powershell
cd "C:\Projects\sankalpam-dev\frontend"
Remove-Item -Recurse -Force node_modules
npm install
```

**Check What's Running on Ports:**
```powershell
netstat -ano | findstr :8000
netstat -ano | findstr :3000
```

