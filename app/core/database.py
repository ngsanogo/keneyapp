"""
Database configuration and session management for KeneyApp.
"""

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Create database engine with tuned connection pool settings
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=max(1, settings.DB_POOL_SIZE),
    max_overflow=max(0, settings.DB_MAX_OVERFLOW),
    pool_timeout=max(5, settings.DB_POOL_TIMEOUT),
    pool_recycle=max(30, settings.DB_POOL_RECYCLE),
    pool_use_lifo=True,
    echo=settings.DB_ECHO,
    future=True,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)

# Base class for SQLAlchemy models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
