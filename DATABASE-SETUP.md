# PostgreSQL Database Setup for Sankalpam

## Current Situation
- ❌ Docker is NOT installed
- ❌ PostgreSQL database is NOT running
- ✅ Application expects PostgreSQL on port 5433

## Solution Options

### Option 1: Install PostgreSQL Directly (Recommended if Docker not available)

#### Step 1: Download PostgreSQL
1. Go to: https://www.postgresql.org/download/windows/
2. Download the PostgreSQL installer
3. Or use direct link: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads

#### Step 2: Install PostgreSQL
1. Run the installer
2. **Important:** During installation:
   - Set port to: **5433** (not default 5432)
   - Set username: **sankalpam_user**
   - Set password: **sankalpam_password**
   - Set database name: **sankalpam_db**
3. Complete the installation

#### Step 3: Verify Installation
```powershell
psql -U sankalpam_user -d sankalpam_db -h localhost -p 5433
```
Enter password when prompted: `sankalpam_password`

#### Step 4: Update .env if needed
The `.env` file is already configured correctly:
```
DATABASE_URL=postgresql://sankalpam_user:sankalpam_password@localhost:5433/sankalpam_db
```

---

### Option 2: Install Docker Desktop (Alternative)

#### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install Docker Desktop
3. Start Docker Desktop

#### Step 2: Start Database Services
```powershell
cd "C:\Projects\sankalpam-dev"
docker-compose up -d
```

#### Step 3: Verify Services
```powershell
docker ps
```
Should show `sankalpam_db` and `sankalpam_redis` containers running.

---

## After Database is Running

### Step 1: Run Database Migrations (if needed)
```powershell
cd "C:\Projects\sankalpam-dev\backend"
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

### Step 2: Verify Connection
```powershell
python -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://sankalpam_user:sankalpam_password@localhost:5433/sankalpam_db'); conn = engine.connect(); print('Database connected!'); conn.close()"
```

---

## Quick Setup Script (PostgreSQL Direct Install)

If you install PostgreSQL directly, use these settings:
- **Port:** 5433
- **Username:** sankalpam_user
- **Password:** sankalpam_password
- **Database:** sankalpam_db

---

## Troubleshooting

### Can't connect to database?
1. Check PostgreSQL service is running:
   ```powershell
   Get-Service postgresql*
   ```
2. Check port 5433 is listening:
   ```powershell
   netstat -ano | findstr :5433
   ```

### Port 5433 already in use?
- Change port in PostgreSQL config
- Update `.env` file with new port

### Wrong credentials?
- Update `backend\.env` file with correct credentials

