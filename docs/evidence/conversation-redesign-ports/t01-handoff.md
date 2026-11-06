# Conversation ports T01 handoff

Date: 2026-10-14

## Delivered

Added narrow Protocol boundaries in `backend/app/services/conversation/ports.py` for world facts, context, memory, safe capability descriptors, typed generation, monotonic/UTC time, and structured trace events. Read calls carry explicit game scope and visibility, and where appropriate NPC and epoch. The generation call carries a purpose, detached `ContextPacket`, contract `Deadline`, and explicit response budget. The module imports standard-library typing/time values and conversation contracts only; it exposes no session or framework/provider types.

Added `backend/tests/conversation_port_conformance.py`. Fake adapters structurally conform to each protocol. Dependency inspection rejects FastAPI, SQLAlchemy, and named concrete-provider roots. The public-context case confirms a `ContextPacket` rejects `server_private` authorization evidence.

## Verification

The test-first check failed before implementation as expected:

```text
PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/conversation_port_conformance.py
exit 1 — ModuleNotFoundError: app.services.conversation.ports
```

After implementation:

| Command | Result |
| --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'conversation_port_conformance.py'` | 4 passed, exit 0 |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 47 passed, exit 0 |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_read_ports.py'` | 12 passed, exit 0 |
| `git diff --check` | exit 0 |

## Limits

These are interface declarations and pure conformance checks. No concrete persistence, game, provider, clock, or trace adapter is part of T01. Python `Protocol` checks structural shape; runtime safety still depends on adapters honoring the requested scope and visibility. Model-visible `ContextPacket` construction independently blocks private evidence sources.
