"""PersonaX — Agentic AI Platform Backend Entry Point."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings
from app.database import init_db, async_session

# ---------------------------------------------------------
# BACKEND ARCHITECTURE: Render (Docker)
# FRONTEND ARCHITECTURE: Vercel
# ---------------------------------------------------------

# Configure structured production logging for Render Log Streams
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("personax")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events optimized for Render container lifecycles."""
    logger.info("Backend Starting on Render...")
    
    # 1. Startup Validation
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL environment variable is missing.")
        raise RuntimeError("DATABASE_URL environment variable is missing in Render.")
        
    try:
        # Import models to register them with Base
        import app.models  # noqa: F401
        
        # 2. Connect to Supabase PostgreSQL and verify connection
        logger.info(f"DATABASE_URL = {settings.DATABASE_URL}")
        logger.info("Trying database connection...")
        
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
            
        await init_db()
        logger.info("Database connected successfully.")
    except Exception as e:
        logger.exception(f"Failed to connect to Supabase. Error: {e}")
        raise

    # 4. Start background resume worker
    from app.engine.resume_manager import resume_paused_simulations
    resume_task = asyncio.create_task(resume_paused_simulations())

    logger.info("Backend Ready to accept Vercel traffic!")

    yield

    # 5. Safe Shutdown (SIGTERM handling from Render)
    logger.info("Render is shutting down the backend...")
    resume_task.cancel()
    try:
        await resume_task
    except asyncio.CancelledError:
        pass


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agentic AI Platform Backend",
    lifespan=lifespan,
)

# CORS middleware for Vercel Frontend
# Removes '*' if allow_credentials is True to prevent production security errors in FastAPI
allowed_origins = [origin for origin in settings.cors_origins_list if origin != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
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
        "message": "API is online on Render."
    }

@app.get("/health")
async def health():
    return {"status": "ok"}
