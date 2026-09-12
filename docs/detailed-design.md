# Detailed Design

## 1 Scope, precedence and status

This is the target module design for [proposal.md](proposal.md) and [high-level-design.md](high-level-design.md). Module paths, signatures and records below are proposed contracts, not a statement that they already exist. This document contains no implementation backlog.

Confirmed architecture decisions take precedence over conflicting sequences in the proposal:

- Local single-player Godot and Python backend; the backend verifies controller reports. One persistent playable save, not multiplayer accounts or a trusted remote simulation server.
- Perception → reasoning → proposal checks → state extraction → fuzzy inference → role conditioning → final control validation → FSEC → controller → verified outcomes → memory.
- Approved internal state changes persist at final approval. Outcome-dependent changes require a verified outcome.
- Village NPC behaviour and the bow quest are required. Economy, factions, combat and a generalized quest engine remain extension points.
- Normal launch resumes saved state. Explicit Restart Game resets playable state and memory and invalidates prior work.
- Numeric performance targets and retention periods remain intentionally deferred for local evaluation.

**New gameplay clarification:** NPC behaviour may refuse or delay required quest help, provided an alternate way to complete the quest remains available. The owner selected a favour or trade that restores cooperation with the same NPC. Recovery is part of the bow-quest interaction, not an extra NPC, self-service recipe or generalized quest subsystem. Specific favour content and prices remain authored policy data rather than assumed requirements.

## 2 Dependency rules and module layout

Use immutable typed records between modules. Domain transformations receive values, not ORM entities, HTTP requests or Godot nodes. Dependencies point from orchestration/adapters toward domain contracts, never from a pure domain rule toward infrastructure.

```text
backend/app/
  contracts/          shared identities, envelopes, typed handoffs, errors
  application/        interaction coordination, decision flow, outcome flow, recovery
  domain/
    world/            eligibility, observation rules, authoritative effects
    perception/       normalization, filtering, salience, snapshot composition
    reasoning/        decision frame, prompt composition, proposal checks
    state/            extraction, state-delta merge policy
    fuzzy/            membership, inference, defuzzification
    roles/            permissions and modifiers
    control/          semantic constraints and temporal continuity
    fsec/             eligibility, utility scoring, parameter mapping
    dialogue/         timing and outcome grounding
    quest/            bow progression and recovery-route eligibility
    memory/           classification, reconciliation, retrieval policy, influence
  ports/              repository, unit-of-work, model, embedding, index, clock ports
  adapters/           FastAPI, SQLAlchemy, Ollama/compatible provider, FAISS
  policy/             versioned content loading and validation
  observability/      trace and metric sinks

frontend/godot/scripts/
  gateway/            contract decoding, polling, acknowledgement, reconciliation
  controllers/        command state machine, navigation and animation adapters
  ui/                 chat, quest, inventory and save/restart presentation
```

These names define logical ownership; they do not require moving every existing file. Existing memory, inventory and bow services can supply adapters while the target contracts become the integration boundary.

**Independent testability rules:** inject Clock, ID source, policies and infrastructure ports; return explicit decisions/effects; avoid hidden settings access in domain functions. Only application services may open a unit of work. A repository never calls an LLM; a model adapter never loads game state; a controller never writes inventory directly. Shared contracts contain no executable domain policy.

## 3 Common public contract conventions

Signatures use Python-like notation to specify language-neutral contracts. `Result[T]` is either a successful value or a typed `DomainError`; an exception is not a normal rejection decision. `Sequence` inputs are immutable at the boundary. Interfaces returning awaitable work use `async`; domain calculations remain synchronous and pure.

### 3.1 Identity and version envelope

Every persistent or transported handoff carries:

| Field | Meaning and validation |
| --- | --- |
| `schema_version` | Explicit supported contract version. Unknown incompatible versions are rejected, not partially decoded. |
| `record_id`, `trace_id`, `causation_id` | Stable record identity, correlated decision trace and direct source record. IDs are server-created except designated client event IDs. |
| `game_id`, `timeline_id` | Scope to the local save and its current restart generation. Timeline mismatch invalidates requests, commands, callbacks and memory jobs. |
| `npc_id`, optional `actor_id` / `target_id` | Stable entity references resolved by the backend. Display names are not identifiers. |
| `created_at` | Server UTC timestamp. Client timestamps are separate observations, never authoritative deadlines. |
| `source_ids`, `policy_versions` | Evidence and configuration lineage; required references must belong to this decision and knowledge scope. |

A `RevisionSet` contains the NPC state revision plus relevant quest, inventory, relationship, policy and controller revisions. It does not invalidate a decision merely because an unrelated NPC moved. Spatial predicates are re-evaluated using fresh accepted positions at command/effect boundaries. The approved state revision is distinct from the pre-decision revision so the decision's own state commit does not invalidate its command.

Client retries reuse the same event ID and canonical payload digest. A duplicate with the same content returns the original receipt; reuse with different content returns `IDEMPOTENCY_CONFLICT`. Domain-effect uniqueness is enforced in persistence, not only in a process cache.

### 3.2 Shared value types

- `Position`: finite coordinates, area ID and accepted spatial revision. Distance units are Godot world units; accepted position is separate from raw reported position.
- `NumericChange`: dimension, previous value, proposed delta, conditioned delta, candidate value, source ID and application timing. Emotion/relationship absolute values use the canonical `[0, 1]` range; narrower policy bounds apply afterward.
- `GroundingRef`: fact/event/memory ID, source category, epistemic status, visibility scope, observed time, confidence and optional expiry.
- `ConstraintSet`: allowed behaviours, target predicates, parameter intervals, timing constraints and mandatory evidence. Later stages may narrow it, not widen it.
- `Diagnostic`: stable code, originating module, source IDs, affected field, before/after values and a concise explanation. Player-facing text is separate.
- `DomainError`: code, stage, retryability, source IDs and safe public message. Internal exceptions and secrets are excluded from transport.

### 3.3 Behaviour and execution vocabularies

