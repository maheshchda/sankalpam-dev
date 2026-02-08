# Database Setup Options

## Option 1: Install Docker Desktop (Recommended for Easy Setup)

### Steps:
1. **Download Docker Desktop:**
   - Go to: https://www.docker.com/products/docker-desktop/
   - Download Docker Desktop for Windows
   - Install it (requires restart)

2. **After Installation:**
   - Start Docker Desktop (from Start Menu)
   - Wait for it to fully start (whale icon in system tray)
   - Open PowerShell and run:
     ```
     cd "C:\Projects\sankalpam-dev"
     docker compose up -d
     ```
   - Note: Newer Docker uses `docker compose` (space, not hyphen)

3. **Verify it's running:**
   ```
   docker ps
   ```
   You should see `sankalpam_db` and `sankalpam_redis` containers

---

## Option 2: Use PostgreSQL Directly (Without Docker)

### Steps:

1. **Install PostgreSQL:**
   - Download from: https://www.postgresql.org/download/windows/
   - Install PostgreSQL (remember the password you set)
   - Default port is 5432

2. **Create Database:**
   - Open pgAdmin (comes with PostgreSQL)
   - Or use command line:
     ```
     psql -U postgres
     CREATE DATABASE sankalpam_db;
     CREATE USER sankalpam_user WITH PASSWORD 'sankalpam_password';
     GRANT ALL PRIVILEGES ON DATABASE sankalpam_db TO sankalpam_user;
     ```

3. **Update backend\.env file:**
   ```
   DATABASE_URL=postgresql://sankalpam_user:sankalpam_password@localhost:5432/sankalpam_db
   ```
   (Change port from 5433 to 5432 if using default PostgreSQL)

4. **Redis (Optional):**
   - Redis is optional for this application
   - You can skip Redis if you don't need caching
   - Or install Redis for Windows: https://github.com/microsoftarchive/redis/releases

---

## Option 3: Skip Database Setup (If Already Configured)

If you already have PostgreSQL running:
1. Just update `backend\.env` with your database connection string
2. Make sure the database and user exist
3. Run database migrations:
   ```
   cd "C:\Projects\sankalpam-dev\backend"
   .\venv\Scripts\Activate.ps1
   alembic upgrade head
   ```

---

## Quick Check: Is Database Needed?

**Yes, you need a database for:**
- User accounts and authentication
- Storing templates
- Storing generated Sankalpam
- User profiles and family members

**Without database, the backend will not start properly.**

---

## Troubleshooting

### Docker command not found:
- Docker Desktop is not installed
- Docker Desktop is not running
- Docker is not in PATH (restart terminal after installation)

### PostgreSQL connection error:
- Check if PostgreSQL service is running
- Verify username, password, and database name in `.env`
- Check if port is correct (5432 for direct install, 5433 for Docker)

### Port already in use:
- Another PostgreSQL instance might be running
- Change the port in `docker-compose.yml` or `.env`

---

**Recommendation:** Use Docker Desktop (Option 1) for easiest setup, especially if you're new to PostgreSQL.


