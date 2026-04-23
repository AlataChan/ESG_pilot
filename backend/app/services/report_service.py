"""
Service layer for handling business logic related to ESG reports.

✅ Week 2: Updated to use ReportDB ORM model
Now uses proper SQLAlchemy ORM instead of non-existent db_models.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Depends

from app.models.report_db import ReportDB
from app.models import report as report_models
from app.db.session import get_db

class ReportService:
    """
    ✅ ORM-based Report Service

    Manages ESG report lifecycle with proper database persistence.
    """
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, report_in: report_models.ReportCreate, user_id: Optional[int] = None) -> ReportDB:
        """
        ✅ Create a new report record in the database using ORM

        Args:
            report_in: Report creation data
            user_id: Optional user ID for ownership tracking

        Returns:
            Created ReportDB object
        """
        report_id = f"report_{uuid.uuid4()}"

        db_report = ReportDB(
            id=report_id,
            conversation_id=report_in.conversation_id,
            company_name=report_in.company_name,
            standard=report_in.standard,
            company_profile=report_in.company_profile,
            user_id=user_id,
            status="generating"
        )
        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)
        return db_report

    def get_report(self, report_id: str) -> Optional[ReportDB]:
        """
        ✅ Retrieve a report by its ID using ORM

        Args:
            report_id: Report ID

        Returns:
            ReportDB object or None
        """
        return self.db.query(ReportDB).filter(ReportDB.id == report_id).first()

    def update_report_status(self, report_id: str, status: str, error_message: Optional[str] = None) -> Optional[ReportDB]:
        """
        ✅ Update the status of a report

        Args:
            report_id: Report ID
            status: New status (generating, completed, failed)
            error_message: Optional error message

        Returns:
            Updated ReportDB object or None
        """
        db_report = self.get_report(report_id)
        if db_report:
            db_report.status = status
            if error_message:
                db_report.error_message = error_message
            self.db.commit()
            self.db.refresh(db_report)
        return db_report

    def update_report_content(self, report_id: str, content: dict) -> Optional[ReportDB]:
        """
        ✅ Update a report with the generated content

        Args:
            report_id: Report ID
            content: Report content dictionary

        Returns:
            Updated ReportDB object or None
        """
        db_report = self.get_report(report_id)
        if db_report:
            db_report.content = content
            db_report.status = "completed"
            db_report.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(db_report)
        return db_report

def get_report_service(db: Session = Depends(get_db)):
    """
    ✅ Dependency injector for the ReportService
    """
    return ReportService(db) 
