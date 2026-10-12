# Master Progress

## Overall status

**Target architecture implementation underway; contracts.core, ports.core, domain.world.eligibility, perception.normalize, memory.reconcile, reasoning.proposal_check, state.merge, fuzzy.membership, roles.permissions, control.fallback, domain.quest.recovery, dialogue.compose, domain.world.inventory, memory.classify, memory.lifecycle, policy.registry and gateway.contract_codec complete; adapters.persistence / T01 is next.** The current game has working foundations, and the common contract, port, world eligibility, perception normalization, memory reconciliation, proposal-check, state-merge, membership, role-permission, fallback, quest-recovery, dialogue composition, inventory planning, memory classification, lifecycle, policy registry and gateway codec layers are now complete against their detailed-design packets.

Sources: [proposal](proposal.md), [detailed design](detailed-design.md), and confirmed decisions in [high-level design](high-level-design.md). The detailed design's **Role Conditioning → final Control Validation → FSEC** sequence controls where proposal examples disagree.

There are **52 named module rows** in the detailed design and **7 supporting packets** for common contracts, ports, persistence, HTTP transport, durable delivery, authored policy content and system integration. All have individual files; parent package directories are organizational boundaries, not additional executable modules to double-count.

- Target modules complete: **17/59**.
- Modules with inspected reusable foundations: **9** (still unchecked).
- New module implementation in progress: **none; next ready task is adapters.persistence / T01**.
- Current verification: **361 backend tests passed** on 2026-10-12 (`PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests`, exit 0). This includes the 44-test baseline, C01/C02 (30), C03 Python checks (4), P01 (12), P03 write-port conformance checks (14), membership T04 (22), domain.world.eligibility T04 (26), perception.normalize T04 (20), memory.reconcile T04 (14), reasoning.proposal_check T04 (21), state.merge T04 (18), roles.permissions T04 (16), control.fallback T04 (14), domain.quest.recovery T04 (16), dialogue.compose T04 (16), domain.world.inventory T04 (14), memory.classify T04 (16), memory.lifecycle T04 (16), policy.registry T04 (14), and gateway.contract_codec T04 (14).
- Live semantic checks were **not run** for this pass. The C03 Godot headless fixture check is recorded below; obtain fresh semantic and full integration evidence during their integration tasks.

## Tracking rules

- `[ ]` in the module list means the entire target module is incomplete; `[x]` requires all task acceptance/test criteria and its integration gate to pass.
- Each packet has task-level checklists. B01, where present, is completed baseline inspection only. Do not infer module completion from similar filenames or partial existing features.
- Mark tasks in progress in their Execution record with task ID/owner. A checkbox changes only when acceptance and test evidence are recorded.
- Assign one local task or coordinator slice at a time. Read that packet, its cited design section and direct contract fixtures; full-system reading is reserved for coordinator/system integration work.
- Start gates require common contracts; production dependency gates apply to final adjacent integration. Pure modules can proceed in parallel using fixed fixtures once shared contracts are stable.
- Shared schemas, ports and migrations have single owning packets to avoid conflicting edits. Runtime feedback through events does not create cyclic build dependencies.

## Completed work

- [x] `fuzzy.membership / T02`: pure triangular/trapezoidal fuzzification accepted on 2026-09-13; configured labels, dimension order, candidate/input identity and policy version propagation are covered by 14 focused tests.

- [x] `fuzzy.membership / T03`: membership invariant hardening accepted on 2026-09-13; trapezoid shoulder endpoints, bounded degrees and typed configuration errors are covered by 19 focused tests.

- [x] `fuzzy.membership / T04`: adjacent handoff verification accepted on 2026-09-13; accepted C01 envelopes produce immutable `Memberships` for the documented `fuzzy.inference` input and mismatched timeline/version cases reject before output.

- [x] `domain.world.eligibility / T01`: local typed event/world/policy/result boundary and fixtures accepted on 2026-09-13; unsupported interaction kind, duplicate evidence fields, fake protocol execution and infrastructure-free import are covered by 8 focused tests.

