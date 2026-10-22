"""Lifecycle facade delegates clear to the atomic lifecycle-store boundary."""
import unittest
from tempfile import TemporaryDirectory
from sqlalchemy import create_engine
from app.database.base import Base
from app.models.player import Player
from app.models.npc import NPC
from app.services.conversation.adapters.persistence import SQLTurnStore

from app.services.conversation import contracts as c


class LifecycleStoreFake:
    def __init__(self):
        self.calls = []
        self.result = None

    def clear(self, key):
        self.calls.append(key)
        if self.result is not None:
            return self.result
        return c.ClearResult(outcome='cleared', previous_key=key,
            current_key=key.model_copy(update={'epoch': key.epoch + 1}))

    def new_game(self, expected_scope):
        self.calls.append(expected_scope)
        if self.result is not None:
            return self.result
        return c.WorldResult(outcome='reset', previous_scope=expected_scope,
            game_scope='run:2', state_projection={}, state_revisions=c.RevisionSet(resources={}))


class LifecycleFacadeTests(unittest.TestCase):
    def setUp(self):
        import importlib.util
        self.assertIsNotNone(importlib.util.find_spec('app.services.conversation.lifecycle'),
            'Lifecycle facade is not implemented')
        from app.services.conversation.lifecycle import Lifecycle
        self.Lifecycle = Lifecycle
        self.key = c.ConversationKey(game_scope='/world', npc_id=4, epoch=7)
        self.store = LifecycleStoreFake()
        self.lifecycle = Lifecycle(self.store)

    def test_clear_delegates_exact_key_and_returns_the_epoch_transition(self):
        result = self.lifecycle.clear(self.key)
        self.assertEqual(self.store.calls, [self.key])
        self.assertEqual(result.previous_key, self.key)
        self.assertEqual(result.current_key.game_scope, '/world')
        self.assertEqual(result.current_key.epoch, 8)

    def test_clear_propagates_typed_store_failure_without_retrying(self):
        self.store.result = c.ConversationError(code='STALE_EPOCH', stage='clear',
            retryable=False, safe_detail='Refresh this conversation.')
        result = self.lifecycle.clear(self.key)
        self.assertEqual(result, self.store.result)
        self.assertEqual(self.store.calls, [self.key])

    def test_invalid_key_returns_typed_error_without_calling_store(self):
        result = self.lifecycle.clear('run:1')
        self.assertIsInstance(result, c.ConversationError)
        self.assertEqual(result.code, 'INVALID_INPUT')
        self.assertEqual(self.store.calls, [])

    def test_new_game_delegates_exact_scope_and_returns_new_scope(self):
        result = self.lifecycle.new_game('run:1')
        self.assertEqual(self.store.calls, ['run:1'])
        self.assertIsInstance(result, c.WorldResult)
        self.assertEqual((result.previous_scope, result.game_scope), ('run:1', 'run:2'))

    def test_invalid_scope_returns_typed_error_without_calling_store(self):
        result = self.lifecycle.new_game('../escape')
        self.assertIsInstance(result, c.ConversationError)
        self.assertEqual(result.code, 'INVALID_INPUT')
        self.assertEqual(self.store.calls, [])

    def test_new_game_propagates_stale_scope_error_without_retry(self):
        stale = c.ConversationError(code='STALE_SCOPE', stage='new_game', retryable=False,
            safe_detail='Refresh this world.')
        self.store.result = stale
        result = self.lifecycle.new_game('run:1')
        self.assertEqual(result, stale)
        self.assertEqual(self.store.calls, ['run:1'])


class SQLLifecycleFacadeIntegrationTests(unittest.TestCase):
    def test_clear_uses_atomic_sql_store_and_returns_new_epoch(self):
        from app.services.conversation.lifecycle import Lifecycle

        with TemporaryDirectory() as tmp:
            engine = create_engine(f'sqlite:///{tmp}/lifecycle.db')
            try:
                Base.metadata.create_all(engine)
                with engine.begin() as db:
                    db.execute(Player.__table__.insert().values(id=1, game_scope='/world'))
                    db.execute(NPC.__table__.insert().values(id=1, name='One', role='craftsman'))
                key = c.ConversationKey(game_scope='/world', npc_id=1, epoch=0)
                result = Lifecycle(SQLTurnStore(engine)).clear(key)
                self.assertIsInstance(result, c.ClearResult)
                self.assertEqual(result.previous_key, key)
                self.assertEqual(result.current_key.epoch, key.epoch + 1)
            finally:
                engine.dispose()

    def test_new_game_uses_atomic_sql_store_and_rotates_scope(self):
        from test_conversation_persistence_lifecycle import SQLPublicationLifecycleTests
        from app.services.conversation.lifecycle import Lifecycle
        from app.models.player import Player
        from sqlalchemy.orm import Session

        fixture = SQLPublicationLifecycleTests(methodName='runTest')
        fixture.setUp()
        try:
            result = Lifecycle(fixture.store).new_game('run:1')
            self.assertIsInstance(result, c.WorldResult)
            self.assertEqual(result.previous_scope, 'run:1')
            self.assertNotEqual(result.game_scope, 'run:1')
            with Session(fixture.fixture.engine) as db:
                self.assertEqual(db.get(Player, 1).game_scope, result.game_scope)
        finally:
            Base.metadata.drop_all(fixture.fixture.engine)
            fixture.fixture.tearDown()
            fixture.tearDown()


if __name__ == '__main__':
    unittest.main()
