"""
Database session management
Provides SQLAlchemy session factory and dependency injection for FastAPI
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings
from app.db.base_class import Base

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine based on environment
engine = None
SessionLocal = None

def init_database():
    """Initialize database engine and session factory"""
    global engine, SessionLocal

    if engine is not None:
        return engine, SessionLocal

    # Get database URL from settings
    database_url = settings.SQLALCHEMY_DATABASE_URI

    if not database_url:
        logger.warning("No database URL configured. Using in-memory SQLite.")
        database_url = "sqlite:///:memory:"

    # Configure engine based on database type
    if database_url.startswith("sqlite"):
        # SQLite-specific configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},  # SQLite specific
            poolclass=NullPool,  # Disable pooling for SQLite
            echo=False  # Set to True for SQL debugging
        )
        logger.info(f"🗄️  Database engine created: SQLite")
    else:
        # PostgreSQL configuration
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,  # Recycle connections after 1 hour
            echo=False
        )
        logger.info(f"🗄️  Database engine created: PostgreSQL")

    # Create session factory
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )

    logger.info("✅ Database session factory initialized")
    return engine, SessionLocal


# Initialize on import
engine, SessionLocal = init_database()

# Base is imported from base_class.py to avoid duplication


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.

    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    Yields:
        Database session that will be automatically closed after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all database tables defined in models"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def drop_tables():
    """Drop all database tables (use with caution!)"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("⚠️  All database tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise


def close_database():
    """Close database connections and dispose engine"""
    global engine
    if engine:
        engine.dispose()
        logger.info("🔒 Database connections closed")
