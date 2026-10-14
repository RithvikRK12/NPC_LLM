# NPC conversation redesign — master progress

Updated: 2026-10-14 (Asia/Kolkata).

## Overall status

**Planning complete; redesign implementation not started/verified in this pass. 0/23 packets complete, 0/21 design modules complete.** The 21 modules in Detailed design §2 each have a packet; baseline and evaluation-release are two supporting workstreams. All implementation checkboxes deliberately remain unchecked. Existing working-tree Craftsman/Gatherer and earlier architecture changes are not proof of completion against this redesign.

Sources: [Proposal](npc-conversation-redesign-proposal.md), [Detailed design](npc-conversation-redesign-detailed-design.md). The detailed design's confirmed decisions govern: per-NPC queues, no timer/turn negotiation expiry, and clarification before choosing among multiple supported actions.

## Module status

Check a module only after every packet task, acceptance criterion, test expectation and adjacent integration gate has evidence. An unchecked module can have completed local tasks; report those separately. Supporting packets are labelled to avoid inflating design-module completion.

- [ ] **[baseline](redesign-tasks/baseline.md)** — supporting workstream; not started; 0/3 tasks complete.
- [ ] **[contracts](redesign-tasks/contracts.md)** — design module; not started; 0/3 tasks complete.
- [ ] **[ports](redesign-tasks/ports.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[turns](redesign-tasks/turns.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[context](redesign-tasks/context.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[capabilities](redesign-tasks/capabilities.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[proposal](redesign-tasks/proposal.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[interactions](redesign-tasks/interactions.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[operations](redesign-tasks/operations.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[composition](redesign-tasks/composition.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[validation](redesign-tasks/validation.md)** — design module; not started; 0/3 tasks complete.
- [ ] **[fallback](redesign-tasks/fallback.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[canon](redesign-tasks/canon.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[memory](redesign-tasks/memory.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[finalization](redesign-tasks/finalization.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[lifecycle](redesign-tasks/lifecycle.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[diagnostics](redesign-tasks/diagnostics.md)** — design module; not started; 0/2 tasks complete.
- [ ] **[persistence-adapters](redesign-tasks/persistence-adapters.md)** — design module; not started; 0/4 tasks complete.
- [ ] **[game-adapters](redesign-tasks/game-adapters.md)** — design module; not started; 0/3 tasks complete.
- [ ] **[coordinator](redesign-tasks/coordinator.md)** — design module; not started; 0/3 tasks complete.
- [ ] **[api-adapter](redesign-tasks/api-adapter.md)** — design module; not started; 0/3 tasks complete.
- [ ] **[godot-adapters](redesign-tasks/godot-adapters.md)** — design module; not started; 0/3 tasks complete.
- [ ] **[evaluation-release](redesign-tasks/evaluation-release.md)** — supporting workstream; not started; 0/4 tasks complete.

## Completed work

- [x] Read proposal and detailed design and map all 21 module boundaries to task packets.
- [x] Create per-task acceptance criteria, test expectations, dependencies, sequencing and execution-record templates.
- [x] Create separate baseline/release workstreams and a master implementation checklist.
- [ ] Verify any runtime redesign module complete. No runtime acceptance was performed by this documentation task.

## In-progress work

No implementation task is assigned or in progress. Planning artifacts are ready for review and task assignment. When work starts, record `module/Txx`, owner, start date, next verification and evidence link here and in that packet; leave its completion checkbox unchecked until verified.

## Dependencies and sequencing

Task IDs in packets are the authoritative prerequisites. This order permits pure work against frozen contracts and delays production wiring until atomic adapters pass:

1. **Baseline and boundaries:** baseline/T01 → contracts/T01–T03 → ports/T01–T02. baseline/T02–T03 adds measurement and frozen evaluation fixtures; provider availability may block measurement without blocking pure contract work.
2. **Independent domain slices:** turns, context, capabilities/T01, proposal, interactions, canon, memory/T01 and diagnostics/T01 after their contract gates. operations follows interactions; composition follows renderer inventory; validation follows composition; fallback follows composition/profile data/validation. No concrete DB/provider needed for pure tests.
3. **Persistence and game boundary:** persistence-adapters/T01–T02 and game-adapters/T01 can proceed after contracts/ports. Then persistence-adapters/T03 → T04 and game-adapters/T02–T03. Finish capabilities/T02 conformance. Finalization/T01 can use doubles earlier; T02 requires the real publication store. Lifecycle and summary publication use atomic store ports.
4. **Application and transport:** coordinator/T01 uses fakes; T02 integrates receipt/recovery; T03 wires durable workers. API contract tests start with fakes after ports; API lifecycle/wiring follows lifecycle/coordinator. Godot request/presentation work follows frozen HTTP fixtures; shared revision application follows game/API integration.
5. **Adoption:** evaluation-release/T01 can begin with scripted/read-only outputs before wiring. T02 requires the complete adapter/client graph; T03 requires passing invariants and measured quality; T04 records cohort enablement and receipt-safe rollback. Do not enable action conversation before atomic receipt and retry gates pass.

Use direct dependency contracts rather than asking each worker to inspect the whole system. Coordinator and final release are the intentional cross-system tasks. Persistence owns SQL transactions/models/migrations; game adapters own game-service transaction/revision changes; API owns transport; Godot owns presentation/state application. Any shared-file edit must coordinate with its packet owner.

## Shared implementation rules

- Domain modules depend on contracts/ports and pure policies, never FastAPI, ORM sessions or concrete provider constructors. Reuse existing immutable values only through explicit semantic adapters; do not assume game_id/timeline_id equals scope/epoch.
- Only deterministic services authorize gameplay. Generated canon is narrative_only; player reports and interpretations retain attribution/uncertainty. Current state and authored constraints override stale memories/generated conflicts.
- Persist turn admission/order before context. Only earliest nonterminal turn per NPC can proceed; different NPCs may generate concurrently. Shared state rechecks serialize through the same writer boundary.
- At most one mutating operation per turn. Multiple supported requests require a choice and do not queue unselected commands. Quoted/hypothetical/negated/ambiguous requests cannot execute. Consent binds exact current question, answer span, terms and preconditions.
- Negotiations never expire by clock or turn count. Relevant precondition failure, explicit cancellation, clear and reset end them. Topic shifts suspend; bare yes cannot select a suspended request.
- One ordinary proposal attempt; action composition may add a call; one repair token shared across proposal-format and final-speech recovery. Persist attempts/repair consumption before dispatch. Summaries are outside the mandatory path.
- No provider, embedding or semantic-check call under DB transaction/lock. Operation effects and receipt commit atomically; final dialogue and accepted continuity commit atomically in a separate transaction. Writer order and fences apply on SQLite and PostgreSQL.
- Receipt recovery precedes execution; HTTP timeout does not discard admitted work. Only durable final dialogue is displayable; delivery retry returns identical final speech. Accepted activity is not completed activity.
- Validate whole assembled replies and fallbacks, including prose around exact slots. Critical quantities/outcomes remain server-rendered. No silent truncation; readable beats partition full dialogue. Semantic checks begin offline and never grant authority.
- Clear advances epoch and removes conversational payloads/drafts/results while preserving generated canon, authored identity and accepted mechanics/receipts; retain minimal invalidation tombstones. New game changes scope and resets run-specific state/canon. Every read/cache/async publish checks scope and applicable epoch/revisions.
- Keep the current 500-character request bound unless separately changed. Policy controls output/context/deadline/queue/lease/summary/retention limits consistently across provider, Pydantic, composer and client. Numeric shipping latency/length and model replacement are not selected by this plan.
- Run deterministic pure tests with fake clock/token counter/provider, adapter tests on isolated SQLite/PostgreSQL, and API/headless Godot lifecycle/retry tests. Mechanical invariants must all pass; live wording is scored, not exact-string asserted.
- Release quality: relevance ≥90%; mixed-concern coverage ≥90%; canon consistency ≥95%; healthy-provider fallback <5%; accidental identical consecutive replies <2% excluding purposeful mechanical repetition. Freeze ≥40 scenarios, generally 4–8 turns, across both NPCs, report counts/model/config and ordinary/action/repair p50/p95. Product acceptance of playable latency/readable limits remains a shipping gate.

## Blockers and risks

**Confirmed execution blockers:** None established by this documentation pass. Provider health, database availability and runtime readiness were not tested; do not treat them as passing.

- Baseline response-origin proportions, numeric policy values and playable latency/readable-length acceptance remain unmeasured or unaccepted for this redesign. Owner: baseline/T02–T03 and evaluation-release/T03.
- Existing inventory/encounter/quest services may commit internally; effects without atomic receipts break retries. Owner: game-adapters/T01 and persistence-adapters/T03.
- Every non-chat shared-state writer needs revision discipline; otherwise publication and delayed client snapshots can be wrong. Owner: game-adapters/T03 and godot-adapters/T03.
- SQLite does not enforce FOR UPDATE; writer-lock ordering, uniqueness and CAS need tests on both engines. Owner: persistence-adapters/T02–T04.
- Existing 240/300-character policies and client presentation can conflict. Owner: baseline/T01, composition/T01, proposal/T02 and godot-adapters/T02.
- Legacy histories/provenance and ID semantics cannot be relabelled automatically. Owner: contracts/T03 and persistence-adapters/T01.
- Concurrent in-flight generation, clear/reset, summary refresh and lease replacement can resurrect erased/stale state. Owner: turns, finalization, lifecycle and persistence-adapters race suites.
- Existing unrelated uncommitted changes are present. This plan does not modify or certify them; packet owners must inspect current neighboring contracts before implementation and avoid overwriting ongoing work.
- Shadow evaluation and rollback must never bypass mutation/receipt boundaries. Owner: evaluation-release/T01/T04 and coordinator/T03.

## Next recommended task

**[baseline/T01 — Inventory current contracts and mechanical authority](redesign-tasks/baseline.md#baselinet01-inventory-current-contracts-and-mechanical-authority).** It needs no implementation dependencies and identifies exact limit conflicts, existing rule owners, internal commits, revision writers and legacy mappings before contracts harden. Deliver the inventory and regression-command list with inspected paths; then start contracts/T01. Provider measurement can continue independently after baseline/T01.

## Progress update procedure

1. Claim a task in its packet execution table and the in-progress section here.
2. Implement only its bounded deliverable and direct prerequisites; report dependency conflicts rather than silently expanding scope.
3. Record acceptance and verification evidence, then check subtasks and task completion. Count only verified tasks in the module row.
4. When all module tasks and adjacent integration pass, check the entire module and update totals/completed work here. Keep quality and mechanical evidence separate.
5. Update blockers/risks and nominate the next unblocked task by exact ID. Do not carry historical test counts forward as fresh redesign evidence.