- [x] `domain.world.eligibility / T02`: primary predicate evaluation accepted on 2026-09-29; target existence, accepted actor/target positions, range, visibility, permitted interaction type and reported-position distrust are covered by 15 focused tests.

- [x] `domain.world.eligibility / T03`: failure and invariant hardening accepted on 2026-09-29; forged ownership/location, missing evidence, absent remote support, missing entity fallback and distance boundary behavior are covered by 22 focused tests.

- [x] `domain.world.eligibility / T04`: adjacent handoff verification accepted on 2026-09-29; C01 envelope compatibility, immutable application handoff and mismatched policy version/timeline rejection are covered by 26 focused tests.

- [x] `perception.normalize / T01`: local typed observed/policy/normalized signal boundary and fixtures accepted on 2026-09-29; unsupported signal kind, strict timestamp/unit fields, fake protocol execution and infrastructure-free import are covered by 8 focused tests.

- [x] `perception.normalize / T02–T04`: normalization behaviour, invariant hardening and adjacent handoff accepted on 2026-09-29; canonical units, UTC timestamps, fact/claim/interpretation status, duplicate-source deduplication, conflict rejection, private visibility preservation and C01/relevance handoffs are covered by 20 focused tests.

- [x] `memory.reconcile / T01–T04`: memory reconciliation boundary, behaviour, invariant hardening and adjacent handoff accepted on 2026-09-29; correction links, supersede, retraction, conflict retention, no embedding-truth merge and C01/lifecycle handoffs are covered by 14 focused tests.

- [x] `reasoning.proposal_check / T01`: local typed raw proposal/snapshot/policy/result boundary and fixtures accepted on 2026-09-29; unsupported vocabulary, missing required fields, strict finite numeric values, duplicate references, fake protocol execution and infrastructure-free import are covered by 8 focused tests.

- [x] `reasoning.proposal_check / T02`: primary proposal validation accepted on 2026-09-29; exact decision construction, policy-allowed vocabularies, relative state fields, source snapshot identity, policy version and permitted snapshot grounding scopes are covered by 14 focused tests.

- [x] `reasoning.proposal_check / T03–T04`: proposal invariant hardening and adjacent handoff accepted on 2026-09-29; unknown fact/memory references, invalid scope, absolute/unsupported state fields, invalid numeric deltas, ungrounded delta sources and state-extraction policy/timeline handoff checks are covered by 21 focused tests.

- [x] `state.merge / T01–T04`: state merge boundary, precedence behaviour, invariant hardening and adjacent handoff accepted on 2026-10-12; explicit source precedence, stable effect identity, duplicate influence/proposal rejection, unknown relationship subjects, no automatic summing and state.extract policy/timeline handoffs are covered by 18 focused tests.

- [x] `roles.permissions / T01–T04`: role permission boundary, primary evaluation, invariant hardening and adjacent handoff accepted on 2026-10-12; role allowlists, denied actions, target restrictions, workshop/material prerequisites, duties, cooperation grants, unknown roles and forbidden violence are covered by 16 focused tests.

- [x] `control.fallback / T01–T04`: safe fallback boundary, zero-effect selection, invariant hardening and adjacent handoff accepted on 2026-10-12; declared safe responses, no model calls, no fabricated targets/evidence/rewards, unsupported fallback rejection and fallback loop bounds are covered by 14 focused tests.

- [x] `domain.quest.recovery / T01–T04`: quest recovery boundary, same-NPC offer selection, invariant hardening and adjacent handoff accepted on 2026-10-12; authored favour/trade routes, attainable prerequisites, verified completion predicates, scoped grants, no circular routes, no claim-only completion and no viable route failures are covered by 16 focused tests.

- [x] `dialogue.compose / T01–T04`: dialogue composition boundary, authored-template outcome wording, invariant hardening and adjacent handoff accepted on 2026-10-12; verified event matching, bounded expression/commitment wording, water-transfer/reward mismatch rejection, unverified references, safe ambiguous-success fallback and dialogue.timing policy/timeline handoffs are covered by 16 focused tests.

