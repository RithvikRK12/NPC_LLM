from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.types import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

try:
    from pgvector.sqlalchemy import Vector
except Exception:  # pragma: no cover - optional dependency during local bootstrapping
    Vector = None


class EmbeddingVectorType(TypeDecorator):
    impl = JSON
    cache_ok = True

    def __init__(self, dimensions: int = 1536) -> None:
        super().__init__()
        self.dimensions = dimensions

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql" and Vector is not None:
            return dialect.type_descriptor(Vector(self.dimensions))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        return value

    def process_result_value(self, value, dialect):
        return value


class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npcs.id"), nullable=False, index=True)
    event: Mapped[str] = mapped_column(String(512))
    importance: Mapped[float] = mapped_column(Float, default=0.5)
    emotion: Mapped[str] = mapped_column(String(64), default="neutral")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    embedding: Mapped[Any] = mapped_column(EmbeddingVectorType(), nullable=True)

    npc = relationship("NPC", back_populates="memories")