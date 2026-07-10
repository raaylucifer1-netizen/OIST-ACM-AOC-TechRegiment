"""Project schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    is_archived: bool = False
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime
    persona_count: int = 0
    simulation_count: int = 0

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