Intent, activity, expression and engine command are separate closed vocabularies. Initial intent categories cover helping, requesting purpose, setting a boundary, declining/deferment, seeking information and ordinary conversation. An item or quest operation is a typed game request, not a free-form LLM action name.

Supported controller kinds are `idle`, `speak`, `face_target`, `move_to`, `approach_target`, `retreat_from_target`, `interact` and `play_animation`. An NPC capability record declares its supported subset. Unknown commands are rejected; unavailable movement on a stationary NPC yields a capability failure rather than a fictitious movement result. Enum expansion requires compatible backend and controller contracts.

## 4 Module responsibilities, interfaces and unit tests

Each row is a small logical module with a primary responsibility. Stateful application modules orchestrate ports; pure modules receive all dependencies as input. The named unit tests use controlled fixtures and do not need a running model, database or Godot unless explicitly stated.

### 4.1 Application, world and quest modules

| Module | Responsibility and public interface | Dependencies | Independent tests |
| --- | --- | --- | --- |
| `application.interactions` | `submit(InteractionEvent) -> Result[InteractionReceipt]`; deduplicate, validate timeline and route dialogue or explicit game requests. | Session/receipt repository, eligibility port, decision dispatcher. | Duplicate retry, changed payload, stale timeline, unknown target and ineligible interaction. |
| `application.decisions` | `async decide(DecisionTrigger) -> DecisionOutcome`; assemble the ordered pipeline and route rejection, approval and command scheduling. Does not calculate domain policy. | Read/commit ports and the pure modules below; model provider. | Stage ordering, stop on rejection, no DB transaction during inference, stale approval, interrupted decision. |
| `domain.world.eligibility` | `check(InteractionEvent, WorldView, InteractionPolicy) -> EligibilityResult`; verify target, range, visibility and operation eligibility. | Values only. | Forged ownership/location, distance boundary, supported remote channel absent, missing entities. |
| `domain.world.observation` | `observe(NPCView, WorldView, SensePolicy) -> ObservedSignals`; limit direct/informed knowledge and distinguish reports from accepted facts. | World/spatial read ports; visibility calculator. | Occlusion, out-of-range signals, private NPC state, expired knowledge and event propagation. |
| `domain.world.inventory` | `plan(InventoryRequest, OwnershipView) -> Result[InventoryEffect]`; conserve quantities and identify transfer/consumption effects without writing. | Item catalog and current ownership values. | Missing quantity, wrong owner, unknown item, repeated effect and conservation across both owners. |
| `domain.quest.bow` | `evaluate(BowQuestState, VerifiedGameEvent, QuestPolicy) -> QuestTransition`; own materials, pickup, timed crafting and one-time reward. | Clock value, catalog, recovery-route interface. | Valid phases, repeated reward, missing materials, early completion, resumed deadline and refusal leaving a viable route. |
| `domain.quest.recovery` | `offers(QuestBlocker, WorldView, RecoveryPolicy) -> RecoveryOfferSet`; select authored alternate routes and check that their prerequisites remain attainable. | Read-only world and quest values. | No circular prerequisites, consumed/missing resources, repeated completion, expired offer, no viable route. Recovery uses authored favour/trade offers from the same NPC; completion restores cooperation for the blocked step. |
| `application.effects` | `commit(ApprovedEffect, ExpectedRevisions) -> Result[VerifiedDomainEvent]`; atomically apply ownership/quest/outcome-dependent changes and their durable events. | Unit of work and owning domain repositories. | Rollback, duplicate event, concurrent consumption, stale ownership, crash before/after commit. |
| `application.sessions` | `load(GameRef) -> WorldView`; `restart(RestartRequest) -> Result[WorldView]`; coordinate save, resume and timeline replacement. | Session and world repositories, unit of work. | Reopen preserves progress; reset clears playable history; late old-timeline callback cannot mutate new state. |

### 4.2 Perception and reasoning modules

| Module | Responsibility and public interface | Dependencies | Independent tests |
| --- | --- | --- | --- |
| `perception.normalize` | `normalize(ObservedSignals) -> Result[NormalizedSignals]`; validate source fields, timestamps and consistent units; merge duplicate evidence by source identity. | Canonical field rules. | Facts versus interpretations, duplicate observations, invalid references and non-finite positions. |
| `perception.relevance` | `filter(Signals, DecisionContext, RelevancePolicy) -> FilterResult`; include only useful, permitted evidence with reasons. | Values only. | Private/unseen facts excluded; current request and urgent visible threats retained. |
| `perception.salience` | `rank(FilteredSignals, BudgetPolicy) -> RankedSignals`; assign reproducible priority and category budgets. | Injected time and policy. | Stable ordering, background flood, token/count limits and ties. Mandatory facts exceeding budget cause a bounded failure, not silent loss. |
| `perception.compose` | `compose(BasePerception, RetrievedMemories, RankedSignals) -> PerceptionSnapshot`; freeze the model input with provenance. | Snapshot ID source; immutable values. | Input mutation cannot alter snapshot; memory scope retained; no circular memory lookup. |
| `reasoning.frame` | `build(Snapshot, ReasoningProfile, DecisionPolicy) -> ReasoningInput`; expose goals and deterministic conflict priorities. | Versioned profile and policy. | Safety over cooperation, profile stability, current facts over claims, unknown conflict evidence. |
| `reasoning.prompt` | `render(ReasoningInput) -> ModelRequest`; serialize trusted instructions separately from bounded historical/player data. | Versioned prompt template. | Prompt budgets, injection-like memory remains data, no credentials/private excluded fields. |
| `adapters.model` | `async generate(ModelRequest) -> Result[RawProposal]`; call configured local/compatible provider with cancellation and deadlines. | HTTP/model client only. | Timeout, malformed response, oversized output, cancelled request and provider error; fake provider contract parity. |
| `reasoning.proposal_check` | `validate(RawProposal, Snapshot, ProposalPolicy) -> Result[DecisionProposal]`; schema, enum and grounding checks. | Values only. | Unknown fact/memory IDs, bad source scope, unsupported state fields, absolute mutations and invalid numeric deltas. |

