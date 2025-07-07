"""
Report-related Pydantic models for request/response validation and data transfer.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

class ReportBase(BaseModel):
    """Base model for a report."""
    company_name: str = Field(..., description="The name of the company.")
    standard: str = Field(default="GRI", description="The reporting standard used (e.g., GRI, SASB).")

class ReportCreate(ReportBase):
    """Model for creating a new report, usually triggered by an agent."""
    conversation_id: str = Field(..., description="The conversation ID that triggered this report.")
    company_profile: Dict[str, Any] = Field(..., description="The complete company profile data.")

class ReportUpdate(BaseModel):
    """Model for updating an existing report."""
    status: Optional[str] = Field(None, description="The new status of the report (e.g., generating, completed, failed).")
    content: Optional[Dict[str, Any]] = Field(None, description="The generated content of the report.")
    error_message: Optional[str] = Field(None, description="Error message if the generation failed.")

class ReportInDB(ReportBase):
    """Model representing a report as stored in the database."""
    id: str = Field(..., description="The unique ID of the report.")
    status: str = Field(..., description="The current status of the report.")
    content: Optional[Dict[str, Any]] = Field(None, description="The JSON content of the report.")
    created_at: datetime = Field(..., description="Timestamp of when the report was created.")
    updated_at: datetime = Field(..., description="Timestamp of the last update.")
    
    class Config:
        from_attributes = True #  for Pydantic V2, orm_mode = True for V1

class ReportResponse(BaseModel):
    """The response model for a report, sent to the client."""
    id: str
    status: str
    company_name: str
    standard: str
    content: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime 