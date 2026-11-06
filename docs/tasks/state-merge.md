# state.merge

## Scope and contract

`merge(CurrentState, ProposedChanges, MergePolicy) -> Result[MergedChanges]`; choose one value per dimension using explicit source precedence and effect identity.

Source: [Detailed design](../detailed-design.md), 4.3 Behavioural-control modules; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** T01–T04 complete; target module complete. **Owner:** Main Agent review/tracking. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for T01–T03 unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md)
- Execute local task IDs in order; T04 requires T01–T03 and the direct integration dependencies. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

Keep domain calculations pure where applicable; external adapters receive fake clients. No hidden ORM, model or Godot dependency is allowed in a domain rule.

## Task checklist

- [x] **T01 — Define the module contract and fixture boundary.**
  - **Acceptance:** Publish the public input/output/error types above, with owned domain fields and shared envelope references. Supply a valid fixture and one rejected fixture; expose no ORM/session or node object in the handoff.
  - **Tests:** Round-trip or construct the valid fixture, reject missing required fields and unsupported variants, and prove input fixtures are not mutated. Import and exercise the module with fake dependencies only.
  - **Depends on:** Start contracts above. Do not wait for full runtime integration.

- [x] **T02 — Implement the primary behaviour.**
  - **Acceptance:** Resolve candidate changes by explicit source precedence and stable effect identity, emitting one accepted change per target dimension.
  - **Tests:** Use the valid T01 fixture and a focused fixture for each successful branch named in this acceptance criterion; assert exact result/state/effect identity rather than generated prose. Use a fixed clock and IDs where relevant.
  - **Depends on:** T01; use immutable upstream result fixtures.

- [x] **T03 — Enforce failures and invariants.**
  - **Acceptance:** Reject unknown relationship subjects and prevent repeated memory influence or duplicate proposals from being summed automatically.
  - **Tests:** Duplicate influence, conflict precedence, unrecognized relationship subject and no automatic sum of repeated proposals. Assert typed rejection/fallback and absence of unintended effects, not merely that an exception occurred.
  - **Depends on:** T02. Failure injection must remain local to this module and its ports.

- [x] **T04 — Verify adjacent handoff and publish evidence.**
  - **Acceptance:** Consume fixtures produced by each direct dependency and show this module's result satisfies the next documented handoff without changing upstream policy or schema implicitly. Record test evidence and unsupported capabilities.
  - **Tests:** One focused adjacent-module contract check plus the module regression suite; include a mismatched source version/timeline where applicable. Do not run the full game unless this is an engine adapter check.
  - **Depends on:** T01–T03 and the direct Integration gate above. Until those dependencies are ready, record this task as waiting without blocking local unit work.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: complete / Main Agent.
- Current task state: T04 accepted by Main Agent (2026-10-12). C01/C02/C03 are accepted; this packet completed a pure values-only state-merge boundary, precedence behaviour, invariant hardening and adjacent handoff proof.
- T01–T04 files: `backend/app/state/{__init__,merge}.py`, `backend/tests/test_state_merge.py` and `backend/tests/fixtures/state/merge-t01-{valid,rejected}.json`.
- T01–T04 evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_state_merge.py'` — 18 passed, exit 0. Full backend regression: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 225 passed, exit 0; existing Starlette/httpx deprecation warning remains and the baseline NPC rejection diagnostic still prints. The module exposes immutable current state, proposed change, merge policy and merged change values over C01 envelopes; resolves one accepted relative change per dimension/subject by explicit source precedence and stable effect identity; rejects unknown relationship subjects, duplicate memory influence/proposal effects, mismatched timeline/policy evidence, unsupported dimensions and invalid numeric deltas; and proves a test-local state.extract handoff for accepted merged changes with policy/timeline mismatch checks. Unsupported capability: no persistence, model provider, application orchestration or runtime state.extract integration is claimed by this pure module gate.
- Blocker: dependency gates above; no additional module-specific blocker recorded.
