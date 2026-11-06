"""Game scopes are opaque values and may include literal path prefixes."""
import unittest

from app.services.conversation.contracts import ConversationKey


class GameScopeContractTests(unittest.TestCase):
    def test_conversation_key_preserves_literal_world_scope(self):
        key = ConversationKey(game_scope='/world', npc_id=1, epoch=0)
        self.assertEqual(key.game_scope, '/world')
        self.assertNotEqual(key.game_scope, 'world')

    def test_rejects_unsafe_path_scope(self):
        for value in ('', '/', '//world', '/../world', '/world?other', 'world/../../x'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ConversationKey(game_scope=value, npc_id=1, epoch=0)


if __name__ == '__main__':
    unittest.main()