- [x] `domain.world.inventory / T01–T04`: inventory planning boundary, transfer/consumption effect generation, invariant hardening and adjacent handoff accepted on 2026-10-12; catalog references, balanced owner quantities, no persistence, unknown item, absent ownership, insufficient quantity, stable effect identity and application.effects policy/timeline handoffs are covered by 14 focused tests.

- [x] `memory.classify / T01–T04`: memory classification boundary, approved-conversation/verified-event behaviour, invariant hardening and adjacent handoff accepted on 2026-10-12; authoritative event facts, reported player claims, excluded greetings, rejected/provider-failure outputs and memory.lifecycle policy/timeline handoffs are covered by 16 focused tests.

- [x] `memory.lifecycle / T01–T04`: memory lifecycle boundary, retention review behaviour, invariant hardening and adjacent handoff accepted on 2026-10-12; retrieval expiry, archival, salience decay, protected provenance, no implicit deletion and memory.retrieve policy/timeline handoffs are covered by 16 focused tests.

- [x] `policy.registry / T01–T04`: policy bundle boundary, version loading, invariant hardening and adjacent handoff accepted on 2026-10-12; profile, bounds, fuzzy, fallback, mapping and recovery-route policy validation plus frozen-version gateway.contract_codec handoff are covered by 14 focused tests.

- [x] `gateway.contract_codec / T01–T04`: command codec boundary, command/display/outcome decoding, invariant hardening and adjacent handoff accepted on 2026-10-12; shared Godot fixture decoding, schema/timeline/vocabulary/parameter validation and controllers.lifecycle handoff are covered by 14 focused tests plus a headless Godot fixture smoke.

- [x] `ports.core / P03`: reusable write-port conformance suite accepted on 2026-09-13; deterministic in-memory fake passes unchanged and broken fakes demonstrate failure detection for premature commit, cursor skipping and wrong error mapping.

- [x] `fuzzy.membership / T01`: local typed input/policy/output and rejection fixtures; 9 focused tests accepted on 2026-09-12.

- [x] `ports.core / P02`: application-owned write transactions, CAS/idempotency contracts, delivery cursors and deterministic in-memory fake; 11 focused tests accepted on 2026-09-13.

- [x] `contracts.core / C03`: shared cross-language fixture corpus and independent Python/Godot reader checks accepted on 2026-09-13.

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

- Main Agent owns review and tracking.

## Module status

The following is a topological integration order, not a demand to serialize all coding. Files contain separate start and final-integration gates. Every module checkbox is deliberately unchecked.

### Dependency layer 0

- [x] [contracts.core](tasks/contracts-core.md) — C01/C02/C03 complete; cross-language fixture gate passed.

### Dependency layer 1

- [x] [ports.core](tasks/ports-core.md) — P01/P02/P03 complete; direct contracts gate passed.
- [x] [domain.world.eligibility](tasks/domain-world-eligibility.md) — T01–T04 complete; direct contracts gate passed.
- [x] [perception.normalize](tasks/perception-normalize.md) — T01–T04 complete; direct contracts gate passed.
- [x] [memory.reconcile](tasks/memory-reconcile.md) — T01–T04 complete; direct contracts gate passed.
- [x] [reasoning.proposal_check](tasks/reasoning-proposal-check.md) — T01–T04 complete; direct contracts gate passed.
- [x] [state.merge](tasks/state-merge.md) — T01–T04 complete; direct contracts gate passed.
- [x] [fuzzy.membership](tasks/fuzzy-membership.md) — T01–T04 complete; direct contracts gate passed.
- [x] [roles.permissions](tasks/roles-permissions.md) — T01–T04 complete; direct contracts gate passed.
- [x] [control.fallback](tasks/control-fallback.md) — T01–T04 complete; direct contracts gate passed.
- [x] [domain.quest.recovery](tasks/domain-quest-recovery.md) — T01–T04 complete; direct contracts gate passed.
- [x] [dialogue.compose](tasks/dialogue-compose.md) — T01–T04 complete; direct contracts gate passed.
- [x] [domain.world.inventory](tasks/domain-world-inventory.md) — B01 and T01–T04 complete; direct contracts gate passed.
- [x] [memory.classify](tasks/memory-classify.md) — B01 and T01–T04 complete; direct contracts gate passed.
- [x] [memory.lifecycle](tasks/memory-lifecycle.md) — T01–T04 complete; direct contracts gate passed.
- [x] [policy.registry](tasks/policy-registry.md) — T01–T04 complete; direct contracts gate passed.
- [x] [gateway.contract_codec](tasks/gateway-contract-codec.md) — T01–T04 complete; direct contracts gate passed.

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
| Port conformance is frozen; no production persistence adapter is registered yet | New adapter work must still prove PostgreSQL concurrency and durable delivery against the reusable suite. | `adapters.persistence`; keep the P03 suite unchanged for adapter registration. |
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

