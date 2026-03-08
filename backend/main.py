from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.database import engine, Base, SessionLocal
from app.routers import auth, users, family, pooja, sankalpam, admin, templates, pooja_calendar, panchang, schedule, rsvp
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
        DEFAULT_POOJAS = [
            ("Ganesh Pooja",           "Ganesha Pooja for auspicious beginnings and removal of obstacles.", 30),
            ("Lakshmi Pooja",          "Sri Mahalakshmi Pooja for prosperity, wealth, and abundance.", 30),
            ("Satyanarayan Pooja",     "Sri Satyanarayan Katha and Pooja for blessings and fulfilment of wishes.", 120),
            ("Rudrabhishek",           "Abhishek of Lord Shiva with sacred offerings for peace and prosperity.", 90),
            ("Navgraha Pooja",         "Pooja for the nine planetary deities to mitigate doshas and seek blessings.", 60),
            ("Durga Pooja",            "Worship of Goddess Durga for strength, protection, and victory.", 60),
            ("Saraswati Pooja",        "Worship of Goddess Saraswati for knowledge, wisdom, and learning.", 45),
            ("Hanuman Pooja",          "Hanuman Pooja for courage, devotion, and protection from evil.", 45),
            ("Kali Pooja",             "Worship of Goddess Kali for liberation and protection.", 60),
            ("Vastu Pooja",            "Vastu Shanti Pooja to purify a new home or building.", 90),
            ("Gruhapravesam",          "Sacred house-warming ceremony with Vedic rituals.", 120),
            ("Ayush Homam",            "Homam for longevity, good health, and a blessed life.", 90),
            ("Mrityunjaya Homam",      "Maha Mrityunjaya Homam for good health and freedom from disease.", 120),
            ("Sudarshana Homam",       "Sudarshana Homam for protection and removal of negative energies.", 90),
            ("Navagraha Homam",        "Fire ritual for all nine planetary deities to balance cosmic energies.", 120),
            ("Ganapathi Homam",        "Fire ritual for Lord Ganesha to remove obstacles and bestow success.", 90),
            ("Lakshmi Kubera Pooja",   "Combined worship of Goddess Lakshmi and Lord Kubera for wealth.", 60),
            ("Satyanarayana Vratam",   "Monthly Satyanarayan Vrat for family well-being and divine grace.", 120),
            ("Seemantham",             "Baby shower ceremony with Vedic blessings for mother and child.", 90),
            ("Naamkaran (Naming)",     "Sacred naming ceremony for a newborn child.", 60),
            ("Annaprasana",            "First rice-feeding ceremony for an infant.", 60),
            ("Upanayanam",             "Sacred thread ceremony marking a boy's entry into studentship.", 180),
            ("Vivaha (Wedding)",       "Traditional Vedic wedding ceremony.", 240),
            ("Sathabhishekam",         "80th birthday celebration ritual for longevity and blessings.", 120),
            ("Pitru Tarpan",           "Ancestral offerings and prayers on auspicious occasions.", 60),
            ("Ekadashi Pooja",         "Special prayers on Ekadashi for spiritual merit.", 45),
            ("Pradosh Pooja",          "Evening prayers to Lord Shiva on Pradosh days.", 45),
            ("Navaratri Pooja",        "Nine-night festival worship of Goddess Durga.", 60),
            ("Diwali Lakshmi Pooja",   "Lakshmi Pooja on the auspicious night of Diwali.", 60),
            ("Sankranti Pooja",        "Makar Sankranti/Ugadi rituals for new beginnings.", 60),
        ]
        for (pname, pdesc, pdur) in DEFAULT_POOJAS:
            if not db.query(Pooja).filter(Pooja.name == pname).first():
                db.add(Pooja(name=pname, description=pdesc, duration_minutes=pdur, is_active=True, created_by=None))
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

