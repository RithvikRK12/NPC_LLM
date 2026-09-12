# adapters.persistence

## Scope and contract

SQLAlchemy repositories, PostgreSQL transactions and additive migrations (design sections 5.2, 6.1 and 7).

Source: [Detailed design](../detailed-design.md), Supporting contract/infrastructure or integration package; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** Planned; target module not complete. **Owner:** unassigned. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for local fixture work unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md); [ports.core](ports-core.md)
- Execute the task IDs below according to their stated dependencies; whole-module completion also requires the direct integration gate. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

This boundary is stateful/integrating: use injected ports and short application-owned transactions. Do not hold a database transaction over model inference or movement.

## Task checklist

- [ ] **D01 — Persist active timeline and revisioned world state.**
  - **Acceptance:** Additive mappings cover game timeline, NPC/relationship revisions and accepted world views; existing inventories/chats and position survive migration.
  - **Tests:** Upgrade an old schema twice; preserve data; PostgreSQL CAS detects concurrent state changes.
  - **Depends on:** the Start contracts above; adapter fakes permitted. Complete the direct integration gate before claiming this module finished.

- [ ] **D02 — Persist interaction receipts and approvals.**
  - **Acceptance:** Uniqueness distinguishes identical retry from changed payload; internal application and durable planning record commit atomically.
  - **Tests:** Concurrent same-ID submission, rollback and crash-after-approval fixtures do not double-apply state.
  - **Depends on:** D01. Complete the direct integration gate before claiming this module finished.

- [ ] **D03 — Persist commands, event identities and delivery cursors.**
  - **Acceptance:** Per-NPC command ordering, terminal lifecycle constraints, outbox records and idempotent consumer state have repository methods.
  - **Tests:** Concurrent issue, lost acknowledgement, duplicate event and rollback never skip delivery or duplicate completion.
  - **Depends on:** D02. Complete the direct integration gate before claiming this module finished.

- [ ] **D04 — Persist recovery offers and cooperation grants.**
  - **Acceptance:** Offer version/cost, agreement status, grant scope and fulfilment identity are represented; trade/grant writes share the caller transaction.
  - **Tests:** Rollback removes both cost transfer and grant; duplicate completion cannot charge twice; failed attempt cannot consume grant.
  - **Depends on:** D03. Complete the direct integration gate before claiming this module finished.

- [ ] **D05 — Persist memory provenance, lifecycle and influence ledger.**
  - **Acceptance:** Source/recipient uniqueness, corrections, model namespace and timeline filters coexist with existing semantic data; ledger identity prevents reward replay.
  - **Tests:** Old vectors remain intact; wrong-timeline query excluded; concurrent ingestion/influence retries produce one logical effect.
  - **Depends on:** D04. Complete the direct integration gate before claiming this module finished.

- [ ] **D06 — Implement the shared UnitOfWork and read adapters.**
  - **Acceptance:** Port conformance passes on PostgreSQL; context reads supply relevant revision sets; no repository calls model inference or independently commits.
  - **Tests:** Run conformance plus multi-session rollback/CAS checks on a disposable PostgreSQL database; SQLite-only success is insufficient.
  - **Depends on:** D05. Complete the direct integration gate before claiming this module finished.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: unassigned.
- Current task state: not started.
- Test evidence for new work: none yet.
- Blocker: dependency gates above; no additional module-specific blocker recorded.
