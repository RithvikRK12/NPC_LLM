# operations/T01 handoff

Task: `operations/T01`. Worker: `operations_t01`. Status: implemented locally, awaiting Main Agent acceptance. Shared worktree: `/Users/rukithnayak/Documents/NPC_LLM-1`. No task packet or master tracker state edited by this worker.

## Delivered

- Added pure `OperationPolicy.decide(proposal, interaction_plan, context)` in `backend/app/services/conversation/operations.py`; it returns the frozen `NoOperation`, `ClarificationRequired`, `Denied`, or `ReadyToRecheck` values.
- Only direct candidates are eligible. Quotes, hypotheticals and negations remain inert; ambiguous candidates require clarification. Multiple supported direct candidates require an explicit first choice even if an empty interaction plan is supplied.
- Command eligibility comes from current scoped capability descriptors: command availability, target equality, audited parameter shape/item allowlist, and request/accept speech acts are checked. The frozen input contracts reject unaudited commands, arbitrary transfer quantities and confidence fields.
- Pending consent must belong to the exact current turn, question, operation terms, current satisfied interaction evaluation and current relevant command preconditions. Current answer spans and visible final-question text are verified. Suspended/terminal questions, cancellation transitions, stale plans and mismatched bindings cannot produce ready results.
- Later action-choice selection preserves the exact offered operation in its binding while checking the current selection span separately. No unselected action is queued. Gateway execution and receipt creation remain T02.
- The redesigned policy imports contracts only and has no provider, prose recognizer, ORM, game-service or execution dependency. No legacy heuristic interception is called by this path. Existing `validation/items.py` and `craftsman_intent.py` remain for the legacy runtime; replacing legacy orchestration is outside T01.
- Added 14 focused tests in `backend/tests/test_conversation_operations.py`. No frozen contracts or shared fixtures were edited.

## Red/green and verification

Commands ran from the repository root; logs are in this directory. Initial red: the first 12 focused tests failed explicitly because the pure operation policy was absent (`t01-red.log`, exit 1). After implementation, the first green attempt exposed one invalid test fixture status reason for an expired interaction; that fixture was corrected to `preconditions_changed`. Two later compatibility tests cover choice selection and conflicting binding evidence; they passed against the implementation.

| Exact command | Exit | Result / log |
| --- | ---: | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_operations -v` | 0 | 14 passed; `t01-green.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_operations backend.tests.test_conversation_interactions backend.tests.test_conversation_contracts backend.tests.test_conversation_contracts_continuity backend.tests.test_conversation_contracts_interfaces backend.tests.test_conversation_contracts_turn_values backend.tests.test_conversation_contracts_validation -v` | 0 | 102 passed; `t01-adjacent.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` | 0 | 287 passed; `t01-conversation.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v` | 0 | 750 passed; `t01-backend.log` |
| `git diff --check` | 0 | `t01-diff-check.log` |
| `git diff --no-index --check /dev/null backend/app/services/conversation/operations.py` and `git diff --no-index --check /dev/null backend/tests/test_conversation_operations.py` | 1 | Both new files differ from `/dev/null`; no whitespace diagnostics |

## Limits and integration requirements

This pure policy consumes validated typed proposals and an application-assembled interaction plan. It does not prove semantic interpretation authenticity by scanning raw language; modality is an explicit interpretation value, and prose alone cannot create a request or consent. The owning server must supply authentic scoped capability/context reads and the accepted InteractionPolicy output. Pydantic unvalidated construction/copy escape hatches are not supported external input decoders.

`ReadyToRecheck` is a selected request, never execution permission. The transaction gateway must re-read selected-command preconditions, ownership/role/availability and consent, enforce the current turn/fence/epoch and one-operation constraint, recover existing receipts, and atomically consume/fulfill consent with effects and receipt. An action-choice aggregate satisfied evaluation does not prove its selected command's preconditions. No gateway, persistence, HTTP or Godot adoption is claimed here. No live provider/player database was used by the focused tests.

## Main Agent review update (2026-10-18)

Main Agent independently reproduced the current checks from the repository root:

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_operations.py'` — exit 0; 14 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_interactions.py'` — exit 0; 18 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py'` — exit 0; 70 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` — exit 0; 305 passed, 0 failed/skipped. Existing Starlette/httpx deprecation warning emitted by FastAPI TestClient.
- `git diff --check` — exit 0.

An independent read-only review approved the T01 pure policy boundary and found no concrete T01 safety defect. The review explicitly did not cover gateway execution, database atomicity or T02. Main Agent accepts operations/T01 locally; the operations module remains incomplete until T02 and adjacent integration gates pass.
