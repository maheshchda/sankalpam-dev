# Fix: Repeating 404 Errors from Browser Extension

## Problem
Getting repeated 404 errors:
```
GET http://localhost:3000/ 404 (Not Found)
check @ (index):5
setTimeout
check @ (index):10
```

This is a **browser extension** (not your application) repeatedly trying to check the page.

## Root Cause
A browser extension (likely a security, location, or monitoring extension) is injecting a script that keeps checking the page status, causing repeated 404 errors.

## Solutions

### Solution 1: Use Incognito/Private Window (Easiest)
1. Open an **Incognito/Private window** (Ctrl+Shift+N in Chrome)
2. Go to: http://localhost:3000
3. Extensions are usually disabled in incognito
4. The errors should stop

### Solution 2: Disable Browser Extensions
1. Go to: `chrome://extensions/` (or your browser's extension page)
2. **Disable all extensions** temporarily
3. Refresh http://localhost:3000
4. If errors stop, re-enable extensions one by one to find the culprit

### Solution 3: Ignore the Errors
**Important:** These errors might not actually break your application!

1. **Check if the page actually loads** - ignore the console errors
2. If the page works, the errors are just from extensions
3. You can filter them out in DevTools console

### Solution 4: Clear Browser Data
1. Press **Ctrl + Shift + Delete**
2. Clear:
   - Cached images and files
   - Cookies and site data
3. Close and reopen browser
4. Try again

---

## Verify Your Application Actually Works

**Don't just look at console errors - check if the page loads:**

1. **Does the page display?** (even with errors in console)
2. **Can you see the UI?**
3. **Can you navigate?**
4. **Can you login?**

If yes to all, **the application is working** - the errors are just from extensions.

---

## Filter Extension Errors in Console

In DevTools Console:
1. Click the filter icon
2. Add filter to hide: `(index)` or `check`
3. This hides extension errors

---

## Most Likely Culprit Extensions

- Location spoofing extensions
- Security/monitoring extensions
- Ad blockers
- Privacy extensions
- Developer tools extensions

---

## Quick Test

1. **Open Incognito window** (Ctrl+Shift+N)
2. Go to: http://localhost:3000
3. Check console - errors should be gone
4. If page works in incognito, it's definitely an extension issue

---

## If Page Doesn't Load At All

If the page itself doesn't load (not just console errors):

1. **Check frontend server is running:**
   - Look for terminal with "Ready" message
   - Check http://localhost:3000 responds

2. **Check backend server is running:**
   - Check http://localhost:8000/docs

3. **Restart both servers** if needed

---

## Summary

- **Extension errors are harmless** if the page loads
- **Try incognito window** to confirm
- **Disable extensions** if they're causing issues
- **Focus on whether the page actually works**, not just console errors

