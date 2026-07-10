"""PersonaX — Agentic AI Platform Backend Entry Point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: create database tables
    print("\n PersonaX Backend Starting...")
    print(f"   Database: {settings.DATABASE_URL}")
    print(f"   Gemini Model: {settings.GEMINI_MODEL}")
    print(f"   CORS Origins: {settings.cors_origins_list}")

    # Import models to register them with Base
    import app.models  # noqa: F401
    await init_db()
    print("   [OK] Database tables created")
    print("   [OK] PersonaX Backend Ready!\n")

    yield

    # Shutdown
    print("\n PersonaX Backend Shutting Down...\n")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic AI Platform — Synthetic Human Population Simulator",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.auth.router import router as auth_router  # noqa: E402
from app.routers.personas import router as personas_router  # noqa: E402
from app.routers.simulations import router as simulations_router  # noqa: E402
from app.routers.conversations import router as conversations_router  # noqa: E402
from app.routers.projects import router as projects_router  # noqa: E402
from app.routers.analytics import router as analytics_router  # noqa: E402
from app.routers.settings import router as settings_router  # noqa: E402
from app.routers.reports import router as reports_router  # noqa: E402

app.include_router(auth_router, prefix="/api")
app.include_router(personas_router, prefix="/api")
app.include_router(simulations_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(projects_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(settings_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
