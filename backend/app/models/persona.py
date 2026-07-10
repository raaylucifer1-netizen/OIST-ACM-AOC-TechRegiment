"""Persona model — maps the 42-column CSV plus enrichments."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Persona(Base):
    __tablename__ = "personas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True)

    # Identity fields from CSV
    persona_id: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # P00001
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)

    # Socioeconomic
    education: Mapped[str] = mapped_column(String(100), nullable=False)
    occupation: Mapped[str] = mapped_column(String(100), nullable=False)
    income_inr: Mapped[int] = mapped_column(Integer, nullable=False)
    language: Mapped[str] = mapped_column(String(255), nullable=False)
    marital_status: Mapped[str] = mapped_column(String(20), nullable=False)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Lifestyle
    lifestyle: Mapped[str] = mapped_column(String(50), nullable=False)
    shopping_frequency: Mapped[str] = mapped_column(String(50), nullable=False)
    online_shopping_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    offline_shopping_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle: Mapped[str] = mapped_column(String(50), nullable=False)
    technology_adoption: Mapped[str] = mapped_column(String(50), nullable=False)

    # Preferences
    health_consciousness: Mapped[int] = mapped_column(Integer, nullable=False)
    food_preference: Mapped[str] = mapped_column(String(50), nullable=False)
    political_interest: Mapped[str] = mapped_column(String(20), nullable=False)
    social_media_usage: Mapped[int] = mapped_column(Integer, nullable=False)
    brand_loyalty: Mapped[int] = mapped_column(Integer, nullable=False)
    price_sensitivity: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_taking: Mapped[int] = mapped_column(Integer, nullable=False)
    impulse_buying: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_preference: Mapped[int] = mapped_column(Integer, nullable=False)
    premium_preference: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_brand: Mapped[str] = mapped_column(String(100), nullable=False)

    # Communication
    communication_style: Mapped[str] = mapped_column(String(50), nullable=False)
    response_length: Mapped[str] = mapped_column(String(20), nullable=False)

    # Big Five personality traits (0-100)
    openness: Mapped[int] = mapped_column(Integer, nullable=False)
    conscientiousness: Mapped[int] = mapped_column(Integer, nullable=False)
    extraversion: Mapped[int] = mapped_column(Integer, nullable=False)
    agreeableness: Mapped[int] = mapped_column(Integer, nullable=False)
    neuroticism: Mapped[int] = mapped_column(Integer, nullable=False)

    # Emotional profile (0-100)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False)
    optimism: Mapped[int] = mapped_column(Integer, nullable=False)
    patience: Mapped[int] = mapped_column(Integer, nullable=False)
    curiosity: Mapped[int] = mapped_column(Integer, nullable=False)
    practicality: Mapped[int] = mapped_column(Integer, nullable=False)
    emotional_score: Mapped[int] = mapped_column(Integer, nullable=False)

    # Enrichments
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array as text for SQLite
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)  # Generated persona description

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="personas")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="persona", cascade="all, delete-orphan")
    memories: Mapped[list["Memory"]] = relationship(back_populates="persona", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Persona {self.persona_id} {self.age}{self.gender[0]} {self.city}>"

    def to_profile_dict(self) -> dict:
        """Return a dict suitable for prompt construction."""
        return {
            "persona_id": self.persona_id,
            "age": self.age,
            "gender": self.gender,
            "city": self.city,
            "state": self.state,
            "education": self.education,
            "occupation": self.occupation,
            "income_inr": self.income_inr,
            "language": self.language,
            "marital_status": self.marital_status,
            "children": self.children,
            "lifestyle": self.lifestyle,
            "shopping_frequency": self.shopping_frequency,
            "online_shopping_pct": self.online_shopping_pct,
            "offline_shopping_pct": self.offline_shopping_pct,
            "payment_method": self.payment_method,
            "vehicle": self.vehicle,
            "technology_adoption": self.technology_adoption,
            "health_consciousness": self.health_consciousness,
            "food_preference": self.food_preference,
            "political_interest": self.political_interest,
            "social_media_usage": self.social_media_usage,
            "brand_loyalty": self.brand_loyalty,
            "price_sensitivity": self.price_sensitivity,
            "risk_taking": self.risk_taking,
            "impulse_buying": self.impulse_buying,
            "discount_preference": self.discount_preference,
            "premium_preference": self.premium_preference,
            "preferred_brand": self.preferred_brand,
            "communication_style": self.communication_style,
            "response_length": self.response_length,
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism,
            "confidence": self.confidence,
            "optimism": self.optimism,
            "patience": self.patience,
            "curiosity": self.curiosity,
            "practicality": self.practicality,
            "emotional_score": self.emotional_score,
        }


from app.models.project import Project  # noqa: E402
from app.models.conversation import Conversation  # noqa: E402
from app.models.memory import Memory  # noqa: E402
