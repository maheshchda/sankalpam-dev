from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

from app.database import engine, Base
from app.routers import auth, users, family, pooja, sankalpam, admin, templates
from app.config import settings

# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Sankalpam API",
    description="API for Pooja Management and Sankalpam Generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - must be added before routers
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(family.router, prefix="/api/family", tags=["Family"])
app.include_router(pooja.router, prefix="/api/pooja", tags=["Pooja"])
app.include_router(sankalpam.router, prefix="/api/sankalpam", tags=["Sankalpam"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(templates.router, prefix="/api/templates", tags=["Templates"])

# Mount static files for audio
audio_path = Path(settings.audio_storage_path)
audio_path.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(audio_path)), name="audio")

@app.get("/")
async def root():
    return {"message": "Sankalpam API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

