from fastapi import Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.pipeline import ConversationPipeline


def get_pipeline(db: Session = Depends(get_db)) -> ConversationPipeline:
    return ConversationPipeline(db)