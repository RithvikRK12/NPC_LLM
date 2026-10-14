# NPC Conversation Redesign — Detailed Design

Date: 2026-10-14  
Status: Proposed detailed design; no runtime implementation is included

Sources: [Proposal](npc-conversation-redesign-proposal.md), [High-level design](npc-conversation-redesign-high-level-design.md).

## 1. Scope and decision record

This design specifies modules, public contracts, persistence, failure handling, integration, and independent testing for the existing Python/FastAPI backend and Godot client. Modules are in-process components, not separately deployed services. The system serves one world, one active save, and one server-resolved current player.

The high-level design governs product behavior, including narrative-only generated canon, authored identity precedence, explicit accepted corrections, and clear-chat/new-game semantics. The following additional decisions were confirmed by the user for this detailed design:

1. Queue turns per NPC. Different NPCs may generate concurrently; shared world state must be rechecked before actions.
2. Pending negotiations have no automatic time or turn expiry. Changed relevant preconditions invalidate them. Explicit cancellation, clear chat, and new game also end them.
3. If a message requests multiple supported actions, ask which action to perform first. Do not automatically execute the first action, and do not silently queue the rest for execution.

Concrete module names, records, interfaces, and transaction mechanisms below are proposed engineering choices implementing those decisions. They do not introduce new gameplay capabilities. Latency, context size, response length, retention periods, and model selection remain measurement/configuration decisions as directed by the source documents; this document does not assign invented shipping values.

### Required invariants

- Only deterministic game services authorize mechanics. Narrative, player reports, summaries, and provider output are never mechanical evidence.
- A turn executes at most one requested mutating operation. Deterministic consequences within that operation, such as quest progress and verified memory, belong to the same transaction.
- One ordinary proposal call; action speech may require a composition call; at most one targeted repair across the entire turn. Summarization is outside this mandatory path.
- No provider, embedding, or semantic-checker call while a database transaction or lock is held.
- Operation effects and their receipt commit atomically. Final dialogue and accepted conversational continuity commit atomically in a separate transaction.
- Per-NPC turn order is established durably before context assembly. Later turns see earlier finalized replies, including fallback replies.
- Clear chat invalidates conversational publication; new game invalidates the entire old scope. Neither permits replay of an old operation.
- Only committed final dialogue is eligible for display. Delivery retry returns that same dialogue rather than generating again.

## 2. Module layout and dependency rules

Use `backend/app/services/conversation/` for the new orchestration and domain modules. Keep storage models in `backend/app/models/`, HTTP schemas/routes in their existing directories, and provider/game adapters beside their existing integrations. The layout is a responsibility map; small closely related value types may share a file.

| Module | Responsibility | Allowed dependencies | Independent test boundary |
| --- | --- | --- | --- |
| `contracts.py` | Immutable conversation values, tagged unions, version validation | Pydantic/value utilities only | Decode/encode fixtures; no DB/provider |
| `ports.py` | Narrow protocols for persistence, world reads, execution, generation, clock, diagnostics | Contracts only | Contract conformance suites |
| `coordinator.py` | Sequence a turn, enforce call/deadline budgets, choose recovery path | Ports and domain modules | In-memory ports and fake clock |
| `turns.py` | Admission, per-NPC sequencing, processing ownership, retry lookup | Turn-store port | Fake repository and race fixtures |
| `context.py` | Assemble NPC-visible evidence, transcript, canon, unresolved subjects | Read ports, budget policy | Fixed snapshots and deterministic token counter |
| `capabilities.py` | Translate game-service capabilities into model-visible descriptors | World-view port | Fake role/encounter views |
| `proposal.py` | Build shared prompt, decode interpretation and candidate reply | Generation port, contracts | Scripted provider outputs |
| `interactions.py` | Pure pending-negotiation transition rules and consent bindings | Contracts only | Transition-table tests |
| `operations.py` | Validate proposed intent and dispatch a supported typed operation | Operation gateway port | Fake gateway and authorization cases |
| `composition.py` | Assemble expressive segments and exact factual/receipt clauses | Contracts, approved renderer catalog | Golden rendering tests |
| `validation.py` | Aggregate schema, grounding, canon, relevance, and style findings | Pure checkers; optional semantic-check port | Independent checker fixtures |
| `fallback.py` | Select safe, relevant degraded speech from known outcomes | Renderer catalog, authored character data | Scenario/receipt fixtures |
| `canon.py` | Plan narrative additions and explicit revisions | Contracts, authored constraints | Pure conflict/admission tests |
| `memory.py` | Plan attributed reports, interpretations, and summary selection | Memory read port, contracts | Provenance and correction tests |
| `finalization.py` | Revalidate publication and atomically persist a final result | Finalization-store port | Fake unit of work plus DB integration tests |
| `lifecycle.py` | Clear/reset invalidation and deletion boundaries | Lifecycle-store port | State matrix and race tests |
| `diagnostics.py` | Emit structured stage events and evaluation metadata | Existing trace adapter | Capturing sink; fault injection |
| Persistence adapters | Implement transactions, scoped queries, leases, uniqueness, recovery | SQLAlchemy and models | SQLite/PostgreSQL integration suites |
| Game adapters | Map typed conversation operations to existing authoritative services | Existing state/encounter/quest services | Adapter conformance and current gameplay tests |
| API adapter | Validate requests, resolve active player, map domain errors/results | Coordinator/lifecycle ports, HTTP schemas | FastAPI tests with fake application services |
| Godot request/presentation adapters | Stable request IDs, ordering, scope suppression, readable beats, state refresh | Validated HTTP contracts | Mock backend and headless Godot tests |

