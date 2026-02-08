# Setting Up Sankalpam Without Docker

## Prerequisites

1. **PostgreSQL** must be installed and running
2. **Redis** is optional (can skip if not needed)

---

## Step 1: Install PostgreSQL (if not installed)

1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Install PostgreSQL (remember the password you set for `postgres` user)
3. During installation, note the port (default is 5432)
4. Make sure PostgreSQL service is running

**Check if PostgreSQL is running:**
- Open Services (Win+R, type `services.msc`)
- Look for "postgresql" service
- Make sure it's "Running"

---

## Step 2: Create Database and User

### Option A: Using pgAdmin (GUI - Easier)

1. Open **pgAdmin** (comes with PostgreSQL)
2. Connect to PostgreSQL server (use password you set during installation)
3. Right-click on "Databases" → "Create" → "Database"
   - Name: `sankalpam_db`
4. Right-click on "Login/Group Roles" → "Create" → "Login/Group Role"
   - Name: `sankalpam_user`
   - Password: `sankalpam_password`
   - Privileges tab: Check "Can login?"
5. Right-click on `sankalpam_db` → "Properties" → "Security"
   - Add `sankalpam_user` with ALL privileges

### Option B: Using Command Line

1. Open Command Prompt or PowerShell
2. Navigate to PostgreSQL bin folder (usually `C:\Program Files\PostgreSQL\15\bin`)
3. Run:
   ```
   psql -U postgres
   ```
   (Enter your postgres password when prompted)
4. Run these commands:
   ```sql
   CREATE DATABASE sankalpam_db;
   CREATE USER sankalpam_user WITH PASSWORD 'sankalpam_password';
   GRANT ALL PRIVILEGES ON DATABASE sankalpam_db TO sankalpam_user;
   \q
   ```

---

## Step 3: Update Backend Configuration

1. Open `backend\.env` file
2. Update the `DATABASE_URL` line:
   ```
   DATABASE_URL=postgresql://sankalpam_user:sankalpam_password@localhost:5432/sankalpam_db
   ```
   (Change port 5432 if you used a different port during installation)

3. **Redis is optional** - you can leave `REDIS_URL` as is or remove it if not using Redis

---

## Step 4: Run Database Migrations

1. Open PowerShell
2. Navigate to backend folder:
   ```
   cd "C:\Projects\sankalpam-dev\backend"
   ```
3. Activate virtual environment:
   ```
   .\venv\Scripts\Activate.ps1
   ```
4. Run migrations:
   ```
   alembic upgrade head
   ```

---

## Step 5: Start Backend Server

**Option A: Using Batch File**
- Double-click `START-BACKEND.bat` in the `backend` folder

**Option B: Manual**
1. Open PowerShell
2. Navigate to backend:
   ```
   cd "C:\Projects\sankalpam-dev\backend"
   ```
3. Activate virtual environment:
   ```
   .\venv\Scripts\Activate.ps1
   ```
4. Start server:
   ```
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this window open!**

---

## Step 6: Start Frontend Server

**Option A: Using Batch File**
- Double-click `START-FRONTEND.bat` in the `frontend` folder

**Option B: Manual**
1. Open a **NEW** PowerShell window
2. Navigate to frontend:
   ```
   cd "C:\Projects\sankalpam-dev\frontend"
   ```
3. Start server:
   ```
   npm run dev
   ```

**You should see:**
```
✓ Ready in X seconds
○ Local: http://localhost:3000
```

**Keep this window open!**

---

## Step 7: Access Application

1. Open browser
2. Go to: **http://localhost:3000**
3. Login and use the application

---

## Troubleshooting

### PostgreSQL Connection Error
- Check if PostgreSQL service is running: `services.msc`
- Verify username, password, and database name in `.env`
- Check if port is correct (default 5432)
- Make sure database and user exist

### Migration Errors
- Make sure database exists
- Check user has proper permissions
- Try: `alembic upgrade head --sql` to see SQL without executing

### Backend Won't Start
- Check PostgreSQL is running
- Verify `.env` file has correct `DATABASE_URL`
- Check virtual environment is activated
- Look for error messages in terminal

### Frontend Won't Start
- Make sure backend is running first
- Check Node.js version: `node --version` (needs 18.17.0+)
- Try deleting `node_modules` and `.next`, then `npm install`

---

## Quick Commands Reference

```powershell
# Check PostgreSQL service
Get-Service -Name "*postgresql*"

# Start PostgreSQL service (if stopped)
Start-Service postgresql-x64-15  # (adjust version number)

# Check if PostgreSQL is listening
Test-NetConnection -ComputerName localhost -Port 5432
```

---

## Summary

**Without Docker, you need:**
1. ✅ PostgreSQL installed and running
2. ✅ Database `sankalpam_db` created
3. ✅ User `sankalpam_user` created with password
4. ✅ `backend\.env` updated with correct `DATABASE_URL`
5. ✅ Database migrations run (`alembic upgrade head`)
6. ✅ Backend server running (port 8000)
7. ✅ Frontend server running (port 3000)

**Redis is optional** - the application will work without it, but some features might be slower.

---

Last Updated: January 2025


