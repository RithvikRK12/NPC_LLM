# ports.core

## Scope and contract

Repository, unit-of-work, model, vector, clock and diagnostic protocols (design section 6.1).

Source: [Detailed design](../detailed-design.md), Supporting contract/infrastructure or integration package; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** P01/P02/P03 complete; target module complete. **Owner:** Main Agent review/tracking. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for local fixture work unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md)
- Execute the task IDs below according to their stated dependencies; whole-module completion also requires the direct integration gate. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

Keep domain calculations pure where applicable; external adapters receive fake clients. No hidden ORM, model or Godot dependency is allowed in a domain rule.

## Task checklist

- [x] **P01 — Define read and external-provider protocols.**
  - **Acceptance:** World/Memory readers are read-only; model/embedding/index interfaces expose typed results and no database handles. Clock and IDs are injectable.
  - **Tests:** Fake implementations pass protocol/result-shape checks, including unavailable-provider and absent-memory results.
  - **Depends on:** the Start contracts above; adapter fakes permitted. Complete the direct integration gate before claiming this module finished.

- [x] **P02 — Define transactional write and delivery protocols.**
  - **Acceptance:** UnitOfWork, StateWriter and DeliveryStore specify commit/rollback, CAS, idempotency and cursor semantics; application owns transactions.
  - **Tests:** Fake rollback restores data; duplicate writes return prior receipts; stale revisions and changed payloads fail.
  - **Depends on:** P01. Complete the direct integration gate before claiming this module finished.

- [x] **P03 — Create reusable port conformance suites.**
  - **Acceptance:** Suites run unchanged against in-memory fakes and registered production adapters; clocks and failures are deterministic.
  - **Tests:** Deliberately broken fake demonstrates failure detection for premature commit, cursor skipping and wrong error mapping.
  - **Depends on:** P02. Complete the direct integration gate before claiming this module finished.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: P01 / `/root/ports_p01` (inherited model; typed protocol boundaries).
- Current task state: P01 accepted by Main Agent (2026-09-12). C01 accepted with 13 focused /57 combined tests; use frozen shared identity/error types. Allowed paths: `backend/app/ports/`, `backend/tests/test_read_ports.py`. No existing target ports; no runtime wiring.
- P01 files: `backend/app/ports/__init__.py`, `backend/app/ports/read.py`, `backend/tests/test_read_ports.py`.
- P01 evidence (repository root): `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_read_ports.py` — 12 passed, exit 0, independently run by Main Agent after code review.
- P01 choices: generic protocols preserve owning-domain handoff types; typed namespace/vector/batch/cosine candidate records; async model with cancellation. VectorIndex returns a typed error union so INDEX_NOT_READY cannot masquerade as no matches. No production adapters or transaction implementation claimed.
- Direct contracts gate satisfied by contracts.core C01/C02/C03; P03 conformance suites remain before the ports.core module can close.

- P02 assigned 2026-09-12 to `/root/ports_p01`; P01 accepted. Allowed paths: `backend/app/ports/write.py`, `fakes.py`, exports in `__init__.py`, `backend/tests/test_write_ports.py`. Typed transaction/CAS/idempotency/delivery contracts and deterministic in-memory tests only; no production concurrency claim.
- P02 accepted 2026-09-13. Files: `backend/app/ports/write.py`, `backend/app/ports/fakes.py`, `backend/app/ports/__init__.py`, `backend/tests/test_write_ports.py`. Evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_write_ports.py'` — 11 passed, exit 0. Protocols and reference fake cover application-owned short transactions, commit/rollback staging, relevant-revision CAS, exact idempotent retry receipts, changed-payload conflicts, delivery cursor retry/order/scope checks and competing transaction rejection. No production persistence or PostgreSQL concurrency claim.

- P03 accepted 2026-09-13. Files: `backend/tests/port_conformance.py`, `backend/tests/test_write_ports.py`. Evidence: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_write_ports.py'` — 14 passed, exit 0. The write-port checks are now a reusable conformance mixin that runs unchanged against the deterministic in-memory fake and can be subclassed by registered production adapters. Clocks/IDs/failures remain deterministic through fixture-provided IDs and seeded revisions. Deliberately broken fakes prove the suite detects premature commit visibility, delivery cursor skipping and wrong INVALID_CONTRACT error mapping.
