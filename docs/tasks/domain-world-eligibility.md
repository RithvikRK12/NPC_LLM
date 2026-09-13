# domain.world.eligibility

## Scope and contract

`check(InteractionEvent, WorldView, InteractionPolicy) -> EligibilityResult`; verify target, range, visibility and operation eligibility.

Source: [Detailed design](../detailed-design.md), 4.1 Application, world and quest modules; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** T01 complete; T02–T04 pending; target module not complete. **Owner:** Main Agent review/tracking. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

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

- [ ] **T02 — Implement the primary behaviour.**
  - **Acceptance:** Evaluate target existence, accepted position, range, visibility and permitted interaction type from a WorldView; return named predicate results.
  - **Tests:** Use the valid T01 fixture and a focused fixture for each successful branch named in this acceptance criterion; assert exact result/state/effect identity rather than generated prose. Use a fixed clock and IDs where relevant.
  - **Depends on:** T01; use immutable upstream result fixtures.

- [ ] **T03 — Enforce failures and invariants.**
  - **Acceptance:** Keep reported position and claimed ownership untrusted; fail missing evidence and unsupported remote interaction rather than assuming eligibility.
  - **Tests:** Forged ownership/location, distance boundary, supported remote channel absent, missing entities. Assert typed rejection/fallback and absence of unintended effects, not merely that an exception occurred.
  - **Depends on:** T02. Failure injection must remain local to this module and its ports.

- [ ] **T04 — Verify adjacent handoff and publish evidence.**
  - **Acceptance:** Consume fixtures produced by each direct dependency and show this module's result satisfies the next documented handoff without changing upstream policy or schema implicitly. Record test evidence and unsupported capabilities.
  - **Tests:** One focused adjacent-module contract check plus the module regression suite; include a mismatched source version/timeline where applicable. Do not run the full game unless this is an engine adapter check.
  - **Depends on:** T01–T03 and the direct Integration gate above. Until those dependencies are ready, record this task as waiting without blocking local unit work.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: T01 / Main Agent.
- Current task state: T01 accepted by Main Agent (2026-09-13). C01/C02/C03 and ports.core are accepted; this packet starts a pure values-only domain boundary.
- T01 files: `backend/app/domain/world/__init__.py`, `backend/app/domain/world/eligibility.py`, `backend/tests/test_world_eligibility.py`, `backend/tests/fixtures/world/eligibility-t01-{valid,rejected}.json`.
- T01 evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_world_eligibility.py'` — 8 passed, exit 0. Full backend regression: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 134 passed, exit 0; existing Starlette/httpx deprecation warning remains. Valid/rejected fixtures cover immutable event/world/policy/result handoffs, unsupported interaction kinds, strict scalar fields, duplicate target/rule/predicate rejection, fake protocol execution and infrastructure-free import. No live world service or eligibility algorithm claimed until T02.