### 4.3 Behavioural-control modules

| Module | Responsibility and public interface | Dependencies | Independent tests |
| --- | --- | --- | --- |
| `state.merge` | `merge(CurrentState, ProposedChanges, MergePolicy) -> Result[MergedChanges]`; choose one value per dimension using explicit source precedence and effect identity. | Values and applied-effect IDs. | Duplicate influence, conflict precedence, unrecognized relationship subject and no automatic sum of repeated proposals. |
| `state.extract` | `extract(CurrentState, MergedChanges) -> CandidateState`; relative-to-absolute conversion with canonical clamps and provenance. | State bounds policy. | Signed deltas, exact bounds, no ORM writes, deterministic output and no inventory/quest fields. |
| `fuzzy.membership` | `fuzzify(CandidateState, MembershipPolicy) -> Memberships`; overlapping triangular/trapezoidal memberships. | Validated policy values. | Overlap, endpoint shoulders, range guarantees, invalid point ordering. |
| `fuzzy.inference` | `infer(Memberships, RuleSet) -> AggregatedOutputs`; weighted antecedents and consequent aggregation. | Rule set only. | Min/all, max/any, weight bounds, disabled rules, conflicting contributions and rule IDs. |
| `fuzzy.defuzzify` | `shape(AggregatedOutputs, OutputPolicy) -> BehaviorShapingResult`; centroid tendencies and declared no-activation fallback. | Numerical policy. | Zero denominator, bounded outputs, precision tolerance, contribution trace and repeatability. |
| `roles.permissions` | `evaluate(Proposal, WorldView, RoleProfile) -> RolePermission`; allowed targets, duties and hard denials. | Profile and values. | Unknown role denied, peaceful role cannot attack, missing workshop/material prerequisites. |
| `roles.condition` | `condition(CurrentState, CandidateState, FuzzyResult, RoleProfile, RolePermission) -> RoleConditionedBehavior`; apply delta and tendency modifiers once. | Validated role policy. | Final absolute caps, sign preservation, separation of internal emotion/expression, no denied action reintroduced. |
| `control.continuity` | `smooth(RoleConditionedBehavior, ApprovedHistory, ControlPolicy, Now) -> ContinuityResult`; rate bounds and emergency override evidence. | Injected time and approved history. | Alternating proposals, elapsed time, ordinary versus urgent transitions, no smoothing from rejected history. |
| `control.fallback` | `build(FailureContext, SafeBehaviorPolicy) -> Result[FallbackCandidate]`; choose a declared zero-effect safe response when available, still subject to role/final checks. | Trusted policy and current evidence only. | No model call, no fabricated target/reward, unsupported fallback rejected and fallback loops bounded. |
| `control.validate` | `validate(Conditioned, Continuity, Evidence, Policies) -> ValidationResult`; final provenance, semantic and cross-variable checks. | Shared constraints and current applicability view. | Unsafe approach, mismatched evidence, invalid repaired result, forbidden fallback and stale policies. |
| `fsec.eligibility` | `candidates(ValidatedBehavior, Capabilities, WorldView) -> EligibleCandidates`; intersect engine capability and approved constraints. | Action catalog only. | No path, missing target, noninterruptible command, cooldown and denied actions. |
| `fsec.utility` | `select(EligibleCandidates, UtilityPolicy, ApprovedHistory) -> SelectionResult`; component scoring, switching margin and deterministic tie-break. | Values only. | Ineligible high-score action cannot win; stable ties; insufficient advantage does not interrupt. |
| `fsec.mapping` | `map(SelectionResult, ValidatedBehavior, Capabilities) -> Result[CommandDraft]`; clamp engine parameters and attach dialogue timing. | Mapping/catalog policy. | Negative speed, unsupported animation, missing outcome dependency and constraints never widened. |

Control Validation checks the role-adjusted state, including any smoothing. A smoothed result cannot escape role or canonical bounds. If a repair makes the original fuzzy/behaviour evidence inapplicable, return a declared safe fallback or require re-evaluation; do not silently iterate the layers until something passes. FSEC may narrow validated parameter ranges but may not select a behaviour outside the validated allowed set.

### 4.4 Execution, dialogue and memory modules

