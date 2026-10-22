"""Deterministic routing for plain NPC role questions."""
import unittest

from app.services.conversation import contracts as c
from app.services.conversation.adapters.requests import (
    guard_role_question_proposal, is_role_question, request_proposal,
)


def context(message):
    key = c.ConversationKey(game_scope='run:role-question', npc_id=1, epoch=0)
    turn = c.TurnRef(turn_id='turn:role-question', request_id='request:role-question',
                     key=key, sequence=1)
    return c.ContextPacket(
        turn=turn,
        current_message=c.TextValue(text_id='message:role-question', text=message),
        character_profile=(), active_canon=(), visible_recent_turns=(), summaries=(),
        reports=(), interpretations=(), visible_facts=(), capabilities=(),
        pending_interactions=(), revisions=c.RevisionSet(resources={}), policy_versions={},
    )


class RequestIntentTests(unittest.TestCase):
    def test_plain_what_do_you_do_question_remains_model_written_chat(self):
        proposal = request_proposal(context('What do you do?'))

        self.assertIsNone(proposal)
        self.assertTrue(is_role_question(context('What do you do?')))

        operation = c.OperationCandidate(candidate_id='model:action', command_id='give_item',
            arguments=c.ItemArguments(item='wood'), target=c.TargetReference(
                reference_id='target:npc:1', entity_kind='npc', entity_id='1'),
            source_spans=(c.TextSpan(text_id='message:role-question', start=0, end=15),),
            modality='direct', pending_question_id=None)
        concern = c.Concern(concern_id='model:question', kind='question', message_spans=(
            c.TextSpan(text_id='message:role-question', start=0, end=15),))
        generated = c.TurnProposal(concerns=(concern,), references=(), reports=(),
            correction_candidates=(), operation_candidates=(operation,), interaction_links=(),
            canon_candidates=(), reply=(c.ExpressiveSegment(kind='expressive',
                segment_id='model:reply', text='I make bows, mostly. The joints have to hold.',
                addressed_concern_ids=('model:question',)),))
        guarded = guard_role_question_proposal(context('What do you do?'), c.Result.success(generated))

        self.assertEqual(guarded.value.operation_candidates, ())
        self.assertEqual(guarded.value.reply, generated.reply)
        self.assertEqual(guarded.value.reply[0].text, 'I make bows, mostly. The joints have to hold.')

    def test_role_question_routing_does_not_swallow_mixed_action_question(self):
        self.assertIsNone(request_proposal(context('What do you do, and can you give me wood?')))


if __name__ == '__main__':
    unittest.main()
