from sqlalchemy import text

from app.database.base import Base
from app.database.session import engine
from app.models import conversation, memory, npc, player, quest  # noqa: F401


def initialize_database() -> None:
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)