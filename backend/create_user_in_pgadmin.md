# Create sankalpam_user in pgAdmin

Since you have pgAdmin open and can see the database, follow these steps:

## Steps in pgAdmin:

1. **In pgAdmin, expand PostgreSQL 18 server**

2. **Create the User:**
   - Expand "Login/Group Roles"
   - Right-click on "Login/Group Roles" → "Create" → "Login/Group Role"
   - In the "General" tab:
     - Name: `sankalpam_user`
   - In the "Definition" tab:
     - Password: `sankalpam_password`
     - Password expiration: Leave empty (or set a future date)
   - In the "Privileges" tab:
     - Check "Can login?"
     - Check "Create databases?" (optional but recommended)
   - Click "Save"

3. **Grant Privileges on Database:**
   - Expand "Databases" → Right-click on `sankalpam_db` → "Properties"
   - Go to "Security" tab
   - Click the "+" button to add a new privilege
   - Grantee: Select `sankalpam_user` from dropdown
   - Privileges: Check "ALL" (or at least: CONNECT, CREATE, TEMPORARY)
   - Click "Save"

4. **Set Database Owner (Optional but recommended):**
   - Still in `sankalpam_db` Properties
   - Go to "General" tab
   - Owner: Select `sankalpam_user` from dropdown
   - Click "Save"

## After Creating the User:

Test the connection by running:
```powershell
cd C:\Projects\sankalpam-dev\backend
.\venv\Scripts\python.exe -c "import psycopg2; conn = psycopg2.connect('postgresql://sankalpam_user:sankalpam_password@localhost:5432/sankalpam_db'); print('Connection successful!'); conn.close()"
```

If you see "Connection successful!", you can start the backend server!
