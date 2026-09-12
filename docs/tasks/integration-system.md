# integration.system

## Scope and contract

Narrow cross-boundary release checks from design section 10; the only intentionally system-wide packet.

Source: [Detailed design](../detailed-design.md), Supporting contract/infrastructure or integration package; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** Planned; target module not complete. **Owner:** unassigned. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for local fixture work unless a task explicitly says otherwise.
- **Integration gate:** All module integration gates in [master-progress](../master-progress.md#module-status); run the slices below individually, not as one monolithic task.
- Execute the task IDs below according to their stated dependencies; whole-module completion also requires the direct integration gate. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

This boundary is stateful/integrating: use injected ports and short application-owned transactions. Do not hold a database transaction over model inference or movement.

## Task checklist

- [ ] **I01 — Verify decision-to-command contract chain.**
  - **Acceptance:** Recorded fixture runs through perception, proposal, extraction, fuzzy, role, final validation and FSEC with matching source versions.
  - **Tests:** Use fake model/clock; rejected stages create no command; FSEC cannot widen constraints and policy replay is deterministic.
  - **Depends on:** the Start contracts above; adapter fakes permitted. Complete the direct integration gate before claiming this module finished.

- [ ] **I02 — Verify verified-outcome and memory feedback slice.**
  - **Acceptance:** One interaction effect becomes one confirmed dialogue event, recipient memory and eligible bounded influence.
  - **Tests:** PostgreSQL fault injection before/after commits and duplicate delivery demonstrate no second item, reward or trust increment.
  - **Depends on:** I01. Complete the direct integration gate before claiming this module finished.

- [ ] **I03 — Verify refusal and same-NPC recovery slice.**
  - **Acceptance:** Both mandatory refusal points expose approved favour/trade routes and successful recovery creates a persistent scoped grant.
  - **Tests:** Run unavailable-cost, false completion claim, repricing, duplicate charge and immediate re-refusal cases; use approved content for playable acceptance.
  - **Depends on:** I02. Complete the direct integration gate before claiming this module finished.

- [ ] **I04 — Verify Godot execution, save, restart and reconnect.**
  - **Acceptance:** Controller movement/animation/interaction and UI reconcile with authoritative outcomes; normal launch preserves the save and restart invalidates old work.
  - **Tests:** Disposable-backend Godot smoke covers blocked path, cancellation, outcome dialogue, resumed crafting, old callbacks and exactly-one bow; inspect visuals separately.
  - **Depends on:** I03. Complete the direct integration gate before claiming this module finished.

- [ ] **I05 — Record model/retrieval and operational evaluation.**
  - **Acceptance:** Produce results for schema/grounding, semantic retrieval, stage latency and diagnostics with versions and limits stated; do not invent performance targets.
  - **Tests:** Separate live local-model smoke from deterministic tests; measure wrong-subject leakage, priority memory inclusion and redaction. No unique-player or hallucination-free claim.
  - **Depends on:** I04. Complete the direct integration gate before claiming this module finished.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: unassigned.
- Current task state: not started.
- Test evidence for new work: none yet.
- Blocker: dependency gates above; no additional module-specific blocker recorded.