Domain modules must not import FastAPI, SQLAlchemy sessions, Godot code, or a concrete LLM provider. Repositories never call providers. The coordinator owns sequencing, not inventory rules, canon conflict rules, or prose policy. Dependencies are supplied at construction, avoiding the current pipeline's direct construction of all services.

Do not move the existing parallel `app/contracts`, `app/dialogue`, `app/ports`, and `app/memory` architecture wholesale into this package. Reuse compatible immutable values and provide explicit adapters where semantics match. In particular, do not equate existing `game_id`/`timeline_id` with `game_scope`/conversation epoch without an explicit mapping.

## 3. Shared data structures

The following are public application-level contracts, expressed as typed field descriptions rather than executable definitions. All timestamps are UTC; durations use an injected monotonic clock during a running process. IDs are opaque server/client identifiers, never instructions. Unknown schema versions and unexpected provider fields are rejected. Collection and text bounds come from one versioned policy.

### 3.1 Identity, revisions, and evidence

| Type | Fields and constraints |
| --- | --- |
| `ConversationKey` | `game_scope: str`, `npc_id: int`, `epoch: int`. Epoch advances on clear chat; a new game changes scope. |
| `TurnSubmission` | `schema_version`, `request_id`, `key`, `player_message`. Resolve the player server-side; do not accept a player selector. |
| `TurnRef` | `turn_id`, `request_id`, `key`, `sequence: int`. Sequence increases within a key; it is not a wall-clock ordering. |
| `RevisionSet` | Immutable map of relevant resource IDs to revision tokens: inventory, quest, encounter/activity, authored content, canon, negotiation. A revision mismatch prompts revalidation; it is not itself proof that a precondition changed. |
| `SourceRef` | `kind`, `source_id`, `revision`, `game_scope`, optional `npc_id`, attribution and knowledge visibility. |
| `Evidence` | Tagged union: `MechanicalFact`, `VerifiedEvent`, `AuthoredKnowledge`, `NarrativeCanon`, `PlayerReport`, `Interpretation`. Each carries source references; only the first three can be consumed by mechanical rules where explicitly permitted. |
| `TextSpan` | `text_id`, `start`, `end`; zero-based Unicode code-point offsets, end exclusive. The referenced text and exact span must exist. |

An evidence ID is resolved against the server's scoped evidence set. A provider cannot create evidence merely by returning a plausible ID. Private authorization evidence is kept out of the model-visible context and out of public denial explanations.

### 3.2 Context and model output

`ContextPacket` contains `turn`, `current_message`, `character_profile`, `active_canon`, `visible_recent_turns`, `summaries`, `reports`, `interpretations`, `visible_facts`, `capabilities`, `pending_interactions`, `revisions`, and `policy_versions`. It contains detached immutable values, never live ORM objects.

`CapabilityDescriptor` contains `command_id`, typed parameter schema, allowed target references, `available`, safe unavailable reason, relevant preconditions, and supported speech acts. It is a view of existing game rules, not a second permission table.

`TurnProposal` contains:

- `concerns`: stable local IDs, kind (`question`, `emotion`, `request`, `correction`, `other`), and message evidence spans.
- `references`: resolved entity/topic references or explicit unresolved references.
- `reports` and `correction_candidates`: attributed statements and evidence spans.
- `operation_candidates`: zero or more candidates, each with `command_id`, typed arguments, target reference, source spans, modality (`direct`, `quoted`, `hypothetical`, `negated`, `ambiguous`), and optional pending-question reference.
- `interaction_links`: proposed links to an outstanding question or subject; these are proposals, not consent authority.
- `reply`: ordered `ReplySegment` values.
- `canon_candidates`: proposed additions/revisions linked to reply segment spans.

`ReplySegment` is a tagged union:

- `ExpressiveSegment(segment_id, text, addressed_concern_ids)` for conversational prose.
- `FactSlot(segment_id, fact_id, renderer_id)` for server-rendered current or authored facts.
- `ReceiptSlot(segment_id, receipt_id, speech_act, renderer_id)` for accepted/progress/completed results.

No segment contains executable code, arbitrary template expressions, or model-supplied critical quantities. Renderer IDs come from a server allowlist. Referencing a concern does not prove that it was answered; evaluation checks the text.

`CandidateReply` carries segments, source/version metadata, and canon candidates. `AssembledReply` carries exact final text, readable beats, a segment-to-final-span map, evidence dependencies, and candidate continuity changes. The span map is rebuilt after repair so old offsets cannot authorize new canon.

### 3.3 Negotiation and action values

`PendingInteraction` contains `interaction_id`, key, kind, originating turn, target/item/quantity, exact question text, `question_id`, `question_turn_id`, required response kind, precondition fingerprint, revision, status, and status reason. Status is `active`, `suspended`, `cancelled`, `fulfilled`, or `expired`. `expired` means relevant preconditions invalidated the negotiation; it never means a timer elapsed. The one active item-negotiation constraint is scoped to the NPC conversation. Suspended records are never implicitly selected by a bare affirmative.

