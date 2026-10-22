"""Capability descriptors are projections of injected authoritative views."""
import importlib
import unittest
from dataclasses import dataclass
import json

from sqlalchemy import select

from app.services.conversation import contracts as c
from app.services.conversation.capabilities import CapabilityReader
from app.services.conversation.adapters.game import AUDITED_COMMANDS, GameReadAdapter
from app.models import BowQuest, CraftsmanEncounter, GathererEncounter, NPC, Player, Quest, ShipRepairQuest
from app.services import craftsman, gatherer

import test_conversation_game_adapters as game_fixtures


@dataclass(frozen=True)
class View:
    command_id: str
    parameter_schema: object
    allowed_target_references: tuple
    available: bool
    safe_unavailable_reason: str | None
    relevant_preconditions: tuple
    supported_speech_acts: tuple
    private_authorization_evidence: object = None


class CapabilityDescriptorTests(unittest.TestCase):
    def setUp(self):
        self.module = importlib.import_module('app.services.conversation.capabilities')

    def source(self, visibility='public'):
        return c.SourceRef(kind='quest', source_id='quest:1', revision=2,
                           game_scope='run:1', npc_id=7, attribution='server', visibility=visibility)

    def view(self, command, *, available=True, reason=None, visibility='public', targets=()):
        preconditions = (c.Precondition(precondition_id='pre:1', source=self.source(visibility), fingerprint='fp:1'),)
        schema = c.NoParameterSchema(kind='none')
        return View(command, schema, targets, available, reason, preconditions, ('request',),
                    {'secret_inventory_count': 99, 'authorization_trace': 'private'})

    def test_projects_only_injected_commands_and_sorts_deterministically(self):
        reader = self.module.CapabilityReader(lambda scope, npc: (
            self.view('wait'), self.view('report_wreck'),
        ))
        first = reader.read('run:1', 7)
        second = reader.read('run:1', 7)
        self.assertEqual(tuple(item.command_id for item in first), ('report_wreck', 'wait'))
        self.assertEqual(first, second)
        self.assertNotIn('give_item', tuple(item.command_id for item in first))

    def test_private_evidence_and_private_preconditions_are_not_publicized(self):
        descriptor, = self.module.build_descriptors((self.view('wait', visibility='server_private'),))
        self.assertEqual(descriptor.relevant_preconditions, ())
        dumped = descriptor.model_dump(mode='json')
        self.assertNotIn('private_authorization_evidence', dumped)
        self.assertNotIn('authorization_trace', str(dumped))
        self.assertNotIn('secret_inventory_count', str(dumped))

    def test_safe_unavailable_reason_is_used_without_private_detail(self):
        descriptor, = self.module.build_descriptors((self.view(
            'report_wreck', available=False, reason='A wreck report is not available right now.',
            visibility='server_private'),))
        self.assertFalse(descriptor.available)
        self.assertEqual(descriptor.safe_unavailable_reason, 'A wreck report is not available right now.')
        self.assertEqual(descriptor.relevant_preconditions, ())

    def test_duplicate_authoritative_command_views_fail_closed(self):
        with self.assertRaises(ValueError):
            self.module.build_descriptors((self.view('wait'), self.view('wait')))


