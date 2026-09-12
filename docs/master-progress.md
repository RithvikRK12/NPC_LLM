# Master Progress

## Overall status

**Target architecture implementation underway; contracts.core / C01 complete.** The current game has working foundations, but none of the 59 target modules is complete against its new detailed-design contract.

Sources: [proposal](proposal.md), [detailed design](detailed-design.md), and confirmed decisions in [high-level design](high-level-design.md). The detailed design's **Role Conditioning → final Control Validation → FSEC** sequence controls where proposal examples disagree.

There are **52 named module rows** in the detailed design and **7 supporting packets** for common contracts, ports, persistence, HTTP transport, durable delivery, authored policy content and system integration. All have individual files; parent package directories are organizational boundaries, not additional executable modules to double-count.

- Target modules complete: **0/59**.
- Modules with inspected reusable foundations: **9** (still unchecked).
- New module implementation in progress: **contracts.core / C03 next; ports.core / P02; fuzzy.membership / T01**.
- Current verification: **95 backend tests passed** on 2026-09-12 (`PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests`, exit 0). This includes the 44-test baseline, C01/C02 (30), P01 (12), and membership T01 (9).
- Live semantic and Godot smoke checks were **not run** for this documentation-only planning change; obtain fresh evidence during their integration tasks.

## Tracking rules

- `[ ]` in the module list means the entire target module is incomplete; `[x]` requires all task acceptance/test criteria and its integration gate to pass.
- Each packet has task-level checklists. B01, where present, is completed baseline inspection only. Do not infer module completion from similar filenames or partial existing features.
- Mark tasks in progress in their Execution record with task ID/owner. A checkbox changes only when acceptance and test evidence are recorded.
- Assign one local task or coordinator slice at a time. Read that packet, its cited design section and direct contract fixtures; full-system reading is reserved for coordinator/system integration work.
- Start gates require common contracts; production dependency gates apply to final adjacent integration. Pure modules can proceed in parallel using fixed fixtures once shared contracts are stable.
- Shared schemas, ports and migrations have single owning packets to avoid conflicting edits. Runtime feedback through events does not create cyclic build dependencies.

## Completed work

- [x] `fuzzy.membership / T01`: local typed input/policy/output and rejection fixtures; 9 focused tests accepted on 2026-09-12.

- [x] `contracts.core / C02`: closed vocabularies, narrowing constraints and timing values; 17 focused tests accepted on 2026-09-12.

- [x] `ports.core / P01`: read/provider protocols, immutable vector records and injected clock/IDs; 12 focused tests accepted on 2026-09-12.

- [x] `contracts.core / C01`: immutable identity/envelope, position, revision and error values; golden fixtures and rejection tests accepted on 2026-09-12.

- [x] Proposal, high-level design and detailed design are present, with scope and control ordering clarified.
- [x] Per-module task packets and this progress inventory created; packet coverage and dependency/link checks passed.
- [x] Existing NPC chat separation, clickable inventory and ownership-checked exchanges identified as reusable foundation ([pipeline tests](../backend/tests/test_npc_pipeline.py)).
- [x] Existing authoritative bow progression, timed crafting and one-time reward identified ([bow service](../backend/app/services/quests/bow.py)).
- [x] Existing rule-based memory selection and semantic retrieval/indexing identified ([memory design](memory-selection.md), [semantic tests](../backend/tests/test_semantic_memory.py)).
- [x] Existing save/resume, position persistence and explicit game reset identified ([world API](../backend/app/api/routes/world.py), [Godot main](../frontend/godot/scripts/main.gd)).
- [x] Baseline backend regression suite passed: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 44 tests. Existing deprecation warnings remain; no test failures.

## In-progress work

- [ ] `ports.core / P02` — `/root/ports_p01`; application-owned transaction/CAS/delivery protocols and in-memory tests.
- Main Agent owns review and tracking.

## Module status

The following is a topological integration order, not a demand to serialize all coding. Files contain separate start and final-integration gates. Every module checkbox is deliberately unchecked.

### Dependency layer 0

- [ ] [contracts.core](tasks/contracts-core.md) — C01/C02 complete; C03 pending.

### Dependency layer 1

- [ ] [ports.core](tasks/ports-core.md) — P01 complete; P02 in progress, P03 and final contract gate pending.
- [ ] [domain.world.eligibility](tasks/domain-world-eligibility.md) — Planned.
- [ ] [perception.normalize](tasks/perception-normalize.md) — Planned.
- [ ] [memory.reconcile](tasks/memory-reconcile.md) — Planned.
- [ ] [reasoning.proposal_check](tasks/reasoning-proposal-check.md) — Planned.
- [ ] [state.merge](tasks/state-merge.md) — Planned.
- [ ] [fuzzy.membership](tasks/fuzzy-membership.md) — T01 complete; T02–T04 pending.
- [ ] [roles.permissions](tasks/roles-permissions.md) — Planned.
- [ ] [control.fallback](tasks/control-fallback.md) — Planned.
- [ ] [domain.quest.recovery](tasks/domain-quest-recovery.md) — Planned.
- [ ] [dialogue.compose](tasks/dialogue-compose.md) — Planned.
- [ ] [domain.world.inventory](tasks/domain-world-inventory.md) — Partial foundation; target incomplete.
- [ ] [memory.classify](tasks/memory-classify.md) — Partial foundation; target incomplete.
- [ ] [memory.lifecycle](tasks/memory-lifecycle.md) — Planned.
- [ ] [policy.registry](tasks/policy-registry.md) — Planned.
- [ ] [gateway.contract_codec](tasks/gateway-contract-codec.md) — Planned.