`ConsentBinding` identifies the current question, the answering turn and text span, requested operation and arguments, and checked preconditions. It is assembled by application logic from interpretation and persisted context; it is not accepted as a provider-issued permission token.

`OperationDecision` is `NoOperation`, `ClarificationRequired`, `Denied`, or `ReadyToRecheck`. `ReadyToRecheck` is deliberately not an executable authorization outside the transaction.

`OperationReceipt` contains `receipt_id`, `turn_id`, game scope, NPC, canonical command/argument digest, target, outcome (`accepted`, `completed`, `rejected`), safe reason code, authoritative result fields, event IDs, before/after revisions, activity ID where applicable, and commit timestamp. An accepted activity is not a completed activity. Later progress/completion is read from authoritative activity/event state rather than rewriting the receipt.

### 3.4 Continuity and final result

`CanonRecord` contains `canon_id`, `revision`, scope, NPC, subject, predicate, content, category, origin (`authored` or `generated`), authority, status, superseded revision reference, introduction turn ID, and accepted claim evidence. Generated authority is always `narrative_only`. An origin reference is metadata, not a permission to retrieve cleared transcript.

`CanonChange` is `Add` or `Revise`, with expected canon revision, exact supporting final-speech span, and explicit correction link for a revision. A player's challenge alone produces a report, not `Revise`.

`MemoryRecord` contains scope/NPC/epoch, kind, attributed subject/content, uncertainty, source references, active/superseded status, and revision. Verified gameplay events remain in authoritative storage; a disposable conversational recollection may reference them. Emotional interpretation is an observation with source turn, not an enduring player attribute.

`ValidationFinding` contains `code`, category, severity (`blocking` or `advisory`), affected field/span, evidence references, repairability, and safe explanation. `ValidationReport` includes findings and checked evidence revisions. No unstructured string matching is treated as full semantic proof.

`FinalTurnResult` contains schema version, turn/key/sequence, `final_dialogue`, ordered `dialogue_beats`, response origin (`generated`, `repaired`, `fallback`, `mock`), degradation reason, operation receipt references, authoritative state projection/revisions, and optional diagnostic reference. It preserves existing API world-state fields through an adapter. `final_dialogue` is the complete assembled text; beats partition it without dropping characters or changing meaning.

## 4. Public interfaces and contracts

Signatures below are application protocols. `Result[T]` means `T | ConversationError`. Expected failures return typed results; unexpected exceptions are caught at the infrastructure boundary and reported as internal failures. `Deadline` and generation budgets are explicit parameters, not hidden globals.

| Interface | Contract |
| --- | --- |
| `TurnService.submit(submission) -> Result[TurnStatus]` | Validate scope/epoch; atomically deduplicate, assign sequence, and enqueue. Same ID and payload returns the existing turn; same ID with different payload is a conflict. |
| `TurnService.claim_next(key, worker_id, lease_policy) -> Result[TurnLease | None]` | Claim only the earliest nonterminal turn. Return a durable fencing token and lease; no lock remains held during work. |
| `TurnService.lookup(key, request_id) -> Result[TurnStatus]` | Read existing status/final result without generation or mutation. |
| `ContextAssembler.build(turn, budget) -> Result[ContextPacket]` | Read only the requested scope/NPC/epoch; apply NPC knowledge filtering; preserve current request and required constraints. |
| `CapabilityReader.read(scope, npc_id) -> Result[tuple[CapabilityDescriptor, ...]]` | Derive supported operations and safe reasons from authoritative services. |
| `ProposalService.propose(context, deadline) -> Result[TurnProposal]` | Exactly one provider attempt for this stage; validate decoded shape and references. Does not write state. |
| `InteractionPolicy.plan(current, proposal, context) -> InteractionPlan` | Pure transitions, question/consent linkage, and required clarification. No persistence or execution. |
| `OperationPolicy.decide(proposal, interaction_plan, context) -> OperationDecision` | Reject ineligible modalities; require clarification for ambiguous consent and multiple action requests. |
| `OperationGateway.execute_once(turn, fence, decision) -> Result[OperationReceipt]` | In one short transaction, recheck authority/preconditions and execute or persist a rejection. Recover an existing receipt before considering any execution. |
| `CompositionService.compose(context, proposal, receipt, deadline) -> Result[CandidateReply]` | For action turns, optionally invoke generation using the committed receipt. Cannot call execution. |
| `ReplyAssembler.assemble(candidate, evidence, policy) -> Result[AssembledReply]` | Pure exact rendering; fail unknown/stale slots, invalid speech acts, or overflow. Never silently truncate. |
| `ResponseValidator.check(reply, context, current_evidence) -> ValidationReport` | Check the assembled text and continuity changes. Has no game writes. |
| `RepairService.repair(candidate, findings, evidence, deadline) -> Result[CandidateReply]` | One targeted regeneration when the coordinator grants its single repair token. Cannot change or add an executable operation. |
| `FallbackPolicy.render(context, decision, receipt, failure) -> Result[AssembledReply]` | Pure, character-specific safe response; receipt outcomes take precedence over generic failure wording. |
| `CanonPolicy.plan(reply, active_canon, authored_constraints) -> Result[tuple[CanonChange, ...]]` | Admit only supported final-speech claims; validate explicit revisions and narrative authority. |
| `MemoryPolicy.plan(turn, reply, proposal) -> MemoryPlan` | Preserve attribution and corrections; exclude rejected drafts and unverified mechanical claims. |
| `Finalizer.commit(turn, fence, reply, continuity_plan) -> Result[FinalTurnResult]` | Recheck publication conditions and atomically save transcript, continuity, and durable final result. |
| `Lifecycle.clear(key) -> Result[ClearResult]` | Increment epoch and clear conversational state atomically, preserving canon and mechanics. |
| `Lifecycle.new_game(expected_scope) -> Result[WorldResult]` | Serialize against game writes, replace active scope, reset run state; reject stale reset requests. |
| `SummaryService.refresh(key, source_range, revisions, deadline) -> Result[SummaryRecord]` | Work outside the turn's mandatory generation path; publish only if sources, corrections, and epoch still match. |
| `TraceSink.emit(event) -> None` | Best-effort diagnostics; failure cannot change gameplay or turn outcome. |

