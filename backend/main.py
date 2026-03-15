from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import engine, Base, SessionLocal
from app.routers import auth, users, family, pooja, sankalpam, admin, templates, pooja_calendar, panchang, schedule, rsvp, email_debug
from app.config import settings
from app.models import Pooja, AdminRole, UserAdminRole, User
import json

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema exists
    Base.metadata.create_all(bind=engine)

    # Seed default poojas (Ganesh Pooja, Lakshmi Pooja) if missing
    db = SessionLocal()
    try:
        # Home-hosted poojas (typically invite guests). state_codes: JSON array or None=all states.
        # Format: (name, description, duration_mins, state_codes_json)
        DEFAULT_POOJAS = [
            # Pan-India (state_codes=None)
            ("Satyanarayan Pooja",     "Sri Satyanarayan Katha at home — housewarming, birthdays, anniversaries. Guests share prasad.", 120, None),
            ("Ganesh Pooja",           "Ganesha Pooja at home for auspicious beginnings. Common during Ganesh Chaturthi.", 45, None),
            ("Lakshmi Pooja",          "Sri Mahalakshmi Pooja for prosperity. Often during Diwali with family and friends.", 45, None),
            ("Gruhapravesam",          "House-warming ceremony. Vastu Shanti with invited family and friends.", 120, None),
            ("Vastu Pooja",            "Vastu Shanti to purify a new home. Performed before moving in.", 90, None),
            ("Navgraha Pooja",         "Nine planetary deities to mitigate doshas. Home ceremony with priest.", 60, None),
            ("Rudrabhishek",           "Abhishek of Lord Shiva for peace and prosperity. Home or temple.", 90, None),
            ("Durga Pooja",            "Goddess Durga worship during Navratri. Home altar with guests.", 60, None),
            ("Navaratri Pooja",        "Nine-night Goddess worship. Home celebration with family and friends.", 60, None),
            ("Saraswati Pooja",        "Goddess Saraswati for knowledge. Basant Panchami, academic year start.", 45, None),
            ("Hanuman Pooja",          "Hanuman Pooja for courage and protection. Home ceremony.", 45, None),
            ("Ayush Homam",            "Fire ritual for longevity. Birthdays, recovery from illness.", 90, None),
            ("Mrityunjaya Homam",      "Maha Mrityunjaya Homam for health and freedom from disease.", 120, None),
            ("Ganapathi Homam",        "Fire ritual for Lord Ganesha. New ventures, exams.", 90, None),
            ("Navagraha Homam",        "Fire ritual for nine planets. Balance cosmic energies.", 120, None),
            ("Ayudha Pooja",           "Blessing of vehicles and tools. During Navratri/Dasara.", 45, None),
            ("Lakshmi Kubera Pooja",   "Lakshmi and Kubera for wealth. Home ceremony.", 60, None),
            ("Diwali Lakshmi Pooja",   "Lakshmi Pooja on Diwali night. Family and guests.", 60, None),
            ("Satyanarayana Vratam",   "Monthly Satyanarayan Vrat. Family well-being.", 120, None),
            ("Kali Pooja",             "Goddess Kali worship. Diwali night in Bengal.", 60, None),
            ("Pitru Tarpan",           "Ancestral offerings. Pitru Paksha, Shraddha.", 60, None),
            ("Ekadashi Pooja",         "Special prayers on Ekadashi. Home observance.", 45, None),
            ("Pradosh Pooja",          "Evening Shiva prayers on Pradosh days.", 45, None),
            ("Sankranti Pooja",        "Makar Sankranti/Ugadi. Harvest, new beginnings.", 60, None),
            ("Seemantham",             "Baby shower with Vedic blessings. Invite family.", 90, None),
            ("Naamkaran (Naming)",     "Sacred naming ceremony for newborn.", 60, None),
            ("Annaprasana",            "First rice-feeding ceremony for infant.", 60, None),
            ("Upanayanam",             "Sacred thread ceremony. Major life event with guests.", 180, None),
            ("Vivaha (Wedding)",       "Traditional Vedic wedding. Large gathering.", 240, None),
            ("Sathabhishekam",         "80th birthday celebration. Longevity ritual.", 120, None),
            # South India — Varalakshmi Vratam (TN, KA, AP, TG)
            ("Varalakshmi Vratam",     "Married women worship Goddess Lakshmi. Home ceremony, invite family.", 90, '["IN-TN","IN-KA","IN-AP","IN-TG"]'),
            # Tamil Nadu — Pongal, Kolu
            ("Pongal",                 "Harvest festival. Home celebration with family, new crop offering.", 60, '["IN-TN"]'),
            ("Kolu / Bommai Kolu",     "Navratri doll display. Guests visit to view and receive prasad.", 60, '["IN-TN"]'),
            # Maharashtra — Gudi Padwa
            ("Gudi Padwa",             "Maharashtrian New Year. Home ceremony with shrikhand, neem.", 60, '["IN-MH"]'),
            # North India — Mata Ki Chowki / Jagran
            ("Mata Ki Chowki",         "Maa Durga devotional program. Bhajan mandali, 3–4 hours. North India.", 180, '["IN-PB","IN-DL","IN-HR","IN-UP","IN-RJ","IN-JK"]'),
            ("Mata Ka Jagran",         "All-night Maa Durga devotion. Tuesday/Saturday. North India.", 360, '["IN-PB","IN-DL","IN-HR","IN-UP","IN-RJ","IN-JK"]'),
            # Bihar, UP, Jharkhand — Chhath
            ("Chhath Puja",            "Sun God worship. Four-day ritual. Can be done at home with water setup.", 120, '["IN-BR","IN-UP","IN-JH"]'),
            # Telangana — Bathukamma
            ("Bathukamma",             "Flower festival. Women arrange flowers, home celebration.", 60, '["IN-TG"]'),
            # Kerala — Onam
            ("Onam Sadya",             "Onam harvest feast. Home celebration with family, floral pookalam.", 90, '["IN-KL"]'),
        ]
        for (pname, pdesc, pdur, scodes) in DEFAULT_POOJAS:
            existing = db.query(Pooja).filter(Pooja.name == pname).first()
            if not existing:
                db.add(Pooja(name=pname, description=pdesc, duration_minutes=pdur, is_active=True, created_by=None, state_codes=scodes))
            elif existing.state_codes is None and scodes:
                existing.state_codes = scodes
        db.commit()

        # ── Seed default admin roles ──────────────────────────────────────────
        DEFAULT_ROLES = [
            {
                "name": "Super Admin",
                "description": "Full unrestricted access to all admin functions.",
                "permissions": ["*"],
                "is_system_role": True,
            },
            {
                "name": "User Manager",
                "description": "Manage frontend users: activate/deactivate accounts, reset passwords, and verify credentials.",
                "permissions": ["user_management", "user_password_reset", "user_verification", "view_stats"],
                "is_system_role": True,
            },
            {
                "name": "Content Manager",
                "description": "Manage Sankalpam templates and Pooja entries.",
                "permissions": ["template_management", "pooja_management", "view_stats"],
                "is_system_role": True,
            },
            {
                "name": "Support Agent",
                "description": "View users and verify email/phone for support purposes.",
                "permissions": ["user_management", "user_verification", "view_stats"],
                "is_system_role": True,
            },
        ]
        for rd in DEFAULT_ROLES:
            if not db.query(AdminRole).filter(AdminRole.name == rd["name"]).first():
                db.add(AdminRole(
                    name=rd["name"],
                    description=rd["description"],
                    permissions=json.dumps(rd["permissions"]),
                    is_system_role=rd["is_system_role"],
                ))
        db.commit()

        # Assign Super Admin role to Admin_SKLPM if not already assigned
        super_admin_user = db.query(User).filter(User.username == "Admin_SKLPM").first()
        super_admin_role = db.query(AdminRole).filter(AdminRole.name == "Super Admin").first()
        if super_admin_user and super_admin_role:
            existing = db.query(UserAdminRole).filter(
                UserAdminRole.user_id == super_admin_user.id,
                UserAdminRole.role_id == super_admin_role.id,
            ).first()
            if not existing:
                db.add(UserAdminRole(
                    user_id=super_admin_user.id,
                    role_id=super_admin_role.id,
                    assigned_by=super_admin_user.id,
                ))
                db.commit()

    finally:
        db.close()

    yield

