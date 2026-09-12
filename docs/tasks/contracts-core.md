# contracts.core

## Scope and contract

Common envelopes, identities, revisions, value types and transport fixture conventions (design sections 3 and 5).

Source: [Detailed design](../detailed-design.md), Supporting contract/infrastructure or integration package; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** C01/C02 complete; C03 pending; target module not complete. **Owner:** Main Agent (review/tracking), `/root/c01_contracts` (C01 implementation). Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** None. Begin with C01; it is the next recommended task.
- **Integration gate:** None.
- Execute the task IDs below according to their stated dependencies; whole-module completion also requires the direct integration gate. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

Keep domain calculations pure where applicable; external adapters receive fake clients. No hidden ORM, model or Godot dependency is allowed in a domain rule.

## Task checklist

- [x] **C01 — Define identity, error and revision value contracts.**
  - **Acceptance:** Version, timeline, source IDs, finite positions, typed errors and relevant RevisionSet serialize without ORM or HTTP dependencies. Before/approved revisions are distinct.
  - **Tests:** Round-trip golden fixtures; reject unknown versions, invalid IDs, non-finite positions and missing provenance.
  - **Depends on:** None. Complete the direct integration gate before claiming this module finished.

- [x] **C02 — Define behaviour vocabulary and shared constraint types.**
  - **Acceptance:** Separate intent, expression and engine actions; ConstraintSet can represent only narrowed permissions and parameter ranges. Domain-specific records remain owned by their modules.
  - **Tests:** Unknown action/enum rejected; constraint intersection cannot add privileges; timing fields reject invalid combinations.
  - **Depends on:** C01. Complete the direct integration gate before claiming this module finished.

- [ ] **C03 — Publish cross-language fixture and ownership conventions.**
  - **Acceptance:** Backend and Godot consume the same stable envelope/command fixtures; document owner of each domain handoff and changes to shared contract versions.
  - **Tests:** Decode fixtures with a small Python harness and an independent Godot fixture reader; incompatible version fixture fails predictably.
  - **Depends on:** C02. Complete the direct integration gate before claiming this module finished.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: C01 / `/root/c01_contracts`, inherited GPT-6 model for shared-contract design; Main Agent owns review and tracking.
- Current task state: C01 accepted by Main Agent (2026-09-12). Allowed writes: `backend/app/contracts/`, `backend/tests/test_contract_values.py`, `backend/tests/fixtures/contracts/c01*.json`. Starting state: no target contracts package; existing unrelated dirty files preserved.
- C01 files: `backend/app/contracts/__init__.py`, `backend/app/contracts/core.py`, `backend/tests/test_contract_values.py`, `backend/tests/fixtures/contracts/c01-values.json`.
- C01 evidence (repository root): `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_contract_values.py` — 13 passed; combined `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 57 passed, exit 0. Main Agent independently reviewed implementation and ran combined checks.
- C01 contract choices: opaque ASCII IDs, UTC-normalized timestamps, 2D accepted positions, tuple-based scoped revisions and distinct base/approved fields (equal allowed for no-change approval). Envelopes require structural source lineage; policy list may explicitly be empty. DomainError is a value so malformed input can be rejected without fabricated envelope IDs. Contextual provenance/authority checks belong to consumers.
- C01 limitations: no runtime migration or transport wiring; NumericChange/GroundingRef/Diagnostic are not implemented by this identity/error/revision slice. No production content or tuning selected.
- Blocker: none for C01; C02/C03 wait for reviewed predecessor evidence.

- C02 assigned 2026-09-12 to `/root/c02_design_review` (inherited model, shared schema algebra); C01 accepted prerequisite. Allowed paths: `backend/app/contracts/behavior.py`, exports in `__init__.py`, `backend/tests/test_behavior_contracts.py`, `backend/tests/fixtures/contracts/c02*.json`. Main Agent owns review/tracking; C01 core frozen.

- C02 accepted 2026-09-12 by Main Agent after code review. Files: `backend/app/contracts/behavior.py`, exports in `__init__.py`, `backend/tests/test_behavior_contracts.py`, `backend/tests/fixtures/contracts/c02_constraints.json`, `c02_denied.json`, `c02_failure_dialogue.json`.
- C02 evidence (root): `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_behavior_contracts.py` — 17 passed, exit 0. Includes 512 associativity combinations; Main Agent separately checked 1000 deterministic algebra trials. Combined regression recorded in master-progress.
- C02 semantics: sorted immutable sets, per-action target alternatives and bounds, conjunctive predicates, accumulating evidence, deny-all on contradictions; empty dialogue permissions retain silent action permissions. Unknown actions reject. Outcome IDs and predicates are structural references, verified by owning modules.
