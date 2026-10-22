# context/T01 handoff

- Owner/model: `context_t01`, gpt-6-luna / medium.
- Scope: detached unified context assembly only; context/T02 retains token budget policy.
- Dependencies: accepted conversation contracts T01-T04 and ports T01-T02. No shared files changed.
- Implementation: `ContextAssembler` asks `ContextReadPort` for the requested turn's scope and NPC-private visibility, requires an exact detached `ContextPacket`, rechecks its history key and earlier sequence, and reconstructs it through Pydantic validation before returning. It passes through profile, canon, reports, interpretations, visible facts, finalized history, summaries, capabilities, pending interactions, revisions, and policy versions without applying binary social permission routing. It requests only facts visible to this NPC; server-private evidence remains excluded by the packet contract.
- Adapter boundary: the frozen `ContextReadPort` returns a `ContextPacket`, so durable-final status and exclusion of raw drafts are adapter guarantees. `VisibleTurn` has no origin field; finalized fallback pairs are therefore retained alongside generated pairs. A concrete adapter must query finalized transcript rows only and scope-filter before constructing the packet. Fake ports are not concrete persistence proof.

## Verification

- Expected red: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_context -v` from repo root, exit 1, 3 failures; each failed because `app.services.conversation.context` was absent.
- Green focused + read-port conformance: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_context backend.tests.conversation_port_conformance -v` from repo root, exit 0, 8 tests passed, 0 failed, 0 skipped.
- Evidence is reproducible from the test file `backend/tests/test_conversation_context.py`; command output is recorded in the task execution transcript. No live DB/provider was used.

## Acceptance outcomes

- Wreck report then fear retains attributed unverified report and earlier final exchange: pass, focused test.
- Action/report turn followed by gratitude retains prior finalized visible pair, including fallback wording: pass, focused test.
- Cross-NPC/scope/epoch and future history rejected: pass, focused test.
- Nonfinal/raw drafts excluded: packet schema has no draft field and read port is specified to return finalized prior pairs; concrete persistence behavior remains unverified and must be proven by adapter tests.
- Private knowledge excluded: packet contract rejects `server_private` sources; existing read-port conformance test verifies that contract rejection. No social permission routing was added.
- Profile, canon, reports, unresolved interaction context, capabilities, revisions and policy versions remain represented in the returned immutable `ContextPacket`; budget selection is intentionally deferred to T02.
- Adjacent read-port conformance: 4/4 tests passed in the combined command (structural conformance, explicit scopes, infrastructure-free imports, private evidence rejection).

## Risks and next handoff

- This task cannot prove SQL scope filtering or that fallback is durable/final because only a fake read port is available; persistence adapter tasks must demonstrate those guarantees.
- `budget` is an accepted but unused argument by design. T02 owns deterministic budget ordering and overflow.
- Proposed packet update: mark context/T01 local implementation/tests complete only after Main Agent diff review; module-level acceptance remains pending adjacent adapter integration.
- Follow-up: context/T02 (budget/degraded retrieval); relevant persistence context-read adapter integration task IDs as scheduled by Main Agent.

## Main Agent review

- Inspected the implementation and tests; changes are limited to the assigned context module, focused tests, and this evidence file.
- Reproduced from the repository root with Python 3.12.14 and `PYTHONPATH=backend`: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_context backend.tests.conversation_port_conformance backend.tests.test_conversation_capabilities backend.tests.test_conversation_contracts backend.tests.test_conversation_contracts_interfaces backend.tests.test_read_ports -v` — exit 0; 52 passed, 0 failed, 0 skipped.
- Local implementation is accepted. Persistence must still prove finalized-only scoped reads and fallback durability; context/T02 owns budget policy.
