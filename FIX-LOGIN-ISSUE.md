# Fix: Login Failed - Troubleshooting Guide

## Common Causes

### 1. Database Not Connected (Most Likely)
**Problem:** PostgreSQL is not running or not installed.

**Check:**
```powershell
# Check if PostgreSQL is running
Get-Service postgresql* | Select-Object Name, Status

# Or check if port 5433 is listening
netstat -ano | findstr :5433
```

**Solution:**
- Install PostgreSQL (see DATABASE-SETUP.md)
- Or install Docker and run: `docker-compose up -d`

---

### 2. No Users in Database
**Problem:** Database exists but no users have been created.

**Solution - Create Admin User:**
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
python create_admin_user.py
```

**Default Admin Credentials:**
- Username: `admin`
- Password: `Admin@123`
- Email: `admin@sankalpam.com`

---

### 3. Frontend Sending Wrong Format
**Problem:** Login endpoint expects form data, but frontend might send JSON.

**Check Backend Logs:**
Look at the backend terminal for error messages when you try to login.

**Expected Format:**
The login endpoint uses `OAuth2PasswordRequestForm` which expects:
- Content-Type: `application/x-www-form-urlencoded`
- Fields: `username` and `password` (not JSON)

---

### 4. Password Hashing Issue
**Problem:** Password was hashed differently or database has old format.

**Solution:**
1. Create a new user via registration endpoint
2. Or reset password using admin tools

---

## Step-by-Step Fix

### Step 1: Verify Database Connection
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT 1')); print('Database connected!'); conn.close()"
```

### Step 2: Check if Users Exist
```powershell
python -c "from app.database import SessionLocal; from app.models import User; db = SessionLocal(); users = db.query(User).all(); print(f'Found {len(users)} users'); [print(f'  - {u.username} ({u.email})') for u in users]; db.close()"
```

### Step 3: Create Admin User (if no users exist)
```powershell
python create_admin_user.py
```

### Step 4: Test Login via API
```powershell
# Test login endpoint directly
$body = @{
    username = "admin"
    password = "Admin@123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
```

---

## Quick Diagnostic Script

Run this to check everything:

```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1

Write-Host "Checking database connection..." -ForegroundColor Yellow
python -c "from app.database import engine; from sqlalchemy import text; conn = engine.connect(); result = conn.execute(text('SELECT 1')); print('✓ Database connected'); conn.close()"

Write-Host "`nChecking users..." -ForegroundColor Yellow
python -c "from app.database import SessionLocal; from app.models import User; db = SessionLocal(); users = db.query(User).all(); print(f'Found {len(users)} users'); [print(f'  - {u.username} (active: {u.is_active})') for u in users]; db.close()"

Write-Host "`nIf no users found, run: python create_admin_user.py" -ForegroundColor Cyan
```

---

## Expected Login Flow

1. Frontend sends POST to `/api/auth/login`
2. Backend checks username exists
3. Backend verifies password hash
4. Backend checks user is active
5. Backend returns JWT token

**If any step fails, check backend logs for specific error.**

---

## Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Incorrect username or password" | User doesn't exist or wrong password | Create user or check password |
| "Inactive user" | User exists but `is_active=False` | Set `is_active=True` in database |
| Connection error | Database not running | Start PostgreSQL/Docker |
| 500 Internal Server Error | Database connection failed | Check DATABASE_URL in .env |

---

## Still Not Working?

1. **Check Backend Logs:** Look at the terminal running `uvicorn` for detailed errors
2. **Check Browser Console:** Look for network errors in DevTools (F12)
3. **Test API Directly:** Use Postman or curl to test the login endpoint
4. **Verify .env file:** Make sure DATABASE_URL is correct

