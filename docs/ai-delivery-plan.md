# NPC AI delivery plan

Status: active implementation scope. Created 2026-10-12. Grounding, disposable Godot verification and scoped C1/C2 behavior with B2 reset safeguards and D1 accepted-experience provenance implemented; evidence and limitations below.

## Goal and scope

Deliver a bounded village NPC system that demonstrates how generative AI improves conversation and behavior through grounded knowledge, validation, fuzzy/FSEC selection and managed memory. The existing village and bow quest are the integration environment. A teammate owns the new story and quest content.

This plan replaces the 59-module architecture checklist as the project goal. The old [master progress](master-progress.md), [design](detailed-design.md) and task packets remain historical evidence and implementation references. Their remaining modules are not a completion requirement. Reuse completed code when it helps the scenarios below; do not build infrastructure simply to satisfy its original packet.

The AI demonstration is due in three days. This is a priority constraint, not a promise that every task below fits that window. Establish progress through working scenarios and measured results. Broader gameplay can follow without reopening the old architecture scope.

## What reliability means

- Ordinary questions receive useful answers supported by supplied knowledge.
- NPCs distinguish public knowledge, observations, historical memories and player claims.
- Unknown information leads to uncertainty or a clarifying question.
- Invalid model output cannot authorize inventory changes, quest completion or rewards.
- Fuzzy tendencies and FSEC affect visible behavior within role and world constraints.
- Important verified experience influences later decisions without repeated rewards.
- Failures are diagnosable and degrade to a bounded, zero-effect response.

No claim of hallucination-free natural language is required. Structured references help inspect grounding but do not prove arbitrary prose is true. Important factual answers and outcome announcements need constrained rendering or equivalent enforceable checks.

## Starting point

The current game already has conversations, inventory transfers, timed bow crafting, save/resume and semantic memory retrieval. Seventeen target modules have recorded completion, including membership, proposal checks, role permissions, safe fallback, memory classification/reconciliation/lifecycle and dialogue composition.

The live conversation pipeline still uses the older services. Completing a pure module does not mean it is connected to gameplay. The backend suite passed 362 tests during the review on 2026-10-12; fresh live-model and full-game evidence is still required.

Confirmed problems to fix first:

- Context contains the speaking NPC but no shared village directory or other NPC locations.
- “Where is the Gatherer?” bypasses the authoritative bow-question handler.
- Generated dialogue mentioning vocabulary such as `wood`, `bow` or `quest` is rejected even when the statement could be supported.
- Godot NPC coordinates and backend named locations are separate representations.
- Existing rule evaluation is calculated without driving the selected behavior.

## Implementation boundaries

Use a small coordinator around the current services. Keep pure behavior calculations separate from game mutations, but do not require a new file or module for every stage.

Target flow:

1. Read relevant game state and permitted knowledge; retrieve bounded memories.
2. Build a compact context and obtain a structured model proposal outside a long-lived write transaction.
3. Check proposal shape, references and permitted state deltas.
4. Derive candidate state and fuzzy tendencies.
5. Apply role conditioning, then final control validation, then FSEC eligibility/selection/mapping.
6. Recheck mutation prerequisites and execute through existing authoritative game services.
7. Produce outcome dialogue from verified events and classify/store appropriate memory.

Prefer exact database/catalog lookups for people, inventory and quest state. Reuse semantic retrieval for experience; do not add a vector database for structured world facts. Read-only model tools can wait until direct context assembly demonstrably becomes insufficient.

## Work package A — Grounded conversation

### A1. Define shared village knowledge and the story handoff

- [x] Create a small validated catalog of people, roles, places, landmarks and public relationships.
- [x] Define stable IDs and distinguish usual location from observed current location.
- [ ] Have the story teammate supply facts, quest prerequisites, outcome conditions and approved recovery routes using this structure. Missing content must remain explicit.
- [x] Keep private NPC state and memories out of shared knowledge.

**Done when:** both existing NPCs can receive the same permitted village facts without duplicate prompt-specific lore. New story content can be added as data. A location without map evidence cannot produce invented route instructions.

### A2. Assemble relevant current context

- [x] Extend the current context builder with permitted village knowledge and relevant authoritative quest/inventory facts.
- [x] Include source IDs, knowledge status and freshness where relevant; keep recent conversation separate from older memories.
- [x] Define the local game's location authority: use named usual locations initially; expose current coordinates only where an actual game source supports them.
- [x] Bound context size and filter by NPC knowledge scope. Do not expose every NPC's private inventory or state.

**Done when:** a captured Craftsman context supports answering “Where is the Gatherer?” and quest requirement questions; it excludes another NPC's private emotions and memories. Current facts take precedence over stale conversation.

### A3. Generate useful grounded answers and handle follow-ups

- [x] Revise the prompt/proposal fields to distinguish answering, clarifying, proposing an action and reporting an outcome.
- [x] Support factual answer fields with source references; use constrained rendering for important locations, requirements and outcomes.
- [x] Replace broad item/quest word rejection with checks on supported facts and authorized effects.
- [x] Preserve short follow-up context and answer uncertainty explicitly.

**Done when:** the A scenarios in the evaluation table pass through the actual `/chat` path. Correct answers mentioning wood or the bow are accepted. Unknown places produce uncertainty. This is a general knowledge path, not a special-case reply for one sentence.

## Work package B — Validation and authoritative execution

### B1. Separate a model proposal from authorization

- [x] Validate schema, finite/bounded deltas, supported actions, source references and grounding scope. Reuse proposal-check code where practical.
- [x] Treat player statements and remembered claims as claims, not inventory or completion evidence.
- [x] Enforce role permissions and current resource prerequisites independently of model reasoning.
- [x] Return an explicit rejection reason and a zero-effect fallback for rejected/provider-failure outputs.

**Done when:** malformed JSON, invented references, forbidden actions and false completion claims cannot change inventory, quest progress or relationship rewards. A valid referenced fact does not excuse contradictory factual wording.

### B2. Connect safe execution and outcome dialogue

- [x] Keep transfers, crafting and rewards in existing authoritative services; recheck prerequisites at mutation time.
- [x] Render success only after the corresponding verified effect. Keep intention distinct from completion.
- [x] Add only the operation/event identities needed to prevent duplicated demonstrated effects.
- [x] Prevent delayed work from an old game/reset scope from committing or re-entering active memory.

**Done when:** a failed action has no success announcement; duplicate submission does not duplicate the demonstrated transfer/reward; a delayed pre-reset result cannot alter the new game. Do not introduce a generalized delivery platform to meet these checks.

## Work package C — Fuzzy behavior and FSEC

### C1. Connect state extraction and a small fuzzy policy

- [x] Derive bounded candidate state from existing NPC dimensions and accepted relative changes.
- [x] Reuse membership functions; implement a small explicit inference and defuzzification policy for cooperation, caution and expression.
- [x] Record rule strengths and numerical outputs. Keep initial tuning in one versioned configuration.

**Done when:** fixed inputs yield reproducible outputs, boundary values remain bounded, and gradual input changes produce inspectable tendencies rather than unused labels.

### C2. Condition, validate and select visible behavior

- [x] Preserve role conditioning → final control validation → FSEC ordering.
- [x] Map answer, clarify, cooperate and optional refusal to supported dialogue/transfers; keep offer recovery explicitly ineligible until authored recovery exists.
- [x] Filter ineligible candidates before utility scoring; define deterministic tie-breaking and bounded mapping parameters.
- [x] Connect the selected behavior to the live response or permitted action. FSEC must not widen validated constraints.

**Done when:** the same request under helpful, cautious and distrustful states produces traceable differences in permitted behavior. A high fuzzy score cannot override role restrictions, missing resources or unsupported execution capabilities.

### C3. Keep required cooperation recoverable

- [ ] Connect an attainable authored recovery route for each required quest step that can be refused.
- [ ] Verify completion through game evidence, persist scoped cooperation and prevent duplicate charges or immediate re-refusal of the recovered step.
- [x] If approved content is unavailable, keep blocking refusal disabled for required steps and demonstrate refusal on optional requests. Report this capability as incomplete.

**Done when:** every enabled mandatory refusal has a reachable resolution. A claimed favour completion cannot grant cooperation. Synthetic fixtures do not count as playable recovery content.

## Work package D — Managed memory

