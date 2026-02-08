# How to Reset PostgreSQL Password

## Method 1: Reset via pgAdmin (Easiest)

1. **Open pgAdmin**
   - Search for "pgAdmin" in Start Menu
   - It comes with PostgreSQL installation

2. **If you can still connect:**
   - Right-click on PostgreSQL server → "Properties"
   - Go to "Connection" tab
   - You can see/change the password there

3. **If you can't connect:**
   - Use Method 2 or 3 below

---

## Method 2: Reset via Windows Service (No Password Needed)

This method works if you have Windows administrator access.

### Steps:

1. **Stop PostgreSQL Service:**
   - Press `Win + R`, type `services.msc`, press Enter
   - Find "postgresql-x64-13" or "postgresql-x64-18" (or your version)
   - Right-click → "Stop"

2. **Edit PostgreSQL Configuration:**
   - Navigate to PostgreSQL data directory (usually):
     - `C:\Program Files\PostgreSQL\13\data\` or
     - `C:\Program Files\PostgreSQL\18\data\`
   - Open `pg_hba.conf` file in Notepad (as Administrator)

3. **Modify Authentication:**
   - Find lines starting with `host` and `local`
   - Change `md5` or `scram-sha-256` to `trust` for local connections
   - Example:
     ```
     # Change this:
     host    all             all             127.0.0.1/32            md5
     
     # To this:
     host    all             all             127.0.0.1/32            trust
     ```
   - Save the file

4. **Start PostgreSQL Service:**
   - Go back to Services (`services.msc`)
   - Right-click PostgreSQL service → "Start"

5. **Connect without password:**
   - Open Command Prompt
   - Navigate to PostgreSQL bin folder:
     ```
     cd "C:\Program Files\PostgreSQL\13\bin"
     ```
   - Run:
     ```
     psql -U postgres
     ```
   - (No password needed now)

6. **Reset password:**
   ```sql
   ALTER USER postgres WITH PASSWORD 'your_new_password';
   ```
   - Replace `your_new_password` with a password you'll remember

7. **Revert pg_hba.conf:**
   - Change `trust` back to `md5` or `scram-sha-256`
   - Save and restart PostgreSQL service

---

## Method 3: Use Alternative User (If Available)

Some PostgreSQL installations create other users. Check:

1. **Open pgAdmin**
2. **Try connecting with different users:**
   - `postgres` (default)
   - Your Windows username
   - `Administrator`

---

## Method 4: Reinstall PostgreSQL (Last Resort)

If nothing else works:

1. **Uninstall PostgreSQL** (keep data if prompted)
2. **Reinstall PostgreSQL** from: https://www.postgresql.org/download/windows/
3. **Set a password you'll remember** during installation
4. **Note it down** somewhere safe

---

## Method 5: Create Database User Without Postgres Password

If you have another admin user or can access PostgreSQL differently:

1. **Check if you have other PostgreSQL users:**
   - Look in pgAdmin → Login/Group Roles
   - Or check Windows user accounts that might have PostgreSQL access

2. **Use Windows Authentication:**
   - Some PostgreSQL installations allow Windows authentication
   - Try connecting with your Windows username

---

## Quick Alternative: Use Different Database User

Instead of using `sankalpam_user`, you can:

1. **Use your Windows username** as the database user
2. **Update `backend\.env`:**
   ```
   DATABASE_URL=postgresql://YOUR_WINDOWS_USERNAME@localhost:5432/sankalpam_db
   ```
   (Remove password if using Windows authentication)

---

## After Resetting Password

Once you have access:

1. **Create the database user:**
   ```sql
   CREATE DATABASE sankalpam_db;
   CREATE USER sankalpam_user WITH PASSWORD 'sankalpam_password';
   GRANT ALL PRIVILEGES ON DATABASE sankalpam_db TO sankalpam_user;
   ALTER DATABASE sankalpam_db OWNER TO sankalpam_user;
   ```

2. **Or run the fix script:**
   ```powershell
   cd "C:\Projects\sankalpam-dev\backend"
   .\venv\Scripts\Activate.ps1
   python fix_database_user.py
   ```

---

## Prevention: Save Password

After resetting, **save your password** in:
- Password manager
- Secure note
- `backend\.env` file (for reference, but don't commit to git)

---

**Recommendation:** Try Method 2 first (reset via Windows Service) - it's the most reliable if you have admin access.


