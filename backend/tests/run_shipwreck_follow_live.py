"""Reproduce shipwreck report/consent through /chat with local Llama and a disposable save.

Run with PYTHONPATH=backend and the config/playtest.env environment exported.
"""
import json

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


def main(report="My ship wrecked! I'm lost"):
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
            player = db.get(Player, 1)
            player.opening_state = 'complete'
            db.commit()
            app.dependency_overrides[get_db] = lambda: db
            for message, expected_offer, expected_active in (
                (report, True, False),
                ('Yes please', False, True),
            ):
                response = client.post('/chat', json={'npc_id': 1, 'player_message': message})
                assert response.status_code == 200, response.text
                data = response.json()
                encounter = data['craftsman_encounter']
                print(json.dumps({'message': message, 'dialogue': data['final_dialogue'],
                    'interpretation': data['grounding_trace']['accepted_interpretation'],
                    'encounter': encounter}), flush=True)
                assert encounter['offer_pending'] == expected_offer, 'Inspection offer was not routed'
                assert encounter['outing_active'] == expected_active, 'Follow activity was not started'
                assert not encounter['inspection_complete'], 'Chat must not complete inspection'
                assert data['ship_repair']['phase'] == 'not_started'
                assert data['player_inventory'] == ['water', 'food']
                if expected_active:
                    assert encounter['mode'] == 'departure_pending'
    finally:
        engine.dispose()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', default="My ship wrecked! I'm lost")
    main(parser.parse_args().report)
