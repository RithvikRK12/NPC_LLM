from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inventory: Mapped[list[str]] = mapped_column(JSON, default=list)
    position: Mapped[dict] = mapped_column(JSON, default=lambda: {"x": 0.0, "y": 0.0})
    current_location: Mapped[str] = mapped_column(String(128), default="village_square")