Repository ports should expose purpose-specific reads and atomic application operations, not an unrestricted shared session. Test doubles implement the same contract, including uniqueness and conflict behavior. The actual SQL transaction belongs to the adapter implementing `execute_once`, `commit`, or lifecycle operations.

## 5. Persistence and concurrency

### 5.1 Proposed records and constraints

| Record | Key/constraints | Ownership |
| --- | --- | --- |
| `conversation_streams` | Unique `(game_scope, npc_id)`; current epoch, next sequence, canon revision | Turn/lifecycle adapter |
| `conversation_turns` | Unique `(game_scope, npc_id, epoch, request_id)` and `(game_scope, npc_id, epoch, sequence)`; payload digest, phase, lease fence/expiry, attempt/call budgets, final-result reference | Turn adapter |
| `conversation_operations` | Unique `turn_id`; command digest, receipt payload, result revisions | Operation gateway |
| `pending_interactions` | Scoped IDs/revisions; transactional enforcement of one active item negotiation per NPC | Finalization and operation adapters |
| `character_canon` | Unique `(scope, npc_id, canon_id, revision)`; revision lineage; active-head constraint | Canon repository through finalization |
| `conversation_summaries` | Scope/NPC/epoch, source range and revision digest, attributed summary entries | Summary adapter |
| Existing `conversations` | Add turn ID/epoch/sequence/origin linkage; unique turn ID; exact visible final text | Finalization adapter |
| Existing `memories` | Add compatible source/correction/epoch metadata; preserve verified provenance | Memory adapter |

Keep durable operation records separate from transcript deletion. Clear chat removes recoverable conversational payloads/results from the old epoch while retaining minimal identity/digest/status tombstones and necessary receipts to prevent replay. A retry from that epoch receives an invalidated status, not the erased dialogue. Canon retains its accepted narrative claim and minimal origin metadata, not a hidden copy of the cleared exchange. Raw drafts must not become an alternate cleared-history store.

### 5.2 Turn state machine

```text
QUEUED -> PREPARING -> PROPOSED -> OPERATION_RESOLVED -> FINALIZING -> FINALIZED
                  \-------------------------------> FINALIZING
Any nonterminal phase -> INVALIDATED (clear/reset)
Any prepublication phase -> recoverable failure, retaining phase/receipt and budgets
```

Recoverable infrastructure failures are not successful final turns. A subsequent claim resumes from durable state. A provider or validation failure normally finalizes a grounded fallback, allowing the next queued turn to proceed. A storage outage leaves the turn pending/retryable; it must not be skipped as if its outcome were known.

A lease supports restart recovery without a process-local mutex being the correctness boundary. Each claim advances a fencing token. Every operation/finalization write checks that token, active scope/epoch, and stream position in the same transaction. A late worker cannot commit after its lease has been replaced. Lease expiry does not itself authorize a second action: receipt uniqueness remains mandatory.

Persist repair consumption and provider-stage attempts before calling the provider. A crash after dispatch makes provider completion uncertain; recovery uses persisted output if available or falls back instead of silently resetting the call budget. Do not repeatedly regenerate an old turn on every HTTP retry. Persist only the intermediate data needed for recovery, isolated from accepted transcript and removed on conversational invalidation.

### 5.3 Transaction boundaries

**Admission:** lock/compare active scope and stream epoch; deduplicate; allocate sequence and persist queued turn. Commit before scheduling work.

**Snapshot:** read detached world/context values and close the read transaction. Context includes only finalized earlier turns. Provider calls occur after transaction release.

**Operation:** acquire the existing player/world writer lock, then NPC/stream and relevant game resources in a consistent order. Check scope, epoch, fence, turn position and existing receipt. Re-read targets, ownership, quantities, role, availability and consent. Execute using transaction-participating game services; persist receipt and turn phase; commit together. A known denial records a rejected result without a gameplay effect. An infrastructure error rolls back the entire transaction.

