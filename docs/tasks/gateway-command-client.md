# gateway.command_client

## Scope and contract

Poll durable cursor, acknowledge receipt and retry events with stable IDs.

Source: [Detailed design](../detailed-design.md), 6.3 Godot modules; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** Planned; target module not complete. **Owner:** unassigned. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for T01–T03 unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md); [gateway.contract_codec](gateway-contract-codec.md)
- Execute local task IDs in order; T04 requires T01–T03 and the direct integration dependencies. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

Use fake transport/controller collaborators for unit checks. Real navigation/render checks are separate; headless tests must not wait for render-only events.

## Task checklist

- [ ] **T01 — Define the module contract and fixture boundary.**
  - **Acceptance:** Publish the public input/output/error types above, with owned domain fields and shared envelope references. Supply a valid fixture and one rejected fixture; expose no ORM/session or node object in the handoff.
  - **Tests:** Round-trip or construct the valid fixture, reject missing required fields and unsupported variants, and prove input fixtures are not mutated. Decode the shared command fixture in Godot.
  - **Depends on:** Start contracts above. Do not wait for full runtime integration.

- [ ] **T02 — Implement the primary behaviour.**
  - **Acceptance:** Poll ordered deliveries through an injectable transport and maintain cursor, receipt and stable outbound event identities.
  - **Tests:** Use the valid T01 fixture and a focused fixture for each successful branch named in this acceptance criterion; assert exact result/state/effect identity rather than generated prose. Use a fixed clock and IDs where relevant.
  - **Depends on:** T01; use immutable upstream result fixtures.

- [ ] **T03 — Enforce failures and invariants.**
  - **Acceptance:** Reconcile disconnect/replay and lost acknowledgements; never advance past an unprocessed command or rebind an old event to a new timeline.
  - **Tests:** Disconnect/reconnect, duplicate batch, lost acknowledgement and no skipped unprocessed command. Assert typed rejection/fallback and absence of unintended effects, not merely that an exception occurred.
  - **Depends on:** T02. Failure injection must remain local to this module and its ports.

- [ ] **T04 — Verify adjacent handoff and publish evidence.**
  - **Acceptance:** Consume fixtures produced by each direct dependency and show this module's result satisfies the next documented handoff without changing upstream policy or schema implicitly. Record test evidence and unsupported capabilities.
  - **Tests:** One focused adjacent-module contract check plus the module regression suite; include a mismatched source version/timeline where applicable. Do not run the full game unless this is an engine adapter check.
  - **Depends on:** T01–T03 and the direct Integration gate above. Until those dependencies are ready, record this task as waiting without blocking local unit work.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: unassigned.
- Current task state: not started.
- Test evidence for new work: none yet.
- Blocker: dependency gates above; no additional module-specific blocker recorded.