| Module | Responsibility and public interface | Dependencies | Independent tests |
| --- | --- | --- | --- |
| `application.approvals` | `approve(ValidationResult, ExpectedRevisions) -> Result[ApprovalReceipt]`; commit internal changes, decision history and a durable command-planning record once. | Unit of work and state repositories. | CAS conflict, duplicate decision, crash recovery, unchanged outcome-dependent values. |
| `application.commands` | `issue(ApprovalReceipt, CommandDraft) -> Result[Command]`; assign ordered controller revision and persist delivery/lifecycle. | Command repository, clock and unit of work. | Repeated issue, stale approval, terminal-state uniqueness, expiry and per-NPC ordering. |
| `application.outcomes` | `accept(ControllerEvent) -> Result[OutcomeReceipt]`; verify event identity, lifecycle, target and plausible execution; request domain effects. | Capability/spatial readers, command and effect ports. | Forged arrival, old timeline, duplicate completion, success after cancellation and wrong target. |
| `dialogue.compose` | `compose(ApprovedExpressionOrVerifiedEvent, DialoguePolicy) -> Result[DialogueEvent]`; bind outcome wording to verified event fields using authored templates; retain bounded validated wording for expression/commitment. | Event schema and dialogue policy. | A water transfer cannot produce bow-success wording; unverified references rejected; ambiguous generated success claim uses a safe line. |
| `dialogue.timing` | `eligible(DialogueEvent, Lifecycle, VerifiedOutcomes) -> DialogueDisposition`; gate expression, commitment and outcome lines. | Values only. | No outcome line without matching committed event; interrupted commitment; wrong recipient and duplicate display ID. |
| `memory.classify` | `classify(ApprovedConversationOrEvent, ImportancePolicy) -> MemoryDecision`; preserve authoritative-event and player-claim rules. | Values only. | Greetings excluded, failed model response excluded, verified transfer retained, claim not promoted to fact. |
| `memory.ingest` | `ingest(VerifiedEvent, RecipientScope) -> IngestionResult`; persist one recipient memory and schedule embedding/influence processing. | Memory repository and unit of work. | Duplicate source event, multiple recipients, scope restrictions and embedding outage not losing source record. |
| `memory.reconcile` | `reconcile(NewRecord, RelatedRecords, ReconciliationPolicy) -> ReconciliationPlan`; link corrections and safe consolidation. | Typed evidence only. | Retraction, authoritative correction, conflicting claims retained and negation not merged by vector similarity. |
| `memory.retrieve` | `retrieve(MemoryQuery) -> RetrievedMemorySet`; apply scope/lifecycle filters, bounded candidate search, priority/lexical fallback and reranking. | Memory reader, embedding/index ports, clock, ranking policy. | Candidate bounds, NPC/target/quest/time filtering, critical-event priority, unavailable embeddings, expired/superseded records. |
| `memory.influence` | `propose(VerifiedMemory, InfluencePolicy, AppliedEffectLedger) -> InfluenceProposals`; bounded state/relationship effects with source identity. | Values only. | Repeated retrieval has no side effects, verified help versus unverified claim, same outcome not rewarded twice. |
| `memory.lifecycle` | `review(Records, Now, RetentionPolicy) -> LifecyclePlan`; distinguish expiry for retrieval from archival/deletion. | Clock and explicit policy. | Temporary expiry, archive exclusion, protected provenance and no deletion when policy is unspecified. |
| `adapters.embedding_index` | `embed_documents`, `embed_query`, `search(IndexScope, vector, limit)`; isolate Ollama/Nomic and FAISS details. | External clients/numeric runtime. | Dimensions/model namespace, finite normalized vectors, reset/rollback invalidation, rebuild and scoped cache reuse. |
| `policy.registry` | `load(PolicyVersionSet) -> Result[PolicyBundle]`; validate one immutable bundle for a decision. | Configuration storage port. | Missing/unknown actions, inconsistent bounds, unsafe fallback, invalid memberships, incomplete recovery routes. |
| `observability.trace` | `record(StageTrace)` and `measure(MetricSample)`; emit correlated redacted diagnostics. | Injectable sink. | Missing correlation, redaction, bounded payload and sink failure not changing a domain decision. |

## 5 Principal data structures

All records below include the Section 3 envelope where applicable. Collections have explicit configurable limits. Optional fields distinguish absence from zero or false; unknown enum values are errors.

| Record | Essential fields and invariants |
| --- | --- |
| `InteractionEvent` | Client event ID, actor, NPC/target, kind, speech or typed request, expected timeline. Reported position/time are untrusted observations. |
| `BasePerception` | Accepted NPC/world view, relevant revisions, current interaction, visible entities and goals; excludes retrieved history until the bounded memory query completes. |
| `PerceptionSnapshot` | Snapshot ID, observation time, identity/profile reference, direct observations, internal state, relevant quest state, claims, selected memories, salient facts and constraints. Immutable after composition. |
| `ReasoningInput` | Snapshot, reasoning profile version, allowed vocabulary, conflict frame, response budget and prompt version. No repository handles. |
| `DecisionProposal` | Proposal/snapshot IDs, intent, behaviour signals/target, expression/dialogue, confidence, grounding IDs, concise rationale and optional relative deltas. No absolute game mutations. |
| `CandidateState` | Base revision; emotion, activity, attention and relationship candidates; per-field previous/delta/value/source/normalization notes. |
| `BehaviorShapingResult` | Source state ID, ruleset version, memberships, normalized tendencies, contributing rule activations and diagnostics. |
| `RoleConditionedBehavior` | Profile version, permission decision, original/conditioned changes, bounded tendencies, allowed behaviour/targets and modifier diagnostics. |
| `ValidationResult` | `approved`, `repaired`, `fallback` or `rejected`; conditioned source IDs; final internal changes; permitted behaviours and parameter constraints; pending outcome requirements; reasons. Rejected results cannot produce commands. |
| `ApprovalReceipt` | Decision ID, before/after state revisions, committed internal effect IDs, retained pending effects and command-planning status. |
| `CapabilityView` | NPC/controller revision, supported actions, accepted position, active command, movement/animation limits and current navigation/target evidence. A client capability claim alone does not grant a role permission. |
| `NPCControllerCommand` | Command/approval IDs, timeline, ordered controller revision, kind/target, bounded parameters, issue/expiry times, interrupt policy and dialogue events. |
| `ControllerEvent` | Event/command IDs, controller revision, monotonic event sequence, type, reported position/time and typed evidence. Unverified until the backend accepts it. |
| `VerifiedDomainEvent` | Event type, authoritative source, participants, before/after references, affected entity revisions, command/effect identity and committed time. Immutable. |
| `DialogueEvent` | Stable display ID, NPC, text/tone, kind (`expression`, `commitment`, `outcome`), timing condition and optional verified-outcome reference. Outcome kind requires that reference before display eligibility. |
| `MemoryRecord` | Source event, recipient NPC, participants, subject/predicate references, summary, epistemic status, confidence, visibility, importance, event/quest/target metadata, timestamps and lifecycle. |
| `MemoryQuery` | Timeline/NPC, participant/target/location/quest filters, current topic/goals/threats, time bounds, category budgets and embedding namespace. Built from BasePerception, not recursively from the final snapshot. |
| `RetrievedMemory` | Record/source IDs, status/provenance, selection method, semantic score where available, reranking components, inclusion reason and bounded prompt content. |
| `MemoryInfluenceProposal` | Source event/memory IDs, subject, bounded relative changes, policy version and stable effect identity. Enters the same extraction/control path; never writes state directly. |
| `CooperationGrant` | Timeline, player/NPC, quest run, blocked step, originating recovery outcome and fulfilment status. Checked as an authoritative obligation; fulfilled once by successful completion of that step. |
| `RecoveryOffer` | Offer ID, blocker, authored route ID/version, involved NPCs, prerequisites, completion predicate, permitted effect, expiry and status. A discriminated favour/trade specification belongs to the same NPC as the blocker; the client cannot author its prerequisites, cost or cooperation reward. |

