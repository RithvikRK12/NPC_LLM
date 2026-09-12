# application.delivery

## Scope and contract

Durable decision planning, command delivery and feedback workers implied by design sections 6 and 7.

Source: [Detailed design](../detailed-design.md), Supporting contract/infrastructure or integration package; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** Planned; target module not complete. **Owner:** unassigned. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for local fixture work unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md); [adapters.persistence](adapters-persistence.md); [application.decisions](application-decisions.md); [application.commands](application-commands.md); [application.outcomes](application-outcomes.md); [memory.ingest](memory-ingest.md); [memory.influence](memory-influence.md); [memory.lifecycle](memory-lifecycle.md)
- Execute the task IDs below according to their stated dependencies; whole-module completion also requires the direct integration gate. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

This boundary is stateful/integrating: use injected ports and short application-owned transactions. Do not hold a database transaction over model inference or movement.

## Task checklist

- [ ] **W01 — Dispatch durable interaction and command-planning work.**
  - **Acceptance:** Leased work resumes after a crash, uses recorded approval revisions and deduplicates completion; per-NPC decision concurrency is bounded.
  - **Tests:** Crash before/after claim and approval with fake clock/handlers recovers without duplicate internal state.
  - **Depends on:** the Start contracts above; adapter fakes permitted. Complete the direct integration gate before claiming this module finished.

- [ ] **W02 — Dispatch verified-event memory and influence work.**
  - **Acceptance:** Verified events reach recipients once logically; influence returns through extraction/role/control approval rather than directly writing trust.
  - **Tests:** Redelivery, worker restart and embedding outage preserve source events and do not reward historical help twice.
  - **Depends on:** W01. Complete the direct integration gate before claiming this module finished.

- [ ] **W03 — Reconcile reset, expiry and deferred maintenance.**
  - **Acceptance:** Worker compares timeline before every result commit; expiry/retry budgets are policy inputs; unspecified retention performs no deletion.
  - **Tests:** Late model/embedding completion after reset cannot recreate memories or grants; poison work terminates under configured budgets.
  - **Depends on:** W02. Complete the direct integration gate before claiming this module finished.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: unassigned.
- Current task state: not started.
- Test evidence for new work: none yet.
- Blocker: dependency gates above; no additional module-specific blocker recorded.