**`adapters.persistence / T01 — Define the module contract and fixture boundary`.**

C01/C02/C03 and ports.core are accepted and `gateway.contract_codec` is complete. Define the persistence adapter contract boundary and disposable-store fixtures without changing the pure domain modules.

## Verification and handoff log

- Plan creation: read source designs, enumerated every named module, added only the seven supporting responsibilities already specified in the detailed design, and inspected existing source/test foundations.
- Baseline tests: 44 passed; no new architecture functionality claimed.
- Documentation checks: unique task IDs, complete named-module coverage, existing local links, acyclic integration dependencies and per-task acceptance/test/dependency fields.
- 2026-09-12: C01 assigned to `/root/c01_contracts`; Main Agent reviewed design and preserved existing changes. Fresh baseline: 44 tests passed, exit 0; existing Starlette/httpx deprecation warning remains.
- Environment: Godot 4.7.2 executable verified at `/private/tmp/npc-godot/Godot.app/Contents/MacOS/Godot` (project editor metadata); use headless disposable fixture checks for C03.
- Ready queue after domain.world.eligibility T01 acceptance: domain.world.eligibility T02. Pure module fixture tasks may proceed once their required common types are frozen, while their final integration gates remain pending.

- 2026-09-12 C01 accepted: four new contracts/fixture/test files listed in the packet; 13 focused tests and 57 combined backend tests passed (exit 0). Review corrected 2D positions and envelope-independent rejection values. No runtime integration claimed.

- C03 environment probe: Godot JSON rounds `9007199254740993` to `9007199254740992`; shared wire integer bounds or encoding must prevent precision loss before fixture freeze. Headless probe passed after log-directory permission approval.

- 2026-09-12 P01 accepted: `backend/app/ports/{__init__,read}.py` and `backend/tests/test_read_ports.py`; Main Agent reviewed and independently ran 12 focused tests, exit 0. Generic handoffs retain domain ownership. P02 next; final gate remains pending.

