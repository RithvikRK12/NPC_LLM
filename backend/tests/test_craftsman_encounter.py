import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.base import Base
from app.database.seed import seed_world, reset_world
from app.models import Player, NPC
from app.api.routes.world import world

class CraftsmanEncounterTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        seed_world(self.db)
        self.player = self.db.get(Player, 1)
        self.player.opening_state = 'complete'
        self.player.position = {'x': 10000., 'y': 10128.}
        self.db.commit()
    def tearDown(self):
        self.db.close()
        self.engine.dispose()
    def command(self, name, key, payload=None, revision=None):
        from app.services.craftsman import apply_command, encounter_snapshot
        revision = encounter_snapshot(self.db, self.player)['revision'] if revision is None else revision
        result = apply_command(self.db, self.player, self.db.get(NPC, 1), name, key, revision, payload or {})
        self.db.commit()
        return result
    def test_world_has_independent_story_and_recipe(self):
        data = world(self.db)
        self.assertIn('craftsman_encounter', data)
        self.assertFalse(data['craftsman_encounter']['intro_seen'])
        self.assertEqual(data['ship_repair']['phase'], 'not_started')
        self.assertEqual({r['item']: r['required'] for r in data['ship_repair']['materials']},
                         dict(ship_plank=12, rope=3, sailcloth_bundle=2, pitch_pot=2))
        self.assertEqual(data['bow_quest']['phase'], 'available')
    def test_command_scope_identity_and_revision(self):
        from app.services.craftsman import apply_command, encounter_snapshot
        from app.services.opening import current_run
        with self.assertRaises(HTTPException): current_run(self.db, 'old-run')
        with self.assertRaises(HTTPException):
            apply_command(self.db, self.player, self.db.get(NPC, 2), 'begin_ship_inspection', 'x', 0, {})
        self.command('intro_complete', 'intro')
        with self.assertRaises(HTTPException): self.command('wait', 'stale', revision=0)
        self.assertTrue(encounter_snapshot(self.db, self.player)['intro_seen'])
    def test_inspection_requires_both_valid_marks_and_is_idempotent(self):
        self.command('begin_ship_inspection', 'accept')
        with self.assertRaises(HTTPException): self.command('complete_inspection', 'bad')
        self.db.rollback()
        from app.services.craftsman import checkpoint
        checkpoint(self.db, self.player, dict(mode='following_player', position={'x': 32., 'y': 3632.},
                   navigation_space='exterior'), 1)
        self.player.position = {'x': -32., 'y': 3632.}
        self.db.commit()
        result = self.command('complete_inspection', 'outcome', {'staged': True})
        again = self.command('complete_inspection', 'outcome', {'staged': True}, revision=0)
        self.assertEqual(result, again)
        data = world(self.db)
        self.assertEqual(data['ship_repair']['phase'], 'gathering_materials')
        self.assertEqual(data['craftsman_encounter']['mode'], 'returning_to_workshop')
        self.assertEqual(data['bow_quest']['phase'], 'available')
        self.assertEqual(self.player.inventory, ['water', 'food'])
        self.db.expire_all()
        self.assertEqual(world(self.db)['craftsman_encounter']['outcome_id'], result['craftsman_encounter']['outcome_id'])
    def test_checkpoint_cannot_create_story_or_skip_return(self):
        from app.services.craftsman import checkpoint, encounter_snapshot
        for value in [dict(mode='returning_to_workshop'), dict(position={'x': 10064., 'y': 9872.}),
                      dict(inspection_complete=True), dict(mode='inspection_dialogue')]:
            with self.subTest(value=value), self.assertRaises(HTTPException): checkpoint(self.db, self.player, value, 0)
        self.assertFalse(encounter_snapshot(self.db, self.player)['inspection_complete'])
    def test_new_game_resets_story(self):
        self.command('intro_complete', 'intro')
        self.command('begin_ship_inspection', 'outing')
        old = self.player.game_scope
        reset_world(self.db)
        self.db.commit()
        data = world(self.db)
        self.assertNotEqual(data['game_scope'], old)
        self.assertFalse(data['craftsman_encounter']['intro_seen'])
        self.assertEqual(data['craftsman_encounter']['mode'], 'workshop_routine')
        self.assertEqual(data['ship_repair']['phase'], 'not_started')

    def test_checkpoints_reject_scenery_and_nonfinite_ground(self):
        from app.services.craftsman import point_clear
        for position in [{'x':-250.,'y':2900.},{'x':250.,'y':2250.},{'x':float('nan'),'y':1.},{'x':'10000','y':10128.}]:
            self.assertFalse(point_clear(position),position)
        self.assertTrue(point_clear({'x':0.,'y':3504.}))