### 5.1 Changes and authority timing

A change has `apply_when = approval | verified_outcome`. Trusted policy determines timing from source and effect kind; the LLM cannot choose to label a reward as an internal change. General expression can reflect approved fear; a fulfilled agreement, inventory transfer or relationship reward for successful help needs the corresponding event.

Extraction starts from the current approved value. Merge policy selects one accepted change per dimension/source occurrence. Role conditioning adjusts the delta against that same base, not against an already incremented value. Final validation smooths the conditioned candidate, rechecks role/global bounds and records the final absolute result. This prevents double addition and silent disagreement between layers.

### 5.2 Persistence records and constraints

Logical records need not each become a separate physical table, but ownership and uniqueness must remain explicit:

| Record group | Required keys and consistency rules |
| --- | --- |
| Game session and state | One active timeline for the local save; revisions on accepted NPC, relationship, inventory, quest and controller state. |
| Interaction receipts and decisions | Unique `(timeline, actor, client_event_id)`; payload digest and durable processing status. One approved internal application per decision. |
| Inventory and quest effects | Unique effect/source identity; consistent ownership changes in one transaction; one bow completion/reward per quest run. |
| Commands and controller events | Unique command ID; ordered `(timeline, npc, controller_revision)`; unique event ID; valid lifecycle transitions only. |
| Domain events and delivery records | Outcome and durable delivery intent commit together. Delivery retries do not duplicate consumers' effects. |
| Memory and reconciliation | Unique `(timeline, recipient_npc, source_event_id, memory_kind)`; correction links and lifecycle; embeddings carry model/preprocessing namespace. |
| Influence ledger | Unique `(timeline, source_event_id, recipient, effect_kind)` after application. A policy-version change does not automatically reapply a historical reward. |
| Recovery offers and cooperation grants | Bound to one blocker/quest run and policy version; completion/cooperation effect applied once; a grant is fulfilled by the covered successful quest step, not by a mere attempt. |

The existing conversation and memory records remain distinct. Database mutations and reset invalidate derived index scopes transactionally. Active-timeline filters are required even when old audit data is retained; resetting the playable game must not depend on successful deletion of a cache file.

### 5.3 Deterministic algorithm contracts

**Fuzzy inference:** membership inputs and output tendencies are normalized. Follow the proposal’s baseline: `min` for all-antecedents, `max` for any-antecedents, activation multiplied by rule weight, consequent clipping, max aggregation and centroid defuzzification. All active contributions retain rule IDs. An empty valid activation set uses configured safe tendencies; invalid configuration is an error. Rule values are versioned content, not recalculated by the LLM.

**Continuity:** apply `alpha * conditioned_candidate + (1 - alpha) * prior_approved` under per-dimension rate limits, then check the intersection of role and canonical bounds. Urgent overrides require authoritative evidence and a diagnostic. Utility switching margins govern whether to replace a running action, independently of smoothing a scalar value.

**Memory selection:** retain the existing importance gate and real Nomic/FAISS path. The baseline semantic path prefilters knowledge/timeline/model/lifecycle metadata, retrieves up to 40 candidates (existing configurable range 20–50), reranks with `0.65 * cosine_similarity + 0.20 * importance + 0.15 * recency`, and selects up to five under the final memory budget. `recency = 1 / (1 + max(age_hours, 0) / 24)`. Exact duplicate context entries are consolidated after scope verification; repeated real effects keep their historical source records.

Relevant authoritative-priority records enter a separate bounded candidate channel before final category-budget selection. Lexical/recency fallback uses the same metadata and knowledge filters; it labels semantic score as absent, not a fabricated zero-valued vector. Do not compare an unnormalized lexical score directly with cosine similarity: rank fallback records using a separately versioned policy. Model revision changes require re-embedding; a query and candidate vector from different namespaces cannot be compared.

**Dialogue composition:** outcome templates receive only a verified event’s typed values and recipient information. An outcome ID cannot legitimize unrelated free-form generated success text. Immediate expression and commitments use approved wording under the current world/role boundary, and their display still follows lifecycle timing.

## 6 Infrastructure ports and integration contracts

### 6.1 Backend ports

```python
WorldReader.read_context(trigger) -> Result[WorldReadSet]
MemoryReader.query_scope(filters, limit) -> Sequence[MemoryRecord]
SpatialVerifier.check(report, command, accepted_world) -> Result[SpatialEvidence]
ModelProvider.generate(request) -> Awaitable[Result[RawProposal]]
EmbeddingProvider.embed_documents(texts, namespace) -> Result[VectorBatch]
EmbeddingProvider.embed_query(text, namespace) -> Result[Vector]
VectorIndex.search(scope, vector, limit) -> Sequence[CandidateIdScore]
UnitOfWork.begin() -> Transaction
StateWriter.compare_and_commit(expected_revisions, approved_changes, events) -> Result[CommitReceipt]
DeliveryStore.poll(timeline, consumer, cursor, limit) -> DeliveryBatch
Clock.now_utc() -> Instant
TraceSink.record(trace) -> None
```

A `WorldReadSet` contains the values and revisions used by pure modules. Read-only ports do not commit. A unit of work owns the short database transaction and supplies scoped repositories; a nested domain module cannot commit it early. `StateWriter` checks relevant revisions at the mutation boundary and writes durable events with the state change.

FAISS returns IDs/scores, not authoritative memory objects. The memory reader rechecks timeline, lifecycle and knowledge filters before prompt presentation. Embedding namespace includes model identity, dimension and preprocessing revision. Hash fingerprints may identify exact duplicates, but are never a semantic-vector fallback.

### 6.2 Transport contract

The target API uses a versioned boundary. These are contract names and proposed resource shapes, not a promise that the current routes already expose them.

