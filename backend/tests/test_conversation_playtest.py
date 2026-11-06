"""Enabled production graph regressions; isolated SQLite, deterministic generation."""
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.database.base import Base
from app.database.seed import seed_world
from app.models import Player, NPC, BowQuest
from app.services.conversation import contracts as c
from app.services.conversation.application import build_conversation_runtime

class RequestedGeneration:
    def generate(self, purpose, context, deadline, dialogue_codepoint_limit):
        if purpose != 'proposal':
            raise RuntimeError('exercise receipt-safe fallback, not model outcome speech')
        text = context.current_message.text
        pending = next(iter(context.pending_interactions), None)
        command = 'discuss_bow' if 'make me a bow' in text else 'give_item'
        operation = c.OperationCandidate(candidate_id='op:current', command_id=command,
            arguments=c.NoArguments() if command=='discuss_bow' else c.ItemArguments(item='wood'),
            target=c.TargetReference(reference_id='npc:2',entity_kind='npc',entity_id='2') if context.turn.key.npc_id==2
                else c.TargetReference(reference_id='npc:1',entity_kind='npc',entity_id='1'),
            source_spans=(c.TextSpan(text_id=context.current_message.text_id,start=0,end=len(text)),),
            modality='direct',pending_question_id=pending.question_id if pending else None)
        operations=(operation,)
        if ' or ' in text:
            operations=(operation,operation.model_copy(update={'candidate_id':'op:axe','arguments':c.ItemArguments(item='axe')}))
        return c.TurnProposal(concerns=(),references=(),reports=(),correction_candidates=(),
            operation_candidates=operations,interaction_links=(),canon_candidates=(),
            reply=(c.ExpressiveSegment(kind='expressive',segment_id='reply:current',text='All right.',addressed_concern_ids=()),))

class PlaytestRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.engine=create_engine('sqlite:///'+str(Path(self.temp.name)/'world.db'))
        self.addCleanup(self.engine.dispose);Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            seed_world(db);player=db.get(Player,1);player.opening_state='complete';self.scope=player.game_scope;db.commit()
        policy=c.ConversationPolicy(schema_version=1,policy_version='test:play',input_char_limit=500,
            total_deadline_seconds=20,provider_stage_budget_seconds=5,context_token_limit=16000,
            output_char_limit=600,beat_char_limit=300,queue_capacity=8,lease_duration_seconds=30,
            summary_trigger_turns=20,diagnostic_retention_seconds=1000)
        self.runtime=build_conversation_runtime(self.engine,policy=policy,generation=RequestedGeneration(),
            worker_id='test:play',delivery_wait_seconds=3,max_workers=1)
        self.addCleanup(self.runtime.application.close)

    def say(self, text, sequence=1, npc=2):
        key=c.ConversationKey(game_scope=self.scope,npc_id=npc,epoch=0)
        result=self.runtime.application.submit(c.TurnSubmission(schema_version=1,key=key,
            request_id='test:request:'+str(sequence),player_message=text))
        self.assertIsInstance(result,c.TurnStatus,result)
        self.assertEqual(result.phase,'finalized',result)
        return result

    def test_stock_requires_exact_persisted_purpose_question_and_durable_retry(self):
        first=self.say('May I have wood?')
        self.assertIn('why',first.response.final_dialogue.lower())
        with Session(self.engine) as db:self.assertNotIn('wood',db.get(Player,1).inventory)
        second=self.say('To help the Craftsman make a bow',2)
        self.assertEqual(len(second.response.receipt_refs),1)
        with Session(self.engine) as db:self.assertEqual(db.get(Player,1).inventory.count('wood'),1)
        self.assertEqual(self.say('To help the Craftsman make a bow',2),second)
        with Session(self.engine) as db:self.assertEqual(db.get(Player,1).inventory.count('wood'),1)

    def test_invented_model_action_for_personal_question_cannot_move_stock(self):
        result=self.say('What do you enjoy about your work?')
        self.assertFalse(result.response.receipt_refs)
        with Session(self.engine) as db:self.assertNotIn('wood',db.get(Player,1).inventory)

    def test_bow_meeting_uses_the_durable_quest_operation(self):
        with Session(self.engine) as db:db.add(BowQuest(player_id=1,phase='meet',string_collected=False));db.commit()
        result=self.say('Can you make me a bow?',npc=1)
        self.assertEqual(len(result.response.receipt_refs),1)
        with Session(self.engine) as db:self.assertEqual(db.get(BowQuest,1).phase,'gather')

    def test_context_overflow_finishes_without_generation_or_actions(self):
        self.runtime.coordinator._policy = self.runtime.coordinator._policy.model_copy(update={'context_token_limit': 1})
        result=self.say('What do you enjoy about your work?')
        self.assertEqual(result.response.degradation_reason,'CONTEXT_BUDGET_EXCEEDED')
        self.assertFalse(result.response.receipt_refs)

    def test_quoted_and_hypothetical_requests_never_move_stock(self):
        for sequence,text in enumerate(('Imagine you give me wood.', 'He said "give me wood".',
                "He said 'I give you water'.", 'Do not give me wood.'),1):
            result=self.say(text,sequence)
            self.assertFalse(result.response.receipt_refs)
        with Session(self.engine) as db:self.assertEqual(db.get(Player,1).inventory,['water','food'])

    def test_cancel_ends_the_persisted_item_request_without_transfer(self):
        from app.models.conversation_state import PendingInteraction
        from sqlalchemy import select
        self.say('May I have wood?')
        cancelled=self.say('cancel',2)
        self.assertEqual(cancelled.response.response_origin,'scripted')
        with Session(self.engine) as db:
            self.assertEqual(db.scalar(select(PendingInteraction)).status,'cancelled')
            self.assertNotIn('wood',db.get(Player,1).inventory)

    def test_stranded_wreck_report_gets_human_reaction_and_waits_for_inspection_consent(self):
        from app.models.craftsman_encounter import CraftsmanEncounter
        message = "my ship just wrecked and i'm stranded!"
        result = self.say(message, npc=1)
        self.assertEqual(len(result.response.receipt_refs), 1)
        self.assertNotIn('recorded', result.response.final_dialogue.lower())
        self.assertNotIn('report', result.response.final_dialogue.lower())
        self.assertIn("glad you made it ashore", result.response.final_dialogue)
        self.assertIn("if you'd like", result.response.final_dialogue)
        self.assertEqual(self.say(message, npc=1), result)
        with Session(self.engine) as db:
            state = db.get(CraftsmanEncounter, 1).state
            self.assertTrue(state['wreck_reported'])
            self.assertTrue(state['offer_pending'])
            self.assertFalse(state['outing_active'])
            self.assertFalse(state['inspection_complete'])
        accepted = self.say('yes please', 2, npc=1)
        self.assertEqual(len(accepted.response.receipt_refs), 1)
        with Session(self.engine) as db:
            state = db.get(CraftsmanEncounter, 1).state
            self.assertTrue(state['outing_active'])
            self.assertFalse(state['inspection_complete'])

    def test_post_inspection_repair_receives_findings_and_generates_without_fallback(self):
        import json
        from app.services.craftsman import record
        with Session(self.engine) as db:
            row = record(db, db.get(Player, 1))
            row.state = row.state | {'wreck_reported': True, 'inspection_complete': True}
            db.commit()
        class CorrectingGeneration:
            calls = []
            def generate(inner, purpose, context, deadline, dialogue_codepoint_limit):
                inner.calls.append(purpose)
                feedback = [json.loads(fact.content) for fact in context.visible_facts
                            if fact.evidence_id.startswith('repair-feedback:')]
                text = ("You're welcome. I'm glad I could help." if feedback else
                        "Thanks for looking at my ship! I can take a look at the damage with you.")
                segment = c.ExpressiveSegment(kind='expressive', segment_id='reply:test',
                    text=text, addressed_concern_ids=())
                if purpose == 'proposal':
                    return c.TurnProposal(concerns=(), references=(), reports=(), correction_candidates=(),
                        operation_candidates=(), interaction_links=(), canon_candidates=(), reply=(segment,))
                return c.CandidateReply(segments=(segment,), canon_candidates=(), source=c.ReplySource(
                    origin='generated', source_id=context.turn.turn_id, schema_version=1,
                    policy_versions=context.policy_versions))
        generation = CorrectingGeneration()
        ports = self.runtime.coordinator._ports
        ports._generation = generation
        ports._proposal._generation = generation
        result = self.say('Thanks for looking at my ship!', npc=1)
        self.assertEqual(generation.calls, ['proposal', 'repair'])
        self.assertEqual(result.response.final_dialogue, "You're welcome. I'm glad I could help.")
        self.assertNotEqual(result.response.response_origin, 'fallback')
        self.assertFalse(result.response.receipt_refs)

    def test_natural_acceptance_starts_inspection_and_replays_the_same_receipt(self):
        self.say("My ship wrecked.", npc=1)
        message = "Sure! That would be helpful."
        accepted = self.say(message, 2, npc=1)
        self.assertEqual(len(accepted.response.receipt_refs), 1)
        state = accepted.response.legacy_projection['craftsman_encounter']
        self.assertTrue(state['outing_active'])
        self.assertFalse(state['offer_pending'])
        self.assertEqual(state['mode'], 'departure_pending')
        self.assertEqual(self.say(message, 2, npc=1), accepted)

    def test_contextual_wreck_help_projects_flat_craftsman_activity_for_the_game(self):
        self.say('The storm broke my ship.',npc=1)
        result=self.say('Could you help me fix it?',2,npc=1)
        self.assertTrue(result.response.legacy_projection['craftsman_encounter'].get('outing_active'))
        self.assertEqual(result.response.legacy_projection['craftsman_encounter']['mode'],'departure_pending')

    def test_multiple_stock_requests_choose_one_then_confirm_its_purpose(self):
        first=self.say('May I have wood or axe?')
        self.assertFalse(first.response.receipt_refs)
        self.assertIn('Which',first.response.final_dialogue)
        choice=self.say('wood please',2)
        self.assertFalse(choice.response.receipt_refs)
        self.assertIn('why',choice.response.final_dialogue)
        final=self.say('To make a bow',3)
        self.assertEqual(len(final.response.receipt_refs),1)
        with Session(self.engine) as db:
            self.assertEqual(db.get(Player,1).inventory.count('wood'),1)
            self.assertNotIn('axe',db.get(Player,1).inventory)

    def test_choice_item_name_never_overrides_an_explicit_gift_direction(self):
        with Session(self.engine) as db:
            player=db.get(Player,1);player.inventory=[*player.inventory,'wood'];db.commit()
        self.say('May I have wood or axe?')
        result=self.say('I give you wood',2)
        self.assertEqual(len(result.response.receipt_refs),1)
        with Session(self.engine) as db:
            self.assertNotIn('wood',db.get(Player,1).inventory)
            self.assertEqual(db.get(NPC,2).inventory.count('wood'),2)

    def test_negated_purpose_answer_does_not_authorize_stock_transfer(self):
        self.say('May I have wood?')
        result=self.say('Do not give me wood because I no longer need it',2)
        self.assertFalse(result.response.receipt_refs)
        with Session(self.engine) as db:self.assertNotIn('wood',db.get(Player,1).inventory)
