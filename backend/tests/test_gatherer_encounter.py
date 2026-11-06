import unittest
from uuid import uuid4
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.database.base import Base
from app.database.seed import seed_world, reset_world
from app.models import NPC, Player, Memory
from app.api.routes.world import world
from app.services.gatherer import apply_command, encounter_snapshot


class GathererEncounterTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://')
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        seed_world(self.db)
        self.player = self.db.get(Player, 1)
        self.player.opening_state = 'complete'
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def state(self):
        return encounter_snapshot(self.db, self.player)

    def command(self, name, payload=None, key=None, revision=None):
        result = apply_command(self.db, self.player, name, key or str(uuid4()),
                               self.state()['revision'] if revision is None else revision, payload or {})
        self.db.commit()
        self.db.expire_all()
        self.assertEqual(world(self.db)['gatherer_encounter'], self.state())
        return result

    def attempt(self):
        return {'attempt_id': self.state()['attempt_id']}

    def test_help_reload_and_exactly_once(self):
        self.assertEqual(self.state()['status'], 'unseen')
        self.command('begin_intro')
        self.assertEqual(self.state()['status'], 'intro_pending')
        self.command('accept', self.attempt())
        attempt = self.attempt()
        revision = self.state()['revision']
        before = self.db.get(NPC, 2).memory_revision
        result = self.command('victory', attempt, 'win')
        self.assertAlmostEqual(result['npc']['trust'], .85)
        duplicate = apply_command(self.db, self.player, 'victory', 'win', revision, attempt)
        self.assertEqual(result, duplicate)
        self.assertEqual(self.state()['status'], 'saved_thanks_pending')
        npc = self.db.get(NPC, 2)
        self.assertAlmostEqual(npc.trust, .85)
        self.assertAlmostEqual(npc.fear, .10)
        self.assertAlmostEqual(npc.aggression, 0)
        self.assertAlmostEqual(npc.curiosity, .80)
        self.assertNotEqual(npc.memory_revision, before)
        memories = list(self.db.scalars(select(Memory).where(Memory.event_type == 'gatherer_encounter')))
        self.assertEqual(len(memories), 1)
        self.assertEqual((memories[0].epistemic_status, memories[0].authority), ('fact', 'authoritative'))
        self.command('finish_presentation')
        self.assertEqual(self.state()['status'], 'resolved_helped')
        self.assertEqual(self.player.inventory, ['water', 'food'])

    def test_retry_invalidates_attempt_without_social_changes(self):
        self.command('begin_intro')
        old = self.attempt()
        self.command('accept', old)
        self.command('restart_attempt', old)
        self.assertNotEqual(self.attempt(), old)
        self.assertEqual(self.state()['accepted_attempt_id'], '')
        for command, payload in [('victory', old), ('accept', old), ('victory', self.attempt())]:
            with self.assertRaises(HTTPException): self.command(command, payload)
        self.assertEqual(self.db.get(NPC, 2).trust, .5)
        self.assertEqual(list(self.db.scalars(select(Memory))), [])
        self.command('decline')
        self.assertEqual(self.state()['status'], 'declined_retreat_pending')

    def test_decline_all_reload_states_and_reset(self):
        self.command('begin_intro')
        result = self.command('decline', key='refuse')
        self.assertEqual(apply_command(self.db, self.player, 'decline', 'refuse', 0, {}), result)
        self.assertEqual(self.db.get(NPC, 2).trust, .15)
        self.assertEqual(self.db.get(NPC, 2).aggression, .75)
        self.command('complete_retreat')
        self.assertEqual(self.state()['status'], 'declined_return_pending')
        self.command('begin_confrontation')
        self.assertEqual(self.state()['status'], 'declined_confrontation_pending')
        self.command('finish_presentation')
        self.assertEqual(self.state()['status'], 'resolved_declined')
        with self.assertRaises(HTTPException): self.command('victory', self.attempt())
        self.assertEqual(len(list(self.db.scalars(select(Memory)))), 1)
        old_scope = self.player.game_scope
        reset_world(self.db)
        self.db.commit()
        self.assertNotEqual(self.player.game_scope, old_scope)
        self.assertEqual(self.state()['status'], 'unseen')
        self.assertEqual(list(self.db.scalars(select(Memory))), [])

    def test_invalid_commands_scope_revision_and_identity(self):
        from app.services.opening import current_run
        with self.assertRaises(HTTPException): current_run(self.db, 'old')
        for command in ['accept', 'victory', 'decline', 'complete_retreat', 'begin_confrontation', 'finish_presentation']:
            with self.assertRaises(HTTPException): self.command(command)
        self.command('begin_intro', key='intro')
        with self.assertRaises(HTTPException): self.command('accept', self.attempt(), revision=0)
        with self.assertRaises(HTTPException): self.command('decline', key='intro')

    def test_context_contains_authoritative_outcome_without_retrieval(self):
        from app.services.context.builder import ContextBuilder
        from unittest.mock import Mock
        self.command('begin_intro')
        self.command('decline')
        memory = Mock(last_retrieval_trace={})
        memory.retrieve_relevant_memories.return_value = []
        context = ContextBuilder(self.db, memory).build(self.db.get(NPC, 2), self.player, 'Hello')
        self.assertEqual(context.encounter['status'], 'declined_retreat_pending')
        self.assertIn('refused', context.encounter['outcome_fact'].lower())

    def test_chat_and_transfer_guard_tracks_active_story(self):
        from app.services.gatherer import chat_blocked
        npc = self.db.get(NPC, 2)
        self.assertFalse(chat_blocked(self.db, self.player, npc))
        self.command('begin_intro')
        self.assertTrue(chat_blocked(self.db, self.player, npc))
        self.assertTrue(chat_blocked(self.db, self.player, self.db.get(NPC, 1)))
        self.command('decline')
        self.command('complete_retreat')
        self.assertTrue(chat_blocked(self.db, self.player, npc))
        self.assertFalse(chat_blocked(self.db, self.player, self.db.get(NPC, 1)))
        self.command('begin_confrontation')
        self.command('finish_presentation')
        self.assertFalse(chat_blocked(self.db, self.player, npc))

    def test_atomic_outcome_rollback_and_clamping(self):
        self.command('begin_intro')
        self.command('accept', self.attempt())
        npc = self.db.get(NPC, 2)
        npc.trust, npc.curiosity = .95, .99
        self.db.commit()
        original_revision = npc.memory_revision
        revision = self.state()['revision']
        apply_command(self.db, self.player, 'victory', 'lost', revision, self.attempt())
        self.db.rollback()
        self.assertEqual(self.state()['status'], 'intro_pending')
        self.assertEqual(npc.trust, .95)
        self.assertEqual(npc.memory_revision, original_revision)
        self.assertEqual(list(self.db.scalars(select(Memory))), [])
        self.command('victory', self.attempt(), 'lost', revision)
        self.assertEqual(npc.trust, 1.)
        self.assertEqual(npc.curiosity, 1.)

    def test_request_identity_and_accepted_decline(self):
        self.command('begin_intro')
        self.command('accept', self.attempt(), 'help')
        with self.assertRaises(HTTPException): self.command('accept', {'attempt_id': 'wrong'}, 'help')
        with self.assertRaises(HTTPException): self.command('decline')
        self.command('restart_attempt', self.attempt())
        self.command('decline')

    def test_mock_dialogue_reflects_recorded_refusal_without_new_penalty(self):
        import json
        from app.services.llm.mock import MockLLMProvider
        self.command('begin_intro')
        self.command('decline')
        self.command('complete_retreat')
        self.command('begin_confrontation')
        self.command('finish_presentation')
        npc = self.db.get(NPC, 2)
        raw = json.loads(MockLLMProvider().generate('', dict(
            npc_role='gatherer', player_input='Hello', encounter=self.state(),
            npc_state={'trust': npc.trust, 'aggression': npc.aggression})))
        self.assertIn('left', raw['dialogue'].lower())
        self.assertNotEqual(raw['emotion'], 'friendly')
        self.assertFalse(any(raw['state_update'].values()))

    def test_relocated_pending_checkpoint_preserves_refusal_outcome(self):
        from app.models import GathererEncounter
        self.command('begin_intro')
        self.command('decline')
        row = self.db.get(GathererEncounter, self.player.id)
        row.state = row.state | {'checkpoint': {'position': {'x': -480., 'y': 70.}, 'staging_version': 1}}
        self.player.position = {'x': -590., 'y': 70.}
        self.db.commit()
        reloaded = self.state()
        self.assertEqual(reloaded['checkpoint']['staging_version'], 2)
        self.assertEqual(reloaded['status'], 'declined_retreat_pending')
        self.assertEqual(self.db.get(NPC, 2).trust, .15)
        self.assertEqual(len(list(self.db.scalars(select(Memory)))), 1)
        self.command('complete_retreat')
        self.assertEqual(self.player.position, {'x': -1000., 'y': 70.})