| Operation | Request | Response and behaviour |
| --- | --- | --- |
| `POST /v1/interactions` | InteractionEvent | Accepted receipt with stable interaction ID/status, or typed rejection. Long model work is not held inside the receipt transaction. |
| `GET /v1/interactions/{id}` | Timeline and interaction ID | Pending, rejected, approved or completed result; dialogue events and command references, not an assumed world success. |
| `GET /v1/controller/commands` | Timeline, controller ID, durable cursor and bounded limit | Ordered batch plus next cursor. Polling does not acknowledge execution. |
| `POST /v1/controller/events` | ControllerEvent | Accepted/deduplicated event receipt, or rejection with reconciliation information. |
| `GET /v1/world` | Current game reference | Authoritative saved state, timeline and relevant revisions; no implicit reset. |
| `POST /v1/world/restart` | Expected timeline and idempotent restart request ID | New timeline and initial world. Retrying the same request returns the same restart result rather than resetting again. |
| `PUT /v1/world/player-position` | Timeline, position report and observation sequence | Accepted position/revision or correction; not a grant of client authority. |
| `POST /v1/quests/bow/recovery/{offer_id}/accept` | Timeline, idempotent event ID and expected offer version | Accepted agreement/verified trade result or changed-prerequisite rejection. Never accepts client-defined costs or success. |
| `GET /v1/quests/bow/recovery` | Current timeline and blocker/quest reference | Applicable authored recovery offers; same-NPC favour/trade completion semantics. |

The current `/chat`, `/inventory`, `/quests`, `/world` and memory inspection endpoints can remain compatibility adapters. They must delegate to the same application/domain rules, not maintain a second implementation. An old `action` string is never promoted to an executable controller command. Legacy clients that cannot carry a timeline must be refreshed or rejected at a reset boundary; the adapter must not attach the new timeline to an old pending mutation.

HTTP `202` means accepted work, not completed gameplay; `200` returns a known result. Invalid contract fields use `422`, missing resources `404`, stale revisions/timeline or idempotency conflicts `409`, bounded overload `429`, unavailable required infrastructure `503`. Domain refusal is an ordinary typed result, not a server error. Polling transports may change later without changing lifecycle/idempotency semantics.

### 6.3 Godot modules

| Module | Public surface and responsibility | Tests with fake dependencies |
| --- | --- | --- |
| `gateway.contract_codec` | `decode_command(payload) -> CommandResult`; validate version, timeline, vocabulary and finite parameters. | Unknown version/action, missing target, old timeline, non-finite values. |
| `gateway.command_client` | Poll durable cursor, acknowledge receipt and retry events with stable IDs. | Disconnect/reconnect, duplicate batch, lost acknowledgement and no skipped unprocessed command. |
| `controllers.lifecycle` | `accept(command)`, `handle(event)`, `cancel(reason)`; only component allowed to change active command state. | Every transition, duplicate receipt, expiry, interruption, terminal-state stability. |
| `controllers.navigation` | `start(target, limits)`, `tick(dt)`, `stop()`; report arrival/blocked/failed through lifecycle. | Missing/blocked paths, moving targets, bounds and stationary NPC using a fake navigation port; separate real physics scene checks. |
| `controllers.animation` | Map lifecycle and expression to supported visual states; expose capability fallback. | Missing clips, bounded blend/speed, no animation callback directly grants inventory. |
| `controllers.interaction` | Submit typed interaction attempt and wait for verified effect. | Out-of-range target, rejected transfer, duplicate acknowledgement and interrupted gesture. |
| `ui.dialogue_presenter` | Present eligible DialogueEvents once; keep per-NPC histories. | Wrong NPC, duplicate display ID, suppressed unverified success, interrupted commitment. |
| `ui.world_presenter` | Render authoritative inventory, quest, refusal/recovery and save/restart state. | Reconciliation replaces stale display, restart clears prior timeline, pending UI never invents a reward. |

Godot movement and visuals run at frame cadence. Decision inference does not. A capability report lists available navigation/animations, but the backend's role catalog decides what may be requested. This local trust model validates plausible reports; it is not a multiplayer anti-cheat design.

## 7 Transactions and lifecycle coordination

### 7.1 Decision processing

1. In a short transaction, check timeline and idempotency, persist receipt and a durable decision-work record. Only one active ordinary decision per NPC owns its expected revision; urgent events can supersede it explicitly.
2. Read a consistent decision context and release database resources. Retrieve bounded memory and perform model work outside mutation transactions. Freeze policy versions and evidence IDs for the attempt.
3. Run pure proposal checks and the control sequence. At approval, compare the relevant revisions. On conflict, discard/rebuild the stale candidate through bounded orchestration; never apply its old absolute values to a new base.
4. Commit approved internal changes, approval history and durable FSEC-planning work together. The receipt stores the new approved state revision. Outcome-dependent changes remain unapplied.
5. FSEC uses the approved result and fresh capability/precondition data. A short command transaction checks that the approval remains current and emits command/delivery records. If FSEC cannot select an action, internal approval remains recorded; the command outcome is no-action/fallback, not a fabricated success.

A crash between approval and command issuance leaves durable planning work to resume. A crash after command issuance leaves the same command to redeliver. Neither case re-applies internal changes.

### 7.2 Execution and effects

```text
issued → acknowledged → running → completed | failed | cancelled | expired
```

A controller cannot skip required interaction verification by reporting `completed`. Outcome verification checks active command, timeline, revision, target and event progression. Arrival is accepted only when supported by the command's movement/range constraints. Inventory/quest effects additionally pass their owning domain service.

World mutations and their outcome event commit together. Event delivery and memory ingestion are at-least-once; effect and consumer uniqueness make processing idempotent. This is not a claim of exactly-once network delivery. Terminal-state changes are rejected or reconciled using the already committed result.

Outcome-dependent relationship changes originate from verified events, pass extraction/fuzzy/role/final validation against current approved state, and commit with an applied-effect ledger entry. They are not applied again merely because the memory later appears in context. Reconciliation distinguishes a historically completed transfer from a later command cancellation: cancellation cannot undo a committed transfer without a separate permitted reversal event.

### 7.3 Refusal, delay and alternate completion

