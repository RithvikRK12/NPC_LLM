from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.gatherer import GathererCommand
from app.services.opening import current_run
from app.services.gatherer import apply_command

router = APIRouter(prefix='/gatherer', tags=['gatherer'])


@router.post('/command')
def command(request: GathererCommand, db: Session = Depends(get_db)):
    player = current_run(db, request.game_scope)
    result = apply_command(db, player, request.command, request.request_id,
                           request.expected_revision, request.payload)
    db.commit()
    return result