class CapabilityExecutorConformanceTests(unittest.TestCase):
    """Real rule owners share the game-adapter disposable SQLite fixture.

    Literal scenario expectations catch a wrong eligibility branch on either
    side; comparing the descriptor only with itself would hide such drift.
    """

    COMMANDS = {'give_item', 'receive_item', 'report_wreck', 'begin_ship_inspection',
                'wait', 'resume', 'postpone', 'return', 'discuss_bow'}
    TRANSFERS = {'give_item', 'receive_item'}

    def setUp(self):
        self.game = game_fixtures.ConversationGameAdapterTests()
        self.addCleanup(self.game.doCleanups)
        self.game.setUp()
        self.db = self.game.db
        self.next_sequence = 10
        self.reader = CapabilityReader(lambda scope, npc_id:
            GameReadAdapter(self.db).read_capabilities(scope, npc_id, 'public'))

    def descriptors(self, npc_id):
        return {cap.command_id: cap for cap in self.reader.read(self.game.scope, npc_id)}

    def new_turn(self, npc_id):
        sequence = self.next_sequence
        self.next_sequence += 1
        return self.game.turn(npc_id).model_copy(update={
            'turn_id': f'conformance-turn:{sequence}', 'request_id': f'conformance-request:{sequence}',
            'sequence': sequence})

    def decision(self, descriptor, npc_id, item=None):
        if item is None and isinstance(descriptor.parameter_schema, c.ItemParameterSchema):
            item = descriptor.parameter_schema.allowed_items[0]
        return self.game.decision(descriptor.command_id, item or 'wood', npc_id).model_copy(
            update={'checked_preconditions': descriptor.relevant_preconditions})

    def assert_scenario(self, npc_id, available):
        caps = self.descriptors(npc_id)
        self.assertEqual(set(AUDITED_COMMANDS), self.COMMANDS)
        self.assertEqual(set(caps), self.COMMANDS)
        self.assertEqual({command for command, cap in caps.items() if cap.available}, available)
        for command, cap in caps.items():
            with self.subTest(npc_id=npc_id, command=command):
                self.assertEqual(cap.allowed_target_references, (c.TargetReference(
                    reference_id=f'npc:{npc_id}', entity_kind='npc', entity_id=str(npc_id)),))
                self.assertTrue(cap.relevant_preconditions)
                self.assertTrue(all(pre.source.visibility == 'public' and pre.fingerprint
                                    for pre in cap.relevant_preconditions))
                if command in self.TRANSFERS:
                    self.assertIsInstance(cap.parameter_schema, c.ItemParameterSchema)
                else:
                    self.assertIsInstance(cap.parameter_schema, c.NoParameterSchema)
                with self.db.begin_nested() as save:
                    before = (list(self.db.get(Player, 1).inventory),
                              list(self.db.get(NPC, npc_id).inventory))
                    decision = self.decision(cap, npc_id)
                    result = self.game.adapter.execute(self.new_turn(npc_id), decision)
                    self.assertEqual(not isinstance(result, c.Denied), command in available)
                    if command not in available:
                        self.assertEqual(before, (self.db.get(Player, 1).inventory,
                                                  self.db.get(NPC, npc_id).inventory))
                        self.assertTrue(cap.safe_unavailable_reason)
                    elif command in self.TRANSFERS:
                        item = decision.operation.arguments.item
                        delta = 1 if command == 'give_item' else -1
                        self.assertEqual(self.db.get(Player, 1).inventory.count(item),
                                         before[0].count(item) + delta)
                        self.assertEqual(self.db.get(NPC, npc_id).inventory.count(item),
                                         before[1].count(item) - delta)
                    elif command == 'begin_ship_inspection':
                        self.assertEqual(result.result.stage, 'accepted')
                        self.assertTrue(self.db.get(CraftsmanEncounter, 1).state['outing_active'])
                        self.assertFalse(self.db.get(CraftsmanEncounter, 1).state['inspection_complete'])
                    else:
                        state = self.db.get(CraftsmanEncounter, 1).state
                        if command == 'report_wreck':
                            self.assertTrue(state['wreck_reported'])
                        else:
                            self.assertEqual(state['mode'], {
                                'wait': 'waiting_for_player', 'resume': 'departure_pending',
                                'postpone': 'workshop_routine', 'return': 'returning_to_workshop',
                            }[command])
                    save.rollback()

    def test_every_registry_command_conforms_for_both_roles_and_activity_states(self):
        self.assert_scenario(1, self.TRANSFERS | {'report_wreck', 'begin_ship_inspection'})
        self.assert_scenario(2, self.TRANSFERS)
        row = craftsman.record(self.db, self.db.get(Player, 1))
        for active, complete, expected in (
            (True, False, self.TRANSFERS | {'report_wreck', 'wait', 'resume', 'postpone', 'return'}),
            (False, True, self.TRANSFERS | {'report_wreck'}),
        ):
            with self.subTest(active=active, complete=complete):
                row.state = craftsman.defaults() | {'outing_active': active, 'inspection_complete': complete}
                self.db.flush()
                self.assert_scenario(1, expected)

    def test_story_opening_and_empty_stock_unavailability_conforms_to_real_dispatch(self):
        self.db.get(Player, 1).opening_state = 'pending'
        self.db.flush()
        self.assert_scenario(1, set())
        self.assert_scenario(2, set())
        self.db.get(Player, 1).opening_state = 'complete'
        self.db.flush()
        gatherer.apply_command(self.db, self.db.get(Player, 1), 'begin_intro', 'intro-conformance', 0, {})
        self.assert_scenario(2, set())
        self.db.get(GathererEncounter, 1).state = gatherer.defaults() | {'status': 'resolved_helped'}
        self.db.get(NPC, 2).inventory = []
        self.db.get(Player, 1).inventory = []
        self.db.flush()
        self.assert_scenario(2, set())

    def test_stale_item_domain_cannot_substitute_another_owned_item_in_either_direction(self):
        for command, owner in (('give_item', NPC), ('receive_item', Player)):
            with self.subTest(command=command), self.db.begin_nested() as save:
                stock_owner = self.db.get(owner, 2 if owner is NPC else 1)
                stock_owner.inventory = ['wood', 'axe']
                self.db.flush()
                cap = self.descriptors(2)[command]
                self.assertEqual(set(cap.parameter_schema.allowed_items), {'wood', 'axe'})
                decision = self.decision(cap, 2, 'wood')
                stock_owner.inventory = ['axe']
                self.db.flush()
                fresh = self.descriptors(2)[command]
                self.assertTrue(fresh.available)
                self.assertEqual(fresh.parameter_schema.allowed_items, ('axe',))
                before = (list(self.db.get(Player, 1).inventory), list(self.db.get(NPC, 2).inventory))
                denied = self.game.adapter.execute(self.game.turn(2), decision)
                self.assertIsInstance(denied, c.Denied)
                self.assertEqual(before, (self.db.get(Player, 1).inventory, self.db.get(NPC, 2).inventory))
                save.rollback()

    def test_stale_available_views_deny_after_story_role_or_opening_gate_changes(self):
        for change in ('story', 'role', 'opening'):
            with self.subTest(change=change), self.db.begin_nested() as save:
                cap = self.descriptors(2)['give_item']
                self.assertTrue(cap.available)
                decision = self.decision(cap, 2, 'wood')
                if change == 'story':
                    gatherer.apply_command(self.db, self.db.get(Player, 1), 'begin_intro', 'stale-story', 0, {})
                elif change == 'role':
                    self.db.get(NPC, 2).role = 'unregistered'
                else:
                    self.db.get(Player, 1).opening_state = 'pending'
                self.db.flush()
                fresh = self.descriptors(2)['give_item']
                self.assertFalse(fresh.available)
                self.assertNotEqual(cap.relevant_preconditions, fresh.relevant_preconditions)
                self.assertIsInstance(self.game.adapter.execute(self.game.turn(2), decision), c.Denied)
                self.assertNotIn('wood', self.db.get(Player, 1).inventory)
                save.rollback()

    def test_each_stale_activity_descriptor_denies_when_its_availability_changes(self):
        for command in ('begin_ship_inspection', 'wait', 'resume', 'postpone', 'return'):
            with self.subTest(command=command), self.db.begin_nested() as save:
                row = craftsman.record(self.db, self.db.get(Player, 1))
                active = command != 'begin_ship_inspection'
                row.state = craftsman.defaults() | {'outing_active': active}
                self.db.flush()
                cap = self.descriptors(1)[command]
                self.assertTrue(cap.available)
                decision = self.decision(cap, 1)
                row.state = craftsman.defaults() | {'outing_active': not active}
                self.db.flush()
                fresh = self.descriptors(1)[command]
                self.assertFalse(fresh.available)
                self.assertNotEqual(cap.relevant_preconditions, fresh.relevant_preconditions)
                before = dict(row.state)
                self.assertIsInstance(self.game.adapter.execute(self.game.turn(), decision), c.Denied)
                self.assertEqual(row.state, before)
                save.rollback()

    def test_every_stale_craftsman_command_denies_after_role_change_without_effects(self):
        for command in sorted(self.COMMANDS):
            with self.subTest(command=command), self.db.begin_nested() as save:
                npc = self.db.get(NPC, 1)
                row = craftsman.record(self.db, self.db.get(Player, 1))
                row.state = craftsman.defaults() | {
                    'outing_active': command in {'wait', 'resume', 'postpone', 'return'}}
                if command == 'discuss_bow':
                    self.db.add(BowQuest(player_id=1, phase='meet', string_collected=False))
                self.db.flush()
                cap = self.descriptors(1)[command]
                self.assertTrue(cap.available)
                decision = self.decision(cap, 1)
                npc.role = 'unregistered'
                self.db.flush()
                fresh = self.descriptors(1)[command]
                self.assertFalse(fresh.available)
                self.assertNotEqual(cap.relevant_preconditions, fresh.relevant_preconditions)

                def snapshot():
                    return json.dumps({
                        'player_inventory': self.db.get(Player, 1).inventory,
                        'npc_inventory': npc.inventory, 'npc_trust': npc.trust,
                        'npc_state': npc.current_state, 'pending_item': npc.pending_item,
                        'activity': row.state, 'revision': row.revision, 'commands': row.commands,
                        'quest_progress': self.db.scalar(select(Quest)).progress,
                    }, sort_keys=True)

                before = snapshot()
                denied = self.game.adapter.execute(self.new_turn(1), decision)
                self.assertIsInstance(denied, c.Denied)
                self.assertEqual(snapshot(), before)
                save.rollback()

    def test_exact_target_and_one_quantity_hold_even_with_available_descriptor(self):
        self.db.get(NPC, 2).inventory = ['wood', 'wood']
        self.db.flush()
        cap = self.descriptors(2)['give_item']
        decision = self.decision(cap, 2, 'wood')
        for arguments, target in (
            ({'item': 'wood', 'quantity': 2}, decision.operation.target),
            ({'item': 'wood', 'quantity': 0}, decision.operation.target),
            (decision.operation.arguments, decision.operation.target.model_copy(update={'reference_id': 'unoffered'})),
        ):
            with self.subTest(arguments=arguments, target=target):
                forged = decision.model_copy(update={'operation': decision.operation.model_copy(
                    update={'arguments': arguments, 'target': target})})
                self.assertIsInstance(self.game.adapter.execute(self.game.turn(2), forged), c.Denied)
                self.assertEqual(self.db.get(NPC, 2).inventory.count('wood'), 2)
                self.assertNotIn('wood', self.db.get(Player, 1).inventory)
        result = self.game.adapter.execute(self.game.turn(2), decision)
        self.assertEqual(result.result.quantity, 1)
        self.assertEqual(self.db.get(Player, 1).inventory.count('wood'), 1)
        self.assertEqual(self.db.get(NPC, 2).inventory.count('wood'), 1)

    def test_quest_progress_and_bow_phase_follow_transfer_owner_without_reward_permissions(self):
        cap = self.descriptors(2)['give_item']
        result = self.game.adapter.execute(self.game.turn(2), self.decision(cap, 2, 'wood'))
        self.assertEqual(result.result.quantity, 1)
        self.assertEqual(self.db.scalar(select(Quest)).progress, 50)
        self.db.get(NPC, 1).inventory = ['wood']
        self.db.get(Player, 1).inventory = ['string']
        bow = self.db.get(BowQuest, 1)
        bow.phase, bow.string_collected = 'gather', True
        self.db.flush()
        cap = self.descriptors(1)['receive_item']
        self.assertTrue(cap.available)
        self.assertEqual(cap.parameter_schema.allowed_items, ('string',))
        result = self.game.adapter.execute(self.game.turn(), self.decision(cap, 1, 'string'))
        self.assertEqual(result.result.direction, 'to_npc')
        self.assertEqual(self.db.get(BowQuest, 1).phase, 'crafting')
        self.assertNotIn('bow', self.db.get(Player, 1).inventory)
        self.assertFalse(self.descriptors(1)['give_item'].available)
        self.assertFalse(self.descriptors(1)['receive_item'].available)
        self.assertNotIn('craft_bow', self.descriptors(1))

    def test_inspection_descriptor_grants_acceptance_and_completion_needs_trusted_staging(self):
        cap = self.descriptors(1)['begin_ship_inspection']
        effect = self.game.adapter.execute(self.game.turn(), self.decision(cap, 1))
        self.assertEqual(effect.result.stage, 'accepted')
        self.assertFalse(self.descriptors(1)['begin_ship_inspection'].available)
        self.assertTrue(self.descriptors(1)['wait'].available)
        self.assertIsNone(self.db.get(ShipRepairQuest, 1))
        row = self.db.get(CraftsmanEncounter, 1)
        self.assertFalse(row.state['inspection_complete'])
        self.assertNotIn('complete_inspection', self.descriptors(1))
        row.state = row.state | {'navigation_space': 'exterior', 'position': dict(
            zip(('x', 'y'), craftsman.MARKS['InspectionCraftsmanMark']))}
        self.db.flush()
        craftsman.apply_command(self.db, self.db.get(Player, 1), self.db.get(NPC, 1),
            'complete_inspection', 'trusted-completion', row.revision, {'staged': True,
            'player_position': dict(zip(('x', 'y'), craftsman.MARKS['InspectionPlayerMark']))})
        self.assertTrue(row.state['inspection_complete'])
        self.assertEqual(self.db.get(ShipRepairQuest, 1).phase, 'gathering_materials')
        self.assert_scenario(1, self.TRANSFERS | {'report_wreck'})
        facts = GameReadAdapter(self.db).read_facts(self.game.scope, 1, 0, 'public')
        activity = next(json.loads(fact.content) for fact in facts
                        if fact.sources[0].source_id == 'activity:ship_inspection')
        self.assertTrue(activity['inspection_complete'])
