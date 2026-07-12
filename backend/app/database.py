"""Database engine and session management."""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# ---------------------------------------------------------
# DATABASE ARCHITECTURE: 
# Backend: Render (Docker)
# Database: Supabase PostgreSQL (Direct Connection: Port 5432)
# ---------------------------------------------------------

# 1. Normalize DATABASE_URL for asyncpg driver
# This ensures that even if you paste `postgresql://` in Render, 
# it safely uses the asyncpg driver required by FastAPI.
db_url = settings.DATABASE_URL
if db_url and db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# 2. Connection Arguments
# Since this runs on Render (Docker) which maintains persistent long-running connections,
# we use the Direct Connection (5432) instead of the Transaction Pooler (6543).
# We leave connect_args empty so asyncpg can utilize native prepared statements for high performance.
connect_args = {}

if db_url.startswith("sqlite"):
    # Fallback for local development if SQLite is used
    connect_args = {"check_same_thread": False, "timeout": 30}


# 3. Create async SQLAlchemy engine
# Optimized for Render handling concurrent Vercel requests
engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    connect_args=connect_args,
    pool_size=20,          
    max_overflow=10,       
    pool_recycle=1800,     # Recycle idle connections to prevent Supabase disconnect timeouts
)

# 4. Async session factory
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base model
class Base(DeclarativeBase):
    pass

# Dependency for FastAPI
async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# Initialize DB Tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)