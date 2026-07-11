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
        logger.error("CRITICAL ERROR: DATABASE_URL environment variable is missing.")
        sys.exit(1)
        
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
        logger.error(f"CRITICAL ERROR: Failed to connect to or initialize the database. Error: {e}")
        sys.exit(1)

    # Auto-import personas for users that have none
    await _auto_import_personas()

    # Start background resume worker
    from app.engine.resume_manager import resume_paused_simulations
    resume_task = asyncio.create_task(resume_paused_simulations())

    logger.info("PersonaX Backend Ready!")

    yield

    # Shutdown
    logger.info("PersonaX Backend Shutting Down...")
    resume_task.cancel()


async def _auto_import_personas():
    """Auto-import 20,000 personas from CSV for any user with 0 personas."""
    import os
    from sqlalchemy import select, func
    from app.database import async_session
    from app.models.user import User
    from app.models.persona import Persona
    from app.utils.csv_importer import import_from_path

    csv_candidates = [
        r"D:\AARU\Personas\personas_20000.csv",
        r"D:\AARU\backend\data\personas_20000.csv",
        "./data/personas_20000.csv",
    ]

    csv_path = None
    for path in csv_candidates:
        if os.path.exists(path):
            csv_path = path
            break

    if not csv_path:
        logger.info("[SKIP] No persona CSV found for auto-import")
        return

    async with async_session() as db:
        # Get all users
        result = await db.execute(select(User))
        users = result.scalars().all()

        for user in users:
            count_result = await db.execute(
                select(func.count(Persona.id)).where(Persona.user_id == user.id)
            )
            count = count_result.scalar() or 0

            if count == 0:
                logger.info(f"[IMPORT] Importing personas for {user.email} ...")
                try:
                    res = await import_from_path(db, csv_path, user.id)
                    logger.info(f"[OK] Imported {res.get('imported', 0)} personas for {user.email}")
                except Exception as e:
                    logger.error(f"[ERROR] Failed to import for {user.email}: {e}")
            else:
                logger.info(f"[OK] {user.email} already has {count:,} personas")


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
