# Manual Database Setup Instructions

Since automatic connection failed, please use one of these methods to set up the database:

## Method 1: Using pgAdmin (Easiest - Recommended)

1. **Open pgAdmin** (comes with PostgreSQL installation)
   - Search for "pgAdmin" in Windows Start Menu
   - If not found, PostgreSQL might not be installed with pgAdmin

2. **Connect to PostgreSQL Server**
   - When pgAdmin opens, it will ask for the PostgreSQL password
   - Enter the password you set during PostgreSQL installation
   - If you don't remember it, see Method 3 below

3. **Create Database**
   - In the left panel, expand "Servers" → "PostgreSQL XX" → "Databases"
   - Right-click on "Databases" → "Create" → "Database"
   - Name: `sankalpam_db`
   - Click "Save"

4. **Create User**
   - In the left panel, expand "Servers" → "PostgreSQL XX" → "Login/Group Roles"
   - Right-click on "Login/Group Roles" → "Create" → "Login/Group Role"
   - In "General" tab:
     - Name: `sankalpam_user`
   - In "Definition" tab:
     - Password: `sankalpam_password`
   - In "Privileges" tab:
     - Check "Can login?"
   - Click "Save"

5. **Grant Privileges**
   - Right-click on `sankalpam_db` → "Properties"
   - Go to "Security" tab
   - Click "+" to add a new privilege
   - Grantee: `sankalpam_user`
   - Privileges: Check "ALL"
   - Click "Save"

---

## Method 2: Using psql Command Line

1. **Open PowerShell or Command Prompt**

2. **Find PostgreSQL bin directory** (usually one of these):
   - `C:\Program Files\PostgreSQL\15\bin\`
   - `C:\Program Files\PostgreSQL\16\bin\`
   - `C:\Program Files\PostgreSQL\13\bin\`

3. **Navigate to bin directory:**
   ```powershell
   cd "C:\Program Files\PostgreSQL\15\bin"
   ```
   (Adjust version number as needed)

4. **Connect to PostgreSQL:**
   ```powershell
   .\psql.exe -U postgres
   ```
   Enter your postgres password when prompted

5. **Run these SQL commands:**
   ```sql
   CREATE DATABASE sankalpam_db;
   CREATE USER sankalpam_user WITH PASSWORD 'sankalpam_password';
   GRANT ALL PRIVILEGES ON DATABASE sankalpam_db TO sankalpam_user;
   ALTER DATABASE sankalpam_db OWNER TO sankalpam_user;
   \q
   ```

---

## Method 3: Reset PostgreSQL Password (If You Forgot It)

If you don't remember the postgres password, you can reset it:

### Quick Method (Using pgAdmin if you can still access it):
1. Open pgAdmin
2. If you can connect, right-click on PostgreSQL server → "Properties"
3. Go to "Connection" tab to see/change password

### Advanced Method (Edit pg_hba.conf):
See `RESET-POSTGRES-PASSWORD.md` in the project root for detailed instructions.

---

## After Database Setup

Once the database and user are created, verify the connection:

```powershell
cd C:\Projects\sankalpam-dev\backend
.\venv\Scripts\Activate.ps1
python -c "import psycopg2; conn = psycopg2.connect('postgresql://sankalpam_user:sankalpam_password@localhost:5432/sankalpam_db'); print('Connection successful!'); conn.close()"
```

If you see "Connection successful!", you can now start the backend:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Troubleshooting

### "psql: command not found"
- Make sure you're in the PostgreSQL bin directory
- Or add PostgreSQL bin to your PATH environment variable

### "Password authentication failed"
- You entered the wrong password
- Try resetting the password (see Method 3)

### "Database already exists"
- That's okay! The database is already set up
- Just make sure the user exists and has privileges

### "Permission denied"
- Make sure you're connecting as the `postgres` superuser
- Or use pgAdmin which handles permissions automatically
