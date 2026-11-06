# Fallback T02 handoff

Implemented fallback validation and safe failure behavior in `backend/app/services/conversation/fallback.py`.

## Behavior

- Fallback requires the configured `ConversationPolicy` and uses its exact `output_char_limit` and `beat_char_limit`; it rejects a mismatched `bounds` policy version before rendering.
- Every rendered fallback is converted to an `AssembledReply` and checked by `ResponseValidator.check` against detached context/evidence, including receipt provenance. Blocking findings fail publication with a safe typed error.
- A renderer exception for a committed receipt returns `EVIDENCE_CHANGED` and never emits generic outage speech in place of the mandatory outcome. Validation or evidence-construction exceptions return `INTERNAL_FAILURE`.
- Accepted activity receipts continue to describe the historical acceptance only. The test supplies a current cancelled activity fact and confirms fallback says it agreed to inspect, without claiming current progress.
- No provider, persistence, or game state is read or changed. The original receipt remains the committed authoritative result when rendering fails.

## Tests and commands

RED evidence is in `t02-red.log`.

- Focused fallback: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_fallback.py' -v` — exit 0, 11 passed.
- Response validation: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_validation.py' -v` — exit 0, 13 passed.
- Composition: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition*.py' -v` — exit 0, 38 passed.
- Contracts: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py' -v` — exit 0, 77 passed.
- Full conversation pattern: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` — 543 tests; 530 passed and 13 failed because `backend/tests/test_conversation_repair.py` requires the not-yet-implemented T03 `RepairService`. All failures report `T03 speech-only RepairService is absent`; this is outside fallback T02.
- `git diff --check` — exit 0.

## Limitation for integration

When `ContextPacket.active_canon` is nonempty, the current `ResponseValidator` requires the typed T06 claim/evidence/comparison projections and returns `CANON_PROJECTION_MISSING` if they are absent. The frozen fallback API does not accept those projections. This implementation therefore fails closed in that state, consistent with the validator contract; making fallback publish in canon-bearing contexts requires a coordinator/API integration decision to supply the projections. No shared contract or task packet was changed here.
