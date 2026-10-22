# proposal/T01 handoff

Date: 2026-10-15
Task: Implement the proposal-stage service boundary, one-call budget, strict typed revalidation, and context reference checks.

## Files changed

- `backend/app/services/conversation/proposal.py`
- `backend/tests/test_conversation_proposal.py`

## Verification

- RED: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_proposal -v` — exit 1 before implementation; all 8 tests failed to import the intentionally absent `app.services.conversation.proposal` module.
- GREEN focused: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_proposal backend.tests.test_conversation_contracts_interfaces backend.tests.test_conversation_contracts_turn_values -v` — exit 0; 52 tests passed.
- Conversation suite: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` — exit 0; 213 tests passed.
- Full backend suite: from `backend`, `PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -v` — exit 0; 676 tests passed. Existing Starlette/httpx deprecation warning was emitted at import.
- `git diff --check` — exit 0 for tracked changes; the three proposal deliverables were untracked during this check.

## Behavior

`ProposalService.propose(context, deadline)` makes one `GenerationPort.generate('proposal', context, stage_deadline, output_char_limit)` call. It converts timeout and invalid output to typed failures, strictly reconstructs returned `TurnProposal` values, resolves all proposal spans against text supplied by this exact context, and validates lifecycle cues using the frozen contract's current-turn/current-message/pending-interaction checks. Resolved entity/topic references, linked questions/corrections, and proposed operation command/target/argument bounds are checked against the supplied capabilities and pending interactions. Multiple concerns and every declared intent modality are retained as proposal data.

## Limits

The accepted `GenerationPort` is a typed boundary. Raw JSON decoding, provider-specific malformed-response classification, and the shared character-data prompt belong to proposal/T02, which owns provider adaptation and prompt parity. Proposal validation does not authorize operations, infer consent from quoted/hypothetical/negated/ambiguous modalities, execute commands, or persist state. The Unicode span test uses the current message's leading supplementary-plane emoji and rejects an out-of-range source span; offsets remain Python Unicode code-point offsets as defined by `TextSpan`.
