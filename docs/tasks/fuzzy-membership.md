# fuzzy.membership

## Scope and contract

`fuzzify(CandidateState, MembershipPolicy) -> Memberships`; overlapping triangular/trapezoidal memberships.

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
  - **Acceptance:** Implement overlapping triangular/trapezoidal membership functions over normalized inputs with configured labels and versions.
  - **Tests:** Use the valid T01 fixture and a focused fixture for each successful branch named in this acceptance criterion; assert exact result/state/effect identity rather than generated prose. Use a fixed clock and IDs where relevant.
  - **Depends on:** T01; use immutable upstream result fixtures.

- [x] **T03 — Enforce failures and invariants.**
  - **Acceptance:** Handle shoulder endpoints correctly and reject unordered points or invalid ranges; output membership degrees must remain bounded.
  - **Tests:** Overlap, endpoint shoulders, range guarantees, invalid point ordering. Assert typed rejection/fallback and absence of unintended effects, not merely that an exception occurred.
  - **Depends on:** T02. Failure injection must remain local to this module and its ports.

- [x] **T04 — Verify adjacent handoff and publish evidence.**
  - **Acceptance:** Consume fixtures produced by each direct dependency and show this module's result satisfies the next documented handoff without changing upstream policy or schema implicitly. Record test evidence and unsupported capabilities.
  - **Tests:** One focused adjacent-module contract check plus the module regression suite; include a mismatched source version/timeline where applicable. Do not run the full game unless this is an engine adapter check.
  - **Depends on:** T01–T03 and the direct Integration gate above. Until those dependencies are ready, record this task as waiting without blocking local unit work.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: T01 / `/root/c01_contracts` (inherited model; immutable membership schema boundary).
- Current task state: T01 accepted by Main Agent (2026-09-12). C01 core types frozen, 13 focused tests passed. Allowed paths: `backend/app/domain/fuzzy/membership.py`, package initializers, `backend/tests/test_fuzzy_membership.py`, `backend/tests/fixtures/fuzzy/*.json`. No primary algorithm until T02 is assigned.
- T01 files: `backend/app/domain/fuzzy/membership.py`, domain/fuzzy package initializers, `backend/tests/test_fuzzy_membership.py`, `backend/tests/fixtures/fuzzy/membership-t01-{valid,rejected}.json`.
- T01 evidence (root): `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_fuzzy_membership.py` — 9 passed, exit 0, independently run after Main Agent review. Valid/rejected typed fixture boundary, finite normalized values and nested immutability verified; no algorithm or semantic policy activation claimed.
- Assigned task/owner: T02 / Main Agent.
- Current task state: T02 accepted by Main Agent (2026-09-13). Pure `fuzzify` evaluates configured triangular and trapezoidal labels for normalized inputs and emits immutable memberships with the candidate input, candidate state and policy version identities preserved. T03 still owns failure/invariant hardening for malformed authored points and endpoint shoulders.
- T02 files: `backend/app/domain/fuzzy/membership.py`, `backend/tests/test_fuzzy_membership.py`, `backend/tests/fixtures/fuzzy/membership-t02-{triangle,trapezoid,branches}.json`.
- T02 evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_fuzzy_membership.py'` — 14 passed, exit 0. Full backend regression: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 118 passed, exit 0; existing Starlette/httpx deprecation warning remains.
- Direct contracts gate satisfied by contracts.core C01/C02/C03; T04 adjacent handoff remains before the fuzzy.membership module can close.
- T03 accepted 2026-09-13. Files: `backend/app/domain/fuzzy/membership.py`, `backend/tests/test_fuzzy_membership.py`. Evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_fuzzy_membership.py'` — 19 passed, exit 0. Full backend regression: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 123 passed, exit 0. Shoulder endpoints on trapezoids now include `a == b` and `c == d`; unordered triangle points, out-of-range policy points and missing dimensions return typed `INVALID_CONTRACT` errors without emitting memberships; output degrees remain bounded.
- T04 accepted 2026-09-13. Files: `backend/app/domain/fuzzy/membership.py`, `backend/tests/test_fuzzy_membership.py`. Evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_fuzzy_membership.py'` — 22 passed, exit 0. Full backend regression: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 126 passed, exit 0. The module consumes accepted C01 envelopes through `MembershipInput`/`MembershipPolicy`, emits immutable `Memberships` suitable for the documented `fuzzy.inference` handoff, rejects mismatched policy timeline/version without output, and records no unsupported runtime capabilities. No full game or live semantic check is required for this pure module gate.
