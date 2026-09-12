# adapters.http

## Scope and contract

Versioned FastAPI and legacy endpoint adapters (design section 6.2).

Source: [Detailed design](../detailed-design.md), Supporting contract/infrastructure or integration package; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** Planned; target module not complete. **Owner:** unassigned. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for local fixture work unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md); [application.interactions](application-interactions.md); [application.decisions](application-decisions.md); [application.commands](application-commands.md); [application.outcomes](application-outcomes.md); [application.sessions](application-sessions.md); [domain.quest.recovery](domain-quest-recovery.md)
- Execute the task IDs below according to their stated dependencies; whole-module completion also requires the direct integration gate. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

This boundary is stateful/integrating: use injected ports and short application-owned transactions. Do not hold a database transaction over model inference or movement.

## Task checklist

- [ ] **H01 — Expose interaction receipt and result endpoints.**
  - **Acceptance:** Versioned input maps to application results; accepted work returns 202 and later typed state; HTTP owns no game policy.
  - **Tests:** Dependency-overridden client tests cover 202/200, 404, 409, 422, 429 and 503 mappings without a model.
  - **Depends on:** the Start contracts above; adapter fakes permitted. Complete the direct integration gate before claiming this module finished.

- [ ] **H02 — Expose command polling and controller event transport.**
  - **Acceptance:** Preserve timeline, cursor and event identities; acknowledgement is not completion. Loopback deployment and restricted origins are configurable.
  - **Tests:** Duplicate events, unsupported schema, stale timeline and reconnect use bounded fake delivery batches.
  - **Depends on:** H01. Complete the direct integration gate before claiming this module finished.

- [ ] **H03 — Expose world, restart, position and recovery endpoints.**
  - **Acceptance:** Restart retry returns the same new timeline; accepted offers use server-owned terms; position is a report pending verification.
  - **Tests:** Lost restart response retry does not reset twice; old position rejected; changed offer terms cannot silently reprice.
  - **Depends on:** H02. Complete the direct integration gate before claiming this module finished.

- [ ] **H04 — Delegate legacy routes through the same application ports.**
  - **Acceptance:** Current chat/inventory/quest/UI compatibility does not retain an independent mutation path or attach a new timeline to old work.
  - **Tests:** Existing route regression fixtures plus old-client reset-boundary cases show consistent validation and no forged engine commands.
  - **Depends on:** H03. Complete the direct integration gate before claiming this module finished.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: unassigned.
- Current task state: not started.
- Test evidence for new work: none yet.
- Blocker: dependency gates above; no additional module-specific blocker recorded.
