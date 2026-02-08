# Fix: 404 Errors for Next.js Static Files

## Problem
Getting 404 errors for:
- `_next/static/chunks/app-pages-internals.js` - 404
- Other `_next/static` files - 404

## Root Cause
The `.next` directory (Next.js build cache) is missing or incomplete. These files are generated when the server starts.

## Solution

### Step 1: Make Sure Frontend Server is Running

**Check if server is running:**
- Look for a terminal window with `npm run dev`
- If you don't see one, the server is NOT running

### Step 2: Start/Restart Frontend Server

**If server is NOT running:**
```powershell
cd "C:\Projects\sankalpam-dev\frontend"
npm run dev
```

**If server IS running but still getting 404s:**
1. Stop it (Ctrl+C)
2. Clear cache:
   ```powershell
   Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
   ```
3. Restart:
   ```powershell
   npm run dev
   ```

### Step 3: Wait for "Ready" Message

**CRITICAL:** Wait for the server to show:
```
✓ Ready in X seconds
```

**DO NOT refresh browser until you see "Ready"**

### Step 4: Hard Refresh Browser

1. Press **Ctrl + Shift + R** (hard refresh)
2. Or close and reopen the browser tab

---

## Why This Happens

The `.next/static` directory contains compiled JavaScript and CSS files. When the server starts, it:
1. Compiles your code
2. Generates static files in `.next/static`
3. Serves them when browser requests them

If the server isn't running or the build is incomplete, these files don't exist → 404 errors.

---

## Verification

After restarting, check:

1. **Terminal shows "Ready"**
2. **Browser console has no 404 errors**
3. **Page loads normally**

---

## Quick Fix Command

Run this (after stopping any running server):

```powershell
cd "C:\Projects\sankalpam-dev\frontend"
Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
npm run dev
```

Then wait for "Ready" and refresh browser (Ctrl+Shift+R).

---

## Still Getting 404s?

1. **Check server is actually running:**
   - Look for terminal with "Ready" message
   - Check http://localhost:3000 responds

2. **Check for port conflicts:**
   ```powershell
   netstat -ano | findstr :3000
   ```

3. **Try different port:**
   ```powershell
   npm run dev -- -p 3001
   ```

4. **Full clean rebuild:**
   ```powershell
   Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
   Remove-Item -Recurse -Force node_modules\.cache -ErrorAction SilentlyContinue
   npm run dev
   ```

---

## Important Notes

- **Server MUST be running** for static files to be served
- **Wait for "Ready"** before accessing the app
- **Don't delete .next while server is running**
- **Hard refresh browser** after server starts

