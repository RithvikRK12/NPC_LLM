# capabilities/T01 handoff

## Task

- ID: capabilities/T01 — build descriptors from authoritative views.
- Owner / model / effort: capabilities_t01 / gpt-6-luna / medium.
- Status: ready for Main Agent review.
- Scope: pure projection module against frozen contracts/T01–T04 and ports/T01. No game adapter implementation, permission table, or executor conformance is included.

## Files changed

- `backend/app/services/conversation/capabilities.py` — injected callable supplies per-command authoritative views; the reader projects only their command IDs and declared schemas, targets, availability, safe reason, preconditions, and speech acts. Output is detached, sorted, and duplicate command views fail closed. Server-private preconditions are filtered; private authorization evidence is never read or copied.
- `backend/tests/test_conversation_capabilities.py` — projection, sorting/no-invention, private evidence filtering, safe unavailable reason, and duplicate command cases.

## Tests run

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1` using Python 3.12.14 at `.venv/bin/python`; `PYTHONPATH=backend`; no provider, DB, or external configuration.

- RED: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_capabilities` — exit 1; 4 errors because `app.services.conversation.capabilities` did not exist. This was the expected missing-module failure before implementation.
- GREEN: same focused command — exit 0; 4 tests passed.
- Adjacent contracts and read ports: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_contracts backend.tests.test_conversation_contracts_interfaces backend.tests.test_read_ports` — exit 0; 40 tests passed.

## Results

- Uses only commands returned by the injected authoritative view; absent/unknown operations cannot be introduced by this module — pass, tested with absent `give_item`.
- Carries through typed parameter schema, allowed targets, availability, safe unavailable reason, preconditions, and supported speech acts — implemented by direct projection; direct detailed field coverage can be expanded in integration fixtures.
- Private authorization evidence is not exposed; `server_private` preconditions are removed from model-facing output — pass, tested.
- Deterministic sorted output and duplicate command fail-closed behavior — pass, tested.
- Adjacent read-port and contract tests — pass (40/40).
- Proposed task status: ready for independent diff review; do not mark module complete until game-adapters/T02 supplies concrete authoritative views and capabilities/T02 verifies execution conformance.

## Risks

- The authoritative view protocol is structural and intentionally narrow, but the concrete game adapter has not yet been integrated. The service supplying `safe_unavailable_reason` must ensure that field is a public-safe explanation; this module cannot infer whether arbitrary reason text leaks private facts.
- This snapshot is informational only; execution must recheck against the same deterministic rule owner.

## Follow-up tasks

- `game-adapters/T02`: provide authoritative views from existing deterministic rule owners, including safe public denial reasons.
- `capabilities/T02`: compare projected availability/preconditions with execution-time rule checks and reject stale snapshots.

## Main Agent review

- Inspected the implementation and tests; changes are limited to the assigned capability module, focused tests, and this evidence file.
- Reproduced from the repository root with Python 3.12.14 and `PYTHONPATH=backend`: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_context backend.tests.conversation_port_conformance backend.tests.test_conversation_capabilities backend.tests.test_conversation_contracts backend.tests.test_conversation_contracts_interfaces backend.tests.test_read_ports -v` — exit 0; 52 passed, 0 failed, 0 skipped.
- Local implementation is accepted. Concrete rule-owner views and execution-time conformance remain assigned to game-adapters/T02 and capabilities/T02.
