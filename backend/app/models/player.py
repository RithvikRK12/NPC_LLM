from uuid import uuid4

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    game_scope: Mapped[str] = mapped_column(String(36), default=lambda: str(uuid4()), server_default="legacy")
    inventory: Mapped[list[str]] = mapped_column(JSON, default=list)
    position: Mapped[dict] = mapped_column(JSON, default=lambda: {"x": 0.0, "y": 0.0})
    current_location: Mapped[str] = mapped_column(String(128), default="village_square")
    opening_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    opening_state: Mapped[str] = mapped_column(String(16), default="complete", server_default="complete")
    map_version: Mapped[int] = mapped_column(Integer, default=2, server_default="0")
    salvage_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    map_recovery_notice: Mapped[str] = mapped_column(String(255), default="", server_default="")