### D1. Store appropriate experience with provenance

- [x] Connect classification to accepted interactions and verified outcomes; exclude routine chatter, rejected output and provider failures.
- [x] Preserve source event, recipient, game scope, fact/claim status and correction links. Deduplicate the same logical event.
- [x] Reuse reconciliation/lifecycle logic as needed; retain verified history while making stale/corrected records ineligible for current factual answers.

**Done when:** a verified transfer is a fact, “I gave you wood” without evidence is a claim, corrections preserve history, and repeated processing creates one logical memory.

### D2. Retrieve relevant memories safely

- [x] Reuse existing embeddings/index/reranking; filter recipient, active game scope and lifecycle eligibility before selecting context.
- [x] Keep current world facts authoritative over remembered state. Preserve recent dialogue independently of semantic retrieval.
- [x] On embedding failure, preserve eligible memory writes and use a bounded degraded retrieval path without fake vectors.

**Done when:** paraphrased experience is retrievable, another NPC's private memories do not leak, corrected/old-game memories do not support current facts, and retrieval failure does not break conversation.

### D3. Demonstrate bounded memory influence

- [ ] Let appropriate verified experience propose a bounded future relationship/behavior influence.
- [ ] Record enough identity to prevent the same experience repeatedly awarding state changes across retrievals and restarts.
- [ ] Pass influence through the same state/role/control boundary; memory cannot grant items or authorize quest completion.

**Done when:** one helpful event affects a later decision, repeated retrieval does not compound its reward, and a player claim cannot manufacture equivalent cooperation.

## Work package E — Evaluation and presentation evidence

Start this package with A, not after implementation.

- [x] Create a small scenario runner and saved input fixtures against the actual coordinator/chat path.
- [x] Capture a decision trace: context source IDs, retrieved memory IDs/status, safe proposal projection, rejection reasons, candidate state, fuzzy rule strengths, eligible actions, scores, selection and verified outcome IDs.
- [x] Keep secrets and unrelated private context out of exported decision traces. The trace is implementation evidence, not hidden model reasoning; raw local conversation audits remain separate.
- [x] Run deterministic failure checks with fake model/clock, then a separate live-model pass on the intended setup.
- [x] Record model/configuration versions, attempts, pass/fail counts, unsupported claims, inappropriate fallbacks and observed latency for the scoped live scenarios. Do not substitute fixture success for live conversational quality.
- [x] Exercise the demonstrated grounding/bow path in rendered Godot; verify scene/process save/resume and reset using disposable saves. Delayed reset races remain separately covered by deterministic B2 checks.
- [x] Prepare repeatable rendered Godot/API demonstrations and clearly labeled recorded screenshot/transcript backups. Final presentation format and release-quality threshold remain unagreed; continuous/narrated video is not claimed.

### Required evaluation scenarios

| ID | Scenario | Expected evidence |
| --- | --- | --- |
| A-01 | “Where is the Gatherer?” / “Where can I find him?” | Known location, same referenced person, no invented detail |
| A-02 | “How do I get there?” with and without route data | Supported directions or explicit lack of route knowledge |
| A-03 | “What do you need?” / “Why?” / “What have I already delivered?” | Relevant requirements and current verified state |
| A-04 | Ask about an unknown person/place | Uncertainty or clarification without invented lore |
| B-01 | Malformed proposal, unknown source ID, forbidden action | Typed rejection/fallback and no unauthorized effects |
| B-02 | Claim possession or quest completion; attempt instruction override | Claims cannot alter authority or bypass constraints |
| B-03 | Duplicate effect request; delayed response after reset | One logical effect; no cross-reset mutation |
| C-01 | Repeat one request at helpful/cautious/distrustful states | Visible behavior differences explained by fuzzy/FSEC trace |
| C-02 | High cooperation with missing materials or forbidden action | Hard constraints still win |
| C-03 | Enabled mandatory refusal and its recovery | Reachable resolution with verified completion |
| D-01 | Helpful verified event, later paraphrased reference | Correct recipient memory and bounded future influence |
| D-02 | Repeat retrieval, correct a claim, switch NPC, restart | No repeated reward, stale truth or private-memory leakage |
| D-03 | Model timeout and embedding outage | Safe response and documented degraded memory behavior |

Use paraphrases and at least one multi-turn version of each relevant conversation scenario. Run live cases more than once and record actual variability. Before declaring release readiness, agree and record the required live quality threshold; do not label the system reliable solely because one run succeeded. Every tested authority, duplicate-effect and reset invariant must pass; unresolved failures block the affected feature.

## Priorities and working rules

| Order | Deliverable | Checkpoint |
| --- | --- | --- |
| 1 | A plus B1 and initial evaluation | Useful grounded conversation through the existing game API |
| 2 | C1/C2 plus necessary B2 execution | A complete visible AI decision path |
| 3 | D1–D3 and required C3 recovery | Verified experience changes later behavior safely |
| 4 | Full evaluation and targeted fixes | Demonstration evidence with explicit limitations |

These are checkpoints, not day-by-day guarantees. Reassess after the first grounded conversation slice. If time is short, reduce action variety, tuning breadth and game content; retain grounding, authority checks and honest reporting of incomplete memory/FSEC behavior.

- Keep one active task and finish its live integration before starting another isolated module.
- Each task must name the user-visible scenario it enables and the evidence needed to close it.
- Use focused checks during development and the full regression suite at integration checkpoints.
- Record changed files, commands/results, live results and known limitations when checking a task.
- Investigate an unexpectedly expanding task for a bounded session, then explicitly simplify or rescope it.
- Completion means the agreed scenarios work in the running system, not that corresponding files exist.

## Explicit exclusions

The final project does not require all original module packets, a generalized quest engine, combat/factions/economy, broad controller restructuring, generalized command polling/outbox delivery, a comprehensive repository migration, additional model-provider abstractions or unrestricted model database access.

Add work only when a demonstrated scenario needs it. Gameplay content belongs to the story collaboration; this plan specifies the AI integration contract rather than inventing final quest content.

## Active work and decisions

- Current checkpoint: E trace/API evidence plus fresh rendered Godot integration and recorded screenshot backup are verified below. D1/D2 guards remain intact; the two D1 live social-quality failures remain recorded. D3 state influence stays deferred.
- Implementation state: shared catalog, current fact context, constrained rendering, proposal enforcement and scenario runner are connected to the live API. The final configured live run passed all 56 scoped checks; see evidence below.
- Next checkpoint requires decisions: agree final presentation/recording format and live-quality threshold, then validate against that target. D3 influence remains explicitly deferred; activating it requires its own authorized slice. Story additions/mandatory recovery require approved authored content. Retain D1 social-quality failures.
- Open decisions: story catalog/content; live quality threshold and evaluation model/configuration. Resolve these during their owning task without blocking independent work.
- Final completion: all enabled core AI capabilities have passing integrated evidence; unfinished capabilities and live-model limitations are stated explicitly. Further gameplay work does not reopen the retired checklist.


## Grounding implementation checkpoint — 2026-10-12

### Running path and decisions

`POST /chat` now assembles shared public village knowledge plus exact current inventory, bow phase, outstanding materials and verified delivery evidence. The catalog is `backend/app/services/context/village.json`; validated people/place IDs and route endpoints are the story handoff structure. Only seed/game-service facts were added. No new story, prices, recovery content or map routes were authored. Story teammate content remains outstanding.

The model selects factual source IDs or requests clarification; the server replaces the entire factual prose with current source text. Contradictory prose attached to a real fact ID is discarded rather than trusted. Important answers can mention wood, string, bows and quests. Unknown references, forbidden actions, malformed output and nonzero factual deltas are rejected. Social exchanges retain generated prose; compact social proposals have zero effects. Free prose outside a bounded social-message class is rejected, so conversational variety is intentionally limited at this checkpoint.

