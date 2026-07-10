"""Persona request/response schemas."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PersonaBase(BaseModel):
    persona_id: str
    age: int
    gender: str
    city: str
    state: str
    education: str
    occupation: str
    income_inr: int
    language: str
    marital_status: str
    children: int
    lifestyle: str
    shopping_frequency: str
    online_shopping_pct: int
    offline_shopping_pct: int
    payment_method: str
    vehicle: str
    technology_adoption: str
    health_consciousness: int
    food_preference: str
    political_interest: str
    social_media_usage: int
    brand_loyalty: int
    price_sensitivity: int
    risk_taking: int
    impulse_buying: int
    discount_preference: int
    premium_preference: int
    preferred_brand: str
    communication_style: str
    response_length: str
    openness: int
    conscientiousness: int
    extraversion: int
    agreeableness: int
    neuroticism: int
    confidence: int
    optimism: int
    patience: int
    curiosity: int
    practicality: int
    emotional_score: int


class PersonaCreate(PersonaBase):
    project_id: Optional[str] = None
    tags: Optional[str] = None


class PersonaResponse(PersonaBase):
    id: str
    user_id: str
    project_id: Optional[str] = None
    tags: Optional[str] = None
    narrative: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PersonaListResponse(BaseModel):
    personas: list[PersonaResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PersonaFilter(BaseModel):
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    city: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    income_min: Optional[int] = None
    income_max: Optional[int] = None
    lifestyle: Optional[str] = None
    technology_adoption: Optional[str] = None
    food_preference: Optional[str] = None
    political_interest: Optional[str] = None
    preferred_brand: Optional[str] = None
    openness_min: Optional[int] = None
    openness_max: Optional[int] = None
    conscientiousness_min: Optional[int] = None
    conscientiousness_max: Optional[int] = None
    extraversion_min: Optional[int] = None
    extraversion_max: Optional[int] = None
    agreeableness_min: Optional[int] = None
    agreeableness_max: Optional[int] = None
    neuroticism_min: Optional[int] = None
    neuroticism_max: Optional[int] = None
    search: Optional[str] = None  # Full-text search across fields


class PersonaStats(BaseModel):
    total_personas: int
    avg_age: float
    gender_distribution: dict
    state_distribution: dict
    income_distribution: dict
    top_occupations: list[dict]
    lifestyle_distribution: dict
    avg_big_five: dict


class ImportProgress(BaseModel):
    total: int
    imported: int
    failed: int
    status: str  # "processing", "completed", "failed"
    errors: list[str] = []
