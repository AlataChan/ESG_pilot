"""
Service layer for handling business logic related to ESG reports.
This includes creating, updating, and retrieving reports from the database.
"""
import uuid
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Depends

from app.db import models as db_models
from app.models import report as report_models
from app.db.session import get_db

class ReportService:
    def __init__(self, db: Session):
        self.db = db

    def create_report(self, report_in: report_models.ReportCreate) -> db_models.Report:
        """
        Create a new report record in the database.
        Initial status is set to 'generating'.
        """
        report_id = f"report_{uuid.uuid4()}"
        
        db_report = db_models.Report(
            id=report_id,
            conversation_id=report_in.conversation_id,
            company_name=report_in.company_name,
            standard=report_in.standard,
            status="generating"
        )
        self.db.add(db_report)
        self.db.commit()
        self.db.refresh(db_report)
        return db_report

    def get_report(self, report_id: str) -> Optional[db_models.Report]:
        """
        Retrieve a report by its ID.
        """
        return self.db.query(db_models.Report).filter(db_models.Report.id == report_id).first()

    def update_report_status(self, report_id: str, status: str, error_message: Optional[str] = None) -> Optional[db_models.Report]:
        """
        Update the status of a report.
        """
        db_report = self.get_report(report_id)
        if db_report:
            db_report.status = status
            if error_message:
                db_report.error_message = error_message
            self.db.commit()
            self.db.refresh(db_report)
        return db_report
        
    def update_report_content(self, report_id: str, content: dict) -> Optional[db_models.Report]:
        """
        Update a report with the generated content and set its status to 'completed'.
        """
        db_report = self.get_report(report_id)
        if db_report:
            db_report.content = content
            db_report.status = "completed"
            self.db.commit()
            self.db.refresh(db_report)
        return db_report

def get_report_service(db: Session = Depends(get_db)):
    """
    Dependency injector for the ReportService.
    """
    return ReportService(db)

# We need to import Depends and get_db for the injector to work.
# from fastapi import Depends
# from app.db.session import get_db 