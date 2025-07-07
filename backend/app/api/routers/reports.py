"""
API endpoints for managing and retrieving ESG reports.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Any

from app.services.report_service import ReportService, get_report_service
from app.models import report as report_models

router = APIRouter()

@router.get(
    "/{report_id}",
    response_model=report_models.ReportResponse,
    summary="Get a Report by ID",
    description="Retrieve the status and content of a specific ESG report."
)
def get_report(
    report_id: str,
    report_service: ReportService = Depends(get_report_service),
) -> Any:
    """
    Get a single report by its unique ID.
    
    - **report_id**: The UUID of the report to retrieve.
    """
    db_report = report_service.get_report(report_id)
    if not db_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with ID {report_id} not found."
        )
    return db_report 