app = FastAPI(
    title="Sankalpam API",
    description="API for Pooja Management and Sankalpam Generation",
    version="1.0.0",
    lifespan=lifespan
)

import os

_EXTRA_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]

def _is_allowed_origin(origin: str) -> bool:
    if not origin:
        return False
    if "localhost" in origin or "127.0.0.1" in origin:
        return True
    if any(origin == o for o in _EXTRA_ORIGINS):
        return True
    # Allow any *.railway.app / *.vercel.app subdomain automatically
    if origin.endswith(".railway.app") or origin.endswith(".vercel.app"):
        return True
    # Allow production custom domain
    if "poojasankalp.org" in origin:
        return True
    return False

# CORS middleware
class LocalhostCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")
        is_localhost = _is_allowed_origin(origin)
        if request.method == "OPTIONS" and is_localhost:
            from starlette.responses import Response
            return Response(
                status_code=200,
                headers={
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "600",
                },
            )
        try:
            response = await call_next(request)
        except Exception as exc:
            from starlette.responses import Response as StarletteResponse
            import traceback
            traceback.print_exc()
            response = StarletteResponse(status_code=500, content="Internal Server Error")
        if is_localhost:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        return response

# Add CORS middleware last so it runs first (outermost) and adds headers to every response
app.add_middleware(LocalhostCORSMiddleware)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(family.router, prefix="/api/family", tags=["Family"])
app.include_router(pooja.router, prefix="/api/pooja", tags=["Pooja"])
app.include_router(pooja_calendar.router, prefix="/api/pooja-calendar", tags=["Pooja Calendar"])
app.include_router(sankalpam.router, prefix="/api/sankalpam", tags=["Sankalpam"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])
app.include_router(panchang.router,   prefix="/api/panchang",   tags=["Panchang"])
app.include_router(schedule.router,   prefix="/api/schedule",   tags=["Schedule"])
app.include_router(rsvp.router,       prefix="/api/rsvp",       tags=["RSVP"])
app.include_router(email_debug.router, prefix="/api/email",     tags=["Email Debug"])

# Mount static files for audio and schedule images
audio_path = Path(settings.audio_storage_path)
audio_path.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_path)), name="audio")

schedule_img_path = Path("uploads/schedule_images")
schedule_img_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads/schedule_images", StaticFiles(directory=str(schedule_img_path)), name="schedule_images")

@app.get("/")
async def root():
    return {"message": "Sankalpam API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/config-check")
async def config_check():
    """Public endpoint to verify FRONTEND_URL and other key config (for debugging)."""
    return {
        "frontend_url": settings.frontend_url or "(not set)",
        "email_from": settings.email_from or "(not set)",
    }

