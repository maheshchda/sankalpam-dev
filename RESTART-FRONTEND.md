# Restart Frontend Server

## Quick Restart

If the browser is not loading, the frontend server may have stopped or crashed.

### Option 1: Manual Restart

1. **Find the terminal running `npm run dev`**
2. **Stop it**: Press `Ctrl+C`
3. **Restart it**:
   ```powershell
   cd "C:\Projects\sankalpam-dev\frontend"
   npm run dev
   ```
4. **Wait for**: `✓ Ready in X seconds`
5. **Then refresh browser**: http://localhost:3000

### Option 2: Kill and Restart

1. **Kill all Node processes**:
   ```powershell
   Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
   ```

2. **Start fresh**:
   ```powershell
   cd "C:\Projects\sankalpam-dev\frontend"
   npm run dev
   ```

### Option 3: Check for Errors

If server won't start, check for compilation errors:

1. **Check the terminal** for error messages
2. **Common issues**:
   - Syntax errors in code
   - Missing dependencies
   - Port already in use

### Check Server Status

```powershell
# Check if port 3000 is in use
netstat -ano | findstr :3000

# Check Node processes
Get-Process -Name node
```

### If Still Not Working

1. **Clear Next.js cache**:
   ```powershell
   cd "C:\Projects\sankalpam-dev\frontend"
   Remove-Item -Recurse -Force .next -ErrorAction SilentlyContinue
   npm run dev
   ```

2. **Check backend is running**:
   - Backend should be on http://localhost:8000
   - Check terminal running `uvicorn main:app --reload`

3. **Try different browser** or **incognito mode**

