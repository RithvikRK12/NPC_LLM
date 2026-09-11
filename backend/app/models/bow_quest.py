from sqlalchemy import Boolean, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base


class BowQuest(Base):
    __tablename__ = 'bow_quests'
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), primary_key=True)
    phase: Mapped[str] = mapped_column(String(32), default='available')
    string_collected: Mapped[bool] = mapped_column(Boolean, default=False)
    ready_at: Mapped[float | None] = mapped_column(Float, nullable=True)