A behavioural refusal is a typed decision with reason, blocker, source evidence and a recovery-route reference. A delay identifies a valid release condition or review time; repeated decisions cannot push that deadline indefinitely without a new recorded reason.

The quest route policy is separate from fuzzy cooperation and utility scoring. Before allowing a refusal to block a mandatory step, it must find an attainable authored recovery offer using current world state. A route requiring the very item or cooperation it is meant to recover is invalid. Both Gatherer material access and Craftsman crafting access need coverage; providing only another wood source does not solve a crafting refusal.

`RecoveryOffer` completion is verified by game services and resolves its blocker exactly once. It does not trust a player's claim that the recovery action happened. The confirmed route is a favour or trade with the refusing NPC. Missing viable route configuration is a policy error: it makes a new discretionary refusal ineligible, rather than activating an unwinnable quest/refusal combination. This does not bypass hard safety, ownership or recipe constraints.

`RecoveryOffer.spec` is a closed union:

- `TradeRecovery`: catalog item/quantity costs, recipient NPC, blocked quest step and the cooperation effect. The inventory service rechecks ownership and transfers the agreed cost atomically with agreement completion. Quoted terms are versioned; changed terms require a new accepted offer, not silent repricing.
- `FavourRecovery`: an authored completion predicate over allowlisted, verified game events, with actor/target constraints and activation time. Predicates are declarative data interpreted by game rules, not executable strings. Player speech or an LLM claim cannot mark the favour complete.

An offer progresses through `offered → accepted → completed`, with cancellation or invalidation recorded explicitly. The player accepts its offer ID; the server checks the timeline, NPC, blocker, policy version and current prerequisites. A repeat acceptance or completion returns the original result. Completing a trade/favour creates a `CooperationGrant` for `(timeline, player, npc, quest_run, blocked_step)` in the same outcome transaction, alongside any verified costs and source event.

A grant is a game obligation to cooperate for that step. It need not force trust above an invented threshold. Role/FSEC policy cannot select an ordinary refusal that contradicts an active grant; actual range, safety, material and controller preconditions still apply. A grant is fulfilled only when the covered authoritative step succeeds, so a failed path, disconnect or interrupted gesture does not consume it. Restart invalidates grants from the old timeline.

Offer selection must avoid dependence on cooperation from the same blocked step. Resource-consuming trades require an attainable authored favour alternative when their costs cannot be obtained. The design specifies the completion contract without choosing a new item, price or favour scenario. Policy activation and runtime reachability checks reject configurations that have no viable resolution.

### 7.4 Save, reset and reconnect

Ordinary save/resume preserves inventory, NPC/relationship state, quest deadlines, accepted position, conversation history, memory and durable command status. Crafting uses the existing server deadline; movement does not secretly simulate while Godot is closed. Reconnect reconciles active commands with current accepted world state and revalidates before resuming them.

Restart creates a new timeline in one authoritative transition, restores initial gameplay and invalidates old commands, decisions, offers, influences and memory work. Late model/embedding/controller responses fail the timeline check. Reset must not depend on completing a slow model request. An explicit restart-request identity survives long enough to deduplicate a retry. Any retained diagnostics are outside the playable memory scope and cannot be retrieved into the new run.

## 8 Error handling and degradation

| Error/result | Owner and response | State/effect guarantee |
| --- | --- | --- |
| `INVALID_CONTRACT`, `UNKNOWN_ENUM` | Gateway or proposal checker rejects with field diagnostics. | No candidate execution or mutation. |
| `UNGROUNDED_REFERENCE`, `KNOWLEDGE_SCOPE_VIOLATION` | Proposal/perception validation rejects or uses an approved safe response. | No invented fact, target or reward. |
| `ROLE_DENIED`, `BEHAVIOUR_REFUSED` | Role/control returns explicit disposition; refusal exposes the applicable recovery path. | Hard denial cannot be outscored by utility. |
| `NO_VIABLE_RECOVERY_ROUTE` | Policy/quest boundary reports configuration failure; exclude a discretionary refusal lacking a viable route; report invalid policy without bypassing hard game constraints. | No fabricated resources, prices or alternate NPC. |
| `STALE_REVISION`, `OLD_TIMELINE` | Application rejects stale work and requests reconciliation/new observation. | No old absolute state or prior-game effect applied. |
| `MODEL_UNAVAILABLE`, `MODEL_INVALID_OUTPUT` | Bounded safe response; log model failure. Retry policy is explicit and does not retry world effects. | Failure response alone creates no importance-worthy gameplay success. |
| `EMBEDDING_UNAVAILABLE`, `INDEX_NOT_READY` | Preserve durable source memory; use permitted scoped lexical/priority/recency retrieval and schedule indexing recovery. | No fake vectors and no loss of authoritative outcome. |
| `PATH_BLOCKED`, `UNSUPPORTED_CAPABILITY` | Controller/FSEC reports failure or eligible fallback. | No arrival or success dialogue without verification. |
| `EFFECT_PRECONDITION_FAILED` | Owning game service rejects effect and returns current applicable state. | Ownership and quest invariants remain intact. |
| `IDEMPOTENCY_CONFLICT` | Application rejects changed payload under reused ID. | Existing result is not overwritten. |
| `STORAGE_UNAVAILABLE` | Return infrastructure error; retry only through durable/idempotent paths. | Never announce an uncommitted outcome. |
| `POLICY_INVALID`, `POLICY_INCONSISTENT` | Reject activation/use of that policy bundle. | No silent unrestricted default role or action. |

Timeouts, queue bounds, retry budgets, rate limits and numerical tuning are explicit policy/configuration fields with validation. Their numeric values remain evaluation parameters, not guessed product guarantees. Validation of diagnostics and public errors must not expose raw credentials or full private snapshots.

## 9 Coupling risks and controls

