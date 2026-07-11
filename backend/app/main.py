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

# Configure structured production logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger("personax")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("PersonaX Backend Starting...")
    
    # Startup Validation
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL environment variable is missing.")
        raise RuntimeError("DATABASE_URL environment variable is missing.")
        
    try:
        # Import models to register them with Base
        import app.models  # noqa: F401
        
        # Connect to Supabase PostgreSQL and verify connection
        logger.info("Attempting to connect to the database...")
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
        logger.info("Successfully connected to the database.")
        
        await init_db()
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.exception(f"Failed to connect to or initialize the database. Error: {e}")
        raise

    # Start background resume worker
    from app.engine.resume_manager import resume_paused_simulations
    resume_task = asyncio.create_task(resume_paused_simulations())

    logger.info("PersonaX Backend Ready!")

    yield

    # Shutdown
    logger.info("PersonaX Backend Shutting Down...")
    resume_task.cancel()
    try:
        await resume_task
    except asyncio.CancelledError:
        pass


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
    return {"status": "ok"}
