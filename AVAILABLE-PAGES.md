# Available Pages in Sankalpam Application

## Main Pages

### Home Page
- **URL:** http://localhost:3000/
- **Description:** Landing/home page

### Login
- **URL:** http://localhost:3000/login
- **Description:** User login page

### Register
- **URL:** http://localhost:3000/register
- **Description:** User registration page

### Dashboard
- **URL:** http://localhost:3000/dashboard
- **Description:** User dashboard (requires login)

### Sankalpam Generation
- **URL:** http://localhost:3000/sankalpam
- **Description:** Generate Sankalpam page (requires login)

### Admin Panel
- **URL:** http://localhost:3000/admin
- **Description:** Admin management panel (requires admin login)

### Other Pages
- **URL:** http://localhost:3000/pooja
- **URL:** http://localhost:3000/family
- **URL:** http://localhost:3000/playback
- **URL:** http://localhost:3000/verify

---

## Common 404 Causes

### 1. Wrong URL
- Make sure you're using the correct URL
- Check for typos in the path
- URLs are case-sensitive

### 2. Not Logged In
- Some pages require authentication
- If not logged in, you'll be redirected or get 404
- **Solution:** Go to http://localhost:3000/login first

### 3. Frontend Server Not Running Properly
- Server might be running but not fully ready
- **Solution:** Restart frontend server

### 4. Route Doesn't Exist
- The page you're trying to access might not exist
- Check the list above for available pages

---

## Quick Fixes

### If you get 404 on any page:

1. **Check the URL is correct:**
   - Start with: http://localhost:3000
   - Add the page path (e.g., /login, /dashboard)

2. **Try the home page first:**
   - http://localhost:3000/
   - If this works, the server is fine

3. **If home page also gives 404:**
   - Restart frontend server:
     ```powershell
     cd "C:\Projects\sankalpam-dev\frontend"
     # Stop server (Ctrl+C)
     npm run dev
     ```

4. **Clear browser cache:**
   - Press Ctrl + Shift + R (hard refresh)
   - Or use Incognito/Private window

---

## Which Page Are You Trying to Access?

Please share:
- What URL are you trying to access?
- What page were you trying to reach?

This will help identify the exact issue.

