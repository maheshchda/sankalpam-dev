# Troubleshooting Login Issues

## Current Login Credentials

**Username:** `maheshc11@gmail.com`  
**Password:** `fZtAUQLsm-szETQc`

## Verification

The password has been verified and works with the API endpoint directly.

## Common Issues

### 1. Frontend Not Running
- Make sure the frontend server is running on http://localhost:3000
- Start it with: `cd frontend && npm run dev`

### 2. Backend Not Running
- Make sure the backend server is running on http://localhost:8000
- Check: http://localhost:8000/health

### 3. Browser Console Errors
- Open browser DevTools (F12)
- Check the Console tab for errors
- Check the Network tab to see the login request/response

### 4. CORS Issues
- Make sure backend CORS is configured correctly
- Backend should allow http://localhost:3000

### 5. Wrong Credentials Format
- Make sure you're using:
  - **Username:** `maheshc11@gmail.com` (not just the email part)
  - **Password:** `fZtAUQLsm-szETQc` (case-sensitive)

## Test API Directly

You can test the login API directly using PowerShell:

```powershell
$body = 'username=maheshc11@gmail.com&password=fZtAUQLsm-szETQc'
$response = Invoke-WebRequest -Uri http://localhost:8000/api/auth/login -Method POST -Body $body -ContentType 'application/x-www-form-urlencoded'
$response.Content
```

If this works but the frontend doesn't, the issue is in the frontend.

## Reset Password Again

If you need to reset the password again:

```powershell
cd backend
.\venv\Scripts\python.exe reset_password_direct.py maheshc11@gmail.com
```

Or with a custom password:

```powershell
.\venv\Scripts\python.exe reset_password_direct.py maheshc11@gmail.com YourNewPassword
```
