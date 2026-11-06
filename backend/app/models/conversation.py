from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npcs.id"), nullable=False, index=True)
    game_scope: Mapped[str | None] = mapped_column(String(36), nullable=True)
    source_event_id: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid4()), nullable=True)
    player_input: Mapped[str] = mapped_column(Text)
    llm_output: Mapped[dict] = mapped_column(JSON)
    validated_output: Mapped[dict] = mapped_column(JSON)
    final_dialogue: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Redesign linkage remains nullable so old rows keep their original provenance.
    turn_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    conversation_epoch: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    origin: Mapped[str | None] = mapped_column(String(32), nullable=True)

    __table_args__ = (Index('uq_conversations_turn_id', 'turn_id', unique=True),)

    npc = relationship("NPC", back_populates="conversations")
