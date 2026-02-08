# How to Run Sankalpam Application

## Quick Start Guide

### Step 1: Start the Backend Server

Open **PowerShell Terminal 1** and run:

```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**What you'll see:**
- The virtual environment will activate (you'll see `(venv)` in your prompt)
- The server will start and show: `Uvicorn running on http://0.0.0.0:8000`
- Keep this terminal open while the application is running

**Backend will be available at:**
- API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

---

### Step 2: Start the Frontend Server

Open a **NEW PowerShell Terminal 2** (keep Terminal 1 running) and run:

```powershell
cd "C:\Projects\sankalpam-dev\frontend"
npm run dev
```

**What you'll see:**
- Dependencies will compile
- Server will start and show: `Ready on http://localhost:3000`
- Keep this terminal open while the application is running

**Frontend will be available at:**
- Application: http://localhost:3000

---

### Step 3: Access Your Application

1. Open your web browser
2. Navigate to: **http://localhost:3000**
3. Your Sankalpam application should be running!

---

## Stopping the Application

To stop the servers:
- Press `Ctrl + C` in each terminal window
- Close the terminal windows

---

## Troubleshooting

### Backend won't start?
- Make sure you activated the virtual environment: `.\venv\Scripts\Activate.ps1`
- Check if port 8000 is already in use
- Verify Python is installed: `python --version`

### Frontend won't start?
- Make sure you're in the frontend directory
- Check if port 3000 is already in use
- Try deleting `node_modules` and running `npm install` again

### Port already in use?
**Backend:** Change the port in the uvicorn command:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

**Frontend:** Change the port:
```powershell
npm run dev -- -p 3001
```

### Database connection errors?
- If using Docker, make sure Docker Desktop is running
- Start Docker services: `cd "C:\Projects\sankalpam-dev" && docker-compose up -d`
- Check the `DATABASE_URL` in `backend\.env`

---

## One-Line Commands (Copy & Paste)

**Terminal 1 - Backend:**
```powershell
cd "C:\Projects\sankalpam-dev\backend" && .\venv\Scripts\Activate.ps1 && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```powershell
cd "C:\Projects\sankalpam-dev\frontend" && npm run dev
```

---

## What Each Server Does

- **Backend (Port 8000):** Handles API requests, database operations, business logic
- **Frontend (Port 3000):** Provides the user interface, makes requests to the backend API

Both servers need to be running simultaneously for the application to work properly!

