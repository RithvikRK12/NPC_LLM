from sqlalchemy import ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class CraftsmanEncounter(Base):
    __tablename__ = 'craftsman_encounters'
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), primary_key=True)
    game_scope: Mapped[str] = mapped_column(String(36))
    revision: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    commands: Mapped[dict] = mapped_column(JSON, default=dict)
