# Sankalpam Application - Quick Start Guide

## Prerequisites
- Python 3.x installed
- Node.js 18.17.0 or higher installed
- PostgreSQL database running (via Docker or direct installation)
- Docker Desktop (optional, for PostgreSQL and Redis)

---

## Starting the Application

### Step 1: Start Database (if using Docker)

**Option A: Using Docker (Recommended)**
1. Open PowerShell or Command Prompt
2. Navigate to project folder:
   ```
   cd "C:\Projects\sankalpam-dev"
   ```
3. Start Docker services:
   ```
   docker-compose up -d
   ```
4. Wait for services to start (PostgreSQL on port 5433, Redis on port 6379)

**Option B: Using Direct PostgreSQL Installation**
- Make sure PostgreSQL is running on your system
- Update `backend\.env` with your PostgreSQL connection details

---

### Step 2: Start Backend Server

**Easiest Method:**
- Double-click `START-BACKEND.bat` in the `backend` folder

**Manual Method:**
1. Open a **NEW** PowerShell or Command Prompt window
2. Navigate to backend folder:
   ```
   cd "C:\Projects\sankalpam-dev\backend"
   ```
3. Activate virtual environment:
   ```
   .\venv\Scripts\Activate.ps1
   ```
   (In CMD, use: `venv\Scripts\activate.bat`)
4. Start the server:
   ```
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Backend URLs:**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

**Keep this window open!**

---

### Step 3: Start Frontend Server

**Easiest Method:**
- Double-click `START-FRONTEND.bat` in the `frontend` folder

**Manual Method:**
1. Open a **NEW** PowerShell or Command Prompt window
2. Navigate to frontend folder:
   ```
   cd "C:\Projects\sankalpam-dev\frontend"
   ```
3. Start the development server:
   ```
   npm run dev
   ```

**You should see:**
```
✓ Ready in X seconds
○ Local: http://localhost:3000
```

**Frontend URL:**
- Application: http://localhost:3000

**Keep this window open!**

---

## Accessing the Application

1. Open your web browser
2. Go to: **http://localhost:3000**
3. Login with your credentials
4. Navigate to **Sankalpam** page to generate Sankalpam

---

## Stopping the Application

1. **Stop Frontend:** Press `CTRL+C` in the frontend terminal window
2. **Stop Backend:** Press `CTRL+C` in the backend terminal window
3. **Stop Database (if using Docker):**
   ```
   cd "C:\Projects\sankalpam-dev"
   docker-compose down
   ```

---

## Troubleshooting

### Backend won't start
- Make sure virtual environment is activated (you should see `(venv)` in your prompt)
- Check if port 8000 is already in use
- Verify PostgreSQL is running

### Frontend won't start
- Make sure Node.js version is 18.17.0 or higher
- Try deleting `node_modules` and `.next` folder, then run `npm install` again
- Check if port 3000 is already in use

### Database connection errors
- Verify Docker services are running: `docker ps`
- Check `backend\.env` file has correct database URL
- Ensure PostgreSQL is accessible on the configured port

### TTS (Text-to-Speech) not working
- Verify Google Cloud TTS credentials file exists at `backend\app\credentials.json`
- Check backend terminal for TTS service logs
- Ensure TTS services are installed: `pip install google-cloud-texttospeech gtts edge-tts`

---

## Quick Reference

| Service | Port | URL | Status Check |
|---------|------|-----|--------------|
| Frontend | 3000 | http://localhost:3000 | Browser |
| Backend API | 8000 | http://localhost:8000 | http://localhost:8000/docs |
| PostgreSQL | 5433 | localhost:5433 | `docker ps` |
| Redis | 6379 | localhost:6379 | `docker ps` |

---

## File Locations

- **Backend:** `C:\Projects\sankalpam-dev\backend`
- **Frontend:** `C:\Projects\sankalpam-dev\frontend`
- **Backend Environment:** `backend\.env`
- **Frontend Environment:** `frontend\.env.local`
- **Start Backend Script:** `backend\START-BACKEND.bat`
- **Start Frontend Script:** `frontend\START-FRONTEND.bat`

---

## Important Notes

1. **Always start Backend BEFORE Frontend** (frontend depends on backend API)
2. **Keep both terminal windows open** while using the application
3. **Backend auto-reloads** when you change code (thanks to `--reload` flag)
4. **Frontend auto-refreshes** in browser when you change code
5. **Database must be running** before starting backend

---

## Support

If you encounter issues:
1. Check the terminal windows for error messages
2. Verify all services are running (see Quick Reference table)
3. Check environment variables in `.env` files
4. Review the troubleshooting section above

---

**Last Updated:** January 2025