- 2026-09-12 C02 and fuzzy.membership T01 accepted after independent review and focused tests (17 and 9 respectively). Combined backend regression: 95 passed, exit 0; existing deprecation warning only.
- 2026-09-13 C03 accepted: Python shared-fixture checks passed (4); independent Godot 4.7.2 headless reader passed 4 valid and 3 invalid checks. Revision wire values are bounded to `2^53-1` for cross-language JSON precision.
- 2026-09-13 P02 accepted: `backend/app/ports/{__init__,fakes,write}.py` and `backend/tests/test_write_ports.py`; focused write-port suite passed 11 tests, exit 0. Short application-owned transactions, rollback staging, relevant-revision CAS, exact retry receipts, changed-payload conflicts and durable cursor semantics are covered by the deterministic fake. Production PostgreSQL concurrency remains a later adapter gate.
- 2026-09-13 P03 accepted: `backend/tests/port_conformance.py` and `backend/tests/test_write_ports.py`; focused write-port conformance passed 14 tests, exit 0. The same reusable suite now runs against the deterministic in-memory fake and is ready for production adapter subclasses. Broken fakes demonstrate detection for premature commit visibility, cursor skipping and wrong INVALID_CONTRACT mapping.
- 2026-09-13 fuzzy.membership T02 accepted: `backend/app/domain/fuzzy/membership.py`, `backend/tests/test_fuzzy_membership.py` and `backend/tests/fixtures/fuzzy/membership-t02-{triangle,trapezoid,branches}.json`; focused membership suite passed 14 tests, exit 0. Full backend regression passed 118 tests, exit 0. Primary behaviour evaluates overlapping triangular/trapezoidal functions over normalized inputs and preserves configured label/version identities; T03 owns malformed-policy and endpoint hardening.
- 2026-09-13 fuzzy.membership T03 accepted: `backend/app/domain/fuzzy/membership.py` and `backend/tests/test_fuzzy_membership.py`; focused membership suite passed 19 tests, exit 0. Full backend regression passed 123 tests, exit 0. Trapezoid shoulder endpoints are included, malformed policy points and missing dimensions return typed `INVALID_CONTRACT` values, and emitted degrees remain bounded.
- 2026-09-13 fuzzy.membership T04 accepted: `backend/app/domain/fuzzy/membership.py` and `backend/tests/test_fuzzy_membership.py`; focused membership suite passed 22 tests, exit 0. Full backend regression passed 126 tests, exit 0. Accepted C01-style envelopes produce immutable `Memberships` suitable for the documented `fuzzy.inference` handoff; mismatched policy timeline/version rejects with typed `INVALID_CONTRACT`; a test-local inference handoff rejects old timelines with `OLD_TIMELINE`. No runtime, full-game or live semantic check was required for this pure module gate.
- 2026-09-13 domain.world.eligibility T01 accepted: `backend/app/domain/world/{__init__,eligibility}.py`, `backend/tests/test_world_eligibility.py` and `backend/tests/fixtures/world/eligibility-t01-{valid,rejected}.json`; focused eligibility suite passed 8 tests, exit 0. Full backend regression passed 134 tests, exit 0. The module exposes immutable event/world/policy/result handoffs over C01 envelopes and values only; no ORM, HTTP, Godot node or live world service dependency is introduced. T02 owns predicate evaluation.
- 2026-09-29 domain.world.eligibility T02 accepted: `backend/app/domain/world/eligibility.py`, `backend/tests/test_world_eligibility.py` and `backend/tests/fixtures/world/eligibility-t01-valid.json`; focused eligibility suite passed 15 tests, exit 0. Full backend regression passed 141 tests, exit 0. The pure checker now emits stable named predicate results for target existence, accepted actor/target positions, range, visibility and permitted interaction type from the immutable `WorldView`; reported client position remains diagnostic and is not used for range. T03 owns forged evidence, missing evidence and unsupported remote interaction hardening.
- 2026-09-29 domain.world.eligibility T03 accepted: `backend/app/domain/world/eligibility.py` and `backend/tests/test_world_eligibility.py`; focused eligibility suite passed 22 tests, exit 0. Full backend regression passed 148 tests, exit 0. Forged actor/location evidence, missing actor/target evidence and policy mismatch return typed `INVALID_CONTRACT` values; missing target, no supported remote channel and range boundary failures remain ineligible predicate fallbacks with no effects. T04 owns adjacent contract handoff verification.
- 2026-09-29 domain.world.eligibility T04 accepted: `backend/app/domain/world/eligibility.py` and `backend/tests/test_world_eligibility.py`; focused eligibility suite passed 26 tests, exit 0. Full backend regression passed 152 tests, exit 0. Eligibility results validate against C01 envelope fields without schema changes, test-local application handoff consumes immutable identity/status/policy values, and mismatched policy version/timeline returns typed `INVALID_CONTRACT`. No live runtime or engine adapter integration claimed by this pure module gate. Module marked complete.
- 2026-09-29 perception.normalize T01 accepted: `backend/app/perception/{__init__,normalize}.py`, `backend/tests/test_perception_normalize.py` and `backend/tests/fixtures/perception/normalize-t01-{valid,rejected}.json`; focused normalization contract suite passed 8 tests, exit 0. Full backend regression passed 160 tests, exit 0. The module exposes immutable observed signal, normalization policy and normalized signal handoffs over C01 envelopes and values only; no ORM, HTTP, Godot node or live perception service dependency is introduced. T02 owns normalization behaviour.
- 2026-09-29 perception.normalize T02–T04 accepted: `backend/app/perception/normalize.py` and `backend/tests/test_perception_normalize.py`; focused normalization suite passed 20 tests, exit 0. Full backend regression passed 172 tests, exit 0. The pure normalizer emits immutable normalized signals with canonical units, finite values, UTC timestamps and explicit fact/claim/interpretation status; identical source duplicates deduplicate, conflicting duplicates and noncanonical units reject with typed `INVALID_CONTRACT`, private visibility is preserved, and C01 envelope plus test-local relevance handoff checks pass. No live perception service or runtime adapter integration claimed by this pure module gate. Module marked complete.
- 2026-09-29 memory.reconcile T01–T04 accepted: `backend/app/memory/{__init__,reconcile}.py`, `backend/tests/test_memory_reconcile.py` and `backend/tests/fixtures/memory/reconcile-t01-{valid,rejected}.json`; focused reconciliation suite passed 14 tests, exit 0. Full backend regression passed 186 tests, exit 0. The pure planner emits correction/supersede/retraction/conflict/retain links from typed evidence while retaining historical records; mismatched timeline/policy evidence and non-authoritative fact/retraction claims reject with typed `INVALID_CONTRACT`; embedding-like similarity does not merge different predicates. C01 envelope plus test-local lifecycle handoff checks pass. No repository, embedding index or live memory service integration claimed by this pure module gate. Module marked complete.
- 2026-09-29 reasoning.proposal_check T01 accepted: `backend/app/reasoning/{__init__,proposal_check}.py`, `backend/tests/test_reasoning_proposal_check.py` and `backend/tests/fixtures/reasoning/proposal-check-t01-{valid,rejected}.json`; focused proposal-check contract suite passed 8 tests, exit 0. Full backend regression passed 194 tests, exit 0. The pure boundary exposes immutable raw proposal, snapshot, proposal policy, grounding reference, relative state delta and decision proposal values over C01/C02 contracts; unsupported vocabulary, missing fields, strict finite numeric values, duplicate references, fake protocol execution and infrastructure-free import are covered. Primary validation behaviour, invariant hardening and adjacent handoff remain T02-T04; module stays unchecked.
- 2026-09-29 reasoning.proposal_check T02 accepted: `backend/app/reasoning/proposal_check.py` and `backend/tests/test_reasoning_proposal_check.py`; focused proposal-check suite passed 14 tests, exit 0. Full backend regression passed 200 tests, exit 0. The validator emits exact immutable decision proposals from accepted raw proposals, requires exact snapshot identity and matching policy version, enforces policy-allowed intents/actions/dialogue budget/state-delta fields, accepts grounding across fact/memory/observation/constraint snapshot scopes and returns typed errors without repairing invalid proposals. T03 owns invariant hardening coverage; module remains unchecked.
- 2026-09-29 reasoning.proposal_check T03–T04 accepted: `backend/tests/test_reasoning_proposal_check.py`; focused proposal-check suite passed 21 tests, exit 0. Full backend regression passed 207 tests, exit 0. Unknown fact/memory references reject as `UNGROUNDED_REFERENCE`; invalid grounding scope, unsupported/absolute state fields and non-finite/out-of-range numeric deltas reject at the contract boundary; ungrounded delta sources and disallowed policy state fields return typed errors without inventing evidence or repairing proposals. A test-local state-extraction handoff consumes immutable decision proposal identity, policy and state deltas and rejects mismatched policy or timeline. No model provider, prompt renderer, application orchestration or runtime state extraction integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 state.merge T01–T04 accepted: `backend/app/state/{__init__,merge}.py`, `backend/tests/test_state_merge.py` and `backend/tests/fixtures/state/merge-t01-{valid,rejected}.json`; focused state-merge suite passed 18 tests, exit 0. Full backend regression passed 225 tests, exit 0. The pure merger emits one accepted relative change per dimension/subject using explicit source precedence and stable effect identity, rejects duplicate memory influence/proposal effects, unknown relationship subjects, mismatched timeline/policy evidence, unsupported dimensions and invalid numeric deltas, and proves a test-local state.extract handoff with policy/timeline mismatch checks. No persistence, model provider, application orchestration or runtime state.extract integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 roles.permissions T01–T04 accepted: `backend/app/roles/{__init__,permissions}.py`, `backend/tests/test_roles_permissions.py` and `backend/tests/fixtures/roles/permissions-t01-{valid,rejected}.json`; focused roles-permissions suite passed 16 tests, exit 0. Full backend regression passed 241 tests, exit 0. The pure evaluator allows and denies role proposals from immutable proposal/world/profile values, covers allowlists, denied actions, target restrictions, workshop/material prerequisites, duties and active grants, denies unknown roles, forbidden violence and grant-contradicting ordinary refusals, and proves a test-local roles.condition handoff with policy/timeline mismatch checks. No persistence, model provider, application orchestration or runtime role-conditioning integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 control.fallback T01–T04 accepted: `backend/app/control/{__init__,fallback}.py`, `backend/tests/test_control_fallback.py` and `backend/tests/fixtures/control/fallback-t01-{valid,rejected}.json`; focused control-fallback suite passed 14 tests, exit 0. Full backend regression passed 255 tests, exit 0. The pure builder selects declared zero-effect speak/idle fallback candidates from trusted evidence without model calls, rejects role-incompatible, effect-bearing, reward-like, unsupported, unavailable-target, missing-evidence and loop-limit fallbacks, and proves a test-local control.validate handoff with policy/timeline mismatch checks. No model provider, persistence, application orchestration or runtime control-validation integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 domain.quest.recovery T01–T04 accepted: `backend/app/domain/quest/{__init__,recovery}.py`, `backend/tests/test_quest_recovery.py` and `backend/tests/fixtures/quest/recovery-t01-{valid,rejected}.json`; focused quest-recovery suite passed 16 tests, exit 0. Full backend regression passed 271 tests, exit 0. The pure selector emits same-NPC authored favour/trade offers with scoped cooperation grants, checks attainable prerequisites and verified completion predicates, rejects circular, wrong-NPC, unavailable, consumed, completed, expired and no-viable routes, ignores player-claim-only completion, and proves a test-local domain.quest.bow handoff with policy/timeline mismatch checks. No persistence, HTTP, production favour/trade content activation or application transaction integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 dialogue.compose T01–T04 accepted: `backend/app/dialogue/{__init__,compose}.py`, `backend/tests/test_dialogue_compose.py` and `backend/tests/fixtures/dialogue/compose-t01-{valid,rejected}.json`; focused dialogue-compose suite passed 16 tests, exit 0. Full backend regression passed 287 tests, exit 0. The pure composer emits authored-template outcome dialogue from typed verified events, preserves bounded expression/commitment wording, rejects mismatched policy/timeline evidence, prevents water-transfer events from announcing reward text, rejects unverified outcome references and falls back to a safe line for ambiguous success claims. A test-local dialogue.timing handoff consumes immutable dialogue event identity, policy and verified outcome values and rejects mismatched policy or timeline. No model provider, persistence, HTTP, Godot node or runtime dialogue timing integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 domain.world.inventory T01–T04 accepted: `backend/app/domain/world/inventory.py`, `backend/tests/test_world_inventory.py` and `backend/tests/fixtures/world/inventory-t01-{valid,rejected}.json`; focused inventory suite passed 14 tests, exit 0. Full backend regression passed 301 tests, exit 0. The pure planner emits immutable transfer and consumption effects with stable effect identity, catalog grounding, balanced owner deltas and expected revisions; unknown items, absent ownership, insufficient quantity, stale ownership revisions and repeated effect identities return typed errors before output. A test-local application.effects handoff consumes immutable effect identity, owner deltas, expected revisions and policy and rejects mismatched policy or timeline. No persistence, HTTP, Godot node, crafting, quest reward or runtime application commit integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 memory.classify T01–T04 accepted: `backend/app/memory/classify.py`, `backend/tests/test_memory_classify.py` and `backend/tests/fixtures/memory/classify-t01-{valid,rejected}.json`; focused memory-classify suite passed 16 tests, exit 0. Full backend regression passed 317 tests, exit 0. The pure classifier adapts existing importance rules to typed approved conversations and verified events, keeps player statements as reported claims, retains verified transfers and quest events as authoritative facts independent of emotion labels, and excludes greetings, routine questions, rejected outputs and provider failures from durable memory. A test-local memory.lifecycle handoff consumes important immutable memory decisions and rejects mismatched policy or timeline. No persistence, embedding index, model provider or runtime lifecycle integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 memory.lifecycle T01–T04 accepted: `backend/app/memory/lifecycle.py`, `backend/tests/test_memory_lifecycle.py` and `backend/tests/fixtures/memory/lifecycle-t01-{valid,rejected}.json`; focused memory-lifecycle suite passed 16 tests, exit 0. Full backend regression passed 333 tests, exit 0. The pure reviewer emits mutation plans for retrieval expiry, archival, salience decay, deletion and protected provenance without writing records, keeps salience decay separate from lifecycle state, archives protected authoritative provenance instead of deleting it, and performs no deletion when retention is unspecified or deletion is disabled. A test-local memory.retrieve handoff consumes lifecycle visibility/archive outcomes and rejects mismatched policy or timeline. No persistence, embedding index, model provider or runtime retrieval integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 policy.registry T01–T04 accepted: `backend/app/policy/{__init__,registry}.py`, `backend/tests/test_policy_registry.py` and `backend/tests/fixtures/policy/registry-t01-{valid,rejected}.json`; focused policy-registry suite passed 14 tests, exit 0. Full backend regression passed 347 tests, exit 0. The pure loader validates one immutable decision bundle from requested policy versions and a supplied catalog, covering role/profile actions, bounds, fuzzy memberships, safe fallbacks, command mappings and recovery routes; missing policies, stale versions, unknown actions, inconsistent bounds, unsafe fallbacks, invalid memberships and incomplete routes return typed errors before output. A test-local gateway.contract_codec handoff consumes the frozen bundle identity and policy versions and rejects mismatched timeline evidence. No configuration storage, HTTP route, application orchestration or runtime codec integration claimed by this pure module gate. Module marked complete.
- 2026-10-12 gateway.contract_codec T01–T04 accepted: `backend/app/gateway/{__init__,contract_codec}.py`, `backend/tests/test_gateway_contract_codec.py`, `backend/tests/fixtures/gateway/contract-codec-t01-{valid,rejected}.json` and `frontend/godot/tests/gateway_contract_codec_smoke.gd`; focused gateway-codec suite passed 14 tests, exit 0. Full backend regression passed 361 tests, exit 0. Headless Godot fixture smoke passed with `/opt/homebrew/bin/godot --headless --path frontend/godot --script res://tests/gateway_contract_codec_smoke.gd` despite local log/certificate warnings. The pure codec decodes command, display and outcome transport records, rejects unsupported schema versions, old timelines, unknown actions, missing targets/parameters and non-finite values, and preserves command IDs plus backend parameter ranges without applying gameplay changes. A test-local controllers.lifecycle handoff consumes immutable command identity, kind, target and controller revision and rejects mismatched timeline evidence. No HTTP route, controller scheduling, gameplay mutation or runtime controller integration claimed by this pure module gate. Module marked complete.