**Publication:** reacquire the same ordering boundary. Recheck scope/epoch/fence, canon heads, interaction revision, and the exact evidence dependencies used in speech. Commit final transcript, accepted canon changes, conversational memory, interaction transitions, final result and terminal turn status together. Receipt references remain valid historical evidence, but current-tense progress clauses require current activity evidence.

Never call the provider under the publication lock. If a relevant fact changed, leave the transaction, refresh evidence, and reassemble/revalidate within the remaining budget. If expressive prose can no longer be justified, use a grounded fallback. Persistent churn yields a recoverable conflict rather than publishing known-stale speech. Unrelated changes do not invalidate every sentence.

SQLite ignores `FOR UPDATE`; reuse the existing `lock_player` writer-lock mechanism. PostgreSQL uses the same logical lock order. Uniqueness constraints and compare-and-swap checks remain necessary on both. Different NPCs can generate concurrently even though short world-write transactions serialize.

### 5.4 Crash and race outcomes

| Failure point | Recovery |
| --- | --- |
| Before admission commits | No admitted turn; same request ID can be submitted again |
| After admission, before generation | Claim oldest turn and resume from stored submission |
| After provider dispatch, before output persistence | Preserve consumed call budget; recover with safe fallback if output is unavailable |
| During operation transaction | Resolve commit status by scoped turn/receipt lookup; never infer failure from connection loss |
| After action commit, before speech | Use existing receipt; compose/fallback without execution |
| After finalization, before HTTP delivery | Return stored exact final result |
| Clear during generation, before execution | Epoch check prevents both old execution and publication |
| Clear after action commit | Preserve action/receipt; suppress old speech/canon and clear negotiation |
| Reset races action | Writer ordering places action in old scope or rejects it; never replay in new scope |
| Lease replaced while old worker returns | Fence rejects old worker writes |
| Other NPC consumes a shared item | Recheck ownership/preconditions; return changed availability, never substitute |

## 6. Module behavior and test strategy

### 6.1 Context and capabilities

Read history using scope, NPC and epoch explicitly, including the `/world` history projection. Keep newest accepted player/reply pairs across social/factual/action categories, including degraded turns. Never retrieve raw rejected output as conversation history.

Reserve budget for current input, instructions, required operation constraints, and critical evidence first. Then retain recent pairs, relevant canon, unresolved subjects, source-linked summaries, and reports. Optional older material can be omitted deterministically. If mandatory content cannot fit, return `CONTEXT_BUDGET_EXCEEDED` and safe degradation; do not drop the current request or authorize an action from incomplete constraints.

Capability snapshots and execution checks must call the same existing rule owners. A hidden reason may be reduced to a safe public reason; private state is not exposed just because execution needs it.

**Tests:** cross-scope/NPC/epoch exclusion; wreck-report/emotional-follow-up continuity; fallback history inclusion; no private NPC knowledge; deterministic budget ordering; mandatory-content overflow; embedding outage with scoped SQL retrieval; capability view versus execution-rule conformance.

### 6.2 Proposal and provider adapter

Use the shared prompt contract with character traits supplied as data. Decode strict versioned output; validate spans, IDs, supported command schemas and parameter bounds. Preserve multiple concerns and modalities. A structurally valid proposal is still untrusted.

Extend the current provider boundary to accept structured generation purpose, output contract, deadline and response budget. Record actual provider/model/configuration. Explicit mock mode produces `origin=mock`; a live outage cannot silently switch to healthy-looking mock output. Map transport timeout, malformed JSON, unsupported schema and provider unavailability separately.

**Tests:** mixed emotion/action output; quotes, hypotheticals and negation; invalid spans and unknown IDs; malformed JSON; timeout and cancellation; exact call count; same shared prompt policy for Craftsman and Gatherer; explicit mock diagnostics.

### 6.3 Pending interactions and operation selection

| Input/condition | Transition/result |
| --- | --- |
| Relevant direct answer to current question | Bind answer to that question; recheck before operation |
| Unrelated topic | Active negotiation becomes suspended; answer new subject |
| Explicit return to suspended subject | Revalidate target/preconditions and resume; ask again if consent remains missing |
| Bare “yes” after topic shift | No operation; clarify the intended current question |
| Explicit cancellation | Mark cancelled; no transfer |
| Relevant preconditions become false or target/terms change | Mark expired with reason; explain changed situation |
| Unrelated resource revision changes | Re-evaluate relevant preconditions; do not expire solely for version churn |
| Multiple supported action requests | No operation; ask which first and persist the offered choices as an outstanding question |
| Selection of one offered action | Resolve only that selection and recheck; unselected actions are not queued commands |
| Clear/reset | Invalidate pending records through lifecycle boundary |

If multiple suspended requests make a reference ambiguous, ask which one. Never choose a suspended record merely because it is newest. A fulfilled interaction cannot authorize another transfer on retry.

**Tests:** transition table; no expiry from clock/turn advancement; unrelated purpose-like words; bare affirmation after topic shift; explicit resume; changed quantity/ownership; compound-request clarification and later selection; duplicate confirmation; cancelled/expired consent rejection.

### 6.4 Operation gateway and game integration

Use an explicit registry of conversation-eligible commands mapped to typed adapters. Registration means the underlying service and its preconditions have been audited; it does not expose every encounter endpoint to the model. For example, requesting inspection can map to accepting an outing, while reporting `complete_inspection` requires the existing arrival/staging evidence and cannot be produced merely by dialogue.

