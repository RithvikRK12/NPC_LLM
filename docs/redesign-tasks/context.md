# context implementation tasks

**Goal:** Deliver the `context` responsibility in the NPC conversation redesign.
**Status:** T01–T05 locally verified; broader integration and live dialogue-quality gates remain open.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§3.2,6.1; Proposal §7.
**Owned files / integration targets:** backend/app/services/conversation/context.py; backend/app/services/context/{builder,social}.py; backend/tests/test_conversation_context.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [contracts](contracts.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### context/T01: Build unified scoped evidence and history

- [x] **Task complete locally** — concrete persistence finality/scope filtering remains an integration gate.

**Depends on:** ports/T01.
**Acceptance criteria:** ContextAssembler.build(turn, budget) reads detached values only for scope/NPC/epoch and finalized earlier pairs, including visible fallback. Include profile, canon, reports, unresolved subjects, capabilities and revisions without binary social permission routing.
**Test expectations:** Wreck report then fear retains context; action then gratitude retains context; reject cross-NPC/scope/epoch, future/nonfinal and raw-draft history; exclude private knowledge.

- [x] Add focused failing behavioral/contract tests; expected missing-module failure recorded in the handoff.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent read-port conformance; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### context/T02: Apply deterministic context budget and degraded retrieval

- [x] **Task complete**

**Depends on:** context/T01; contracts/T03.
**Acceptance criteria:** Reserve current input, instructions, operation constraints and critical evidence first; then recent pairs, canon, unresolved subjects and source-linked older context. Mandatory overflow returns CONTEXT_BUDGET_EXCEEDED; SQL scope filtering precedes optional index retrieval.
**Test expectations:** Deterministic token counter pins retention order; overflow never drops current request or constraints; embedding/index outage uses scoped nonsemantic retrieval; stale canon/summary revisions excluded.

- [x] Add focused failing behavioral/contract tests for the cases above (or reproducible measurement checks for baseline/release evidence).
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and the adjacent dependency conformance cases relevant to this task; record passing evidence.
- [x] Review acceptance criteria, record handoff/output changes, and update this task and master progress.

### context/T03: Integrate persisted scoped history into ContextReadPort

- [x] **Task complete locally** — accepted 2026-10-18 after SQLite/PostgreSQL integration and full backend reproduction.

**Recorded expansion (2026-10-18):** persistence-adapters/T04 now provides detached finalized prior-turn reads and SQL summary sources, but no concrete `ContextReadPort` producer exists. A complete `ContextPacket` also requires context-owned profile/canon/report/interaction/fact sources, and the context producer must prove the deterministic player-text ID convention. This integration belongs to context, while persistence remains the authority for scope/finality filtering.
**Depends on:** context/T01–T02; persistence-adapters/T04; ports/T01; contracts/T08 (literal `/world` scope value).
**Acceptance criteria:** Implement a concrete context read adapter that assembles detached, scope/NPC/epoch-checked inputs from authoritative readers, including finalized prior turns from `read_prior_turns`; preserve `/world` as a literal scope; never admit draft/legacy-unproven history; bind player text source IDs exactly to producer values; call optional ranking only after the SQL snapshot is closed.
**Test expectations:** SQLite and PostgreSQL integration for exact scope/NPC/epoch/finality, `/world`, text-ID binding, and read connection closure before embedding; context contract tests for packet composition and fail-closed unavailable evidence.

- [x] Add focused integration tests and demonstrate expected failure before implementation.
- [x] Implement the concrete ContextReadPort adapter through owned context/read contracts.
- [x] Run SQLite/PostgreSQL and adjacent context checks; record evidence.
- [x] Review source coverage, handoff and module interfaces; update task and master progress.

### context/T04: Author rich NPC bibles and deliver bounded personal context to both dialogue paths

- [x] **Task complete locally** — user-approved and verified 2026-10-19; live dialogue-quality gates remain open.

**Recorded expansion (2026-10-19, explicit user request):** Develop rich, consistent characters for every current NPC (the seed roster contains Craftsman and Gatherer). This is a new bounded deliverable; T01–T03 and proposal/T02 acceptance criteria remain unchanged. The user explicitly requests review of the character/profile design and affected files before implementation. Historical evaluation fixtures and release gates remain unchanged.
**Depends on:** context/T03; proposal/T02.
**Affected modules:** context (source profiles, deterministic compact selection, legacy personal-topic classification, SQL read projection); proposal/prompts (both prompt paths and revised narrative instructions); legacy validation (only profile-related false positives); adjacent canon/grounding/capability boundaries tested without adding canon extraction or mechanics.
**Owned files / permitted integration targets:** `backend/app/services/context/characters/{craftsman,gatherer}.json` (new rich authored sources); `backend/app/services/context/character_profiles.py` (new shared loader/projector); `backend/app/services/context/craftsman_profile.py` (compatibility); `backend/app/services/context/social.py`; `backend/app/services/prompts/builder.py`; `backend/app/services/conversation/adapters/context_read.py`; `backend/app/services/validation/service.py`; focused new `backend/tests/test_character_profiles.py`; existing generation/context/grounding tests as needed; `docs/evidence/conversation-redesign-context/t04/`. Confirm the final subset during design review; preserve existing changes in shared targets.
**Acceptance criteria:**
1. Rich source bibles for both seeded NPCs cover formative background; motives/values/contradictions/flaws/boundaries; routines/skills/tastes/mannerisms; relationships and audience-dependent behavior; voice/emotional tells and varied example dialogue; known/believed/suspected/misremembered/unknown information; conditional story threads; fixed continuity and forbidden claims. Personal history is explicitly authored narrative, never verified gameplay state. No new reachable people/places, inventory, quests, recipes, schedules, abilities or relationship mechanics.
2. A shared, deterministic, bounded projection supplies stable identity/voice/continuity boundaries plus relevant personal details to the legacy prompt and the concrete redesigned SQL context/prompt flow, including when identity evidence already exists. Do not send the full bible on every turn or add provider calls/dependencies. Use role/identity consistently and a safe fallback for unsupported NPCs; keep profile provenance/version explicit.
3. Instructions prioritize answering the current message and mixed concerns directly; use personal detail only when relevant; avoid player paraphrase, stock openings, repeated replies and compulsory anecdotes. Separate self-belief and uncertain recollection from facts; examples are style references, never completed player events. Story progression requires visible conversation or verified state, never a fabricated prior discussion/encounter.
4. Narrow legacy personal-topic/validation adjustments permit source-backed personal dialogue for both characters while preserving factual rendering, state/action constraints, encounter guards and rejection of false stock, deliveries, locations, promises and outcomes. No general routing redesign, new semantic validator, response-limit changes, migrations or generated-canon producer.
5. Test-first behavioral checks demonstrate both real profile-to-prompt flows, relevant bounded selection, distinct characters, authority separation, continuity constraints and representative allowed personal/rejected mechanical claims. Run relevant existing context/generation/grounding/pipeline tests. Record unavailable live quality checks honestly; deterministic prompt tests do not prove live dialogue quality.
**Test expectations:** Source completeness/roster coverage; short greeting vs background/fear/relationship/follow-up projection; no full-bible dump; both legacy and SQL-context-to-structured-provider prompt capture; supplied identity does not suppress persona; scoped profile source/version and detached data; unsupported identity safety; no private counterpart history; authored narrative cannot authorize inventory/quests/encounter changes; example replies and hostile player attempts preserve existing mechanics. Reproduce relevant SQLite/PostgreSQL context adapter checks if adapter behavior changes; no player save. Preserve frozen evaluation evidence; any new live comparison is separately labelled.

- [x] Inspect roster, profiles, lore/facts, legacy and redesigned profile-to-prompt paths; identify blockers and bounded ownership.
- [x] Record task in packet, master progress and task graph before implementation/design scope expansion.
- [x] Present proposed characters, profile projection, affected files and verification for user approval — user approved 2026-10-19.
- [x] After approval, add focused failing checks, implement only T04, and verify adjacent boundaries — 1,079 backend tests and five PostgreSQL checks pass.
- [x] Review acceptance, record evidence/limitations, update packet/master/graph and recommend next task — independent review approved; [handoff](../evidence/conversation-redesign-context/t04/handoff.md).

### context/T05: Improve continuity and gameplay grounding while preserving the 600-character ceiling

- [x] **Task complete locally; live quality limitations recorded**

**Recorded expansion (2026-10-19, explicitly authorized):** T06 Reviewer 1 scores and notes identify repeated Craftsman context, unsupported activity/mechanics claims, and replies cut at the 600-character ceiling. Improve the shared dialogue directions and enforce the hard maximum without increasing it. This is a new bounded task; T04 profile content and game mechanics remain unchanged.
**Depends on:** context/T04; evaluation-release/T06.
**Affected modules:** context/profile-to-prompt direction; structured and legacy prompt builders; ConversationPolicy output-bound contract; read-only configured replay adapter and new replay evidence.
**Owned files / permitted integration targets:** `backend/app/services/context/character_profiles.py`; `backend/app/services/prompts/builder.py`; `backend/app/services/conversation/contracts.py`; focused profile/prompt and policy contract tests; `docs/evidence/conversation-redesign-release/t01/configured_replay.py`; a new `improved-character-guidance-600/` evidence directory; this packet, master progress and task graph. Preserve all existing T04/T06/profile and T05/T06 replay artifacts.
**Acceptance criteria:** (1) Prompt guidance makes the current player turn primary, prevents redundant recap, treats prior NPC speech as conversational context rather than authoritative game evidence, and directs all mechanic/activity claims to supplied current facts/capabilities. (2) Replies should complete within the applicable output contract; optional detail is removed before sentence completion is sacrificed. (3) No configured conversation policy may permit final dialogue above 600 Unicode code points; reject a policy configured above 600 and retain exact 600 as the maximum. Preserve any stricter configured limit. (4) No new game mechanics, profile canon, model, or dialogue ceiling. (5) Run the frozen 44-scenario/176-turn replay under the same model/settings and 600-character max in a new directory; record hashes, six denominators, state digest, cap-hit count and punctuation/ending observations. Leave T06 artifacts untouched.
**Test expectations:** First add failing tests for current-turn/non-recap and non-authoritative-history guidance in both prompt builders, and for `output_char_limit=601` rejection while 600 is accepted. Verify assembled output cannot pass 600 under valid configured policy. Run focused prompt, policy, composition/fallback tests and the complete conversation suite; run the live replay if the frozen local provider remains available.

- [x] Inspect T06 Reviewer 1 form, exact candidate provenance, prompt paths and output-bound enforcement; identify module/file scope.
- [x] Record this task in the packet, master progress and task graph before implementation.
- [x] Add focused failing behavioral/contract tests and record expected failures.
- [x] Implement prompt guidance and hard-cap changes; preserve existing boundaries.
- [x] Run focused and adjacent checks; replay all 176 turns under the unchanged 600-character maximum.
- [x] Record evidence, findings and next action in this packet and master progress.

**Results (2026-10-19):** Both prompt paths prioritize the current turn, avoid unrequested recaps, and distinguish conversational history from authoritative mechanics. Policies above 600 are rejected; legacy rendered and generated responses remain capped at 600. Focused checks passed (164/164), and the full backend suite passed (1,083/1,083). The separate Llama 3 replay generated 176/176 turns with matching state digests and unchanged denominators. Cap hits fell from 13/176 in T06 to 4/176; all four still lack sentence-final punctuation. The raw adjacent exact-repeat count rose from 17 to 21, but includes purposeful reminders and repeated stress-fixture turns and is not a reliable unwanted-repetition measure. Reviewer 1 then scored the same 24 sample references in T06 and T05: continuity rose from 2.75 to 4.00, but the overall mean fell from 4.00 to 3.29, with declines in directness, coverage, character consistency, grounding and naturalness. Treat the prompt change as mixed, not as a validated overall improvement. [Replay, completed form and analysis](../evidence/conversation-redesign-release/t01/improved-character-guidance-600/README.md).

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | context_t01 / locally accepted 2026-10-15; gpt-6-luna / medium; Main Agent reproduced 52/52 combined checks | [Handoff](../evidence/conversation-redesign-context/t01-handoff.md); focused and conformance reproduced: exit 0, 52 pass, 0 fail/skip | Durable-final filtering and SQL scope remain persistence-adapter duties; budget policy is T02 |
| T02 | context_t02 / accepted by Main Agent 2026-10-18; gpt-6.1-sol / high | 14 focused, 65 adjacent, 363 conversation, and 826 backend tests pass; independent review approved; evidence `../evidence/conversation-redesign-context/t02-handoff.md` | Concrete ContextReadPort assembly and provider tokenizer integration remain open |
| T03 | Main Agent / locally accepted 2026-10-18; runtime model routing unavailable | Focused SQLite 28/28; PostgreSQL 16.15 4/4; conversation 497/497; full backend 965/965; diff check clean | [Handoff](../evidence/conversation-redesign-context/t03-handoff.md); logs: `../evidence/conversation-redesign-context/t03-sqlite.log`, `t03-postgresql.log`, `t03-backend-suite.log` | ContextReadPort implemented; live interaction-precondition projection and coordinator/pipeline wiring remain downstream |

| T04 | Main Agent / locally accepted 2026-10-19; independent reviewer approved; runtime model/effort identifier unavailable | [Handoff](../evidence/conversation-redesign-context/t04/handoff.md); 106 focused/adjacent; final affected checks 48/48; final backend 1,079/1,079; PostgreSQL 16.15 context/scoped reads 5/5; no failures/skips; graph and whitespace checks pass | Rich source bibles and bounded shared profiles reach both real prompt paths; conservative legacy paraphrase and unmeasured live quality limitations recorded; no gameplay changes |
| T05 | Main Agent / locally verified 2026-10-19; runtime model/effort identifier unavailable | Prompt/policy tests 164/164; backend 1,083/1,083; 176-turn replay and review forms in [improved-character-guidance-600](../evidence/conversation-redesign-release/t01/improved-character-guidance-600/) | Cap-hit rate improved but four likely cutoffs remain; raw exact-repeat count is inconclusive. Human review and broader integration remain open. T04/T06 history preserved |
