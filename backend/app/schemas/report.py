"""Report schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ReportResponse(BaseModel):
    id: str
    user_id: str
    simulation_id: Optional[str] = None
    title: str
    content: Optional[str] = None
    charts: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    reports: list[ReportResponse]
    total: int