Recent accepted source IDs and an explicit conversation focus preserve subjects independently of semantic memories. A small locative query adapter resolves catalog names and pronouns, binds location versus route facets, and prevents an explicitly unknown target being silently replaced by a known place. It is a bounded grammar over catalog data, not a general language parser or question/reply table; other topics remain model-selected. A clarification clears the previously resolved focus. Structured facts use exact catalog/SQL lookups; semantic retrieval remains the existing recipient-scoped memory service. Full provenance is retained in context/trace; the model gets a smaller projection to reduce token cost. The existing OpenAI-compatible provider now requests JSON Schema output when facts are present (`LLM_STRUCTURED_OUTPUT=true`, the default). [Ollama documents this capability](https://github.com/ollama/ollama/blob/main/docs/capabilities/structured-outputs.mdx). Other compatible providers can opt out if unsupported; server validation still applies.

The named catalog locations are **usual locations**. Godot's spawn coordinates are a separate representation, without a synchronized NPC observation endpoint. No current coordinates are claimed. Route facts explicitly report missing directions. A synthetic route fixture tests rendering with supplied data; it is not playable route evidence.

Rejected output/provider failures bypass state application and automatic crafting, use zero-effect fallbacks, and cannot create important memory. Existing ownership-checked transfers and timed bow crafting/rewards remain in their authoritative services. Delivery answers consult executed transfer records, retained quest materials and the service's consumed-material phase; no player assertion establishes delivery. Clearing chat can erase older returned-material history, but retained/consumed bow-material evidence remains available. This is not a new event ledger or a completed reset-race solution.

### Changed files

- Catalog/context: `backend/app/services/context/{village.json,grounding.py,builder.py,models.py}`.
- Proposal/prompt/enforcement: `backend/app/services/prompts/builder.py`, `backend/app/services/validation/{models.py,service.py}`, `backend/app/services/pipeline.py`.
- API/provider configuration: `backend/app/schemas/chat.py`, `backend/app/services/llm/openai_compatible.py`, `backend/app/config/settings.py`, `backend/.env.example`.
- Verification: `backend/tests/{test_grounded_chat.py,test_npc_pipeline.py,grounding_scenarios.json,run_grounding_live.py}` and `docs/evidence/grounding-live*.json`.
- This delivery document. Pre-existing changes to `docs/master-progress.md` and `docs/validation-steps.md` were preserved.

### Verification and remaining work

Deterministic enforcement runs the actual HTTP route with explicit fake model outputs and disposable in-memory databases. It covers shared/private context, usual versus observed location, current material requirements, retained delivery evidence after clearing chat, contradictory prose with valid IDs, unknown IDs, unknown subjects, malformed JSON, non-finite/out-of-range state, forbidden actions, vague false success, false player claims, provider failures and craftable stock during rejection. Existing regressions cover transfers, timed crafting, one bow reward, persistence and disposable reset. Final full regression result: **377 tests passed**; the focused grounding suite was also run during implementation. `git diff --check` passed.

Commands:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_grounded_chat.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tests/run_grounding_live.py --output docs/evidence/grounding-live.json
git diff --check
```

Live runner uses the configured `llama3:latest`, temperature 0.2, two attempts per NPC and 14 sequential scenarios per attempt (56 requests). No generation or embedding mocks are installed in that runner; game sessions use disposable in-memory SQLite. It mounts the production API routes without production startup hooks. Each saved record contains actual answers, proposals, selected source IDs, rejection reasons, elapsed time and invariant checks; the final run also fingerprints implementation files. Initial sandbox network denial is recorded in `grounding-live-probe.json`, not counted as a successful model run. Earlier interrupted runs are explicitly partial, with their actual completed-request counts retained. Full earlier runs (`compact-v1`: 43/56, `focus-v2`: 48/56, `schema-v4`: 52/56, `negative-v5`: 53/56) exposed enum/schema, follow-up and wrong-subject failures; their failures were not relabeled as passes. The final correction added catalog reference binding rather than treating valid IDs as proof of relevance.

Final live results: **56/56 scoped checks passed**, including **56/56 authority checks**, with two attempts per NPC using schema-constrained `llama3:latest`. Median latency 2.427 s; observed range 1.079–5.403 s; sample p95 3.733 s. All recorded implementation fingerprints match the final code. [Actual answers and proposals](evidence/grounding-live.json) retain both the raw model selection and the final resolved references. These live worlds exercised the initial available quest phase; progressed quest/transfer/crafting/save/reset behavior was checked deterministically, not claimed as a live full-game run. No release reliability claim is made from deterministic fixtures or one live pass. Godot UI and live semantic-memory quality have not been exercised in this checkpoint. Authored story/recovery content, synchronized observed NPC positions, full fuzzy/FSEC execution, delayed pre-reset protection and managed-memory influence remain unfinished.

Next smallest task: exercise this `/chat` path from Godot using a disposable save, including progressed quest facts, before starting C1/C2. No failing scenario remains in the final 56-request set; broader wording and live quality thresholds still require evaluation. Keep the retired module checklist out of scope.


## Disposable Godot verification checkpoint — 2026-10-12

### Running path and concrete fix

Verified the actual `Main.tscn` scene, chat controls, `HTTPRequest` response parsing, rich-text display, transfer controls, F pickup, quest progress and timed reward. The main scene defaults to `http://127.0.0.1:8000` and passes that endpoint to chat windows. Verification overrides the scene endpoint before `_ready`; the runner reserves a separate loopback socket, starts production FastAPI startup/routes with `DATABASE_URL` pointing to a new temporary SQLite file, and copies the Godot project into the same disposable directory. No saved player world was reset or used, no production `.env` was edited, and no generation/embedding mocks were installed. Existing port-8001 smoke scripts were not used against an unverified backend.

The first rendered run exposed a concrete grounding regression: **“Can you make me a bow?”** no longer entered the existing authoritative bow handler. It went to the model, left the started quest at `meet`, and consequently blocked string pickup and crafting. `validation/items.py` now recognizes bounded explicit make/craft-bow requests and routes them through the existing ownership/role/quest path. Material questions, conditional requests, negations, multi-item requests and completion claims retain their previous boundaries. The Craftsman can advance the started quest; asking the Gatherer does not advance it. No new quest content or execution service was introduced.

### Changed files and repeatable setup

- `backend/app/services/validation/items.py`: restore explicit bow crafting request routing.
- `backend/tests/test_grounded_chat.py`: route-level regression with an offline model, request paraphrases and role/claim boundaries.
- `backend/tests/run_godot_grounding.py`: disposable backend/project setup, real provider configuration, raw proposals, implementation fingerprints, backend restart and evidence capture. Existing evidence directories are refused rather than overwritten.
- `frontend/godot/tests/grounded_chat_smoke.gd`: actual scene/control/HTTP checks for both NPCs, progressed materials, persistence, reward uniqueness, reset and provider failure.
- This delivery document and new `docs/evidence/godot-*` artifacts. Earlier uncommitted work and unrelated documents were preserved.

Run from the repository root with an installed Godot 4 executable (the verified executable was temporary Godot 4.5.1):

```sh
PYTHONPATH=backend .venv/bin/python backend/tests/run_godot_grounding.py --godot /path/to/Godot --output docs/evidence/godot-new-live-run --rendered
PYTHONPATH=backend .venv/bin/python backend/tests/run_godot_grounding.py --godot /path/to/Godot --output docs/evidence/godot-new-failure-run --provider-failure
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_grounded_chat.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
git diff --check
```

Omit `--rendered` for headless scene/HTTP checks. Loopback access and native Godot execution may require sandbox approval; denied connections/execution are not live passes. The runner reserves its own endpoint and owns all data it resets. Its temporary database/project are removed after verification.

### Actual evidence and limits

Final [rendered run summary](evidence/godot-grounding-rendered-v3/summary.json): **155/155 assertions passed**, 35 dialogue submissions, both NPCs, configured `llama3:latest`, temperature 0.2, schema output enabled, real `nomic-embed-text` embeddings. Godot 4.5.1 rendered through Metal. [Displayed text and API responses](evidence/godot-grounding-rendered-v3/godot.json), [raw proposals and verified outputs](evidence/godot-grounding-rendered-v3/conversations.json), and [backend restart checks](evidence/godot-grounding-rendered-v3/resume.json) are retained. All recorded implementation fingerprints were checked against the final code. Across the 35 submissions, observed latency was 0.095–4.043 s, median 2.497 s; these include authoritative requests that skip generation, so this is end-to-end interaction latency rather than a pure model benchmark.

The run exercised the 14 grounding scenarios sequentially for each NPC, including location/pronoun/route/work follow-ups, requirements/“Why?”, unknown people/places and false possession/completion claims. It then completed the existing quest through real material transfers and pickup. After wood delivery, displayed facts recorded only wood and only string outstanding. A scene relaunch restored position, partial inventory/quest state and grounded history. The second delivery started timed crafting without an instant bow; completion granted exactly one bow. Consumed materials remained in verified delivery answers. A genuine backend and Godot process restart preserved the completed quest, reward, position and history. Two further advance requests did not duplicate the reward. Explicit restart confirmation reset only the disposable world and cleared its old dialogue.

Visually inspected screenshots show readable wrapped dialogue, missing-route uncertainty, updated supplies, the crafting panel, and the final satchel with one bow: [route](evidence/godot-grounding-rendered-v3/route-npc-1.png), [partial delivery](evidence/godot-grounding-rendered-v3/partial-delivery.png), [crafting](evidence/godot-grounding-rendered-v3/crafting.png), [completion](evidence/godot-grounding-rendered-v3/completed.png). No frontend parser/display fix was needed.

Separate [provider failure run](evidence/godot-provider-failure-v1/summary.json): **11/11 assertions passed** through headless Godot with a deliberately unreachable generation endpoint, real provider code and no mocks. Both NPCs displayed a fallback, restored controls, preserved inventory/quest/NPC state and stored no important memory. This checks connection failure, not every possible provider timeout or malformed transport response. Embeddings remained configured normally.

Focused grounding regression: **16 tests passed**. Final full deterministic regression: **378 tests passed**. `git diff --check` passed. The earlier 377-test result and 56-request backend live result remain historical evidence; neither was relabeled as this Godot run.

Earlier Godot artifacts remain honest failure/partial evidence: `godot-grounding-headless-v1` stopped at sandbox socket denial; `godot-grounding-rendered-v1` recorded the real bow-routing regression and its downstream failures, then was terminated while waiting for impossible completion. `godot-grounding-rendered-v2` was interrupted while correcting an overly strict harness assertion that treated an accepted response changing `current_state` from `available` to `speak` as an unauthorized effect. The final harness checks exact relationship dimensions, inventory, pending transfers and quest phase; rejected provider responses also preserve `current_state`. These earlier runs are not successful checkpoints.

This closes the scoped Godot verification slice, not the delivery plan. It is automated control-driven rendered verification, not a manual playthrough, release threshold or recorded demonstration. Only one final rendered pass was run; broader language quality and semantic-memory quality remain unmeasured. Backend restart was exercised after completion, not during in-flight crafting/generation. No delayed pre-reset generation protection is claimed. Story/recovery content and current NPC position synchronization remain outstanding.

**Next smallest task:** connect C1/C2 to visible supported response behavior, starting with the necessary B2 game/reset scope check around delayed generation and authoritative execution. Keep one active slice, reuse existing policy/membership modules, preserve role conditioning → final validation → FSEC ordering, and keep blocking mandatory refusal disabled without authored recovery. Managed-memory influence remains deferred.


## Visible fuzzy/FSEC and reset safeguard checkpoint — 2026-10-12

### Running path

`POST /chat` and inventory transfer requests now run role conditioning → final control validation → FSEC eligibility/selection/mapping before execution. Candidate state is current trust/fear/aggression/curiosity plus accepted, conditioned relative changes, clamped to [0,1]. `rule_engine/behavior_policy.json` holds one versioned policy (`village-response`, version `1`): low/high trapezoidal memberships reuse the existing pure `fuzzify` implementation, AND rules use minimum strength, and weighted singleton averages produce cooperation, caution and expression. A baseline rule guarantees coverage at boundaries. This small adapter replaces the unused bucket evaluation in the coordinator; it does not mark the retired FSEC task packets complete. The generic policy registry requires recovery-route bundles and is deliberately not forced into this content-free slice.

Ineligible behaviors are removed before scoring. Scores are bounded to [0,1], ties resolve by behavior ID, and complete authoritative dialogue is retained within the 240-character mapping bound (expression is omitted when it would overflow). Helpful NPCs select cooperation and display “Glad to help”; cautious NPCs retain purpose clarification and display “Let's be careful”; distrustful NPCs can explicitly decline optional owned outgoing items. Refusal cancels the pending optional request, supplies no item and applies zero relationship deltas. Accepted generated social prose remains visible with a bounded expression prefix. Factual text remains server-rendered and receives no expression prefix. Required wood/string/bow requests and incoming deliveries cannot be refused. Missing stock and unsupported roles/capabilities remain hard constraints. `offer_recovery` is always ineligible because no authored recovery route exists. C3 remains incomplete; no location, price, objective or recovery content was invented.

Transfers, material consumption, timed crafting and rewards remain in existing services. Behavior and grounding traces are returned through the API and persisted with the conversation: candidate state, membership degrees, rule strengths, outputs, eligibility with reasons, scores, selection, bounded mapping, before/after inventory, pending request and quest phase, final executed dialogue, and the existing durable conversation row ID. No new command bus, ledger or generalized action framework was added. The persisted revision/decision token rejects competing stale processing; the existing BowQuest phase continues to prevent repeated rewards. There is no general client idempotency-key/replenished-stock replay protocol.

### Transaction and reset boundary

Context is read without mutation locks, then its read transaction is rolled back before provider generation. After generation, the coordinator acquires the single-player writer lock and atomically compares/rotates the NPC's existing persisted `memory_revision`. Reset and clear already rotate this token. A delayed pre-reset, pre-clear or superseded reply receives HTTP 409 before validation, state application, automatic crafting, conversation insertion or important memory storage. A reset of either NPC invalidates its old work across sessions/restarts without a new schema migration. Current inventory and quest facts are re-read under the mutation lock before source rendering and execution; model prose cannot freeze outdated authority.

A shared player-first writer lock uses a no-op SQL UPDATE because SQLite ignores FOR UPDATE. Chat, reset, clear, quest start/pickup/advance and position writes use the same lock order. This also serializes timed reward/memory writes with reset. Generation runs without an open DB transaction, verified in delayed-provider tests using independent sessions and disposable file-backed SQLite. Existing important-memory embedding still runs inside the serialized mutation transaction; a reset waits for that write to finish, then clears it. Moving that embedding work out of the transaction is deferred to managed-memory work. PostgreSQL lock semantics are used but were not exercised in this checkpoint.

### Files changed in this slice

- Coordinator/API: `backend/app/services/pipeline.py`, `backend/app/schemas/chat.py`, `backend/app/api/routes/{chat,inventory,quests,world}.py`.
- Behavior/control: new `backend/app/services/rule_engine/{behavior.py,behavior_policy.json}`, final control checks in `backend/app/services/validation/service.py`.
- Persistence boundary: new `backend/app/services/state/locking.py`, `backend/app/database/seed.py`; reuse existing NPC revision field and migrations.
- Verification: new `backend/tests/{test_behavior_pipeline.py,run_behavior_live.py}`, updated `test_grounded_chat.py`, `run_godot_grounding.py`, and `frontend/godot/tests/grounded_chat_smoke.gd`.
- This document and new behavior evidence. All prior uncommitted work and historical evidence were preserved; nothing was reset, staged or committed.

### Verification and limits

Focused behavior tests: **13 passed**. Full deterministic regression: **391 passed**. Tests cover helpful/cautious/distrustful optional requests, refusal after purpose confirmation, required cooperation, repeated transfer, missing resources, unsupported role, generated social expression, factual preservation, rejected-output zero effects, conditioned/clamped candidate state, reproducible/gradual membership outputs, eligibility before scoring, stable ties, delayed reset/clear/competing conversation with independent sessions, persistent world inspection and HTTP 409 on both chat/transfer routes. Existing regressions retain the complete timed quest and unique reward/reset checks. `git diff --check` passed.

Configured live API evidence: [behavior-live-v2.json](evidence/behavior-live-v2.json), **38/44 scenario checks**, **44/44 authority checks**, two attempts per NPC across controlled helpful/cautious/distrustful states. All 20 optional request/purpose-confirmation checks and all 12 factual-location checks passed; six of 12 social checks passed. The six failures were first-attempt “Hello” generations that introduced inventory/quest vocabulary and were replaced by validated, zero-effect fallbacks. Second-attempt “Good morning” generations passed. These failures remain failures and limit conversational quality; no release-readiness claim is made. See [provider log](evidence/behavior-live-v2.log). `llama3:latest`, temperature 0.2, schema output enabled. Configured `nomic-embed-text` calls returned HTTP 404 from `/api/embed`; important writes survived without vectors. This is real generation with an actual embedding outage, not successful semantic-memory retrieval evidence. The earlier [behavior-live-v1.json](evidence/behavior-live-v1.json) was blocked by sandbox socket denial (20/44 request-only checks passed); it is not a live-provider pass.

Rendered [Godot behavior verification](evidence/godot-behavior-rendered-v1/summary.json): **170/170 assertions passed**, 39 dialogue submissions, Godot 4.5.1/Metal, real configured generation and actual embedding-outage behavior. It visibly checks distrustful optional refusal and helpful cooperation, executes/returns an optional item through authoritative services, then completes the required bow quest with a distrustful Craftsman, timed crafting, exactly one bow, partial/completed fact answers, save/resume, genuine backend/Godot restart and explicit disposable reset. End-to-end latency median 2.914 s, range 0.050–5.451 s, including authority requests that skip generation. [API/displayed text](evidence/godot-behavior-rendered-v1/godot.json), [persisted proposals/decision traces](evidence/godot-behavior-rendered-v1/conversations.json), [restart checks](evidence/godot-behavior-rendered-v1/resume.json) and backend/provider logs are retained. Visually inspected [optional refusal](evidence/godot-behavior-rendered-v1/optional-refusal.png) and [cooperation](evidence/godot-behavior-rendered-v1/optional-cooperation.png): complete readable dialogue and usable controls. Separate headless [provider connection failure regression](evidence/godot-behavior-provider-failure-v1/summary.json): **11/11 passed**. Fingerprints of all implementation files in both Godot runs and the live API behavior run match the checkpoint code. These are automated checks with controlled disposable NPC state, not a manual playthrough, recorded demonstration or quality threshold. Actual reset-during-generation races were checked deterministically; they were not induced with a real in-flight provider in Godot. No managed-memory influence was added.

Commands from repository root:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_behavior_pipeline.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tests/run_behavior_live.py --output docs/evidence/NEW-BEHAVIOR.json
PYTHONPATH=backend .venv/bin/python backend/tests/run_godot_grounding.py --godot /path/to/Godot --output docs/evidence/NEW-GODOT-BEHAVIOR --rendered --behavior-fixtures
PYTHONPATH=backend .venv/bin/python backend/tests/run_godot_grounding.py --godot /path/to/Godot --output docs/evidence/NEW-GODOT-FAILURE --provider-failure
git diff --check
```

The Godot `--behavior-fixtures` option sets controlled NPC dimensions only in the runner-owned disposable SQLite world. It is verification data, not a playable recovery route or a user-facing state-edit API. The harness checks visible refusal/cooperation, a real optional transfer and return, then the existing grounding and full bow quest sequence, restart, unique reward and explicit reset.

Next smallest task: diagnose the configured embedding HTTP 404 and improve the bounded social-generation prompt against the six saved failures, then rerun the same real-model cases. Keep managed-memory influence deferred until that checkpoint; authored mandatory recovery and a demonstration/release threshold remain outstanding.


## Embedding availability and social-generation follow-up — 2026-10-12

### Diagnosis and implemented fixes

The embedding HTTP 404 came from missing model weights, not an unsupported API route: local Ollama 0.34.2 returned `model "nomic-embed-text" not found, try pulling it first`, and `/api/tags` listed only `llama3:latest`. Pulled the already configured `nomic-embed-text` model through local Ollama. The installed model is 274,302,450 bytes, digest `0a109f422b47e3a30ba2b10eca18548e944e8a23073ee3f3e947efcf3c45e59f`. No saved-world database, configuration or existing memories were reset/reindexed. [Before/after diagnostics](evidence/embedding-recovery-v1.json) record successful real document/query embeddings, 768 dimensions and unit norms. A small paraphrase probe favored the delivered-water document over an unrelated preference; this is an availability/sanity check, not a semantic-quality benchmark.

`EmbeddingService` now reports a missing configured model explicitly when Ollama returns that error. Other HTTP 404s retain their transport failure. It still preserves eligible writes without vectors during an outage and never manufactures substitute vectors. Installation is an environment repair, not an automatic download on a player request.

Inspection of the six saved greeting failures showed two causes: the Craftsman volunteered bow/material facts during social chat, while the Gatherer's correct self-introduction was rejected merely for containing its name. The prompt now tells social generation to reply naturally without volunteering job, inventory, quest, location or promise details. Validation permits only a complete self-introduction sentence containing the exact supplied speaker name. Naming another NPC, adding a location to that sentence, or claiming items/crafting/outcomes still fails validation. Generated social prose remains intact apart from the existing bounded fuzzy expression prefix; no greeting lookup/canned-reply path was added and no factual authority was delegated to prose.

### Changed files and verification

Changed `backend/app/services/prompts/builder.py`, `backend/app/services/validation/service.py`, `backend/app/services/memory/embedding.py`; added regression cases in `backend/tests/{test_grounded_chat.py,test_semantic_memory.py}`. Extended `backend/tests/run_behavior_live.py` to fingerprint prompt/embedding/provider code and record actual memory vector metadata and recipient-scoped retrieval of verified transfers. This document and new evidence were added. Prior uncommitted work and historical failed evidence remain preserved; no staging or commits.

Focused deterministic checks: **17 grounding tests passed**, **13 semantic-memory tests passed**. Full regression: **393 tests passed**. Missing-model diagnostics and other 404s are distinguished; exact speaker introductions pass while cross-NPC introductions, added locations and item/quest claims remain rejected. Existing reset, role, resource, fuzzy, timed-crafting and reward tests still pass. `git diff --check` passed.

[Configured live behavior rerun](evidence/behavior-social-embedding-v1.json): **44/44 scenario checks**, **44/44 authority checks**, **8/8 real embedding storage/retrieval checks**. Same two attempts per NPC and controlled helpful/cautious/distrustful states as the previous 38/44 run; all six previously failed “Hello” cases now passed, as did “Good morning”, factual locations, optional requests/refusal and actual purpose-confirmed transfers. Important verified transfer memories have real normalized 768-dimensional vectors and appear in the correct NPC's paraphrased retrieval. No generation/embedding mocks were installed. Configured `llama3:latest`, temperature 0.2, schema output enabled, `nomic-embed-text`. End-to-end median latency 0.874 s, range 0.007–3.226 s, including authority requests that skip generation. [Actual provider-run log](evidence/behavior-social-embedding-v1.log) is retained. Recorded implementation fingerprints match the checkpoint code.

[Configured grounding regression](evidence/grounding-social-prompt-v1.json): **56/56 scenario checks**, **56/56 authority checks**, two attempts per NPC across the original 14-scenario set. Locations, pronouns, routes, work, requirements/reasons, verified delivery facts, unknown references and false possession/completion claims retained their scoped behavior after the social-prompt change. [Run log](evidence/grounding-social-prompt-v1.log) and actual proposals/answers remain separate from historical evidence. Recorded implementation fingerprints match the checkpoint code. No failing case remains in these two new live sets; broader social wording and semantic quality remain unmeasured.

This repairs the specific provider and social-boundary failures; it does not establish universal conversational accuracy, managed provenance/lifecycle, memory-driven behavior, a release quality threshold or recovery content. No new Godot run was performed for this backend-only follow-up; the prior 170/170 rendered result remains historical evidence for its own fingerprinted implementation. The player's existing vectorless memories were left untouched; repairing those requires an explicitly scoped reindex task.

Commands from repository root:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_grounded_chat.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_semantic_memory.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tests/run_behavior_live.py --output docs/evidence/NEW-SOCIAL-EMBEDDING.json
PYTHONPATH=backend .venv/bin/python backend/tests/run_grounding_live.py --output docs/evidence/NEW-GROUNDING.json
git diff --check
```

**Next smallest task:** connect D1 provenance to accepted experience: use the existing durable conversation outcome identity, recipient and reset scope; distinguish verified events from player claims and deduplicate logical writes. Keep memory-driven state influence deferred until those boundaries and retrieval eligibility are connected and tested. Authored recovery content and a demonstration/release quality threshold remain outstanding.


## D1 accepted-experience provenance checkpoint — 2026-10-12

### Connected behavior and boundaries

New important memories now carry the recipient NPC, persistent game scope, server-assigned source-event UUID, source conversation ID, epistemic status, evidence authority, lifecycle status and correction links. A stable `Player.game_scope` survives ordinary conversation and process/session restarts; explicit new-game reset rotates it. It is separate from the existing volatile NPC memory/index revision. Each processed conversation gets an opaque source identity; only accepted eligible experience becomes a memory. The existing conversation row remains the durable evidence record, without a new event bus or delivery framework.

The coordinator executes authoritative effects, captures actual transfer counts before any immediate material consumption, flushes the source conversation, then records its memory in the same transaction. Ownership-checked transfers, quest phase transitions and timed bow rewards become historical **facts** with authoritative evidence. Transfer summaries no longer embed the player's unverified purpose as fact; the original explanation remains in the source conversation. The final material-delivery source retains both transfer count evidence and its crafting phase transition. Timed completion uses the same source path and verifies one bow was actually added before recording completion.

Preferences, commitments, personal statements and bounded “I gave/delivered you …” delivery statements are **reported claims**, not facts. The latter cannot establish inventory or delivery. Rejected generation, provider failures and routine chatter create no important memory. Factual answers still render exact current world facts; memory status and retrieved source IDs are inspectable in API/context traces and do not authorize gameplay.

`store_conversation` checks the persisted source UUID, recipient and current run before classification/storage. Reprocessing a source returns the existing memory without re-embedding. A database unique index on run/recipient/source event backs that guarantee. Distinct real transfers with identical wording retain distinct source identities. Repeated identical active claims consolidate into their first memory, preserving its original provenance/timestamp; subsequent accepted conversations retain a reference to that memory. Reset or clear removes the source and invalidates old processing, including SQLite row-ID reuse.

Explicit `I no longer prefer/like/love …` statements can retract an exact earlier corresponding preference. The adapter reuses the existing pure reconciliation planner and lifecycle tags: original text/source remain in history, the original becomes `retracted`, and both records carry correction links. The corrected record is excluded from active retrieval before vector search. Reasserting then retracting the same preference creates and corrects the new claim rather than reviving the earlier one. This is a bounded exact-preference retraction path, **not** general contradiction detection, arbitrary correction authoring or semantic belief reconciliation. No prices, objectives, locations or recovery content were invented.

Recipient, current game scope and active lifecycle are SQL predicates before semantic candidate indexing and are rechecked when materializing results. The memory history endpoint retains retracted records for inspection within the current run; active search/prompt context excludes them. Unknown-scope legacy memories remain physically preserved but are excluded from active retrieval. Reindexing vectors does not invent their source or game scope. The additive, repeatable migration preserves old text, vectors, inventory and conversation data and leaves unknown provenance null. No migration, reset or reindex was run against the player's saved database.

### Social-generation integration fix

Live preference tests exposed generated replies that volunteered quest details or addressed the player by the NPC name. The established bounded social-message class is now shared by validation, prompt assembly and provider decoding. Social generation receives relevant preference/personal/commitment claims, a compact social prompt and social conversation history; world/transfer facts and factual assistant turns remain on the grounding path. Its schema allows chat with an empty fact-ID list. World questions retain the full current fact path. Rejected replies no longer re-enter accepted prompt history. Exact punctuation-delimited self-name clauses are permitted while the rest of the text still undergoes the existing social/factual boundary checks. This preserves generated replies and does not add a question/reply lookup table. Role prose outside that boundary can still cause an inappropriate fallback, as measured below.

### Changed files

- Models/migration: `backend/app/models/{player,conversation,memory}.py`, `backend/app/database/{memory_migration,seed}.py`.
- Runtime provenance/classification: new `backend/app/services/memory/provenance.py`, updated `memory/{importance,service,reindex}.py`, `services/pipeline.py`, `services/quests/bow.py`.
- API/context: `schemas/memory.py`, `api/routes/memory.py`, `services/context/builder.py`, new `services/context/social.py`, `services/prompts/builder.py`, `services/validation/service.py`, `services/llm/openai_compatible.py`.
- Verification: new `backend/tests/{test_memory_provenance,run_memory_provenance_live}.py`, updated `test_semantic_memory.py`, `test_grounded_chat.py`, and `run_godot_grounding.py` (persisted source-link capture).
- This delivery document and new evidence. Existing uncommitted work and all earlier evidence remain intact; nothing was staged or committed.

### Actual verification and limitations

Focused provenance tests: **13 passed**. Final full deterministic regression: **408 passed**. Coverage includes verified transfer versus delivery claim, exclusion of player explanations from facts, exact retraction history/links, repeated claim consolidation, distinct real transfers, source reprocessing after reopening, wrong recipient/deleted/old-run sources, database duplicate-source rejection, embedding outage with provenance preserved, source/count evidence required for transfer, timed reward provenance without duplicate reward, scope/lifecycle filtering before indexing and repeatable additive legacy migration. Existing delayed-generation reset/clear/concurrent-conversation tests, role/resource constraints, complete crafting and reward regressions still pass. `git diff --check` passed.

Final [configured D1 live run](evidence/memory-provenance-live-v4.json): **77/84 checks passed**, **26/28 dialogue submissions accepted**, two attempts per NPC, real `llama3:latest` at temperature 0.2 with schema output and real `nomic-embed-text`. Three of four complete preference/consolidation/retraction flows passed. In the remaining flow, two preference replies said “I'm more of a gatherer myself …”, outside the permitted social-prose boundary; both were rejected and stored no important memory. Five dependent checks consequently failed because the original preference was never accepted. Those failures remain explicit. Accepted claims, transfers and retractions carry real vectors and source metadata; snapshots retain 19 memory records across the four disposable runs. All tested source-reprocessing, wrong-recipient, old-source/reset and verified-transfer guards passed. No invalid proposal was stored or allowed to change game authority. Final live implementation fingerprints match the checkpoint code. [Actual provider log](evidence/memory-provenance-live-v4.log) is retained.

Earlier live runs remain separate: `memory-provenance-live-v1` **75/84** included one rejected player/NPC-name-confused retraction, dependent failures, and four overly strict delivery-answer assertions that expected one exact fact despite unchanged game authority. `v2` **76/84** exposed unsolicited workshop/bow prose in preference replies. `v3` **50/84** narrowed context but exposed an overly strict sentence-only self-introduction check. Its valid comma-delimited introductions were still counted as failures in that artifact. None was overwritten or relabeled as a pass. This bounded implementation session stops short of general social-prose tuning or a release-quality claim.

[Headless Godot integration](evidence/godot-memory-provenance-headless-v1/summary.json): **170/170 assertions passed**, including production startup with the new schema, optional cooperation/refusal, full required quest, timed unique reward, backend/Godot restart and disposable reset. [Persisted memory capture](evidence/godot-memory-provenance-headless-v1/memories.json) contains **9/9 records with valid source/recipient/run links**; the corresponding conversations and logs are retained. This run occurred before the final social-context/history/provider and self-name validation refinements. Its source-storage, schema, coordinator and reward implementation fingerprints match the final code; its four changed prompt/context/provider/validation fingerprints are historical, not a final-code UI claim. No new rendered/manual playthrough was performed.

PostgreSQL migration/concurrency was not exercised. Legacy unscoped memories are preserved but require evidence-backed provenance repair before active use. Embedding generation for important writes still holds the serialized mutation transaction; reset waits for it and then clears the old run. Automatic expiry/archive retention, generalized corrections, degraded retrieval during embedding outage and memory-driven state influence remain unfinished. Existing explicit reset/clear retains its intentional deletion behavior.

Commands from repository root:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_memory_provenance.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tests/run_memory_provenance_live.py --output docs/evidence/NEW-MEMORY-PROVENANCE.json
PYTHONPATH=backend .venv/bin/python backend/tests/run_godot_grounding.py --godot /path/to/Godot --output docs/evidence/NEW-MEMORY-GODOT --behavior-fixtures
git diff --check
```

**Next smallest task:** finish D2's bounded degraded retrieval path for an embedding outage, using the same recipient, game-scope and lifecycle predicates, without fake vectors or new state rewards. Preserve the two social-generation failures for evaluation rather than weakening the fact boundary. D3 influence, authored mandatory recovery and a demonstration/release quality threshold remain deferred.


## D2 checkpoint — bounded retrieval during embedding outages (2026-10-12)

**Completed scenario:** important accepted experience remains available when query embeddings fail or a stored memory has no usable current vector. The existing HNSW/cosine path is retained. No new gameplay, memory-driven state changes, automatic reindexing, or source authority is introduced.

### Retrieval behavior and bounds

Both paths share SQL recipient, current `Player(1).game_scope`, active lifecycle, minimum importance, excluded/routine category, optional event-type/quest and UTC date predicates before candidate selection. Unknown-scope history stays ineligible. The existing outside-world text backstop still discards such candidates before returning context. Provenance, claim/fact status, authority and correction links are carried unchanged; current world facts remain independently supplied and authoritative.

When indexed vectors exist and query embedding succeeds, semantic search/reranking is unchanged. A separate lexical pool includes vectorless records, mismatched/absent embedding models and a deterministic sample of up to 50 malformed-vector IDs rejected during index construction. SQL NULL and JSON null vectors are handled. With no eligible indexed vectors, or an actual query embedding failure, the lexical pool uses all otherwise eligible records. Important writes during an outage still persist without vectors; explicit reindex remains the recovery mechanism.

Lexical candidate SQL orders bounded query-term substring hits, importance, timestamp and ID, with `LIMIT memory_candidate_count` (default 40, configured range 20–50). Query processing uses the first 500 characters and at most 12 distinct ASCII terms of 2–32 characters; empty-term input falls back to importance/recency. Only that bounded pool is reranked using `.65 * lexical term coverage + .20 * importance + .15 * recency`. Semantic scores retain cosine relevance in the first term. Payload `retrieval_mode` and `score_kind` distinguish these measures; lexical scores are never called semantic similarity.

Each full-record SQL materialization is limited to the configured candidate bound: at most 40 semantic plus 40 lexical records by default (maximum 100 combined). Returned results are limited to `min(top_k, memory_candidate_count)`, after exact text/category/quest deduplication. Separate rankings are interleaved semantic-first rather than comparing incompatible scores, so vectorless memories can occupy context slots in a healthy system. With only one requested slot, semantic takes precedence. The pre-existing cached index construction still reads all eligible ID/vector pairs on a cache miss; the record-materialization bound does **not** claim to bound that vector build or database sort work.

Each call records mode, reason, candidate/materialization/result bounds, actual pool sizes and selected IDs through `MemoryService.last_retrieval_trace` and a structured info log, including empty/early-return results. Context captures a copy before later retrieval calls; the coordinator persists it under `grounding_trace.memory_retrieval`. Diagnostics contain no raw query or private memory text and are not injected into generation prompts. `/memory/{npc_id}/search` remains a JSON list with additive per-result score labels.

### Verification and evidence

Final deterministic regression: **416 passed**. Focused suites comprise **20 semantic/embedding tests** and **14 provenance/integration tests**. Added checks cover query outage with existing vectors, vectorless writes, healthy mixed retrieval, explicit recovery, malformed vectors, recipient/run/lifecycle isolation, importance/category/quest/date filtering before bounds, SQL limits, oversized `top_k`, deterministic ID ties, exact deduplication, lexical/importance/recency ordering, outside-world exclusion, empty diagnostics, list-shaped HTTP search and persisted coordinator traces. The actual `/chat` integration test uses deterministic generation and verifies that a recalled delivery claim cannot override authoritative undelivered state. Existing regression checks still exercise transfers, crafting, rewards and reset guards. `git diff --check` passed.

Final live evidence: **18/18 checks passed** in [memory-retrieval-live-v3.json](evidence/memory-retrieval-live-v3.json), with [provider log](evidence/memory-retrieval-live-v3.log). The runner uses a temporary file-backed SQLite world, the real `EmbeddingService` and configured `nomic-embed-text` 768-dimensional vectors. A reserved loopback port that is never put into listening state creates a real transport outage, including a direct failed provider probe and failed accepted-experience writes. It repeats outage retrieval, restores the actual endpoint, explicitly reindexes only disposable data and verifies semantic recovery. Accepted conversation inputs are synthetic fixtures; **no real generation-quality or new Godot claim** is made by this embedding-focused run. Evidence includes implementation fingerprints, per-retrieval latency, diagnostics, selected payloads and the actual transport error.

Earlier evidence is preserved: `memory-retrieval-live-v1` stopped at the sandbox's loopback bind restriction before exercising retrieval; `v2` passed **18/18** before the final trace-label/selected-mode refinements and added ranking test. D1 and Godot artifacts remain historical with their original counts and limitations.

Changed for D2: `services/memory/{service,index}.py`, `services/context/{models,builder}.py`, `services/pipeline.py`, `tests/{test_semantic_memory,test_memory_provenance,run_memory_retrieval_live}.py`, this plan, the historical progress pointer and new evidence. Existing uncommitted work is preserved; nothing is staged or committed. Player saves and the unknown port-8001 service were not used.

### Remaining limitations and next slice

Fallback is a bounded lexical approximation, not paraphrase-equivalent semantic retrieval or a guarantee of globally optimal recency/importance ranking. ASCII substring terms can match partial words; missing vocabulary can yield importance/recency-only results. Database matching/sorting may still inspect many eligible rows; no text-search index or PostgreSQL execution/performance verification was added. In mixed mode only the lowest 50 malformed-vector IDs join the lexical pool; null/mismatched-model candidates have the ordinary SQL limit. Outside-world filtering and deduplication can underfill the bounded result without an unbounded retry. Reindex currently repairs missing/mismatched vectors, not malformed vectors bearing the current model key. Existing synchronous embedding writes and index construction costs remain.

**Next smallest authorized task:** E decision-trace completeness audit and repeatable demonstration evidence for existing grounded/behavior/memory scenarios. D3 memory-driven state influence stays deferred; it needs its own bounded, idempotent state/role/control integration slice. Authored mandatory recovery, automatic retention/general corrections, the two D1 social-generation failures and a release-quality threshold remain outstanding.

Commands:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_semantic_memory.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_memory_provenance.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tests/run_memory_retrieval_live.py --output docs/evidence/NEW-MEMORY-RETRIEVAL.json
git diff --check
```


## E checkpoint — decision evidence and repeatable API demo (2026-10-12)

**Completed slice:** inspect why an NPC answered, clarified, cooperated or refused using a durable, bounded decision trace; repeat the existing scenarios against real providers and retain a clearly labeled recorded API transcript. This does not complete rendered presentation recording, agree a release-quality threshold or enable D3.

### Runtime changes

`/chat` now returns additive `decision_trace` schema version 1 and stores the same JSON in `Conversation.validated_output`. It joins current context source IDs, retrieved memory provenance/status and retrieval diagnostics, a bounded non-authorizing proposal projection, generation status, validation/rejection reason, candidate state, memberships/rule strengths/tendencies, eligible/scored actions, selection/mapping, memory-write metadata, timing and durable conversation/event IDs. Response/persisted trace equality is tested. Generation distinguishes succeeded, bypassed and provider-or-decode failure; an authoritative override is explicit. The existing behavior outcome receipt now includes the event UUID alongside its conversation ID; timed bow reward receipts also carry both IDs without inventing a generation/FSEC decision for automatic completion.

The shareable trace omits prompt/history text, raw dialogue, model reasoning, credential fields, endpoint URLs and other NPC inventory/state. Proposal references are limited to two known context IDs; unknown references/fields produce counts instead of copied strings. Numeric deltas must be finite/bounded; arbitrary legacy emotion labels are omitted from the exported mapping. Schema rejection reasons are now generic instead of embedding Pydantic input excerpts. Provider failure logging retains its existing error-level signal without copying transport exceptions/credentials. The ordinary response dialogue and original raw conversation audit still exist separately; they are not the privacy-filtered export and should not be treated as shareable diagnostic artifacts.

Changed for E: new `backend/app/services/decision_trace.py`; updated `services/pipeline.py`, `schemas/chat.py`, `services/validation/service.py`, `services/quests/bow.py`; new `tests/test_decision_trace.py`, `tests/decision_demo_scenarios.json`, `tests/run_decision_demo.py`; new [demo runbook](demo-runbook.md), evidence and progress updates. Existing uncommitted work is preserved. No staging, commits, saved-world resets or use of the unknown port-8001 service occurred.

### Verification

Final focused trace suite: **8 passed**. Final full deterministic regression: **424 passed**, exit 0. Tests run production HTTP/persistence with explicitly deterministic providers and cover accepted trace/source/outcome links, persisted/response equality, malformed-output/private-state/credential canaries, provider failure without exception-text leakage or effects, accepted legacy label redaction, authoritative generation bypass, actual transfer-to-memory source identity, recalled claim/current-fact precedence, safe numeric/reference projection, and one durable timed reward receipt across repeated advances. Existing failure, transfer, crafting, role, scope and reset-race regressions still pass. `git diff --check` passed.

Final [live API evidence](evidence/decision-demo-live-v3/evidence.json): **26/26 scenarios**, **262/262 trace invariant checks**, two complete attempts through the real `/chat` path using a disposable file-backed SQLite world. Fourteen calls used configured real generation; twelve authoritative requests bypassed generation as designed. Configuration: `llama3:latest`, temperature **0.2**, schema enabled, `nomic-embed-text`, **768 dimensions**, embedding revision `v1`; Python and installed Ollama version/model digests are recorded. Those model digests are metadata from the configured embedding server, not a remote-provider weight attestation. All final application/runner/fixture fingerprints match the saved evidence.

The scenario sequence covers known location/follow-up, missing directions, unknown location, a delivery claim and later scoped recall without verified delivery, helpful transfer, repeated transfer request, cautious clarification/cancel, optional refusal and recipient isolation. State changes used to compare helpful/cautious/distrustful behavior are explicit test fixtures, not remembered rewards or new gameplay content.

There were **0 rejected replies**, **0 inappropriate fallbacks** and **0 authority failures** in this bounded run. [Answer review](evidence/decision-demo-live-v3/answer-review.json) inspected all 26 final answers against sources/execution evidence and observed **0 unsupported factual/outcome statements**. All 13 paired final answers matched across attempts, as expected for constrained rendering/authoritative replies; this does not assert deterministic underlying generation. Total API latency: **0.031–3.352 seconds**, median **0.863 seconds**, p95 **3.329 seconds**; these aggregate generation and bypass calls, with per-case/per-stage timing retained. This is evidence for the recorded scenarios, not unrestricted language quality or an agreed release threshold.

The [recorded transcript backup](evidence/decision-demo-live-v3/transcript.md) contains actual visible answers plus safe decision traces and explicitly states it is recorded API execution, not live replay, Godot gameplay or a screen recording. [Run log](evidence/decision-demo-live-v3/run.log) is preserved. [Runbook](demo-runbook.md) documents a new disposable run, presentation sequence, backup use and separate failure checks. The runner refuses to overwrite evidence and exits nonzero on failed scenarios/invariants; partial results survive a runner failure.

Earlier `decision-demo-live-v1` and `v2` also passed **26/26** scenarios and **262/262** trace checks and remain preserved. `v1` predates the arbitrary legacy-label export guard and timed receipt IDs; `v2` predates final provider-log wording. Only `v3` is the exact final-code claim. D1 live social failures and older Godot/D2 artifacts retain their original results and implementation limits.

### Remaining work

A fresh rendered/manual Godot walkthrough or video is still outstanding, as is the agreed presentation/release quality threshold. The new API demo does not retest the complete bow playthrough, actual generation timeout transport, social preference variability or every required evaluation scenario; those existing deterministic/historical/live artifacts remain separate. No completion claim is made for D3, authored mandatory recovery, automatic retention/general corrections or PostgreSQL execution/concurrency/performance. Stable IDs and field projection make the decision export inspectable but are not a general secret scrubber for arbitrary customized catalog/configuration content; do not place credentials in those trusted inputs.

**Next smallest task:** fresh rendered/Godot demonstration evidence for the current implementation, using disposable saves and existing authored scenarios. D3 remains deferred. Before final release/presentation acceptance, agree the expected recording format and live-quality threshold.

Commands:

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_decision_trace.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tests/run_decision_demo.py --output docs/evidence/decision-demo-NEW --attempts 2
git diff --check
```


## E rendered integration checkpoint — 2026-10-13

**Completed slice:** fresh native rendered Godot execution against the current application, including parsed decision traces, the full existing bow path, save/resume/reset and real provider connection failure. No gameplay or application behavior was changed. Verification-only edits extend `frontend/godot/tests/grounded_chat_smoke.gd` and `backend/tests/run_godot_grounding.py`; runbook/progress and new evidence are updated.

### Actual evidence

[Rendered live summary](evidence/godot-decision-rendered-v1/summary.json): **334/334 assertions passed**, Godot **4.5.1 stable** (`f62fdbde1`), native macOS display, Metal 3.2 Forward+ on Apple M5. Generation used configured `llama3:latest`, temperature **0.2**, schema enabled; embeddings used `nomic-embed-text`. The recorded binary version is authoritative for this run; earlier references to another Godot version do not describe this capture. Thirty-nine explicit chat submissions had **0 rejected replies**, with end-to-end latency **0.059–5.959 seconds** (including HTTP/display handling and deterministic bypasses). Three additional UI transfer conversations and the automatic timed reward were captured in the persisted audit.

Checks cover both NPCs' known-location/follow-up/missing-route/unknown-location/current-delivery/inventory/claim-injection scenarios, visible optional refusal and cooperation, confirmed owned-item transfers, string pickup, partial delivery, scene relaunch preserving phase/position/dialogue/inventory, timed crafting with no instant reward, exactly one bow, consumption-safe delivery history, a full backend/Godot process restart, repeated reward polling and explicit disposable reset. The existing required quest succeeds under the controlled distrustful Craftsman fixture; mandatory refusal/recovery is not enabled.

Godot now checks actual parsed trace schema/recipient/scope, durable event/conversation identities, selected FSEC eligibility/scores and bounded memory diagnostics after each explicit chat. Capture validates **42/42 chat decision-trace source links** and **9/9 memory provenance links**; the automatic reward remains a separate authoritative receipt, not a fabricated model/FSEC decision. [Shareable trace export](evidence/godot-decision-rendered-v1/decision-traces.json), original local conversation audit, memory capture, logs and restart report are preserved.

[Rendered provider-failure summary](evidence/godot-decision-provider-failure-v1/summary.json): **22/22 assertions passed**, **2/2 rejected zero-effect replies**, **0 important memories**, **2/2 valid decision-trace source links**. The real generation provider uses an unreachable local endpoint; this is actual connection failure, not mocked generation, a slow timeout or an embedding outage. The real UI displays fallback, restores controls and parses explicit provider/decode-failure status with no authorized action.

[Recorded screenshot walkthrough](evidence/godot-decision-rendered-v1/walkthrough.md): **8 live-flow PNGs plus 1 provider-failure PNG**, all **1280×720** and visually inspected. It shows optional refusal/cooperation, both NPCs' missing-route answers, partial delivery, crafting progress, one completed bow, reset and provider fallback. [Screenshot review/hashes](evidence/godot-decision-rendered-v1/screenshot-review.json) are retained. This is recorded automated rendered gameplay evidence, not a manual playthrough, continuous screen recording or narrated video. The [runbook](demo-runbook.md) reproduces both captures and labels backup use explicitly.

Full deterministic regression after verification edits: **424 passed**, exit 0. `git diff --check` passed. All captured application/frontend/verification-source fingerprints match the current files. Earlier Godot/API/D1/D2 artifacts remain preserved and are not relabeled. Existing uncommitted changes are intact; nothing was staged or committed. Both native runs reserved their own backend socket and used temporary databases/projects. Player saves and the unknown port-8001 service were never used.

### Remaining limits and next checkpoint

This bounded slice closes fresh rendered integration and a screenshot backup for enabled scenarios. No unrestricted conversational-quality/release-readiness claim is made: the live-quality threshold and final presentation/recording format still require agreement. The two D1 social preference rejections remain unresolved historical results; this run did not retune or rerun that social suite. Actual slow generation timeout, D2 embedding outage inside a rendered UI, PostgreSQL concurrency/performance, general corrections/retention, new story content and authored mandatory recovery remain separate. D3 memory-driven state influence remains deferred and was not activated by these checks.

**Next checkpoint:** agree the presentation format and release-quality threshold, then run the matching acceptance pass or capture the requested continuous/narrated recording. D3 requires a separately authorized bounded influence/idempotency slice; story-dependent tasks require authored content. Do not invent those decisions or content to check off the plan.
