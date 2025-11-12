"""
Knowledge Database Models

✅ Week 2: Data Persistence
SQLAlchemy ORM models for knowledge management system.

This replaces the raw SQLite implementation with proper ORM models
that work with both SQLite (dev) and PostgreSQL (production).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base
from app.models.knowledge import DocumentStatus, DocumentType


class KnowledgeCategoryDB(Base):
    """
    ✅ SQLAlchemy ORM model for knowledge categories

    Replaces raw SQL table with proper ORM model.
    """
    __tablename__ = "knowledge_categories"

    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    color = Column(String(7), nullable=False, default="#1976d2")  # Hex color code
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="knowledge_categories")
    documents = relationship("KnowledgeDocumentDB", back_populates="category")


class KnowledgeDocumentDB(Base):
    """
    ✅ SQLAlchemy ORM model for knowledge documents

    Replaces raw SQL table with proper ORM model.
    Stores document metadata and processing status.
    """
    __tablename__ = "knowledge_documents"

    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)  # UUID-based safe filename
    original_filename = Column(String(255), nullable=False)  # Original user filename
    file_path = Column(String(500), nullable=False)  # Full path to file
    file_type = Column(String(20), nullable=False)  # DocumentType enum value
    file_size = Column(Integer, nullable=False)  # File size in bytes

    # Category
    category_id = Column(String, ForeignKey("knowledge_categories.id"), nullable=True, index=True)

    # Processing status
    status = Column(
        String(20),
        nullable=False,
        default=DocumentStatus.PROCESSING.value,
        index=True
    )
    vector_indexed = Column(Boolean, default=False, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    processing_error = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="knowledge_documents")
    category = relationship("KnowledgeCategoryDB", back_populates="documents")

    # ✅ Week 3: Composite indexes for query optimization
    __table_args__ = (
        # Most common query: list documents by user + status
        Index('ix_user_status', 'user_id', 'status'),

        # Query: list documents by user + category + status
        Index('ix_user_category_status', 'user_id', 'category_id', 'status'),

        # Query: list documents by user + file_type + status
        Index('ix_user_type_status', 'user_id', 'file_type', 'status'),

        # Query: pagination with date sorting (user + created_at)
        Index('ix_user_created', 'user_id', 'created_at'),

        # Query: find vector indexed documents for user
        Index('ix_user_vector', 'user_id', 'vector_indexed'),
    )

    def __repr__(self):
        return f"<KnowledgeDocument(id={self.id}, filename={self.original_filename}, status={self.status})>"
