"""
Database module initialization

✅ Week 1 Day 4-5: Import all SQLAlchemy models
This ensures all models are registered with SQLAlchemy's metadata
before create_all() is called.
"""
from .base_class import Base
from .session import (
    engine,
    SessionLocal,
    get_db,
    create_tables,
    drop_tables,
    close_database,
    init_database
)

# ✅ Import all SQLAlchemy ORM models (must be imported BEFORE create_tables)
# This registers them with Base.metadata so tables can be created
from app.models.user import User
from app.models.conversation import Conversation, ConversationMessage
from app.models.conversation_state import ConversationState

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "create_tables",
    "drop_tables",
    "close_database",
    "init_database",
    # Models
    "User",
    "Conversation",
    "ConversationMessage",
    "ConversationState",
]