The gateway invokes existing inventory, Craftsman, Gatherer, quest and activity rules. It must not call the current `StateService.apply` with unchecked generated `state_update` or action strings. Existing deterministic relationship consequences remain permitted; free-form charm or biography cannot award trust/rewards. This design adds no new conversational relationship scoring rules.

The adapter normalizes existing service exceptions into typed denials. Services that commit internally must be refactored or wrapped at their transaction boundary before use; an effect committed separately from its receipt violates this design. Existing encounter command IDs must be derived from the stable turn operation identity, not regenerated for speech retry.

**Tests:** ownership, role and target rejection; negative/quoted/hypothetical requests; stale consent; one-operation constraint; atomic rollback on receipt failure; duplicate request under concurrent workers; lost commit acknowledgement; accepted versus completed inspection; no arbitrary relationship delta; SQLite and PostgreSQL behavior.

### 6.5 Composition, validation, repair and fallback

Exact renderer slots own critical quantities, resources, capability states and operation outcomes. Expressive prose may answer emotional/personal concerns but cannot contradict the rendered clause. Validate the entire assembled reply, not just evidence IDs or individual fragments.

Use independent checkers for structure/reference validity, mechanically consequential statements, canon conflicts, attribution, concern coverage, repetition and style. Semantic checking starts offline as prescribed by the source design. Runtime activation is selective and measured; it never authorizes an operation. Deterministic checks do not claim to prove all free prose safe.

One repair token covers proposal-format recovery or final-response repair; spending it earlier leaves none later. Repair may change speech and proposed narrative additions, but cannot add, replace or rerun an operation. Revalidate the whole repaired reply and rebuild canon spans.

Fallback priority is committed receipt, missing clarification, known unavailability, then character-specific generation-failure speech. A successful transfer followed by provider timeout must say what actually happened. General failure speech must not fabricate an answer. Fallback is also structurally/grounding validated; if even its mandatory receipt text cannot be represented, fail publication rather than misreport success.

**Tests:** accepted versus completed outcome; cancelled ongoing activity; unknown fact/receipt IDs; expressive contradiction around a correct slot; harmless “I have a soft spot” and “Fear can destroy your confidence”; whole-response repair; maximum one repair across stages; repair cannot execute; outage after successful action; role-appropriate fallback; long story beats preserve all text.

### 6.6 Canon, memory and summaries

Canon admission uses final speech, not draft metadata alone. An explicit NPC acceptance of a correction may revise generated canon if authored constraints allow it. Preserve lineage and require expected-revision matching. A player contradiction without acceptance remains an attributed report. Authored identity cannot be rewritten by this path; authorized content events belong to content/game services.

Narrative references to distant relatives or historical places remain narrative. Any implied current reachable shop, item cache, recipe or capability must be checked as an affordance, even when embedded in a story.

Summary entries retain source IDs, report attribution, uncertainty, and correction status. Refresh outside mandatory turn calls, using a durable dirty/source revision marker so a missed in-process notification is recoverable. Before writing, check epoch and source/correction revisions. Failures retain the prior valid summary or use scoped unsummarized retrieval; indexes are disposable caches. Canon revisions must invalidate stale summary interpretations rather than reviving superseded claims.

**Tests:** accepted biography survives follow-up; draft/failed-repair biography never persists; authored conflict; explicit accepted correction versus challenge; concurrent revision conflict; no generated world entity; report never promoted into event; retracted report excluded; clear removes summaries/reports but preserves canon; summary completing after clear rejected; embedding/index failure retains scope filtering.

### 6.7 Finalization and lifecycle

Finalization is the sole publisher of conversational continuity. An operation transaction may fulfill an existing negotiation; publication then reads that committed status and cannot overwrite it with an earlier interaction plan. No transcript/canon write may succeed partially.

Clear chat increments the NPC epoch and removes transcript, conversation summaries/memories, emotional interpretations and negotiations. It preserves generated canon, authored identity, relationship/encounter progress and accepted operations. Old queued work is invalidated as well as active generation. Persist a minimal invalidation record so a retry cannot revive erased speech.

New game changes scope and resets all run-scoped state. Old receipts may remain for recovery/diagnostics under a retention policy but are inaccessible to new-run conversation and gameplay. All cached/async reads and writes require matching scope; caches must not rely only on NPC ID.

**Tests:** rollback halfway through canon/transcript finalization; exact final retry; old-worker fence failure; clear before/after operation commit; preservation/deletion matrix; old `/world` history exclusion; reset during generation, summary, operation and delivery; no canon origin cascade deletion; cache invalidation across runs.

### 6.8 Diagnostics and evaluation

Extend the existing decision trace with turn/sequence/key, fence/attempt identity, stage timings, context/source IDs, policy versions, provider/model settings, proposal decisions/evidence spans, authorization, receipt, findings, repair consumption and final origin. Do not store hidden reasoning. Keep credentials out of traces. Trace sink failure cannot roll back a legitimate action or prevent receipt recovery.

