# Fallback T01 handoff

Implemented pure receipt-first fallback rendering in `backend/app/services/conversation/fallback.py`.

## Behavior

- `FallbackPolicy.render(context, decision, receipt, failure)` returns `Result[AssembledReply]`.
- A matching committed receipt takes priority over any provider failure and is rendered through the existing exact `_receipt_text` clause allowlist. The reply carries an `operation_receipt` provenance dependency. A receipt from another turn/scope/NPC fails closed with `EVIDENCE_CHANGED`.
- With no receipt, `ClarificationRequired.question` is returned verbatim. A typed `Denied.safe_explanation` is returned verbatim as the known unavailability explanation.
- Otherwise an authored outage line is selected for NPC 1 (Craftsman) or NPC 2 (Gatherer); other IDs receive a neutral authored default. Failure detail is never inserted into speech.
- Output is a complete `AssembledReply` with exact span coverage and no continuity changes. The module makes no provider, persistence, or game-service calls.

## Tests and commands

RED: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_fallback.py'` failed all five cases because `FallbackPolicy` did not yet exist.

GREEN checks:

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_fallback.py'` — 5 tests passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py'` — 70 tests passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition*.py'` — 38 tests passed.

Focused coverage includes transfer receipt priority during provider timeout, accepted inspection remaining accepted, exact clarification and denial text, and role-specific non-fabricating outage speech. T02 structural/grounding validation and publication-failure handling remain outside this task.
