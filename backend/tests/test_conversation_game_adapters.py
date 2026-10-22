"""Game effects use disposable SQLite; no provider, embeddings or player save."""
import unittest
import json
from dataclasses import replace
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.seed import seed_world
from app.models import BowQuest, CraftsmanEncounter, GathererEncounter, Memory, NPC, Player, Quest
from app.services import gatherer
from app.services.conversation import contracts as c

try:
    from app.services.conversation.adapters.game import (
        AUDITED_COMMANDS, GameOperationAdapter, encounter_command_id,
    )
except ModuleNotFoundError:
    AUDITED_COMMANDS = GameOperationAdapter = encounter_command_id = None


try:
    from app.services.conversation.adapters.game import GameReadAdapter, ConsentSnapshot
except ImportError:
    GameReadAdapter = ConsentSnapshot = None


class ConversationGameAdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(GameOperationAdapter, 'audited game operation adapter is absent')
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.engine = create_engine('sqlite:///' + str(Path(self.temp.name) / 'game.sqlite'))
        self.addCleanup(self.engine.dispose)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.addCleanup(self.db.close)
        seed_world(self.db)
        self.player = self.db.get(Player, 1)
        self.player.opening_state = 'complete'
        self.scope = self.player.game_scope
        self.db.commit()
        self.adapter = GameOperationAdapter(self.db)

    def turn(self, npc_id=1, **changes):
        return c.TurnRef.model_validate(dict(
            turn_id='turn:2', request_id='request:2', sequence=2,
            key=dict(game_scope=self.scope, npc_id=npc_id, epoch=0), **changes))

    def decision(self, command='give_item', item='wood', npc_id=2):
        checks = ()
        if GameReadAdapter is not None and self.db.in_transaction():
            checks = next(cap.relevant_preconditions for cap in
                GameReadAdapter(self.db).read_capabilities(self.scope, npc_id, 'public')
                if cap.command_id == command)
        return c.ReadyToRecheck.model_validate(dict(
            kind='ready_to_recheck', consent=None, checked_preconditions=checks,
            operation=dict(candidate_id='candidate:1', command_id=command,
                           arguments={'item': item} if command in {'give_item', 'receive_item'} else {},
                           target=dict(reference_id=f'npc:{npc_id}', entity_kind='npc', entity_id=str(npc_id)),
                           source_spans=[dict(text_id='message:2', start=0, end=10)],
                           modality='direct', pending_question_id=None)))

    def begin(self):
        self.db.begin()

    def test_bow_discussion_advances_meet_through_audited_transaction_only(self):
        self.db.add(BowQuest(player_id=1, phase='meet', string_collected=False))
        self.db.commit()
        self.begin()
        decision = self.decision('discuss_bow', npc_id=1)
        effect = self.adapter.execute(self.turn(), decision)
        self.assertIsInstance(effect.result, c.CommandResult)
        self.assertTrue(effect.result.changed)
        self.assertEqual(self.db.get(BowQuest, 1).phase, 'gather')
        self.assertNotIn('bow', self.db.get(Player, 1).inventory)
        self.db.rollback()
        self.assertEqual(self.db.get(BowQuest, 1).phase, 'meet')

    def test_bow_discussion_rechecks_current_phase_and_role(self):
        self.db.add(BowQuest(player_id=1, phase='meet', string_collected=False))
        self.db.commit()
        self.begin()
        decision = self.decision('discuss_bow', npc_id=1)
        self.db.get(BowQuest, 1).phase = 'completed'
        self.db.flush()
        self.assertIsInstance(self.adapter.execute(self.turn(), decision), c.Denied)
        self.assertEqual(self.db.get(BowQuest, 1).phase, 'completed')
        self.assertIsInstance(self.adapter.execute(self.turn(2), self.decision('discuss_bow', npc_id=2)), c.Denied)

    def test_registry_audits_only_existing_commands_and_cannot_be_extended(self):
        self.assertEqual(set(AUDITED_COMMANDS), {
            'give_item', 'receive_item', 'report_wreck', 'begin_ship_inspection',
            'wait', 'resume', 'postpone', 'return', 'discuss_bow',
        })
        for command, entry in AUDITED_COMMANDS.items():
            with self.subTest(command=command):
                self.assertEqual(entry.command_id, command)
                self.assertEqual(entry.argument_type, c.ItemArguments if command.endswith('_item') else c.NoArguments)
                self.assertEqual(entry.rule_owner, 'app.services.state.service.StateService.apply'
                                 if command.endswith('_item') else ('app.services.quests.bow.dialogue'
                                 if command == 'discuss_bow' else 'app.services.craftsman.apply_command'))
        with self.assertRaises(TypeError):
            AUDITED_COMMANDS['victory'] = AUDITED_COMMANDS['report_wreck']

    def test_unsupported_endpoints_and_generated_state_never_dispatch(self):
        self.begin()
        valid = self.decision('report_wreck', npc_id=1)
        for command in ('complete_inspection', 'victory', 'accept', 'pickup-string', 'start', 'advance', 'craft_bow'):
            with self.subTest(command=command):
                forged = valid.model_copy(update={'operation': valid.operation.model_copy(update={'command_id': command})})
                self.assertIsInstance(self.adapter.execute(self.turn(), forged), c.Denied)
        for arguments in ({'trust': 1}, {'biography': 'My father taught me to award bows.'},
                          {'item': 'bow', 'quantity': 10}, {'state_update': {'trust': 1}}):
            with self.subTest(arguments=arguments):
                forged = valid.model_copy(update={'operation': valid.operation.model_copy(update={'arguments': arguments})})
                self.assertIsInstance(self.adapter.execute(self.turn(), forged), c.Denied)
        self.assertIsNone(self.db.get(CraftsmanEncounter, 1))
        self.assertIsNone(self.db.get(BowQuest, 1))
        self.assertEqual(self.db.get(NPC, 1).trust, .65)
        self.assertEqual(self.db.get(Player, 1).inventory, ['water', 'food'])

    def test_requires_caller_transaction_and_typed_values(self):
        with self.assertRaises(ValueError):
            self.adapter.execute(self.turn(2), self.decision())
        self.begin()
        with self.assertRaises(TypeError):
            self.adapter.execute(self.turn(2).model_dump(), self.decision())
        with self.assertRaises(TypeError):
            self.adapter.execute(self.turn(2), self.decision().model_dump())

    def test_inventory_and_legacy_quest_effects_rollback_on_caller_failure(self):
        self.begin()
        result = self.adapter.execute(self.turn(2), self.decision())
        self.assertEqual(result.result, c.TransferResult(kind='item_transfer', item='wood', quantity=1, direction='to_player'))
        self.assertEqual(self.db.get(Player, 1).inventory, ['water', 'food', 'wood'])
        self.assertEqual(self.db.get(NPC, 2).inventory, ['axe', 'fruits'])
        self.assertEqual(self.db.scalar(select(Quest)).progress, 50)
        self.assertTrue(self.db.in_transaction())
        self.db.rollback()  # e.g. receipt write failed after the operation
        with Session(self.engine) as read:
            self.assertEqual(read.get(Player, 1).inventory, ['water', 'food'])
            self.assertEqual(read.get(NPC, 2).inventory, ['axe', 'wood', 'fruits'])
            self.assertEqual(read.scalar(select(Quest)).progress, 0)

    def test_caller_can_commit_transfer_and_quantity_is_exactly_one(self):
        npc = self.db.get(NPC, 2)
        npc.inventory = ['wood', 'wood']
        self.db.commit()
        self.begin()
        self.adapter.execute(self.turn(2), self.decision())
        self.db.commit()
        with Session(self.engine) as read:
            self.assertEqual(read.get(NPC, 2).inventory, ['wood'])
            self.assertEqual(read.get(Player, 1).inventory.count('wood'), 1)
            self.assertEqual(read.get(NPC, 2).trust, .5)

    def test_exact_transfer_ownership_target_and_role_are_rechecked(self):
        self.begin()
        for decision in (
            self.decision(item='bow'),
            self.decision(npc_id=1),  # target and conversation NPC differ
            self.decision('receive_item', item='bow'),
        ):
            with self.subTest(decision=decision):
                self.assertIsInstance(self.adapter.execute(self.turn(2), decision), c.Denied)
        self.db.get(NPC, 2).role = 'unregistered_role'
        self.db.flush()
        self.assertIsInstance(self.adapter.execute(self.turn(2), self.decision()), c.Denied)
        self.assertEqual(self.db.get(Player, 1).inventory, ['water', 'food'])

    def test_opening_scope_and_gatherer_story_gates_are_preserved(self):
        self.begin()
        old = self.turn(2).model_copy(update={'key': c.ConversationKey(game_scope='other-run', npc_id=2, epoch=0)})
        self.assertIsInstance(self.adapter.execute(old, self.decision()), c.Denied)
        self.player = self.db.get(Player, 1)
        self.player.opening_state = 'pending'
        self.db.flush()
        self.assertIsInstance(self.adapter.execute(self.turn(2), self.decision()), c.Denied)
        self.player.opening_state = 'complete'
        self.db.flush()
        gatherer.apply_command(self.db, self.player, 'begin_intro', 'intro', 0, {})
        self.assertIsInstance(self.adapter.execute(self.turn(2), self.decision()), c.Denied)
        self.assertEqual(self.player.inventory, ['water', 'food'])

    def test_transfer_preserves_authoritative_bow_crafting_without_granting_reward(self):
        npc = self.db.get(NPC, 1)
        npc.inventory = list(npc.inventory) + ['wood']
        self.player = self.db.get(Player, 1)
        self.player.inventory = list(self.player.inventory) + ['string']
        self.db.add(BowQuest(player_id=1, phase='gather', string_collected=True))
        self.db.commit()
        self.begin()
        self.adapter.execute(self.turn(), self.decision('receive_item', 'string', 1))
        self.assertEqual(self.db.get(BowQuest, 1).phase, 'crafting')
        self.assertIsNotNone(self.db.get(BowQuest, 1).ready_at)
        self.assertNotIn('wood', self.db.get(NPC, 1).inventory)
        self.assertNotIn('string', self.db.get(NPC, 1).inventory)
        self.assertNotIn('bow', self.db.get(Player, 1).inventory)
        self.assertEqual(self.db.get(NPC, 1).trust, .65)
        self.db.rollback()
        with Session(self.engine) as read:
            self.assertEqual(read.get(BowQuest, 1).phase, 'gather')
            self.assertIn('wood', read.get(NPC, 1).inventory)
            self.assertIn('string', read.get(Player, 1).inventory)

    def test_accepting_inspection_records_verified_acceptance_not_completion(self):
        self.begin()
        result = self.adapter.execute(self.turn(), self.decision('begin_ship_inspection', npc_id=1), expected_encounter_revision=0)
        self.assertEqual(result.result.kind, 'activity')
        self.assertEqual(result.result.stage, 'accepted')
        self.assertEqual(result.result.activity_id, result.command_key)
        encounter = self.db.get(CraftsmanEncounter, 1)
        self.assertTrue(encounter.state['outing_active'])
        self.assertFalse(encounter.state['inspection_complete'])
        from app.models.ship_repair_quest import ShipRepairQuest
        self.assertIsNone(self.db.get(ShipRepairQuest, 1))
        memory = self.db.scalar(select(Memory).where(Memory.authority == 'authoritative'))
        self.assertEqual(memory.epistemic_status, 'fact')
        self.assertIn('agreed to inspect', memory.event)
        self.db.rollback()
        with Session(self.engine) as read:
            self.assertIsNone(read.get(CraftsmanEncounter, 1))
            self.assertEqual(list(read.scalars(select(Memory))), [])

    def test_all_effects_and_existing_deterministic_social_consequence_rollback_together(self):
        # Combat completion is trusted game evidence, deliberately NOT registered
        # as a conversation command. Existing consequences must share the writer.
        player = self.db.get(Player, 1)
        gatherer.apply_command(self.db, player, 'begin_intro', 'intro', 0, {})
        row = self.db.get(GathererEncounter, 1)
        attempt = {'attempt_id': row.state['attempt_id']}
        gatherer.apply_command(self.db, player, 'accept', 'accept', 1, attempt)
        self.db.commit()
        before_memory_revision = self.db.get(NPC, 2).memory_revision
        self.db.rollback()
        self.begin()
        player = self.db.get(Player, 1)
        gatherer.apply_command(self.db, player, 'victory', 'verified-combat', 2, attempt)
        gatherer.apply_command(self.db, player, 'finish_presentation', 'presentation', 3, {})
        self.adapter.execute(self.turn(2), self.decision())
        self.adapter.execute(self.turn(), self.decision('begin_ship_inspection', npc_id=1), expected_encounter_revision=0)
        self.assertAlmostEqual(self.db.get(NPC, 2).trust, .85)
        self.assertEqual(self.db.scalar(select(Quest)).progress, 50)
        self.assertIn('wood', player.inventory)
        self.assertGreaterEqual(len(list(self.db.scalars(select(Memory).where(Memory.authority == 'authoritative')))), 2)
        self.db.rollback()
        with Session(self.engine) as read:
            self.assertEqual(read.get(Player, 1).inventory, ['water', 'food'])
            self.assertIn('wood', read.get(NPC, 2).inventory)
            self.assertEqual(read.scalar(select(Quest)).progress, 0)
            self.assertEqual(read.get(NPC, 2).trust, .5)
            self.assertEqual(read.get(NPC, 2).memory_revision, before_memory_revision)
            self.assertEqual(read.get(GathererEncounter, 1).state['status'], 'intro_pending')
            self.assertEqual(list(read.scalars(select(Memory))), [])
            self.assertIsNone(read.get(CraftsmanEncounter, 1))

    def test_encounter_replay_uses_stable_turn_and_terms_across_new_adapter_instances(self):
        self.begin()
        turn = self.turn()
        decision = self.decision('report_wreck', npc_id=1)
        first = self.adapter.execute(turn, decision, expected_encounter_revision=0)
        self.db.commit()
        with Session(self.engine) as reopened, reopened.begin():
            again = GameOperationAdapter(reopened).execute(turn, decision, expected_encounter_revision=0)
            self.assertEqual(first.command_key, again.command_key)
            self.assertEqual(first.result, c.CommandResult(kind='command', changed=True))
            self.assertEqual(again.result, c.CommandResult(kind='command', changed=False))
            row = reopened.get(CraftsmanEncounter, 1)
            self.assertEqual(row.revision, 1)
            self.assertEqual(list(row.commands), [first.command_key])
            self.assertEqual(len(list(reopened.scalars(select(Memory)))), 1)

    def test_encounter_command_id_is_stable_scoped_and_bound_to_operation_terms(self):
        turn, decision = self.turn(), self.decision('report_wreck', npc_id=1)
        key = encounter_command_id(turn, decision.operation)
        self.assertEqual(key, encounter_command_id(c.TurnRef.model_validate(turn.model_dump()), decision.operation))
        # Candidate IDs and wording are proposal artifacts, not operation terms.
        self.assertEqual(key, encounter_command_id(turn, decision.operation.model_copy(update={'candidate_id': 'other-candidate'})))
        for changed in (
            turn.model_copy(update={'turn_id': 'other-turn'}),
            turn.model_copy(update={'request_id': 'other-request'}),
            turn.model_copy(update={'sequence': 3}),
            turn.model_copy(update={'key': turn.key.model_copy(update={'epoch': 1})}),
            turn.model_copy(update={'key': turn.key.model_copy(update={'game_scope': 'other-scope'})}),
            turn.model_copy(update={'key': turn.key.model_copy(update={'npc_id': 2})}),
        ):
            with self.subTest(turn=changed):
                self.assertNotEqual(key, encounter_command_id(changed, decision.operation))
        self.assertNotEqual(key, encounter_command_id(turn, self.decision('wait', npc_id=1).operation))
        give = self.decision()
        self.assertNotEqual(encounter_command_id(self.turn(2), give.operation),
                            encounter_command_id(self.turn(2), self.decision(item='axe').operation))

    def test_craftsman_revision_and_role_rejections_do_not_create_outings(self):
        self.begin()
        self.assertIsInstance(self.adapter.execute(self.turn(), self.decision('begin_ship_inspection', npc_id=1), expected_encounter_revision=10), c.Denied)
        self.assertIsInstance(self.adapter.execute(self.turn(2), self.decision('begin_ship_inspection', npc_id=2), expected_encounter_revision=0), c.Denied)
        self.assertIsNone(self.db.get(CraftsmanEncounter, 1))
        self.assertEqual(list(self.db.scalars(select(Memory))), [])

    def test_inspection_noop_cannot_be_reported_as_a_new_accepted_activity(self):
        self.begin()
        decision = self.decision('begin_ship_inspection', npc_id=1)
        self.adapter.execute(self.turn(), decision, expected_encounter_revision=0)
        other_turn = self.turn().model_copy(update={'turn_id': 'turn:3', 'request_id': 'request:3', 'sequence': 3})
        self.assertIsInstance(self.adapter.execute(other_turn, decision, expected_encounter_revision=1), c.Denied)
        row = self.db.get(CraftsmanEncounter, 1)
        row.state = row.state | {'inspection_complete': True, 'outing_active': False}
        self.db.flush()
        self.assertIsInstance(self.adapter.execute(other_turn, decision, expected_encounter_revision=1), c.Denied)
        self.assertEqual(row.revision, 1)

    def test_existing_outing_controls_use_the_audited_owner(self):
        self.begin()
        for sequence, command, mode, active in (
            (2, 'begin_ship_inspection', 'departure_pending', True),
            (3, 'wait', 'waiting_for_player', True),
            (4, 'resume', 'departure_pending', True),
            (5, 'postpone', 'workshop_routine', False),
            (6, 'begin_ship_inspection', 'departure_pending', True),
            (7, 'return', 'returning_to_workshop', False),
        ):
            with self.subTest(command=command):
                turn = self.turn().model_copy(update={'turn_id': f'turn:{sequence}', 'request_id': f'request:{sequence}', 'sequence': sequence})
                self.adapter.execute(turn, self.decision(command, npc_id=1), expected_encounter_revision=sequence - 2)
                row = self.db.get(CraftsmanEncounter, 1)
                self.assertEqual(row.state['mode'], mode)
                self.assertEqual(row.state['outing_active'], active)

    def reader(self):
        self.assertIsNotNone(GameReadAdapter, 'detached authoritative game views are absent')
        return GameReadAdapter(self.db)

    def test_detached_public_views_exclude_private_state_and_create_no_records(self):
        reader = self.reader()
        npc = self.db.get(NPC, 1)
        npc.pending_item = 'secret-negotiation'
        npc.current_state = 'private-state'
        self.db.flush()
        caps = reader.read_capabilities(self.scope, 1, 'public')
        facts = reader.read_facts(self.scope, 1, 0, 'public')
        self.assertEqual(len(caps), 9)
        self.assertEqual({cap.command_id for cap in caps}, set(AUDITED_COMMANDS))
        self.assertEqual({source.visibility for fact in facts for source in fact.sources}, {'public'})
        rendered = json.dumps([value.model_dump(mode='json') for value in (*caps, *facts)])
        for private in ('secret-negotiation', 'private-state', 'trust', 'fear', 'commands'):
            self.assertNotIn(private, rendered)
        self.assertIsNone(self.db.get(CraftsmanEncounter, 1))
        self.assertIsNone(self.db.get(GathererEncounter, 1))
        self.assertIsNone(self.db.get(BowQuest, 1))
        with self.assertRaises(Exception):
            caps[0].available = False
        old = json.dumps([fact.model_dump(mode='json') for fact in facts])
        npc.inventory = ['bow']
        self.db.flush()
        self.assertEqual(old, json.dumps([fact.model_dump(mode='json') for fact in facts]))
        self.assertEqual(reader.read_capabilities('another-game', 1, 'public'), ())
        self.assertEqual(reader.read_facts('another-game', 1, 0, 'public'), ())

    def test_craftsman_gatherer_inventory_capabilities_conform_to_execution(self):
        reader = self.reader()
        for npc_id in (1, 2):
            caps = reader.read_capabilities(self.scope, npc_id, 'public')
            self.assertEqual(len(caps), 9)
            for cap in caps:
                with self.subTest(npc_id=npc_id, command=cap.command_id):
                    item = cap.parameter_schema.allowed_items[0] if isinstance(cap.parameter_schema, c.ItemParameterSchema) else 'wood'
                    decision = self.decision(cap.command_id, item, npc_id).model_copy(update={
                        'checked_preconditions': cap.relevant_preconditions})
                    with self.db.begin_nested() as save:
                        result = self.adapter.execute(self.turn(npc_id), decision)
                        self.assertEqual(not isinstance(result, c.Denied), cap.available)
                        save.rollback()
        self.assertNotIn('complete_inspection', {cap.command_id for cap in caps})

    def test_unavailable_item_is_safe_denial_without_partial_owner_mutation(self):
        self.begin()
        npc = self.db.get(NPC, 2)
        before = (npc.current_state, npc.pending_item, list(npc.inventory))
        result = self.adapter.execute(self.turn(2), self.decision(item='bow'))
        self.assertIsInstance(result, c.Denied)
        self.assertEqual(result.reason_code, 'NOT_AVAILABLE')
        self.assertEqual(before, (npc.current_state, npc.pending_item, npc.inventory))
        self.assertEqual(self.db.get(Player, 1).inventory, ['water', 'food'])

    def test_private_owner_exception_is_sanitized_and_effect_savepoint_rolls_back(self):
        self.begin()
        def fail(db, player, npc, *args):
            player.inventory = ['bow']
            db.flush()
            raise HTTPException(409, {'secret': 'private evidence and trust=0.2'})
        with patch('app.services.conversation.adapters.game.craftsman.apply_command', fail):
            result = self.adapter.execute(self.turn(), self.decision('report_wreck', npc_id=1))
        self.assertIsInstance(result, c.Denied)
        self.assertNotIn('private', result.model_dump_json())
        self.assertNotIn('trust', result.model_dump_json())
        self.assertNotIn('secret', result.model_dump_json())
        self.assertEqual(self.db.get(Player, 1).inventory, ['water', 'food'])
        self.assertIsNone(self.db.get(CraftsmanEncounter, 1))
        self.assertTrue(self.db.in_transaction())

    def test_public_quest_activity_facts_distinguish_acceptance_from_staged_completion(self):
        reader = self.reader()
        self.begin()
        self.adapter.execute(self.turn(), self.decision('begin_ship_inspection', npc_id=1))
        facts = reader.read_facts(self.scope, 1, 0, 'public')
        activity = next(json.loads(f.content) for f in facts if f.sources[0].kind == 'activity')
        self.assertTrue(activity['outing_active'])
        self.assertFalse(activity['inspection_complete'])
        ship = next(json.loads(f.content) for f in facts if f.sources[0].source_id == 'quest:ship_repair')
        self.assertEqual(ship['phase'], 'not_started')
        npc = self.db.get(NPC, 1)
        row = self.db.get(CraftsmanEncounter, 1)
        from app.services import craftsman
        row.state = row.state | {'navigation_space': 'exterior', 'position': dict(zip(('x', 'y'), craftsman.MARKS['InspectionCraftsmanMark']))}
        craftsman.apply_command(self.db, self.db.get(Player, 1), npc, 'complete_inspection',
                                'trusted-staging', row.revision,
                                {'staged': True, 'player_position': dict(zip(('x', 'y'), craftsman.MARKS['InspectionPlayerMark']))})
        facts = reader.read_facts(self.scope, 1, 0, 'public')
        activity = next(json.loads(f.content) for f in facts if f.sources[0].kind == 'activity')
        self.assertTrue(activity['inspection_complete'])
        ship = next(json.loads(f.content) for f in facts if f.sources[0].source_id == 'quest:ship_repair')
        self.assertEqual(ship['phase'], 'gathering_materials')

    def consent_fixture(self):
        self.assertIsNotNone(ConsentSnapshot, 'current authoritative consent loader is absent')
        descriptor = next(cap for cap in self.reader().read_capabilities(self.scope, 2, 'public') if cap.command_id == 'give_item')
        turn = self.turn(2)
        question_turn = turn.model_copy(update={'turn_id': 'turn:1', 'request_id': 'request:1', 'sequence': 1})
        operation = self.decision().operation.model_copy(update={'pending_question_id': 'question:1', 'source_spans': (c.TextSpan(text_id='message:2', start=0, end=3),)})
        pending = c.PendingInteraction.model_validate(dict(
            interaction_id='interaction:1', key=turn.key.model_dump(), kind='item_negotiation',
            originating_turn=question_turn.model_dump(), target=operation.target.model_dump(), item='wood', quantity=1,
            question_text='Do you want one wood?', question_id='question:1', question_turn_id='turn:1',
            required_response_kind='affirmation', precondition_fingerprint='terms:wood:1', revision=1,
            status='active', status_reason=None))
        binding = c.ConsentBinding(interaction_id=pending.interaction_id, question_id=pending.question_id,
            question_turn_id=question_turn.turn_id, question_turn=question_turn, answering_turn=turn,
            answer_span=operation.source_spans[0], operation=operation,
            checked_preconditions=descriptor.relevant_preconditions, precondition_fingerprint=pending.precondition_fingerprint)
        decision = c.ReadyToRecheck(kind='ready_to_recheck', operation=operation, consent=binding,
                                    checked_preconditions=descriptor.relevant_preconditions)
        snapshot = ConsentSnapshot(interaction=pending, operation=operation, texts={'question:1': pending.question_text, 'message:2': 'yes'}, expected_answer='yes')
        return turn, decision, snapshot

    def test_consent_is_reloaded_inside_transaction_and_binds_exact_current_terms(self):
        turn, decision, snapshot = self.consent_fixture()
        calls = []
        def load(current_turn, interaction_id):
            calls.append((current_turn, interaction_id, self.db.in_transaction()))
            return snapshot
        result = GameOperationAdapter(self.db, consent_loader=load).execute(turn, decision)
        self.assertNotIsInstance(result, c.Denied)
        self.assertEqual(calls, [(turn, 'interaction:1', True)])
        self.assertEqual(self.db.get(Player, 1).inventory.count('wood'), 1)

    def test_missing_cancelled_changed_and_wrong_question_consent_deny_without_substitution(self):
        turn, decision, snapshot = self.consent_fixture()
        for current in (None,
            ConsentSnapshot(operation=snapshot.operation, interaction=snapshot.interaction.model_copy(update={'status': 'cancelled', 'status_reason': 'player_cancelled'}), texts=snapshot.texts, expected_answer='yes'),
            ConsentSnapshot(operation=snapshot.operation, interaction=snapshot.interaction.model_copy(update={'item': 'axe'}), texts=snapshot.texts, expected_answer='yes'),
            ConsentSnapshot(operation=snapshot.operation, interaction=snapshot.interaction.model_copy(update={'precondition_fingerprint': 'changed'}), texts=snapshot.texts, expected_answer='yes'),
            ConsentSnapshot(operation=snapshot.operation, interaction=snapshot.interaction, texts={'question:1': 'Would you like my axe?', 'message:2': 'yes'}, expected_answer='yes'),
            ConsentSnapshot(operation=snapshot.operation, interaction=snapshot.interaction, texts=snapshot.texts, expected_answer='no')):
            with self.subTest(current=current):
                result = GameOperationAdapter(self.db, consent_loader=lambda *_: current).execute(turn, decision)
                self.assertIsInstance(result, c.Denied)
                self.assertNotIn('wood', self.db.get(Player, 1).inventory)
                self.assertIn('axe', self.db.get(NPC, 2).inventory)
        self.assertIsInstance(self.adapter.execute(turn, decision), c.Denied)

    def test_changed_current_role_ownership_and_outing_terms_fail_closed(self):
        reader = self.reader()
        cap = next(c for c in reader.read_capabilities(self.scope, 2, 'public') if c.command_id == 'give_item')
        decision = self.decision().model_copy(update={'checked_preconditions': cap.relevant_preconditions})
        self.db.get(NPC, 2).inventory = ['axe']
        self.db.flush()
        result = self.adapter.execute(self.turn(2), decision)
        self.assertIsInstance(result, c.Denied)
        self.assertNotIn('axe', self.db.get(Player, 1).inventory)
        self.db.get(NPC, 2).inventory = ['wood']
        self.db.get(NPC, 2).role = 'private-secret-role'
        self.db.flush()
        result = self.adapter.execute(self.turn(2), decision)
        self.assertIsInstance(result, c.Denied)
        self.assertNotIn('private-secret-role', result.model_dump_json())

    def test_changed_target_reference_is_denied_even_for_same_entity_id(self):
        self.begin()
        decision = self.decision()
        forged = decision.model_copy(update={'operation': decision.operation.model_copy(update={
            'target': decision.operation.target.model_copy(update={'reference_id': 'unoffered-alias'})})})
        result = self.adapter.execute(self.turn(2), forged)
        self.assertIsInstance(result, c.Denied)
        self.assertNotIn('wood', self.db.get(Player, 1).inventory)

    def test_craftsman_owner_gate_is_shared_and_views_conform_across_activity_states(self):
        from app.services import craftsman
        self.assertTrue(callable(getattr(craftsman, 'conversation_command_available', None)),
                        'Craftsman owner has no shared pure eligibility gate')
        self.begin()
        player = self.db.get(Player, 1)
        row = craftsman.record(self.db, player)
        for active, complete in ((False, False), (True, False), (False, True)):
            row.state = craftsman.defaults() | {'outing_active': active, 'inspection_complete': complete}
            self.db.flush()
            for cap in self.reader().read_capabilities(self.scope, 1, 'public'):
                if cap.command_id.endswith('_item'):
                    continue
                with self.subTest(command=cap.command_id, active=active, complete=complete):
                    self.assertEqual(cap.available, craftsman.conversation_command_available(cap.command_id, row.state))
                    with self.db.begin_nested() as save:
                        result = self.adapter.execute(self.turn(), self.decision(cap.command_id, npc_id=1))
                        self.assertEqual(not isinstance(result, c.Denied), cap.available)
                        save.rollback()

    def test_gatherer_gate_and_empty_inventory_views_conform_without_disclosing_private_reasons(self):
        self.begin()
        player = self.db.get(Player, 1)
        gatherer.apply_command(self.db, player, 'begin_intro', 'intro-current', 0, {})
        self.db.flush()
        for cap in self.reader().read_capabilities(self.scope, 2, 'public'):
            self.assertFalse(cap.available)
            self.assertEqual(cap.safe_unavailable_reason, 'That action is not available right now.')
        self.db.get(GathererEncounter, 1).state = gatherer.defaults() | {'status': 'resolved_helped'}
        self.db.get(NPC, 2).inventory = []
        self.db.flush()
        cap = next(cap for cap in self.reader().read_capabilities(self.scope, 2, 'public') if cap.command_id == 'give_item')
        self.assertFalse(cap.available)
        self.assertIsInstance(self.adapter.execute(self.turn(2), self.decision()), c.Denied)
        self.db.get(NPC, 2).inventory = ['wood']
        self.db.flush()
        cap = next(cap for cap in self.reader().read_capabilities(self.scope, 2, 'public') if cap.command_id == 'give_item')
        self.assertTrue(cap.available)
        self.assertEqual(cap.parameter_schema.allowed_items, ('wood',))

    def test_consent_requires_current_authoritative_command_terms_not_just_same_item(self):
        turn, decision, snapshot = self.consent_fixture()
        self.assertTrue(hasattr(snapshot, 'operation'), 'current consent snapshot lacks authoritative command terms')
        player = self.db.get(Player, 1)
        player.inventory = [*player.inventory, 'wood']
        self.db.flush()
        for update in ({'command_id': 'receive_item'}, {'modality': 'negated'}):
            with self.subTest(update=update):
                changed = snapshot.operation.model_copy(update=update)
                result = GameOperationAdapter(self.db, consent_loader=lambda *_: replace(snapshot, operation=changed)).execute(turn, decision)
                self.assertIsInstance(result, c.Denied)
        self.assertEqual(self.db.get(Player, 1).inventory.count('wood'), 1)
        self.assertEqual(self.db.get(NPC, 2).inventory.count('wood'), 1)

    def test_question_text_cannot_be_reused_as_the_admitted_answer_span(self):
        turn, decision, snapshot = self.consent_fixture()
        span = c.TextSpan(text_id='question:1', start=0, end=3)
        operation = decision.operation.model_copy(update={'source_spans': (span,)})
        binding = decision.consent.model_copy(update={'answer_span': span, 'operation': operation})
        decision = decision.model_copy(update={'operation': operation, 'consent': binding})
        snapshot = replace(snapshot, operation=operation,
            interaction=snapshot.interaction.model_copy(update={'question_text': 'yes'}),
            texts={'question:1': 'yes', 'message:2': 'no'})
        result = GameOperationAdapter(self.db, consent_loader=lambda *_: snapshot).execute(turn, decision)
        self.assertIsInstance(result, c.Denied)
        self.assertNotIn('wood', self.db.get(Player, 1).inventory)

    def test_empty_checked_preconditions_cannot_bypass_final_current_rule_comparison(self):
        self.begin()
        decision = self.decision().model_copy(update={'checked_preconditions': ()})
        result = self.adapter.execute(self.turn(2), decision)
        self.assertIsInstance(result, c.Denied)
        self.assertEqual(result.reason_code, 'TERMS_CHANGED')
        self.assertNotIn('wood', self.db.get(Player, 1).inventory)


