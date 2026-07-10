"""Memory model for persona long-term memory."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    persona_id: Mapped[str] = mapped_column(String(36), ForeignKey("personas.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    memory_type: Mapped[str] = mapped_column(String(20), nullable=False, default="episodic")  # episodic, semantic, emotional
    importance: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)  # 0.0 to 1.0
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    persona: Mapped["Persona"] = relationship(back_populates="memories")

    def __repr__(self):
        return f"<Memory {self.memory_type}: {self.content[:50]}>"


from app.models.persona import Persona  # noqa: E402