Maintain at least 40 reproducible multi-turn scenarios, generally 4–8 turns, across both NPCs. Freeze game-state fixtures and model settings; record counts and evaluate relevance, mixed-concern coverage, continuity, consistency, grounding and naturalness separately. Use human-calibrated review; an automated judge is supporting evidence.

**Tests:** complete stage attribution for success/fallback/recovery; redaction; trace outage; shadow run cannot access mutation/canon-write ports. Release requires all mechanical invariant tests to pass. Quality targets remain ≥90% relevance and mixed-concern coverage, ≥95% canon consistency, <5% healthy-provider fallback, and <2% accidental consecutive repetition. Measure ordinary/action/repair p50/p95 separately; no invented latency threshold.

## 7. HTTP and Godot integration

### 7.1 Proposed additive transport

The redesigned `POST /chat` request adds `schema_version`, stable `request_id`, and `conversation_epoch` to existing `game_scope`, `npc_id`, and `player_message`. Scope and epoch are required for the redesigned path; the client obtains them from `/world`. Keep the current 500-character input bound unless separately changed. Response-length policy is separate from input length.

- `200`: durable final result, preserving `final_dialogue`, NPC, inventory, quest and encounter fields. Add turn ID, sequence, epoch, beats, state revisions and diagnostic reference.
- `202`: admitted/pending turn with turn identity and status URL. It contains no publishable draft dialogue.
- `GET /chat/turns/{turn_id}` with scope/epoch context: read pending/final/invalidated status. Polling never executes a fresh operation.
- `DELETE /chat/{npc_id}`: require expected scope/epoch for the redesigned path; return new epoch and preserved-state explanation.
- `POST /world/new-game`: require expected scope for the redesigned path and return the replacement scope.

Use one application service for synchronous completion and queued continuation. The request handler may wait within its delivery budget, then return `202`; admitted work belongs to the durable turn queue, not the HTTP connection. A process-local notification may wake a worker, but restart recovery must scan durable pending turns.

An old client without a stable ID cannot receive the new retry guarantee. Keep legacy transport behind the versioned migration path until the Godot update is deployed; do not invent a new ID on each retry and claim idempotency. The exact final speech is immutable; replayed world-state snapshots are revision-labelled and must not overwrite newer client state.

### 7.2 Client responsibilities

Split request tracking from the existing `chat_window.gd` presentation. Proposed `conversation_gateway.gd` owns request IDs, pending status/polling, retry and scope/epoch checks; `conversation_presenter.gd` owns ordered transcript/beat presentation; the existing window composes these with controls.

Persist/reuse the same request ID for delivery retries. A new player submission uses a new ID. Display finalized turns once by turn ID and sequence. Suppress invalidated epochs/scopes and deduplicate delayed repeated results. Server state refresh supplies invalidated/terminal sequence information so the UI does not wait forever for a suppressed turn.

Apply authoritative state snapshots only if their resource revisions are current/newer; never apply inventory as a repeated delta. Existing world/encounter gateways must share revision-aware state application with chat responses. If a connection fails after submission, resolve the existing turn and refresh authoritative world state rather than submitting a new action.

Text never commands movement or grants items. Animation follows verified activity/event identity, with its own deduplication. Readable beats do not imply separate game operations. Clear-chat copy explicitly states that biography and accepted actions remain; new-game copy states that run-specific progress and biography reset.

**Client tests:** final result redelivery; out-of-order replies; different-NPC shared-state snapshots; clear/reset while polling or showing beats; disconnect after action commit; old snapshot cannot rewind inventory/activity; long replies without truncation; story wording cannot trigger animation.

## 8. Error handling matrix

`ConversationError` contains stable code, stage, retryability, turn reference when known, and safe client detail. Internal exception/context data stays in diagnostics. A retry always means lookup/resume using the same submitted identity unless the client explicitly submits a new message.

| Error/condition | Handling | External result |
| --- | --- | --- |
| Invalid input/schema/bounds | Reject before admission | HTTP 422 |
| Unknown NPC/current save missing | Reject without generation | HTTP 404 or explicit unavailable-save error |
| Stale scope/epoch | Invalidate/reject; no old publication | HTTP 409; refresh world |
| Request ID reused with different payload | Reject; preserve original turn | HTTP 409 |
| Turn already pending | Return same identity/status | HTTP 202 |
| Provider timeout/unavailable/malformed output | Use remaining repair only if appropriate; otherwise fallback | Final 200 with degraded origin, if persistence succeeds |
| Action unsupported/ambiguous/unavailable | Clarification or grounded denial; no unauthorized mutation | Final 200 with actual decision |
| Resource changed before action | Revalidate; deny/clarify changed terms | Final 200; no silent substitution |
| Evidence/canon changed before publication | Reassemble outside lock or fallback; do not publish stale claims | Final result or recoverable 409 |
| DB busy/unavailable/commit uncertain | Roll back where known; resolve durable receipt/status before retry | HTTP 503 or connection failure; never fabricated success |
| Embedding/index failure | Scoped nonsemantic retrieval | Normal/degraded final result with trace |
| Summary failure | Retain valid previous summary or omit stale one | No mandatory turn failure |
| Trace failure | Best effort diagnostic handling | No gameplay change |
| Unexpected internal exception | Preserve recoverable state, record safe failure | HTTP 500; same-ID recovery |

