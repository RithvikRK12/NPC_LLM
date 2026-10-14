from sqlalchemy import ForeignKey, JSON, String, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class ShipRepairQuest(Base):
    __tablename__ = 'ship_repair_quests'
    player_id: Mapped[int] = mapped_column(ForeignKey('players.id'), primary_key=True)
    game_scope: Mapped[str] = mapped_column(String(36))
    phase: Mapped[str] = mapped_column(String(32), default='gathering_materials')
    contributions: Mapped[dict] = mapped_column(JSON, default=dict)
    outcome_id: Mapped[str] = mapped_column(String(64), unique=True)

class StoryEvent(Base):
    """Future repair transaction emits main_story_completed once per run.

    No completion writer is exposed until actual repair is implemented.
    """
    __tablename__ = 'story_events'
    __table_args__ = (UniqueConstraint('game_scope', 'event_type'),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_scope: Mapped[str] = mapped_column(String(36))
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
