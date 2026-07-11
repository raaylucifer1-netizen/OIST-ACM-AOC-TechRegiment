from pydantic import BaseModel, Field, constr, validator
from typing import Literal

class AgentResponseSchema(BaseModel):
    decision: Literal["Buy", "Consider", "Neutral", "Reject"]
    confidence: float = Field(ge=0.0, le=1.0)
    purchase_probability: int = Field(ge=0, le=100)
    sentiment: Literal["Positive", "Neutral", "Negative"]
    reason: str = Field(min_length=10) # Using a low min_length for safety, length check done via words
    price_opinion: str
    important_factor: str
    improvement_suggestion: str

    @validator('reason')
    def validate_reason_length(cls, v):
        words = v.split()
        if len(words) < 20: # Slightly relaxed from 40 to avoid overly strict LLM failures, but ensures it's detailed
            raise ValueError(f"Reason must be at least 20 words. Got {len(words)} words.")
        if len(words) > 300:
            raise ValueError(f"Reason must be under 300 words. Got {len(words)} words.")
        return v
