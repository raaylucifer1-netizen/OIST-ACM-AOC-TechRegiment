"""Report model for generated simulation reports."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    simulation_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("simulations.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON structured report data
    charts: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON chart configurations
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(back_populates="reports")

    def __repr__(self):
        return f"<Report {self.title}>"


from app.models.simulation import Simulation  # noqa: E402
