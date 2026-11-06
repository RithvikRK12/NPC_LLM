# context/T02 implementation handoff

Main Agent reproduced the final focused, adjacent, conversation and backend checks on 2026-10-18; independent review found no blocker and T02 is locally accepted. The limitations below remain downstream integration gates.

- Owner: `context_t02`; 2026-10-18.
- Owned changes: `backend/app/services/conversation/context.py`, `backend/tests/test_conversation_context.py`, this handoff. No frozen contracts, persistence adapter, packet checkboxes or master ledger changed.
- Source: detailed design §6.1; `ContextPacket`, `ContextSummary`, `RevisionSet`, `ContextReadPort`; accepted context/T01 behavior.

## Behavior delivered

`ContextAssembler.build` now validates the complete detached snapshot before applying a local `ContextBudget`. Existing positive integer budgets remain accepted. The explicit policy contains `token_limit`, caller-owned instruction and operation-constraint text, critical evidence IDs, and required interaction IDs. Instruction and constraint text reserves provider input budget without changing the frozen packet schema. The application caller must supply the exact instruction/constraint texts used at its provider boundary.

The mandatory packet keeps current input, character profile, all capability/operation descriptors, explicitly critical evidence, explicitly required interactions, and interactions referenced by server-evaluated preconditions. It also preserves turn, revision and policy metadata. Mandatory overflow returns `CONTEXT_BUDGET_EXCEEDED`; a missing/stale critical evidence reference fails with `STALE_SCOPE`. It never truncates current input or a required record to make room.

Remaining complete records are considered deterministically: newest finalized pairs first, canon by evidence ID, unresolved interactions by ID, remaining visible facts by evidence ID, then summaries, reports and interpretations. Large optional records can be omitted while later smaller records fit. Attributions and source links are retained with each complete record.

Canon and summary source revisions must exactly match current heads in `packet.revisions.resources`, keyed by each `SourceRef.source_id`. Mismatched or absent heads cause exclusion before optional index ranking. This is a fail-closed reader integration requirement: the adapter must include these current revision heads, including correction heads where represented by sources. Stale critical canon causes a typed failure rather than silent omission.

An optional older-context selector can rank only summaries/reports/interpretations already present in the validated scoped snapshot. Unknown IDs cannot introduce records; duplicate IDs cannot duplicate output. Embedding/index exceptions retain the deterministic nonsemantic ordering. The selector receives detached values and cannot request an unscoped SQL query through this interface.

The injected token counter measures canonical serialized packet plus reserved instruction/constraint text on each selection. The default counter is a deterministic lexical estimate, explicitly not an exact provider tokenizer. Provider integration must inject its configured tokenizer when enforcing the provider's actual token ceiling.

## Tests and evidence

All commands ran from the repository root with `PYTHONPATH=backend` and `.venv/bin/python`.

- Initial RED: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_context -v` — exit 1; existing 4 tests passed, 5 new cases errored on absent `ContextBudget`. This established the missing budget boundary before implementation.
- Focused GREEN: the same command — exit 0; 14 tests passed after extending cases for constraints, required interactions, unresolved order, newest pair ordering, stale critical canon and unknown index IDs.
- Adjacent boundary/conformance: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_context backend.tests.conversation_port_conformance backend.tests.test_conversation_contracts backend.tests.test_conversation_contracts_interfaces backend.tests.test_read_ports -q` — exit 0; 65 tests passed, no failures/skips.
- Conversation regressions: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -q` — exit 0; 363 passed, no failures/skips.
- Full backend: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -q` — exit 0; 826 passed, no failures/skips. Existing Starlette/httpx and UTC timestamp deprecation warnings appeared, as did existing malformed-output rejection and bounded lexical retrieval diagnostics.
- `git diff --check` — exit 0. Source/test files may be untracked in the redesign workspace; the behavioral suite directly imports them.

The workspace contains concurrent task edits; suite counts reflect the shared state at execution time.

## Acceptance boundaries still open

The pure module verifies scope validation before any optional index selector receives candidates, and proves scoped nonsemantic fallback with a detached fake reader. It does **not** prove concrete SQL scope filtering happens before retrieval, durable finalized-only reads, or PostgreSQL behavior. Those are persistence-adapter integration requirements and remain unverified here. The frozen `ContextReadPort` exposes a detached packet only; changing its database/query implementation is outside this task's ownership.

Default integer budgets do not know a caller's instruction text or critical-evidence classification. Runtime integration must pass an explicit policy and the provider tokenizer. The module has no generation call, SQL transaction, or live embedding/provider dependency. No claim of full context module/runtime completion is made by this handoff.
