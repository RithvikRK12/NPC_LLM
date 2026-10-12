from sqlalchemy import Float, Integer, String, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class NPC(Base):
    __tablename__ = "npcs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    role: Mapped[str] = mapped_column(String(120), index=True)
    trust: Mapped[float] = mapped_column(Float, default=0.5)
    fear: Mapped[float] = mapped_column(Float, default=0.1)
    aggression: Mapped[float] = mapped_column(Float, default=0.05)
    curiosity: Mapped[float] = mapped_column(Float, default=0.5)
    location: Mapped[str] = mapped_column(String(128), default="village_square")
    current_state: Mapped[str] = mapped_column(String(128), default="idle")

    memory_revision: Mapped[str] = mapped_column(String(36), default="initial", server_default="initial")

    pending_item: Mapped[str | None] = mapped_column(String(64), nullable=True)
    inventory: Mapped[list[str]] = mapped_column(JSON, default=list)

    memories = relationship("Memory", back_populates="npc", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="npc", cascade="all, delete-orphan")