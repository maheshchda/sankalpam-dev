# Changes Required to Run Sankalpam Application

This document summarizes what is **required** vs **optional** to run the sankalpam-dev app.

---

## Required to Run

### 1. PostgreSQL database

The backend uses PostgreSQL. Either:

- **Docker** (recommended): From project root run `docker-compose up -d`.  
  Database is on **port 5433** (mapped from container 5432).
- **Local PostgreSQL**: Install and create a database. Use port **5432** or **5433** and set `DATABASE_URL` accordingly.

### 2. Backend `.env` (required variables)

In `backend/.env` you **must** set:

```env
# Required: database (adjust if using different user/port)
DATABASE_URL=postgresql://sankalpam_user:sankalpam_password@localhost:5433/sankalpam_db
```

- With **Docker**: use port **5433** and the credentials in `docker-compose.yml` (sankalpam_user / sankalpam_password).
- With **local PostgreSQL**: use your actual host, port (e.g. 5432), user, password, and database name.

Optional but recommended for production:

```env
SECRET_KEY=your-secure-secret-key-change-in-production
```

### 3. Backend virtual environment and dependencies

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Frontend dependencies

```powershell
cd frontend
npm install
```

### 5. Backend port consistency

- Backend runs on **port 8001** (`START-BACKEND.bat` and `frontend/lib/api.ts` default).
- Frontend calls `http://localhost:8001` unless `NEXT_PUBLIC_API_URL` is set in `frontend/.env.local`.

### 6. Start order

1. Start PostgreSQL (Docker or local).
2. Start backend: from `backend/` run `START-BACKEND.bat` or  
   `.\venv\Scripts\Activate.ps1; uvicorn main:app --reload --host 0.0.0.0 --port 8001`
3. Start frontend: from `frontend/` run `npm run dev`.

Then open **http://localhost:3000**.

---

## Optional (improves features)

| Item | Purpose | Where to set |
|------|---------|--------------|
| **Divine API** | Panchang / accurate sankalpam data | `backend/.env`: `Divine_API_Key`, `Divine_Access_Token` (or `DIVINE_API_KEY`, `DIVINE_ACCESS_TOKEN`) |
| **Google Maps API key** | Nearby river/place names | `backend/.env`: `GOOGLE_MAPS_API_KEY` |
| **SMTP** | Email verification | `backend/.env`: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `FRONTEND_URL` |
| **Twilio** | SMS verification | `backend/.env`: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` |
| **Frontend API URL** | Point frontend to different backend | `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8001` |

Without these, the app still runs: location uses fallback river names, sankalpam uses built-in templates, and email/SMS verification is skipped or disabled.

---

## Database migrations (if schema changed)

If you have existing data or ran older migrations:

```powershell
cd backend
.\venv\Scripts\Activate.ps1
alembic upgrade head
```

New installs: tables are created on first backend startup via `Base.metadata.create_all(bind=engine)` in `main.py`.

---

## Summary checklist

- [ ] PostgreSQL running (Docker on 5433 or local)
- [ ] `backend/.env` has valid `DATABASE_URL`
- [ ] Backend: `venv` created, `pip install -r requirements.txt`
- [ ] Frontend: `npm install`
- [ ] Start backend on **8001**, then frontend (`npm run dev`)
- [ ] (Optional) Set Divine API, Google Maps, SMTP, Twilio in `backend/.env` as needed

For step-by-step run instructions, see **HOW-TO-RUN.md**.
