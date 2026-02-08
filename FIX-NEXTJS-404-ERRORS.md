# Fix: Next.js 404 Errors for Static Files

## Problem
Getting 404 errors for Next.js static files:
- `_next/static/css/app/layout.css` - 404
- `_next/static/chunks/main-app.js` - 404
- Other `_next/static` files - 404

## Cause
Next.js build cache (`.next` directory) is corrupted, missing, or out of sync.

## Solution

### Step 1: Stop the Frontend Server
1. Go to the terminal running `npm run dev`
2. Press **Ctrl+C** to stop it

### Step 2: Clear Next.js Cache
```powershell
cd "C:\Projects\sankalpam-dev\frontend"
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
```

### Step 3: Restart Frontend Server
```powershell
npm run dev
```

Wait for it to say "Ready" before refreshing the browser.

### Step 4: Hard Refresh Browser
1. Press **Ctrl + Shift + R** (or **Ctrl + F5**)
2. This clears browser cache and forces reload

---

## Alternative: Full Clean Rebuild

If the above doesn't work:

```powershell
cd "C:\Projects\sankalpam-dev\frontend"

# Stop server (Ctrl+C if running)

# Remove all caches
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue

# Restart
npm run dev
```

---

## Why This Happens

1. **Server restarted while files were being served** - cache got out of sync
2. **Build interrupted** - incomplete build files
3. **File system issues** - files not written correctly
4. **Port conflict** - multiple instances trying to use same port

---

## Prevention

- Always stop the server properly (Ctrl+C) before restarting
- Don't delete `.next` folder while server is running
- Wait for "Ready" message before accessing the app

---

## Still Getting 404s?

1. **Check if frontend server is actually running:**
   ```powershell
   # Should see "Ready" message
   npm run dev
   ```

2. **Check for port conflicts:**
   ```powershell
   netstat -ano | findstr :3000
   ```

3. **Try different port:**
   ```powershell
   npm run dev -- -p 3001
   ```

4. **Check browser console** for other errors

5. **Clear browser cache completely:**
   - Ctrl + Shift + Delete
   - Clear cached images and files
   - Or use Incognito/Private window

---

## Quick Fix Command

Run this to fix it quickly:

```powershell
cd "C:\Projects\sankalpam-dev\frontend"
# Stop server first (Ctrl+C in the terminal running npm run dev)
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm run dev
```

Then hard refresh browser: **Ctrl + Shift + R**

