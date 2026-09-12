# policy.content

## Scope and contract

Owner-reviewed village profiles, recovery content and evaluation configuration; design sections 7.3 and 12.

Source: [Detailed design](../detailed-design.md), Supporting contract/infrastructure or integration package; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** Planned; target module not complete. **Owner:** unassigned. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for local fixture work unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md); [policy.registry](policy-registry.md); [domain.quest.recovery](domain-quest-recovery.md)
- Execute the task IDs below according to their stated dependencies; whole-module completion also requires the direct integration gate. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

Keep domain calculations pure where applicable; external adapters receive fake clients. No hidden ORM, model or Godot dependency is allowed in a domain rule.

## Task checklist

- [ ] **K01 — Create versioned demonstration policy fixtures.**
  - **Acceptance:** Craftsman/Gatherer profiles, fuzzy/mapping inputs and safe fallbacks are explicit fixtures, not claims of final tuning or new product scope.
  - **Tests:** Registry rejects unknown capabilities and contradictory bounds; fixtures exercise helpful, cautious and refusal branches.
  - **Depends on:** the Start contracts above; adapter fakes permitted. Complete the direct integration gate before claiming this module finished.

- [ ] **K02 — Obtain authored favour and trade content for both refusal points.**
  - **Acceptance:** Record owner-approved favour predicates and trade costs, with an attainable resource-free-or-obtainable favour alternative; do not invent prices/tasks.
  - **Tests:** Run reachability scenarios for Gatherer wood and Craftsman crafting, including absent trade resources and no circular prerequisites. BLOCKED for production content until owner provides/approves it; synthetic fixtures may proceed.
  - **Depends on:** K01. Complete the direct integration gate before claiming this module finished.

- [ ] **K03 — Publish approved content bundle and unresolved parameter register.**
  - **Acceptance:** Only owner-approved offers activate in the playable demo. Performance, retention and tuning remain explicitly evaluation-scoped with no assumed deletion period.
  - **Tests:** Full bundle validation covers accepted terms, grant fulfilment and safe fallback; missing required recovery content prevents activation of dead-end refusals.
  - **Depends on:** K02. Complete the direct integration gate before claiming this module finished.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: unassigned.
- Current task state: not started.
- Test evidence for new work: none yet.
- Blocker: dependency gates above; production favour/trade content awaits owner approval (K02), while fixtures and contract tests can proceed.