| Coupling risk | Required separation |
| --- | --- |
| A large pipeline owns domain rules and transactions | Coordinator only sequences ports; inventory, quest, control and memory rules return typed results. |
| Shared DTO package becomes a circular dependency hub | Shared envelopes/value types only; domain-specific records stay with their owning contract package and are passed by value. |
| Perception requires final snapshot to retrieve the memories needed to build it | BasePerception → MemoryQuery → retrieved evidence → final snapshot; one bounded retrieval boundary. |
| LLM confidence or explanation becomes execution authority | Confidence/rationale remain diagnostics; evidence and deterministic services authorize changes. |
| Repeated clamps/modifiers apply state delta twice | Preserve one base value and explicit change lineage; each transformation replaces a candidate, never independently increments persisted state. |
| Role adjustment undoes temporal/semantic validation | Role precedes final validation; FSEC can only narrow its permitted set and ranges. |
| Presentation speed/animation timing becomes authoritative completion | Separate controller reports from verified domain effects; dialogue requires matching outcome IDs. |
| Quest progress is encoded in conversational keywords | Typed quest events and recovery offers own transitions; compatibility parsing only proposes a request. |
| Refusal logic changes quest solvability implicitly | A dedicated route policy validates attainable alternatives independently of fuzzy preferences. |
| Conversation logging and semantic indexing block game commits | Durable source event first; memory and embedding work are idempotent consumers. |
| FAISS cache holds uncommitted or previous-game records | Database/timeline/model/revision scope, transactional invalidation and post-search metadata verification. |
| A policy update replays historic social rewards | Applied-effect identity excludes incidental retry/configuration changes; explicit correction is a new authorized event. |
| Godot and backend enums drift | Shared versioned fixtures and capability negotiation; reject unsupported contracts. |
| Raw SQL or a compatibility route bypasses invariants | Writes through owning application ports and the same timeline/revision/effect checks; database constraints provide a second boundary. |

## 10 Integrated test strategy

The module tables define unit tests. Pure modules use fixed clocks, IDs, policies and immutable fixtures. Ports have reusable contract suites so a fake and its production adapter must obey the same result/error semantics.

**Cross-module contracts:** serialize/deserialize every handoff, verify source lineage and policy versions, reject unsupported schema versions, and assert that all accepted controller commands satisfy the final ConstraintSet. Golden fixtures describe representative calm/helpful, fearful/avoidant, refusal/recovery and urgent interruption cases. Exact LLM prose is not the oracle.

**PostgreSQL integration:** concurrent item consumption, decision approval CAS, outcome plus delivery atomicity, duplicate memory influence, restart racing a completion, atomic recovery trade/cooperation grant, and reconnect after a crash. SQLite tests remain useful but do not substitute for PostgreSQL locking/concurrency checks. Fault injection covers each side of a commit, not only failed model generation.

**Model and retrieval evaluation:** deterministic fake proposals exercise all policy branches. Separately, a live local-model suite checks schema/grounding behaviour and paraphrase retrieval. Record retrieval recall, critical-fact inclusion, wrong-subject leakage and latency components; no unmeasured quality threshold is assumed. Fuzzy properties include membership bounds, empty-rule fallback and repeatability.

**Godot integration:** real navigation collision/arrival, unsupported animations, queued/duplicate commands, controller interruption and outcome-gated dialogue. Headless tests avoid waiting for render-only signals; visual tests inspect animation and UI independently.

**Game scenarios:** start and finish the bow quest, request-purpose confirmation, verified gifts and thank-you dialogue, behaviour-induced refusal/delay followed by the chosen recovery route, blocked execution without success claims, restart clearing prior timeline work, and reopening a saved game without replaying rewards. Test both refusal points, not only the Gatherer. Verify that an accepted favour cannot be completed by a claim, a repeated trade cannot charge twice, a cooperation grant prevents immediate repeat refusal, and unavailable trade resources do not eliminate all recovery paths.

**Replay and observability:** replay recorded approved proposals through deterministic modules under recorded policies. Check output equivalence within documented numeric precision, correlation IDs, redaction, duplicate suppression and the absence of forbidden effects. Model regeneration is a separate evaluation and need not reproduce the original wording.

## 11 Integration with the existing project

| Existing area | Target relationship |
| --- | --- |
| `services/pipeline.py` | Compatibility entry into application coordination; stops owning extraction, role, effect and memory rules directly. |
| `services/context/` | Adapter for current fields to BasePerception and PerceptionSnapshot. Recent dialogue retains provenance and bounded scope. |
| `services/llm/` and prompt builder | Provider/prompt adapters behind ReasoningInput and proposal contracts. |
| `services/validation/` | Early schema/grounding checks remain distinct from final behavioural validation; item/world truth stays with owning services. |
| `services/state/`, `services/npc/conditioning.py`, rule engine | Existing behaviour is not presented as full fuzzy/FSEC support. Pure target modules isolate extraction, role policy and fuzzy inference. |
| `services/quests/bow.py` and inventory routes | Authoritative game adapters using typed transitions/effects; new refusal recovery integrates at the quest-policy boundary. |
| `services/memory/` | Preserve rule filtering, real embeddings, FAISS candidate retrieval, reranking and migration/reindex support beneath richer ingestion/retrieval contracts. |
| SQLAlchemy models and session management | Infrastructure adapters for repositories and unit of work; ORM objects do not enter pure control modules. |
| Godot main/chat/NPC scripts | UI compatibility and controller adapters; nontrivial actions consume commands and verified dialogue events instead of raw action strings. |

No new faction/combat/economy implementation or generalized quest engine is implied by these interfaces. Recovery content must be consistent with the confirmed village scope; it is not a reason to silently expand the game into those domains.

## 12 Clarifications and intentionally deferred parameters

The owner confirmed that refusal/delay may affect required quest help, and that a favour or trade with the same NPC restores cooperation. Sections 5 and 7 define the recovery offers, verified completion and scoped cooperation grant. No alternate NPC or self-service crafting path is part of the selected design.

Policy thresholds, membership tuning, utility weights, deadlines beyond the existing bow timer, budgets, response-time objectives and retention periods remain explicit configuration/evaluation parameters. This design does not invent specific favours, item prices or dialogue scripts. Contract and safety invariants are fixed independently of those content values.