### Dependency layer 2

- [ ] [adapters.persistence](tasks/adapters-persistence.md) — Planned.
- [ ] [perception.relevance](tasks/perception-relevance.md) — Planned.
- [ ] [adapters.embedding_index](tasks/adapters-embedding-index.md) — Partial foundation; target incomplete.
- [ ] [adapters.model](tasks/adapters-model.md) — Partial foundation; target incomplete.
- [ ] [state.extract](tasks/state-extract.md) — Planned.
- [ ] [fuzzy.inference](tasks/fuzzy-inference.md) — Planned.
- [ ] [domain.world.observation](tasks/domain-world-observation.md) — Planned.
- [ ] [domain.quest.bow](tasks/domain-quest-bow.md) — Partial foundation; target incomplete.
- [ ] [dialogue.timing](tasks/dialogue-timing.md) — Planned.
- [ ] [memory.influence](tasks/memory-influence.md) — Planned.
- [ ] [observability.trace](tasks/observability-trace.md) — Planned.
- [ ] [gateway.command_client](tasks/gateway-command-client.md) — Planned.
- [ ] [controllers.lifecycle](tasks/controllers-lifecycle.md) — Planned.
- [ ] [policy.content](tasks/policy-content.md) — Planned; production content gate open.

### Dependency layer 3

- [ ] [application.interactions](tasks/application-interactions.md) — Planned.
- [ ] [perception.salience](tasks/perception-salience.md) — Planned.
- [ ] [memory.retrieve](tasks/memory-retrieve.md) — Partial foundation; target incomplete.
- [ ] [fuzzy.defuzzify](tasks/fuzzy-defuzzify.md) — Planned.
- [ ] [application.effects](tasks/application-effects.md) — Planned.
- [ ] [application.sessions](tasks/application-sessions.md) — Partial foundation; target incomplete.
- [ ] [memory.ingest](tasks/memory-ingest.md) — Planned.
- [ ] [controllers.navigation](tasks/controllers-navigation.md) — Planned.
- [ ] [controllers.animation](tasks/controllers-animation.md) — Planned.
- [ ] [controllers.interaction](tasks/controllers-interaction.md) — Planned.
- [ ] [ui.dialogue_presenter](tasks/ui-dialogue-presenter.md) — Partial foundation; target incomplete.
- [ ] [ui.world_presenter](tasks/ui-world-presenter.md) — Partial foundation; target incomplete.

### Dependency layer 4

- [ ] [perception.compose](tasks/perception-compose.md) — Planned.
- [ ] [roles.condition](tasks/roles-condition.md) — Planned.
- [ ] [application.outcomes](tasks/application-outcomes.md) — Planned.

### Dependency layer 5

- [ ] [reasoning.frame](tasks/reasoning-frame.md) — Planned.
- [ ] [control.continuity](tasks/control-continuity.md) — Planned.

### Dependency layer 6

- [ ] [reasoning.prompt](tasks/reasoning-prompt.md) — Planned.
- [ ] [control.validate](tasks/control-validate.md) — Planned.

### Dependency layer 7

- [ ] [application.approvals](tasks/application-approvals.md) — Planned.
- [ ] [fsec.eligibility](tasks/fsec-eligibility.md) — Planned.

### Dependency layer 8

- [ ] [fsec.utility](tasks/fsec-utility.md) — Planned.

### Dependency layer 9

- [ ] [fsec.mapping](tasks/fsec-mapping.md) — Planned.

### Dependency layer 10

- [ ] [application.commands](tasks/application-commands.md) — Planned.

### Dependency layer 11

- [ ] [application.decisions](tasks/application-decisions.md) — Planned.

### Dependency layer 12

- [ ] [adapters.http](tasks/adapters-http.md) — Planned.
- [ ] [application.delivery](tasks/application-delivery.md) — Planned.

### Dependency layer 13

- [ ] [integration.system](tasks/integration-system.md) — Planned.

## Sequencing and assignment guidance

