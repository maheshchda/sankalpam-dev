# Railway Environment Variables

## Fix: Live site calling localhost instead of production API

If your live site (https://www.poojasankalp.org) shows CORS errors or tries to call `localhost:8000`, the frontend was built without the production API URL.

### Frontend service (Railway)

Add this variable to your **frontend** service in Railway:

| Variable | Value |
|----------|-------|
| `NEXT_PUBLIC_API_URL` | `https://YOUR-BACKEND-URL.up.railway.app` |

Replace `YOUR-BACKEND-URL` with your actual backend Railway URL (e.g. if backend is at `sankalpam-backend-production-xxxx.up.railway.app`, use that).

**Important:** After adding the variable, **redeploy** the frontend. `NEXT_PUBLIC_*` vars are baked in at build time.

### Backend service (Railway)

If using a custom domain, ensure CORS allows it. The backend already allows `poojasankalp.org`. For other domains, add:

| Variable | Value |
|----------|-------|
| `ALLOWED_ORIGINS` | `https://www.poojasankalp.org,https://poojasankalp.org` |

### Checklist

1. [ ] Backend deployed on Railway (or elsewhere)
2. [ ] `NEXT_PUBLIC_API_URL` set in frontend service = backend URL
3. [ ] Redeploy frontend after adding env var
4. [ ] Backend CORS allows your domain (poojasankalp.org is already in code)
