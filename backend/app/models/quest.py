from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Quest(Base):
    __tablename__ = "quests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(64), default="not_started")
    progress: Mapped[int] = mapped_column(Integer, default=0)

    player = relationship("Player")