1. Complete `contracts.core / C01` first, then C02/C03. Review envelopes, timeline/revision semantics and handoff ownership before parallel module changes.
2. Define `ports.core` and its conformance fakes. Independent pure-module contracts/fixtures can then be assigned without waiting for PostgreSQL or Godot.
3. Build pure world, perception, reasoning-check, state, fuzzy, role, control, dialogue and memory policies against fixtures. The module dependency layers determine when their adjacent integration tests become eligible.
4. Build persistence, provider/index, HTTP and Godot adapters against the same port/contract suites. Use disposable databases and test scenes; do not reset a player's save to run tests.
5. Wire application approval, effect, command, outcome and durable-delivery services only after their narrow port contracts exist. Do not leave transactions open over inference or movement.
6. Validate authored recovery content before enabling discretionary refusals in the playable game. Contract and synthetic reachability tests can proceed while content is pending.
7. Run `integration.system` slices separately. It is the intentional full-system exception; passing baseline tests alone cannot complete it.

## Blockers and risks

| Item | Impact | Owner / mitigation |
| --- | --- | --- |
| Envelopes exist; behaviour contracts and ports remain in progress | New modules can otherwise invent incompatible identities or source references. | `contracts.core`, then `ports.core`; next task below. |
| Specific favour scenarios and trade prices are not approved | Blocks production recovery-content activation, not generic offer/grant mechanics. | `policy.content / K02` requests owner-approved content; never invent prices or an alternate NPC. |
| Numerical tuning, performance objectives and retention periods are intentionally deferred | Cannot claim latency/scale targets or silently delete history. | `policy.content / K03` records deferral; `integration.system / I05` produces measurements. This is not a blocker to pure modules. |
| Existing helpers mix extraction, persistence and dialogue orchestration | Refactoring may duplicate effects or keep the model inside transactions. | Application and persistence packets enforce pure candidates, relevant revision checks and short commits. |
| Code supports the current demo, not target command/timeline contracts | Calling a baseline complete would hide missing replay/reset guarantees. | Keep target checkboxes unchecked until command, outcome and reset race tests pass. |
| Fuzzy and role transformations may double-apply deltas or undo validation | Implausible state and unauthorized commands. | Preserve one approved base; role before final validation; FSEC only narrows constraints. |
| Behavioural refusal can make the bow quest unwinnable | Both material and crafting access may be blocked. | Recovery reachability plus scoped grant; missing viable route makes a discretionary refusal ineligible without bypassing hard constraints. |
| Embeddings or FAISS cache can return stale or wrong-scope evidence | Incorrect NPC knowledge after corrections or restart. | Model/timeline/revision/lifecycle filters, authoritative priority channel and scoped no-embedding fallback. |
| SQLite tests do not prove PostgreSQL concurrency | Duplicate consumption or approval might survive unit tests. | `adapters.persistence` and system slices require disposable PostgreSQL multi-session evidence. |
| Multiple assignments edit shared contracts or adapters simultaneously | Integration conflicts and mismatched schemas. | One owner per shared packet; downstream work uses frozen fixtures and explicit contract changes. |

## Next recommended task

**`contracts.core / C03 — Publish cross-language fixture and ownership conventions`.**

C01/C02 are accepted. Freeze representative envelopes/commands, validate them with independent Python and Godot readers, reject incompatible versions, and document handoff ownership and version changes. Address observed Godot JSON integer precision before freeze. P02 and fuzzy membership T01 continue independently.

## Verification and handoff log

- Plan creation: read source designs, enumerated every named module, added only the seven supporting responsibilities already specified in the detailed design, and inspected existing source/test foundations.
- Baseline tests: 44 passed; no new architecture functionality claimed.
- Documentation checks: unique task IDs, complete named-module coverage, existing local links, acyclic integration dependencies and per-task acceptance/test/dependency fields.
- 2026-09-12: C01 assigned to `/root/c01_contracts`; Main Agent reviewed design and preserved existing changes. Fresh baseline: 44 tests passed, exit 0; existing Starlette/httpx deprecation warning remains.
- Environment: Godot 4.7.2 executable verified at `/private/tmp/npc-godot/Godot.app/Contents/MacOS/Godot` (project editor metadata); use headless disposable fixture checks for C03.
- Ready queue: C01 → C02 → C03; then ports.core P01. Pure module fixture tasks may proceed once the required common types are frozen, while their final integration gates remain pending.

- 2026-09-12 C01 accepted: four new contracts/fixture/test files listed in the packet; 13 focused tests and 57 combined backend tests passed (exit 0). Review corrected 2D positions and envelope-independent rejection values. No runtime integration claimed.

- C03 environment probe: Godot JSON rounds `9007199254740993` to `9007199254740992`; shared wire integer bounds or encoding must prevent precision loss before fixture freeze. Headless probe passed after log-directory permission approval.

- 2026-09-12 P01 accepted: `backend/app/ports/{__init__,read}.py` and `backend/tests/test_read_ports.py`; Main Agent reviewed and independently ran 12 focused tests, exit 0. Generic handoffs retain domain ownership. P02 next; final gate remains pending.

- 2026-09-12 C02 and fuzzy.membership T01 accepted after independent review and focused tests (17 and 9 respectively). Combined backend regression: 95 passed, exit 0; existing deprecation warning only.
