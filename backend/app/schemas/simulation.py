"""Simulation schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SimulationCreate(BaseModel):
    project_id: Optional[str] = None
    type: str  # market, election, product_launch, pricing, feature_test, ad_test, policy, crisis, brand, interview
    title: str
    question: str
    sample_size: int = 100
    config: Optional[dict] = None  # filters, extra params


class SimulationResponse(BaseModel):
    id: str
    user_id: str
    project_id: Optional[str] = None
    type: str
    title: str
    question: str
    status: str
    sample_size: int
    results_summary: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SimResponseItem(BaseModel):
    persona_id: str
    persona_label: str  # e.g. "P00001 (28M, Mumbai)"
    response: str
    sentiment: Optional[float] = None
    confidence: Optional[float] = None
    decision: Optional[str] = None

    model_config = {"from_attributes": True}


class SimulationResultFull(BaseModel):
    simulation: SimulationResponse
    responses: list[SimResponseItem]
    analytics: dict  # sentiment_distribution, demographic_breakdown, etc.


class SimulationListResponse(BaseModel):
    simulations: list[SimulationResponse]
    total: int
