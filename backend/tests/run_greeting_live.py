"""Check first-call local Llama greeting routing through /chat in a disposable save."""
import json
from time import monotonic

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.router import api_router
from app.config.settings import get_settings
from app.database.base import Base
from app.database.seed import seed_world
from app.database.session import get_db
from app.models import Player


def main():
    settings = get_settings()
    assert settings.llm_model == 'llama3:willowbrook'
    assert settings.llm_base_url.rstrip('/') == 'http://127.0.0.1:11434/v1'
    engine = create_engine('sqlite://', poolclass=StaticPool,
                           connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    app = FastAPI()
    app.include_router(api_router)
    try:
        with Session(engine) as db, TestClient(app) as client:
            seed_world(db)
            db.get(Player, 1).opening_state = 'complete'
            db.commit()
            app.dependency_overrides[get_db] = lambda: db
            started = monotonic()
            response = client.post('/chat', json={'npc_id': 1, 'player_message': 'hello'})
            assert response.status_code == 200, response.text
            data = response.json()
            trace = data['grounding_trace']
            print(json.dumps({'seconds': round(monotonic() - started, 3),
                'dialogue': data['final_dialogue'], 'trace': trace}), flush=True)
            assert not trace['rejected'], trace['rejection_reason']
            assert trace['model_calls'] == {'interpretation': 1, 'speech_and_repair': 1}
            concerns = trace['accepted_interpretation']['concerns']
            assert len(concerns) == 1 and concerns[0]['kind'] == 'social', concerns
            assert data['final_dialogue'].strip()
            assert not data['craftsman_encounter']['outing_active']
            assert data['player_inventory'] == ['water', 'food']
    finally:
        engine.dispose()


if __name__ == '__main__':
    main()
