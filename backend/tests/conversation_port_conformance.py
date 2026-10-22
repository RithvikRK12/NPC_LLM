"""T01 port boundaries: structural fakes, dependency hygiene and visibility."""
import ast
import inspect
from pathlib import Path
import unittest
from datetime import datetime, timezone

from pydantic import ValidationError

from app.services.conversation.contracts import (
    ContextPacket, ConversationKey, ConversationPolicy, Deadline, MemoryRecord,
    TurnRef,
)
from app.services.conversation.ports import (
    CapabilityReadPort, ContextReadPort, GenerationPort, MemoryReadPort,
    ClockPort, TracePort, WorldReadPort, Visibility,
)


class FakeWorld:
    def read_facts(self, game_scope, npc_id, epoch, visibility):
        return ()


class FakeContext:
    def read_context(self, turn, game_scope, visibility):
        return None


class FakeMemory:
    def read_memories(self, game_scope, npc_id, epoch, visibility):
        return ()


class FakeCapabilities:
    def read_capabilities(self, game_scope, npc_id, visibility):
        return ()


class FakeGeneration:
    def generate(self, purpose, context, deadline, dialogue_codepoint_limit):
        return None


class FakeTrace:
    def record(self, turn, stage, values):
        return None


class FakeClock:
    def monotonic(self):
        return 10.0

    def utc_now(self):
        return datetime(2026, 10, 14, tzinfo=timezone.utc)


class ConversationPortConformance(unittest.TestCase):
    def test_fake_adapters_structurally_conform(self):
        self.assertIsInstance(FakeWorld(), WorldReadPort)
        self.assertIsInstance(FakeContext(), ContextReadPort)
        self.assertIsInstance(FakeMemory(), MemoryReadPort)
        self.assertIsInstance(FakeCapabilities(), CapabilityReadPort)
        self.assertIsInstance(FakeGeneration(), GenerationPort)
        self.assertIsInstance(FakeClock(), ClockPort)
        self.assertIsInstance(FakeTrace(), TracePort)

    def test_protocols_use_contract_values_and_explicit_scope_visibility(self):
        self.assertIn('game_scope', inspect.signature(WorldReadPort.read_facts).parameters)
        self.assertIn('visibility', inspect.signature(WorldReadPort.read_facts).parameters)
        self.assertIn('deadline', inspect.signature(GenerationPort.generate).parameters)
        self.assertEqual(Visibility, __import__('typing').Literal['public', 'npc_private'])

    def test_generation_port_names_the_dialogue_codepoint_unit_explicitly(self):
        self.assertIn('dialogue_codepoint_limit', inspect.signature(GenerationPort.generate).parameters)

    def test_port_module_has_no_framework_database_or_provider_imports(self):
        path = Path(__file__).parents[1] / 'app/services/conversation/ports.py'
        tree = ast.parse(path.read_text())
        roots = set()
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split('.')[0] for alias in node.names)
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split('.')[0])
                imported_modules.add(node.module)
        self.assertFalse(roots & {'fastapi', 'sqlalchemy', 'openai', 'anthropic', 'ollama'})
        self.assertFalse(any(name.startswith('app.') and name != 'app.services.conversation.contracts'
                             for name in imported_modules))

    def test_public_context_contract_rejects_private_authorization_evidence(self):
        key = {'game_scope': 'scope-a', 'npc_id': 7, 'epoch': 1}
        turn = {'turn_id': 'turn-1', 'request_id': 'request-1', 'key': key, 'sequence': 1}
        source = {
            'kind': 'inventory', 'source_id': 'authz:1', 'revision': 1,
            'game_scope': 'scope-a', 'npc_id': 7, 'attribution': 'server',
            'visibility': 'server_private',
        }
        fact = {
            'kind': 'mechanical_fact', 'evidence_id': 'fact:1', 'content': 'A private check',
            'sources': [source], 'created_at': '2026-10-14T00:00:00Z',
        }
        context = {
            'turn': turn, 'current_message': {'text_id': 'message:1', 'text': 'hello'},
            'character_profile': [], 'active_canon': [], 'visible_recent_turns': [],
            'summaries': [], 'reports': [], 'interpretations': [], 'visible_facts': [fact],
            'capabilities': [], 'pending_interactions': [], 'revisions': {'resources': {}},
            'policy_versions': {},
        }
        with self.assertRaises(ValidationError):
            ContextPacket.model_validate(context)


if __name__ == '__main__':
    unittest.main()
