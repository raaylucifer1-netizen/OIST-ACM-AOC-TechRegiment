"""Simulation and SimulationResponse models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("projects.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # market, election, product_launch, etc.
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: filters, sample_size, params
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, running, completed, failed
    sample_size: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    results_summary: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON aggregate results
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(back_populates="simulations")
    responses: Mapped[list["SimulationResponse"]] = relationship(back_populates="simulation", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="simulation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Simulation {self.type}: {self.title}>"


class SimulationResponse(Base):
    __tablename__ = "simulation_responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    simulation_id: Mapped[str] = mapped_column(String(36), ForeignKey("simulations.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(String(36), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    sentiment: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Positive, Neutral, Negative
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0 to 1.0
    purchase_probability: Mapped[int | None] = mapped_column(Integer, nullable=True) # 0 to 100
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Buy, Consider, Neutral, Reject
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    price_opinion: Mapped[str | None] = mapped_column(Text, nullable=True)
    important_factor: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvement_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider_used: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generation_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Extra structured data
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(back_populates="responses")

    def __repr__(self):
        return f"<SimResponse sim={self.simulation_id} persona={self.persona_id}>"


from app.models.project import Project  # noqa: E402
from app.models.report import Report  # noqa: E402