if __name__ == '__main__':
    unittest.main()


class GameResourceRevisionTests(unittest.TestCase):
    """The same writer/snapshot/race contract runs on file SQLite or npc_test_* PostgreSQL."""
    def setUp(self):
        import importlib
        import os
        from sqlalchemy.engine import make_url
        from sqlalchemy import text
        try:
            self.revisions = importlib.import_module('app.services.state.resources')
        except ModuleNotFoundError:
            self.revisions = None
        self.assertIsNotNone(self.revisions, 'game-owned resource revision boundary is absent')
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        configured = os.environ.get('GAME_REVISION_TEST_DATABASE_URL')
        if configured and not (make_url(configured).database or '').startswith('npc_test_'):
            raise RuntimeError('Only disposable npc_test_* databases may be used')
        url = configured or 'sqlite:///' + str(Path(self.temp.name) / 'revisions.sqlite')
        self.engine = create_engine(url, connect_args={'timeout': 15} if url.startswith('sqlite:') else {})
        self.addCleanup(self.engine.dispose)
        if configured:
            with self.engine.begin() as conn:
                conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            Base.metadata.drop_all(self.engine)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, autoflush=False)
        self.addCleanup(self.db.close)
        seed_world(self.db)
        self.player = self.db.get(Player, 1)
        self.player.opening_state = 'complete'
        self.scope = self.player.game_scope
        self.db.commit()

    def snap(self, db=None, scope=None):
        return self.revisions.resource_snapshot(db or self.db, scope or self.scope)

    def labels(self):
        return self.snap()['state_revisions']

    def changed(self, before, after):
        return {key for key in after if after[key] != before.get(key, 0)}

    def turn(self, npc_id):
        return c.TurnRef(turn_id=f'turn:{npc_id}', request_id=f'request:{npc_id}', sequence=1,
                         key=c.ConversationKey(game_scope=self.scope, npc_id=npc_id, epoch=0))

    def decision(self, db, npc_id, command='receive_item', item='food'):
        descriptor = next(cap for cap in GameReadAdapter(db).read_capabilities(self.scope, npc_id, 'public')
                          if cap.command_id == command)
        return c.ReadyToRecheck(kind='ready_to_recheck', consent=None, checked_preconditions=descriptor.relevant_preconditions,
            operation=c.OperationCandidate(candidate_id='candidate:1', command_id=command,
                arguments=c.ItemArguments(item=item) if command.endswith('_item') else c.NoArguments(),
                target=c.TargetReference(reference_id=f'npc:{npc_id}', entity_kind='npc', entity_id=str(npc_id)),
                source_spans=(c.TextSpan(text_id='message:1', start=0, end=1),), modality='direct', pending_question_id=None))

    def test_detached_complete_snapshot_has_zero_baselines_and_no_read_writes(self):
        snapshot = self.snap()
        expected = {'world', 'inventory:player', 'inventory:npc:1', 'inventory:npc:2',
                    'npc:1', 'npc:2', 'quest:legacy', 'quest:bow', 'quest:ship_repair',
                    'activity:ship_inspection', 'encounter:gatherer'}
        self.assertEqual(set(snapshot['state_revisions']), expected)
        self.assertTrue(all(value == 0 for value in snapshot['state_revisions'].values()))
        self.assertIsNone(self.db.get(CraftsmanEncounter, 1))
        snapshot['resources']['inventory:player'].append('bow')
        self.assertNotIn('bow', self.player.inventory)
        self.assertEqual(self.player.resource_revisions, {})

    def test_chat_transfer_revisions_rollback_with_exact_resources(self):
        before = self.labels()
        result = GameOperationAdapter(self.db).execute(self.turn(2), self.decision(self.db, 2, 'give_item', 'wood'))
        self.assertNotIsInstance(result, c.Denied)
        after = self.labels()
        self.assertEqual(self.changed(before, after), {'inventory:player', 'inventory:npc:2', 'npc:2', 'quest:legacy', 'quest:bow'})
        self.db.rollback()
        self.assertEqual(self.labels(), before)
        self.assertNotIn('wood', self.db.get(Player, 1).inventory)

    def test_nonchat_pickup_invalidates_relevant_fact_revision_without_changing_activity(self):
        from app.api.routes.quests import pickup, PickupRequest
        from app.services.quests.bow import STRING_POSITION
        self.db.add(BowQuest(player_id=1, phase='gather', string_collected=False))
        self.db.commit()
        before = self.labels()
        facts = GameReadAdapter(self.db).read_facts(self.scope, 1, 0, 'public')
        self.db.rollback()
        pickup(PickupRequest(**STRING_POSITION), self.db)
        after = self.labels()
        self.assertEqual(self.changed(before, after), {'inventory:player', 'quest:bow'})
        current = GameReadAdapter(self.db).read_facts(self.scope, 1, 0, 'public')
        old = {f.sources[0].source_id: f.sources[0].revision for f in facts}
        new = {f.sources[0].source_id: f.sources[0].revision for f in current}
        self.assertNotEqual(old['inventory:player'], new['inventory:player'])
        self.assertNotEqual(old['quest:bow'], new['quest:bow'])
        self.assertTrue(all(isinstance(value, int) for value in new.values()))
        self.assertFalse(self.revisions.revisions_match(self.db, self.scope, {'inventory:player': old['inventory:player']}))

    def test_opening_salvage_and_position_are_labelled_and_retry_does_not_bump(self):
        from app.services.opening import collect_salvage
        from app.services.island import BEACH
        from app.api.routes.world import save_position, PlayerPosition
        before = self.labels()
        self.db.rollback()
        collect_salvage(self.db, self.scope, *BEACH['salvage_at'])
        after = self.labels()
        self.assertEqual(self.changed(before, after), {'world', 'inventory:player'})
        self.db.rollback()
        collect_salvage(self.db, self.scope, *BEACH['salvage_at'])
        self.assertEqual(self.labels(), after)
        self.db.rollback()
        save_position(PlayerPosition(x=80, y=0, game_scope=self.scope), self.db)
        self.assertEqual(self.changed(after, self.labels()), {'world'})

    def test_quest_start_replenishment_and_timed_reward_version_every_projection(self):
        from app.api.routes.quests import start, advance
        self.db.get(NPC, 2).inventory = ['axe']
        self.db.commit()
        before = self.labels()
        self.db.rollback()
        start(self.db)
        started = self.labels()
        self.assertEqual(self.changed(before, started), {'quest:bow', 'inventory:npc:2', 'npc:2'})
        quest = self.db.get(BowQuest, 1)
        quest.phase, quest.ready_at = 'crafting', 1.0
        self.db.commit()
        self.db.rollback()
        before = self.labels()
        self.db.rollback()
        with patch('app.services.memory.service.MemoryService.store_conversation') as store:
            store.return_value.payload.return_value = {}
            advance(self.db)
        self.assertEqual(self.changed(before, self.labels()), {'quest:bow', 'inventory:player'})
        self.assertEqual(self.db.get(Player, 1).inventory.count('bow'), 1)

    def test_activity_cancellation_and_idempotent_replay_preserve_monotonic_labels(self):
        from app.services import craftsman
        before = self.labels()
        npc = self.db.get(NPC, 1)
        accepted = craftsman.apply_command(self.db, self.player, npc, 'begin_ship_inspection', 'accept', 0, {})
        middle = self.labels()
        self.assertEqual(self.changed(before, middle), {'activity:ship_inspection'})
        cancelled = craftsman.apply_command(self.db, self.player, npc, 'postpone', 'cancel', 1, {})
        after = self.labels()
        self.assertGreater(after['activity:ship_inspection'], middle['activity:ship_inspection'])
        self.assertEqual(cancelled['state_revisions']['activity:ship_inspection'], after['activity:ship_inspection'])
        replay = craftsman.apply_command(self.db, self.player, npc, 'postpone', 'cancel', 1, {})
        self.assertEqual(self.labels(), after)
        self.assertEqual(replay, cancelled)
        self.assertEqual(accepted['state_revisions']['activity:ship_inspection'], middle['activity:ship_inspection'])

    def test_snapshot_triggered_staging_migration_and_topic_changes_are_versioned(self):
        from app.services import craftsman
        from app.services.craftsman_intent import dialogue
        from types import SimpleNamespace
        row = GathererEncounter(player_id=1, game_scope=self.scope, revision=7,
            state=gatherer.defaults() | {'status': 'intro_pending', 'checkpoint': {'staging_version': 1}}, commands={})
        self.db.add(row)
        self.db.commit()
        before = self.labels()
        gatherer.encounter_snapshot(self.db, self.player)
        after = self.labels()
        self.assertEqual(self.changed(before, after), {'world', 'encounter:gatherer'})
        self.assertEqual(row.revision, 7)
        craftsman.record(self.db, self.player)
        before = self.labels()
        dialogue(self.db, self.db.get(NPC, 1), 'the bow', self.player,
                 SimpleNamespace(recent_dialogue=[], conversation_focus=None))
        self.assertEqual(self.changed(before, self.labels()), {'activity:ship_inspection'})

    def test_nested_writer_preserves_unflushed_player_changes_with_autoflush_disabled(self):
        from app.services.state.locking import lock_player
        from app.services import craftsman
        player = lock_player(self.db)
        player.position = {'x': 24.0, 'y': 35.0}
        with self.revisions.game_writer(self.db):
            player.inventory = [*player.inventory, 'rope']
            craftsman.apply_command(self.db, player, self.db.get(NPC, 1), 'report_wreck', 'report', 0, {})
        self.assertEqual(player.position, {'x': 24.0, 'y': 35.0})
        self.assertIn('rope', player.inventory)
        self.db.commit()
        self.assertIn('rope', self.db.get(Player, 1).inventory)

    def test_reset_rotates_scope_and_clears_counters_atomically(self):
        from app.database.seed import reset_world
        with self.revisions.game_writer(self.db):
            self.player.inventory = [*self.player.inventory, 'rope']
        self.db.commit()
        self.assertGreater(self.labels()['inventory:player'], 0)
        self.db.rollback()
        reset_world(self.db)
        self.assertNotEqual(self.player.game_scope, self.scope)
        self.assertEqual(self.player.resource_revisions, {})
        self.assertFalse(self.revisions.revisions_match(self.db, self.scope, {'inventory:player': 0}))
        self.db.rollback()
        self.assertEqual(self.db.get(Player, 1).game_scope, self.scope)
        self.assertGreater(self.labels()['inventory:player'], 0)

    def race(self, work):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        barrier = Barrier(2)
        def run(index):
            with Session(self.engine, autoflush=False) as db:
                barrier.wait(timeout=10)
                return work(db, index)
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(run, range(2)))

    def test_different_npc_operations_serialize_one_shared_item(self):
        decisions = [self.decision(self.db, npc) for npc in (1, 2)]
        self.db.rollback()
        def work(db, index):
            db.begin()
            result = GameOperationAdapter(db).execute(self.turn(index + 1), decisions[index])
            db.commit()
            return result
        results = self.race(work)
        self.assertEqual(sum(not isinstance(result, c.Denied) for result in results), 1)
        snapshot = self.snap()
        self.assertNotIn('food', snapshot['resources']['inventory:player'])
        inventories = [snapshot['resources'][f'inventory:npc:{npc}'] for npc in (1, 2)]
        self.assertEqual(sum(items.count('food') for items in inventories), 1)
        self.assertEqual(snapshot['state_revisions']['inventory:player'], 1)

    def test_cancellation_race_denies_stale_outing_control(self):
        from app.services import craftsman
        craftsman.apply_command(self.db, self.player, self.db.get(NPC, 1), 'begin_ship_inspection', 'begin', 0, {})
        self.db.commit()
        decision = self.decision(self.db, 1, 'wait')
        self.db.rollback()
        with Session(self.engine, autoflush=False) as other:
            player = other.get(Player, 1)
            craftsman.apply_command(other, player, other.get(NPC, 1), 'postpone', 'cancel', 1, {})
            other.commit()
        self.db.begin()
        result = GameOperationAdapter(self.db).execute(self.turn(1), decision)
        self.assertIsInstance(result, c.Denied)
        self.assertFalse(self.snap()['resources']['activity:ship_inspection']['state']['outing_active'])

    def test_reset_waits_for_operation_then_invalidates_old_scope(self):
        from app.database.seed import reset_world
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        decision = self.decision(self.db, 2)
        self.db.rollback()
        self.db.begin()
        GameOperationAdapter(self.db).execute(self.turn(2), decision)
        attempted = Event()
        done = Event()
        def reset():
            with Session(self.engine, autoflush=False) as other:
                attempted.set()
                reset_world(other)
                other.commit()
                done.set()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(reset)
            self.assertTrue(attempted.wait(5))
            self.assertFalse(done.wait(.15), 'reset escaped the Player writer lock')
            self.db.commit()
            future.result(timeout=10)
        self.db.begin()
        denied = GameOperationAdapter(self.db).execute(self.turn(2), decision)
        self.assertIsInstance(denied, c.Denied)
        self.assertEqual(self.db.get(Player, 1).resource_revisions, {})

    def test_opening_completion_versions_world_once(self):
        from app.services.opening import complete_opening
        self.player.opening_state = 'pending'
        self.db.commit()
        before = self.labels()
        self.db.rollback()
        complete_opening(self.db, self.scope, 1)
        after = self.labels()
        self.assertEqual(self.changed(before, after), {'world'})
        self.db.rollback()
        complete_opening(self.db, self.scope, 1)
        self.assertEqual(self.labels(), after)

    def test_bow_dialogue_and_crafting_consumption_label_existing_owner_effects(self):
        from app.services.quests import bow
        self.db.add(BowQuest(player_id=1, phase='meet', string_collected=True))
        npc = self.db.get(NPC, 1)
        npc.inventory = [*npc.inventory, 'wood', 'string']
        self.db.commit()
        before = self.labels()
        bow.dialogue(self.db, npc, 'a bow', self.player)
        gathering = self.labels()
        self.assertEqual(self.changed(before, gathering), {'quest:bow'})
        output = bow.reply('ready')
        bow.maybe_start(self.db, self.player, npc, output)
        after = self.labels()
        self.assertEqual(self.changed(gathering, after), {'quest:bow', 'inventory:npc:1', 'npc:1'})
        self.assertNotIn('bow', self.player.inventory)
        self.db.rollback()
        self.assertEqual(self.labels(), before)

    def test_trusted_inspection_completion_labels_quest_activity_and_position(self):
        from app.services import craftsman
        npc = self.db.get(NPC, 1)
        craftsman.apply_command(self.db, self.player, npc, 'begin_ship_inspection', 'begin', 0, {})
        craftsman.checkpoint(self.db, self.player,
            dict(position=dict(zip(('x', 'y'), craftsman.MARKS['InspectionCraftsmanMark'])),
                 navigation_space='exterior', mode='following_player'), 1)
        before = self.labels()
        craftsman.apply_command(self.db, self.player, npc, 'complete_inspection', 'complete', 2,
            {'staged': True, 'player_position': dict(zip(('x', 'y'), craftsman.MARKS['InspectionPlayerMark']))})
        after = self.labels()
        self.assertEqual(self.changed(before, after), {'world', 'activity:ship_inspection', 'quest:ship_repair'})
        self.assertEqual(self.snap()['resources']['quest:ship_repair']['phase'], 'gathering_materials')

    def test_gatherer_position_and_existing_social_outcome_have_separate_labels(self):
        before = self.labels()
        gatherer.apply_command(self.db, self.player, 'begin_intro', 'begin', 0, {})
        intro = self.labels()
        self.assertEqual(self.changed(before, intro), {'world', 'encounter:gatherer'})
        gatherer.apply_command(self.db, self.player, 'decline', 'decline', 1, {})
        after = self.labels()
        self.assertEqual(self.changed(intro, after), {'npc:2', 'encounter:gatherer'})
        self.assertEqual(self.db.get(NPC, 2).trust, .15)
        self.assertEqual(self.player.inventory, ['water', 'food'])

    def test_same_payload_after_aba_has_newer_labels_and_unrelated_churn_rechecks(self):
        original = self.snap()
        decision = self.decision(self.db, 2, 'give_item', 'wood')
        with self.revisions.game_writer(self.db):
            self.player.inventory = [*self.player.inventory, 'rope']
        with self.revisions.game_writer(self.db):
            self.player.inventory = [item for item in self.player.inventory if item != 'rope']
        current = self.snap()
        self.assertEqual(original['resources']['inventory:player'], current['resources']['inventory:player'])
        self.assertGreater(current['state_revisions']['inventory:player'], original['state_revisions']['inventory:player'])
        result = GameOperationAdapter(self.db).execute(self.turn(2), decision)
        self.assertNotIsInstance(result, c.Denied)
        self.assertIn('wood', self.player.inventory)

    def test_snapshot_waits_for_writer_and_pairs_current_values_with_current_labels(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Event
        with self.revisions.game_writer(self.db):
            self.player.inventory = [*self.player.inventory, 'rope']
        attempted, done = Event(), Event()
        def read():
            with Session(self.engine, autoflush=False) as other:
                attempted.set()
                result = self.snap(other)
                done.set()
                return result
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(read)
            self.assertTrue(attempted.wait(5))
            self.assertFalse(done.wait(.15), 'snapshot escaped the Player writer lock')
            self.db.commit()
            result = future.result(timeout=10)
        self.assertIn('rope', result['resources']['inventory:player'])
        self.assertEqual(result['state_revisions']['inventory:player'], 1)

    def test_direct_owner_refreshes_clean_npc_loaded_before_another_writer(self):
        from app.services.state.service import StateService
        from app.services.validation.models import LLMResponse, StateUpdate
        npc = self.db.get(NPC, 2)
        quest = self.db.scalar(select(Quest))
        with Session(self.engine, autoflush=False) as other:
            with self.revisions.game_writer(other):
                other.get(NPC, 2).inventory = ['axe', 'fruits']
            other.commit()
        output = LLMResponse(intent='inform', emotion='calm', dialogue='Here.', action='give_item',
            item='wood', reasoning='Existing deterministic transfer.', state_update=StateUpdate())
        with self.assertRaises(ValueError):
            StateService(self.db).apply(npc, self.player, quest, output)
        self.db.rollback()
        self.assertNotIn('wood', self.db.get(Player, 1).inventory)
