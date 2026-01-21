"""
Database Configuration - Async SQLAlchemy Engine
Configura la conexión async a PostgreSQL
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from functools import lru_cache

from app.core.config import get_settings

# Base para modelos declarativos
Base = declarative_base()


@lru_cache
def get_engine():
    """Crea engine async singleton para PostgreSQL"""
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )
    return engine


def get_session_factory():
    """Factory de sesiones async"""
    engine = get_engine()
    return sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncSession:
    """
    Dependency Injection para FastAPI
    Uso: async def endpoint(db: AsyncSession = Depends(get_db))
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Crea todas las tablas (para desarrollo/testing)"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Elimina todas las tablas (solo para testing)"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
