from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Index, event as sa_event, update
from uuid import uuid4
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

    # Separate column preserves legacy 1536-dimensional hashed vectors during migration.
    semantic_embedding: Mapped[Any] = mapped_column(JSON, nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), default='legacy', server_default='legacy')
    quest_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    duplicate_key: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    game_scope: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_event_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_conversation_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    epistemic_status: Mapped[str] = mapped_column(String(24), default='interpretation', server_default='interpretation')
    authority: Mapped[str] = mapped_column(String(24), default='inferred', server_default='inferred')
    lifecycle: Mapped[str] = mapped_column(String(24), default='active', server_default='active')
    claim_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    correction_of_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    superseded_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    __table_args__ = (
        Index('ix_memory_scope', 'npc_id', 'embedding_model', 'event_type', 'quest_id', 'timestamp'),
        Index('uq_memory_source', 'game_scope', 'npc_id', 'source_event_id', unique=True),
    )

    npc = relationship("NPC", back_populates="memories")

@sa_event.listens_for(Memory, 'after_insert')
@sa_event.listens_for(Memory, 'after_update')
@sa_event.listens_for(Memory, 'after_delete')
def invalidate_memory_index(mapper, connection, target):
    # The revision is committed/rolled back WITH the memory, preventing cache ghosts.
    from app.models.npc import NPC
    connection.execute(update(NPC).where(NPC.id == target.npc_id).values(memory_revision=str(uuid4())))
