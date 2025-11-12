"""
Database seeding script

✅ Week 1 Day 4-5: Create initial admin user

This script creates an initial admin user for the system.
Run this after creating the database tables.

Usage:
    python -m app.db.seed
"""

import logging
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.db.session import SessionLocal, init_database
from app.models.user import User
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(db_session):
    """
    Create initial admin user if it doesn't exist

    Default credentials:
        Username: admin
        Password: admin123
        Email: admin@esg-pilot.local

    ⚠️ IMPORTANT: Change the admin password after first login!
    """
    # Check if admin user already exists
    existing_admin = db_session.query(User).filter(User.username == "admin").first()

    if existing_admin:
        logger.info("Admin user already exists. Skipping creation.")
        return existing_admin

    # Create admin user
    admin_user = User(
        username="admin",
        email="admin@esg-pilot.local",
        full_name="System Administrator",
        hashed_password=get_password_hash("admin123"),
        is_active=True,
        is_superuser=True,
        role="admin"
    )

    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)

    logger.info(f"✅ Admin user created successfully!")
    logger.info(f"   Username: admin")
    logger.info(f"   Password: admin123")
    logger.info(f"   Email: admin@esg-pilot.local")
    logger.warning(f"⚠️  CHANGE THE ADMIN PASSWORD AFTER FIRST LOGIN!")

    return admin_user


def create_demo_user(db_session):
    """
    Create a demo regular user for testing

    Default credentials:
        Username: demo
        Password: demo123
        Email: demo@esg-pilot.local
    """
    # Check if demo user already exists
    existing_demo = db_session.query(User).filter(User.username == "demo").first()

    if existing_demo:
        logger.info("Demo user already exists. Skipping creation.")
        return existing_demo

    # Create demo user
    demo_user = User(
        username="demo",
        email="demo@esg-pilot.local",
        full_name="Demo User",
        hashed_password=get_password_hash("demo123"),
        is_active=True,
        is_superuser=False,
        role="user"
    )

    db_session.add(demo_user)
    db_session.commit()
    db_session.refresh(demo_user)

    logger.info(f"✅ Demo user created successfully!")
    logger.info(f"   Username: demo")
    logger.info(f"   Password: demo123")
    logger.info(f"   Email: demo@esg-pilot.local")

    return demo_user


def seed_database():
    """
    Main seeding function

    Creates initial users for the system.
    """
    logger.info("🌱 Starting database seeding...")

    try:
        # Initialize database connection
        init_database()
        db = SessionLocal()

        try:
            # Create admin user
            create_admin_user(db)

            # Create demo user
            create_demo_user(db)

            logger.info("🎉 Database seeding completed successfully!")

        except Exception as e:
            logger.error(f"❌ Error during seeding: {e}")
            db.rollback()
            raise

        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Failed to seed database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    seed_database()
