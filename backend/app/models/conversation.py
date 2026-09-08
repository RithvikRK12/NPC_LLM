from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    npc_id: Mapped[int] = mapped_column(ForeignKey("npcs.id"), nullable=False, index=True)
    player_input: Mapped[str] = mapped_column(Text)
    llm_output: Mapped[dict] = mapped_column(JSON)
    validated_output: Mapped[dict] = mapped_column(JSON)
    final_dialogue: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    npc = relationship("NPC", back_populates="conversations")