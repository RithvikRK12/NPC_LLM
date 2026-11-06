# memory.reconcile

## Scope and contract

`reconcile(NewRecord, RelatedRecords, ReconciliationPolicy) -> ReconciliationPlan`; link corrections and safe consolidation.

Source: [Detailed design](../detailed-design.md), 4.4 Execution, dialogue and memory modules; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

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
  - **Acceptance:** Produce lifecycle and correction-link plans from typed subject/predicate/provenance evidence while retaining historical records.
  - **Tests:** Use the valid T01 fixture and a focused fixture for each successful branch named in this acceptance criterion; assert exact result/state/effect identity rather than generated prose. Use a fixed clock and IDs where relevant.
  - **Depends on:** T01; use immutable upstream result fixtures.

- [x] **T03 — Enforce failures and invariants.**
  - **Acceptance:** Keep unresolved claims separate; never equate embedding similarity with truth, negate a claim silently or overwrite historical evidence.
  - **Tests:** Retraction, authoritative correction, conflicting claims retained and negation not merged by vector similarity. Assert typed rejection/fallback and absence of unintended effects, not merely that an exception occurred.
  - **Depends on:** T02. Failure injection must remain local to this module and its ports.

- [x] **T04 — Verify adjacent handoff and publish evidence.**
  - **Acceptance:** Consume fixtures produced by each direct dependency and show this module's result satisfies the next documented handoff without changing upstream policy or schema implicitly. Record test evidence and unsupported capabilities.
  - **Tests:** One focused adjacent-module contract check plus the module regression suite; include a mismatched source version/timeline where applicable. Do not run the full game unless this is an engine adapter check.
  - **Depends on:** T01–T03 and the direct Integration gate above. Until those dependencies are ready, record this task as waiting without blocking local unit work.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: complete / Main Agent.
- Current task state: T04 accepted by Main Agent (2026-09-29). C01/C02/C03 are accepted; this packet completed a pure values-only memory boundary.
- T01–T04 files: `backend/app/memory/{__init__,reconcile}.py`, `backend/tests/test_memory_reconcile.py`, `backend/tests/fixtures/memory/reconcile-t01-{valid,rejected}.json`.
- T01–T04 evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_memory_reconcile.py'` — 14 passed, exit 0. Full backend regression: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 186 passed, exit 0; existing Starlette/httpx deprecation warning remains and the baseline NPC rejection diagnostic still prints. The module exposes immutable memory record, related record, policy and plan handoffs, produces correction/supersede/retraction/conflict/retain links from typed evidence, retains historical records, rejects mismatched timeline/policy evidence and non-authoritative fact/retraction claims, avoids embedding-similarity truth merges, and passes C01 envelope plus test-local lifecycle handoff checks. Unsupported capability: no repository, embedding index or live memory service integration is claimed by this pure module gate.
- Blocker: dependency gates above; no additional module-specific blocker recorded.
