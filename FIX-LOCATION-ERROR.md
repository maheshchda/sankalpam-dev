# Fix: setLocation is not defined Error

## Problem
You're seeing this error:
```
ReferenceError: setLocation is not defined
```

## Root Cause
The error is coming from a **Chrome browser extension** (location-spoofing extension), NOT from your application code. The extension is trying to interact with your page but can't find the `setLocation` function it expects.

## Solutions

### Solution 1: Disable the Location Spoofing Extension (Quickest Fix)

1. Open Chrome
2. Go to: `chrome://extensions/`
3. Find the location spoofing extension
4. **Disable** or **Remove** it
5. Refresh your application page

### Solution 2: Add Location Handling to Your App (If you need location features)

If your app needs location functionality, add this to your main page or layout:

**For Next.js App Router (app directory):**
```typescript
'use client'
import { useEffect } from 'react'

export default function Layout({ children }) {
  useEffect(() => {
    // Provide setLocation function for browser extensions
    if (typeof window !== 'undefined') {
      (window as any).setLocation = (location: any) => {
        console.log('Location set:', location)
        // Handle location if needed
      }
    }
  }, [])

  return <>{children}</>
}
```

**For Next.js Pages Router (pages directory):**
Add to `_app.tsx` or `_app.js`:
```typescript
import { useEffect } from 'react'

export default function App({ Component, pageProps }) {
  useEffect(() => {
    // Provide setLocation function for browser extensions
    if (typeof window !== 'undefined') {
      (window as any).setLocation = (location: any) => {
        console.log('Location set:', location)
        // Handle location if needed
      }
    }
  }, [])

  return <Component {...pageProps} />
}
```

### Solution 3: Use Incognito/Private Window

Run your application in an incognito/private browser window where extensions are typically disabled.

### Solution 4: Use a Different Browser

Test your application in Firefox or Edge to avoid the extension conflict.

## Recommended Action

**Disable the location spoofing extension** - This is the quickest and cleanest solution since the error is from a browser extension, not your application code.

## Verify the Fix

1. Disable the extension
2. Hard refresh the page (Ctrl+Shift+R or Cmd+Shift+R)
3. The error should disappear
4. Your application should work normally

## If Error Persists

If you still see the error after disabling the extension:

1. Check browser console for other errors
2. Clear browser cache
3. Check if other extensions are interfering
4. Verify your application code doesn't have location-related issues

