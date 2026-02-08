# Using pgAdmin Instead of psql

If you don't have `psql` in your PATH, you can use **pgAdmin** (GUI tool) instead.

## pgAdmin is Already Installed

pgAdmin comes with PostgreSQL installation. You don't need to install it separately.

## How to Open pgAdmin

1. **Search in Start Menu:**
   - Press `Win` key
   - Type "pgAdmin"
   - Click on "pgAdmin 4" or "pgAdmin"

2. **Or find it in:**
   - `C:\Program Files\PostgreSQL\[version]\pgAdmin 4\bin\pgAdmin4.exe`

## Using pgAdmin to Create Database

### Step 1: Connect to PostgreSQL

1. Open pgAdmin
2. In the left panel, expand "Servers"
3. Click on "PostgreSQL [version]" (or your server name)
4. **If it asks for password:**
   - Try common passwords: `postgres`, `admin`, or empty
   - If none work, you'll need to reset password (see RESET-POSTGRES-PASSWORD.md)

### Step 2: Create Database

1. Right-click on "Databases" → "Create" → "Database"
2. In the "General" tab:
   - **Name:** `sankalpam_db`
3. In the "Security" tab:
   - **Owner:** Select or type `sankalpam_user` (we'll create this next)
4. Click "Save"

### Step 3: Create User

1. Expand "Login/Group Roles" in the left panel
2. Right-click → "Create" → "Login/Group Role"
3. In the "General" tab:
   - **Name:** `sankalpam_user`
4. In the "Definition" tab:
   - **Password:** `sankalpam_password`
   - **Password expiration:** Uncheck (or leave as is)
5. In the "Privileges" tab:
   - Check "Can login?"
   - Check "Create databases?" (optional)
6. Click "Save"

### Step 4: Grant Privileges

1. Right-click on `sankalpam_db` database → "Properties"
2. Go to "Security" tab
3. Click "+" to add a new privilege
4. Select:
   - **Grantee:** `sankalpam_user`
   - **Privileges:** Check "ALL" or select specific privileges
5. Click "Save"

### Alternative: Set Database Owner

1. Right-click on `sankalpam_db` → "Properties"
2. Go to "General" tab
3. **Owner:** Select `sankalpam_user` from dropdown
4. Click "Save"

## Done!

After creating the database and user in pgAdmin:

1. The backend should be able to connect
2. Start the backend server:
   ```powershell
   cd "C:\Projects\sankalpam-dev\backend"
   .\venv\Scripts\Activate.ps1
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

## If pgAdmin Asks for Password

If pgAdmin asks for the postgres password and you don't remember it:

1. **Try common passwords:**
   - `postgres`
   - `admin`
   - `password`
   - Empty (just press Enter)

2. **If none work:**
   - See RESET-POSTGRES-PASSWORD.md to reset the password
   - Or use the Python script: `create_db_without_postgres.py`

## Advantages of pgAdmin

- ✅ No need to add PostgreSQL to PATH
- ✅ Visual interface (easier than command line)
- ✅ Can see all databases, users, tables
- ✅ Can browse data easily
- ✅ No need to remember psql commands

---

**Recommendation:** Use pgAdmin if you prefer a GUI, or use the Python script (`create_db_without_postgres.py`) for automation.


