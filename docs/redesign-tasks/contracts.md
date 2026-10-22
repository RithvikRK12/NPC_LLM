# contracts implementation tasks

**Goal:** Deliver the `contracts` responsibility in the NPC conversation redesign.
**Status:** T01–T09 locally accepted; adapter provenance and runtime integration remain open.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§1,3,8,10.
**Owned files / integration targets:** backend/app/services/conversation/contracts.py; backend/app/services/conversation/interactions.py; backend/app/services/conversation/operations.py; backend/tests/test_conversation_contracts.py; backend/tests/test_conversation_interactions.py; backend/tests/test_conversation_operations.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [baseline](baseline.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### contracts/T01: Define identity, evidence and policy values

- [x] **Task complete**

**Depends on:** baseline/T01.
**Acceptance criteria:** Implement immutable ConversationKey, TurnSubmission, TurnRef, RevisionSet, SourceRef, TextSpan, six tagged Evidence classes, ConversationPolicy, Deadline and ConversationError. UTC timestamps; Unicode code-point spans; one versioned bounds policy; server-resolved player.
**Test expectations:** Round-trip fixtures; reject unknown versions/fields, invalid bounds and spans; fake clock validates finite positive policies; generated canon/reports cannot inhabit mechanical tags.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### contracts/T02: Define proposal, negotiation and operation values

- [x] **Task complete**

**Depends on:** contracts/T01.
**Acceptance criteria:** Implement ContextPacket, CapabilityDescriptor, TurnProposal, ReplySegment union, CandidateReply, AssembledReply, PendingInteraction, ConsentBinding, OperationDecision and OperationReceipt exactly as design §3. One operation per turn; accepted differs from completed.
**Test expectations:** Strict union decoding; reject arbitrary renderer expressions, model-supplied slot quantities and malformed command arguments; exercise all modalities/statuses and exact span references.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### contracts/T03: Define continuity, result and cross-language fixtures

- [x] **Task complete**

**Depends on:** contracts/T02.
**Acceptance criteria:** Implement CanonRecord/CanonChange, MemoryRecord, ValidationFinding/Report, FinalTurnResult and interface result/status values from §4. Beats preserve complete text; origin includes mock; scope/epoch are distinct from legacy IDs.
**Test expectations:** Shared valid/rejected JSON fixtures verify full-text beat reconstruction, revisions, correction lineage and legacy mapping; confirm values are detached and immutable.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### contracts/T04: Complete public interface value envelopes

- [x] **Task complete**

**Depends on:** contracts/T03.
**Recorded expansion (2026-10-14):** During ports/T02 signature review, detailed design §4 references `TurnLease`, `LeasePolicy`, `InteractionPlan`, `MemoryPlan`, `ContinuityPlan`, `ClearResult`, `WorldResult`, and `SummaryRecord`, and durable attempt/recovery values for persisted provider-stage consumption/output snapshots, which are absent from the accepted contracts. Existing `Result[T]` also cannot represent a successful optional/no-value result because its exactly-one-branch validator treats `value=None` as empty. This task fills those contract gaps; it does not implement ports or adapters.
**Acceptance criteria:** Define immutable, typed, detached values for the missing §4 interface envelopes and an unambiguous typed successful-none/optional result representation, preserving existing contracts and the distinction between expected errors and successful absence. Keep lease policy separate from conversation policy; preserve explicit scope/epoch, fencing, revisions, source ranges, durable attempt/recovery state, and lifecycle outcomes where applicable.
**Test expectations:** Valid/rejected shared JSON fixtures, round trips and immutability; none-ready turn is distinct from an error; stale fences/revisions and malformed scopes/statuses rejected; schema/import boundaries remain pure.

- [x] Add focused failing contract tests for the missing §4 value shapes.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent contract conformance; record evidence.
- [x] Review acceptance criteria and update task/master progress.

### contracts/T05: Add typed interaction lifecycle cues

- [x] **Task complete locally** — contract values and fixtures are frozen; interaction policy remains downstream.

**Recorded expansion (2026-10-15):** interaction/T01 requires explicit cancel/resume and authoritative relevant-precondition outcomes, but frozen `TurnProposal` and `ContextPacket` cannot carry these cues. The user selected a versioned shared contract boundary. This task adds typed, scoped values and fixtures before interaction policy implementation; it does not infer lifecycle intent from raw text or grant authority to provider output.
**Depends on:** contracts/T04.
**Acceptance criteria:** `TurnProposal` can carry explicit, span-linked cancellation/resume cues as proposals only; `ContextPacket` can carry current server-evaluated relevant-precondition state for pending interactions, scoped by interaction ID and fingerprint. Invalid/mismatched/missing values fail closed; server-private details do not enter public explanations. Keep consent and actual lifecycle changes under application/persistence authority.
**Test expectations:** Valid/rejected JSON fixture round trips; cancel/resume cues require exact source spans and known IDs; authoritative precondition status is tied to matching current interaction fingerprint; stale/missing status cannot authorize resume or expire by itself; immutable nested values; pure imports.

- [x] Add focused failing contract tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent conversation-contract/read-port checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

### contracts/T06: Define typed validator claim and evidence projections

- [x] **Task complete locally**

**Recorded expansion (2026-10-15; user selected versioned shared contract):** Main Agent review of validation/T01 found that its frozen inputs can identify source references and active canon records but cannot express typed final-speech propositions for a reliable canon-conflict check. The current `AssembledReply` has prose/spans and continuity IDs; `NarrativeCanon` has current canon content, but no proposition relation. String matching alone cannot establish semantic contradiction under detailed design §3.4. This task adds versioned, detached claim/evidence projection values before validator work resumes. No provider output or projection grants gameplay authority.
**Depends on:** contracts/T05.
**Acceptance criteria:** Define strict versioned claim projections tied to exact final-reply spans and scoped current evidence projections with canonical IDs/revisions/authority. Explicitly represent supported, contradicted, and unknown comparison outcomes; missing/unknown projection never authorizes or silently marks a claim consistent. Keep semantic checking offline and preserve narrative-only canon authority.
**Test expectations:** Round-trip/rejection fixtures for malformed spans, scope/ID/revision mismatch, private evidence, unknown outcomes and explicit contradictions; pure imports.
**Decision:** User selected a versioned shared contract boundary. Keep this deliverable within the contracts module; validation/T01 resumes after the contract is accepted.

- [x] Add focused failing contract tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent conversation-contract checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

### contracts/T07: Preserve exact executable terms in consent-bearing interactions

- [x] **Task complete** — accepted by Main Agent 2026-10-18 after contract, interaction, operation and gateway reproduction.

**Recorded expansion (2026-10-18):** persistence-adapters/T03 review found that `PendingInteraction` stores item/quantity/target for item negotiation and options for action choice, but cannot identify the exact command direction for a single item/activity offer. `ConsentSnapshot.operation` must be persisted authority; reconstructing it from the submitted answer would bypass the exact-consent boundary. This task adds the missing typed operation binding and makes the pure interaction/operation policies validate it when consuming an existing single-offer interaction. The current answer span remains separate from the stored operation’s original source spans. It does not create new item/activity interactions, authorize execution or change game behavior.
**Depends on:** contracts/T06; interactions/T02.
**Acceptance criteria:** Extend `PendingInteraction` with an optional typed `authorized_operation` for a single executable item negotiation/activity offer. Require it to be a direct operation, target the same entity, and bind the current question; item and quantity must match the interaction. Action-choice continues to preserve `offered_operations` and selects only one exact option. Legacy/missing bindings remain representable but must fail closed in the gateway and pure consent/operation policies; current deterministic precondition and consent checks remain required. The interaction policy compares the answering operation terms (command, arguments, target, modality, current question) with the persisted binding before producing consent. Keep the current answer operation and its source span in `ConsentBinding` and `ReadyToRecheck`; the gateway independently compares its terms with the persisted operation and validates the answer span against the admitted turn. Do not require a per-turn candidate ID or source span to equal the original stored candidate; do not add item/activity interaction creation.
**Test expectations:** Round-trip and reject malformed/mismatched command, arguments, target, question and modality; item negotiation command direction survives storage; exact single activity offer survives; choices retain all inert options until exact selection; old missing binding is not promoted to consent; mismatched/ambiguous/non-direct answering proposals produce no consent. Contract, interaction, and operation focused suites pass.

- [x] Add focused failing contract, interaction, and operation-policy tests.
- [x] Implement the typed binding and interaction/operation policy validation; preserve existing consent invariants.
- [x] Run focused and adjacent conversation tests; record evidence.
- [x] Review the interface handoff and update task/master progress.

### contracts/T08: Permit literal path-prefixed game scopes

- [x] **Task complete locally** — accepted 2026-10-18 after contract tests and SQLite/PostgreSQL context integration.

**Recorded expansion (2026-10-18):** context/T03 requires `/world` to remain a literal scope through context reads. `ConversationKey.game_scope` and dependent provenance/result scope fields currently reuse the general `Identifier`, whose pattern rejects `/world`. This task adds a dedicated, bounded game-scope value across contracts while preserving the general identifier rules. It does not alias `/world` to `world`, change legacy ID mappings, or relax unrelated identifiers.
**Depends on:** contracts/T07; context/T03 integration requirement.
**Acceptance criteria:** Define a strict game-scope contract that accepts existing opaque IDs and supported slash-prefixed scopes such as `/world`, rejects blank/unsafe values, and is used consistently for conversation keys and provenance/result values carrying a game scope. Persistence and API continue comparing scopes literally.
**Test expectations:** Contract round trips and rejects malformed scopes; SQLite/PostgreSQL context read tests prove `/world` and `world` remain distinct.

- [x] Add focused failing scope-contract tests and capture expected failure.
- [x] Implement the dedicated scope type in the task-owned contract fields only.
- [x] Run focused contract and context-read checks; record exact evidence.
- [x] Review serialized fixture impact and update task/master progress.

### contracts/T09: State typed speech-claim projection coverage

- [x] **Task complete** — Main Agent accepted 2026-10-18 after validation/T01 review and fail-closed coverage verification.

**Depends on:** contracts/T06.
**Acceptance criteria:** Version `ValidatorClaimProjection` with an explicit coverage outcome (`complete`, `partial`, or `unavailable`) bound to the exact final text. Consumers distinguish complete extraction from partial/missing claims without inferring completeness from a nonempty claim list. No projection field grants mechanical authority or bypasses source validation.
**Test expectations:** Missing/invalid coverage is rejected; partial and unavailable coverage produce blocking validator findings; complete coverage is accepted only for the exact projected text; wrong text ID remains invalid.

- [x] Add focused failing contract and validator tests.
- [x] Implement the additive versioned contract and fail-closed validator consumption.
- [x] Run contract/validation and full conversation suites.
- [x] Record handoff, evidence and limitations.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | contracts_identity / accepted 2026-10-14; gpt-6.1-sol / high; independent review_contracts_t01 approved | [Handoff/red-green evidence](../evidence/conversation-redesign-contracts/t01-handoff.md); focused 16/16 pass exit 0 reproduced by Main Agent; dependency 13/13 pass; infrastructure/schema check exit 0 | Frozen T01 values; no runtime integration or shipping tuning. contracts/T02 ready. |
| T02 | contracts_turn_values / accepted 2026-10-14; gpt-6.1-sol / high; independent review_contracts_t02 approved | [Handoff/red-green evidence](../evidence/conversation-redesign-contracts/t02-handoff.md); 24/24 focused, 40/40 combined conversation, 13/13 dependency tests pass; schema/import and diff checks pass | Strict turn/proposal/reply/interaction/operation/receipt values; consent binds the current question TurnRef and later answer; source authenticity remains with interaction adapter |
| T03 | contracts_t03_design / accepted 2026-10-14; gpt-6-luna / medium; independent review_contracts_t03 approved after projection immutability correction | [Handoff/red-green evidence](../evidence/conversation-redesign-contracts/t03-handoff.md); 7/7 focused, 47/47 combined conversation, 13/13 dependency tests pass; schema/import and diff checks pass | Canon, memory, validation, final-result and explicit legacy mapping values; no runtime wiring or source-authenticity proof |
| T04 | contracts_t04 / accepted 2026-10-14; gpt-6.1-sol / high; independent review_contracts_t04 approved after shared repair-token correction | [Handoff/red-green evidence](../evidence/conversation-redesign-contracts/t04-handoff.md); 12/12 focused, 71/71 conversation, 13/13 dependency, 534/534 backend tests pass; schema/import and diff checks pass | Added explicit lease, plan, lifecycle, summary, durable attempt/recovery and optional-success envelopes; adapters still prove authority/atomicity |
| T05 | contracts_t05 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed and reproduced full backend suite | [Handoff/red-green evidence](../evidence/conversation-redesign-contracts/t05-handoff.md); focused 7/7, adjacent 102/102, full backend 655/655 pass; schema/import and whitespace checks pass | Versioned explicit cancel/resume proposals and server-evaluated precondition values; lifecycle policy, server authenticity and persistence remain downstream |
| T06 | contracts_t06 / locally accepted 2026-10-15; gpt-6-luna / medium; Main Agent reviewed and reproduced | [Handoff/red-green evidence](../evidence/conversation-redesign-contracts/t06-handoff.md); focused 4/4, contract suite 70/70, validation 6/6 pass; imports, compile and diff check clean | Typed claim/evidence/comparison values are versioned and narrative-only; authoritative provenance remains an adapter duty |
| T07 | contracts_t07 / assigned 2026-10-18; gpt-6.1-sol / high | Add typed exact-operation binding and pure interaction/operation policy validation | Contract/policy seam only; adapters remain execution authority |
| T08 | Main Agent / locally accepted 2026-10-18; runtime model routing unavailable | RED: `/world` rejected by generic Identifier; GREEN: 2/2 scope tests; SQLite/PostgreSQL context integration passed | [Handoff](../evidence/conversation-redesign-contracts/t08-handoff.md); full backend 965/965 in context/T03 evidence | General identifiers unchanged; context/T03 owns persistence integration |
| T09 | Main Agent / accepted 2026-10-18 | [Handoff](../evidence/conversation-redesign-contracts/t09-handoff.md); contracts 5/5, validation 13/13, conversation 518/518, backend 986/986; diff check clean | Exact-text whole-reply coverage is explicit; partial/unavailable outcomes fail closed and carry no mechanical authority |