Queue saturation and worker lease/deadline values are deployment policies, not gameplay intent. Validate finite positive policy bounds at startup and exercise them with fake clocks. Once a turn is admitted, reaching an HTTP timeout cannot discard its identity or reset its execution budget.

## 9. Existing integration map and coupling risks

| Existing area | Required integration/change | Coupling risk and mitigation |
| --- | --- | --- |
| `services/pipeline.py` | Delegate to injected coordinator and adapters | Existing constructor hides concrete dependencies; remove direct provider/DB coupling from domain orchestration |
| `services/context/social.py`, `context/builder.py` | Retire binary permission routing; use unified scoped context | Old social-history assertions can erase action context; replace with authority/scope tests |
| `context/grounding.py`, `prompts/builder.py` | Supply facts/renderers and shared character-data prompt | Duplicated fact policy; maintain one evidence/renderer contract |
| `services/llm/*` | Deadline-aware versioned proposal/composition/repair adapter | Provider decoder and API length limits can disagree; one policy version across layers |
| `validation/items.py`, `craftsman_intent.py` | Replace heuristic consent interception with interaction/operation contracts | Broad text heuristics can bypass interpretation; no direct mutation from those recognizers |
| `services/state/service.py` | Adapt authoritative effects; exclude generated state deltas | Current output combines speech and mechanics; split typed requests from validated prose |
| `services/craftsman.py`, `gatherer.py`, quest services | Expose views and transaction-participating operations/receipts | Nested commits or duplicate command identities break atomicity; adapter conformance tests |
| `models/conversation.py`, `memory.py`, memory retrieval | Add scope/epoch/turn provenance and separate canon | Transcript deletion may erase canon origins or receipts; minimal independent origin metadata |
| `api/routes/chat.py`, `world.py` | Versioned submission/status/clear/reset and scoped histories | Current `/world` history query uses NPC alone; enforce active scope/epoch everywhere |
| `app/dialogue/compose.py` | Reuse only compatible renderers/value contracts or adapt explicitly | Existing 300-character contract and substring success checks conflict with new prose; do not silently run both policies |
| `services/decision_trace.py` | Extend existing trace sink | Diagnostic failure must not become gameplay failure |
| `chat_window.gd`, `main.gd`, encounter gateways | Stable turn IDs, beats, epoch and revision-aware state application | Multiple response handlers can rewind world state; centralize application by resource revision |

Further coupling risks:

- **Shared writer lock:** needed for cross-NPC mechanics; keep transactions short so concurrent generation remains useful. Never hold it across provider calls.
- **Catch-all context object:** avoid passing the entire context into every checker; use small typed projections so tests need only relevant evidence.
- **Finalizer becoming a policy engine:** it checks preconditions and commits prevalidated plans; canon/interaction/memory rules remain pure modules.
- **Capability drift:** do not independently author permissions in prompts, capability descriptors and execution. Derive views from the authoritative rule owner and test conformance.
- **Unversioned external state writes:** all inventory, quest and activity mutation paths must participate in revision discipline, including non-chat endpoints. Otherwise publication checks and client snapshot ordering are unreliable.
- **Summaries and caches as authority:** every cached record retains scope/source revision; DB-filtered retrieval precedes index use. Semantic similarity never upgrades provenance.
- **Rollback bypassing recovery:** legacy generation may be restored, but accepted operations and receipts must remain under the idempotent boundary. Never route an unresolved redesigned turn through an executor that ignores its receipt.

## 10. Verification and adoption boundaries

Use three layers of automated verification:

1. Pure module tests with immutable fixtures, fake clock/token counter, scripted provider and no database/network. Each module's cases are specified in section 6.
2. Adapter contract and transaction tests on both supported database engines. Include duplicate concurrent submissions, lease fencing, commit uncertainty, clear/reset races and cross-NPC contention.
3. API/Godot integration and conversation replay tests. Separate deterministic mechanical assertions from human-calibrated language quality scoring; do not require exact live-model prose.

Use additive migrations and a versioned behavior switch. Preserve existing mechanical regression coverage. Do not reclassify old memories as generated canon; unknown legacy scope/provenance is excluded from new context unless migration can establish it. Shadow evaluation receives read-only snapshots and cannot execute operations, publish canon, or alter active interactions.

Before enabling the redesigned path, verify provider health and baseline response origins, inventory all current limits, establish renderer/operation registries from actual game services, and run the full lifecycle and retry suite. Both NPCs must have authored profiles and fallback support. Rollback preserves actions/receipts and can leave generated canon stored but inactive, as required by the proposal.

### Measurements intentionally left to implementation baseline

The source documents explicitly defer numeric latency and tuning. Maintain a versioned `ConversationPolicy` for total processing deadline, provider stage budget, context tokens, output/beat limits, queue capacity, lease duration, summary trigger, and diagnostic retention. Validate compatibility across provider, Pydantic, composer and Godot before rollout. Lease and request budgets are distinct from negotiation lifetime; no value in this policy may introduce automatic negotiation expiry.

Record measured candidate values and obtain product acceptance for playable latency and readable reply limits before shipping. This design does not choose a replacement model, invent new relationship mechanics, expand supported actions, or define new authored character identities. Those require their own explicit requirements if pursued.
