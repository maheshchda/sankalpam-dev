# Fix: 404 Errors for Next.js Static Files

## Problem
Getting 404 errors for Next.js static files:
- `app-pages-internals.js` - 404
- `main-app.js` - 404  
- `page.js` - 404
- `layout.css` - 404

## Root Cause
Next.js `.next` build directory is missing or corrupted. These files are generated during the build process.

## Solution - Complete Fix

### Step 1: Stop Frontend Server
1. Go to the terminal running `npm run dev`
2. Press **Ctrl+C** to stop it
3. **Wait for it to fully stop**

### Step 2: Clear All Caches
```powershell
cd "C:\Projects\sankalpam-dev\frontend"

# Remove Next.js build cache
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue

# Remove any other caches
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
```

### Step 3: Restart Frontend Server
```powershell
npm run dev
```

**IMPORTANT:** Wait for the server to show:
```
✓ Ready in X seconds
```

**DO NOT refresh the browser until you see "Ready"**

### Step 4: Hard Refresh Browser
1. Press **Ctrl + Shift + R** (hard refresh)
2. Or close and reopen the browser tab

---

## Why This Happened

The `.next` directory contains compiled Next.js files. When it's missing or corrupted:
- Next.js can't serve the static files
- Browser requests for `_next/static/...` files return 404
- Page appears broken or doesn't load

**This is NOT a code issue** - it's a build cache issue that happens when:
- Server is stopped while files are being served
- Build process is interrupted
- Cache gets corrupted

---

## Verification

After restarting, check:

1. **Frontend terminal shows "Ready"**
2. **Browser console has no 404 errors**
3. **Page loads normally**

---

## If Still Getting 404s

### Option 1: Full Clean Rebuild
```powershell
cd "C:\Projects\sankalpam-dev\frontend"

# Stop server (Ctrl+C)

# Remove everything
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue

# Reinstall dependencies (if needed)
# npm install

# Restart
npm run dev
```

### Option 2: Check Port Conflicts
```powershell
# Check if port 3000 is in use
netstat -ano | findstr :3000

# If something else is using it, use different port
npm run dev -- -p 3001
```

### Option 3: Check File Permissions
Make sure you have write permissions in the frontend directory.

---

## Prevention

- Always stop the server properly (Ctrl+C)
- Wait for "Ready" before accessing the app
- Don't delete `.next` while server is running
- If build seems stuck, stop and restart cleanly

---

## Quick Command to Fix

Run this (after stopping the server):

```powershell
cd "C:\Projects\sankalpam-dev\frontend"
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm run dev
```

Then wait for "Ready" and hard refresh browser (Ctrl+Shift+R).

