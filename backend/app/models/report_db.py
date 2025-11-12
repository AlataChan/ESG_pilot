"""
Report Database Model

✅ Week 2: Data Persistence
SQLAlchemy ORM model for ESG report storage.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ReportDB(Base):
    """
    ✅ SQLAlchemy ORM model for ESG reports

    Stores generated ESG reports with status tracking.
    """
    __tablename__ = "reports"

    id = Column(String, primary_key=True)  # report_uuid format
    conversation_id = Column(String(100), ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    # Company information
    company_name = Column(String(200), nullable=False, index=True)
    standard = Column(String(50), nullable=False, default="GRI")  # GRI, SASB, etc.

    # Report content
    content = Column(JSON, nullable=True)  # Full report content as JSON
    company_profile = Column(JSON, nullable=True)  # Company profile data

    # Status tracking
    status = Column(String(20), nullable=False, default="generating", index=True)
    # Status options: generating, completed, failed
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, company={self.company_name}, status={self.status})>"
