"""SQLite acceptance for exact-scope finalized conversation history reads."""
import tempfile
import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

from app.database.base import Base
from app.models.conversation_state import ConversationTurn
from app.services.conversation import contracts as c
from app.services.conversation.adapters.scoped_reads import read_prior_turns
import app.models  # register all mapped model metadata


class ScopedTurnReadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        configured_url = os.environ.get('CONVERSATION_TEST_DATABASE_URL')
        url = configured_url or f'sqlite:///{self.temp.name}/reads.db'
        if configured_url and not (make_url(url).database or '').startswith('npc_test_'):
            raise RuntimeError('SQL acceptance requires a disposable npc_test_* database')
        self.engine = create_engine(url, connect_args={'timeout': 15} if url.startswith('sqlite:') else {})
        Base.metadata.drop_all(self.engine, tables=[ConversationTurn.__table__])
        Base.metadata.create_all(self.engine, tables=[ConversationTurn.__table__])
        self.key = c.ConversationKey(game_scope='world:primary', npc_id=1, epoch=2)
        self.current = c.TurnRef(turn_id='turn:current', request_id='request:current',
            key=self.key, sequence=9)

    def tearDown(self):
        Base.metadata.drop_all(self.engine, tables=[ConversationTurn.__table__])
        self.engine.dispose()
        self.temp.cleanup()

    def _row(self, turn_id, *, scope='world:primary', npc=1, epoch=2, sequence=1,
             phase='finalized', payload_ok=True):
        key = c.ConversationKey(game_scope=scope, npc_id=npc, epoch=epoch)
        ref = c.TurnRef(turn_id=turn_id, request_id=f'request:{turn_id}', key=key, sequence=sequence)
        submission = c.TurnSubmission(schema_version=1, request_id=ref.request_id,
            key=key, player_message=f'player says {turn_id}')
        assembled = c.AssembledReply(text_id=f'reply:{turn_id}', final_text=f'NPC says {turn_id}',
            beats=(f'NPC says {turn_id}',), segment_spans={}, evidence_dependencies=(),
            candidate_continuity_changes=())
        recovered = c.RecoveredReply(turn=ref, fence=1, reply=assembled)
        final = c.FinalTurnResult(schema_version=1, turn=ref, final_dialogue=assembled.final_text,
            dialogue_beats=assembled.beats, response_origin='generated', degradation_reason=None,
            receipt_refs=(), state_projection={}, state_revisions=c.RevisionSet(resources={}),
            diagnostic_ref=None)
        payload = ({'submission': submission.model_dump(mode='json'),
                    'assembled_reply': recovered.model_dump(mode='json'),
                    'final_result': final.model_dump(mode='json')} if payload_ok else {})
        return dict(turn_id=turn_id, game_scope=scope, npc_id=npc, epoch=epoch,
            request_id=ref.request_id, sequence=sequence, payload_digest='digest', payload=payload,
            phase=phase, lease_fence=1, attempt_count=0, provider_call_count=0,
            final_result_id=assembled.text_id if payload_ok else None)

    def test_returns_only_ordered_finalized_rows_from_exact_scope_npc_epoch_before_current(self):
        rows = [
            self._row('late', sequence=8),
            self._row('early', sequence=2),
            self._row('other-world', scope='world', sequence=1),
            self._row('other-npc', npc=2, sequence=1),
            self._row('other-epoch', epoch=1, sequence=1),
            self._row('current-or-later', sequence=9),
            self._row('unfinished', sequence=3, phase='finalizing'),
            self._row('unknown-provenance', scope='legacy-unknown', sequence=1),
            self._row('bad-payload', sequence=4, payload_ok=False),
        ]
        with self.engine.begin() as db:
            db.execute(ConversationTurn.__table__.insert(), rows)

        result = read_prior_turns(self.engine, self.current, game_scope='world:primary')
        self.assertEqual([item.turn.turn_id for item in result], ['early', 'late'])
        self.assertEqual([item.turn.sequence for item in result], [2, 8])
        self.assertEqual(result[0].player_message.text, 'player says early')
        self.assertEqual(result[0].player_message.text_id, 'turn:2')
        self.assertEqual(result[0].final_reply.text, 'NPC says early')
        self.assertEqual(result[0].final_reply.text_id, 'reply:early')
        # Contracts are detached, and a namespaced world stays distinct from bare world.
        self.assertEqual(read_prior_turns(self.engine, self.current.model_copy(update={
            'key': self.key.model_copy(update={'game_scope': 'world'})}), game_scope='world:primary'), ())

    def test_rejects_mismatched_explicit_scope_guard(self):
        with self.engine.begin() as db:
            db.execute(ConversationTurn.__table__.insert(), [self._row('prior', sequence=1)])
        self.assertEqual(read_prior_turns(self.engine, self.current, game_scope='another-world'), ())


if __name__ == '__main__':
    unittest.main()
