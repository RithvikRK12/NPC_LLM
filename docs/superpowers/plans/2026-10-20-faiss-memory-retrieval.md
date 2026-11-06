# FAISS Memory Retrieval Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to implement this plan task by task. This document proposes work; it does not enable retrieval or authorize a deployment.

**Goal:** Connect semantic retrieval of relevant older NPC memories to the active conversation runtime while always supplying authoritative current game state.

**Architecture:** SQL owns state, history, provenance and memory revisions. FAISS is a disposable index that ranks eligible older context. The backend combines mandatory current facts, recent conversation, and relevant retrieved memories before asking Llama to write dialogue.

**Tech stack:** Existing FastAPI/SQLAlchemy backend, SQLite and PostgreSQL, local Ollama embeddings, existing `faiss-cpu`, and the current Llama model. No replacement dialogue model is proposed.

**Design references:** [Detailed redesign](../../npc-conversation-redesign-detailed-design.md), [context task](../../redesign-tasks/context.md), [memory task](../../redesign-tasks/memory.md). This plan supplies the missing runtime integration and verification work.

**Status:** Implementation in progress, 2026-10-20. Code, offline tests, paired local trials, PostgreSQL checks and targeted Godot regressions ran. Broader semantic evaluation and local enablement remain open. Existing prompt/state/repair fixes remain in place.

## Why retrieval was left unwired

There are two separate facts:

1. The context module deliberately made semantic ranking optional. Its [T02 handoff](../../evidence/conversation-redesign-context/t02-handoff.md) says the selector ranks only already validated, scoped candidates and falls back to deterministic ordering on embedding/index errors. This protects privacy, provenance and availability.
2. Production assembly in [application.py](../../../backend/app/services/conversation/application.py) constructs `ContextAssembler(self._context_reader)` without providing `older_context_selector`. Therefore that optional selector is never invoked by the active runtime.

The first explains the extension point's design; it does **not** explain or justify leaving the production connection absent. The handoff explicitly limited its evidence to the pure module and fake-reader tests, leaving concrete integration to later tasks. I found no documented benchmark showing that disconnected retrieval is better, and no recorded product decision to remove FAISS from the active NPC memory path.

The defensible diagnosis is an integration and verification gap: coverage of a hook and its outage behavior was treated as sufficient evidence without proving that production used the real index. The redesign files are currently uncommitted, so repository history does not establish a more precise chronological explanation or the intent of each contributor. Do not present a speculative rationale as a documented decision.

## Current implementation and missing pieces

| Area | Present behavior | Required change |
| --- | --- | --- |
| Current game facts | SQL-backed game adapter projects inventory, encounters and quests | Retain these as authoritative; pin facts required for this turn in the context budget |
| Older-memory selection | Optional selector defaults to `None`; deterministic ordering remains | Add query-aware semantic ranking and wire it into production |
| Selector input | Receives a `TurnRef` and older candidates | Supply the current query text explicitly; `TurnRef` alone cannot be embedded meaningfully |
| Existing FAISS implementation | Legacy memory service uses Ollama embeddings and an HNSW index | Reuse embedding/index primitives through a new adapter for redesigned records |
| Memory schemas | Legacy `Memory` rows and redesigned revisioned memories are distinct | Preserve redesigned IDs, scope, epoch, revisions and uncertainty; do not substitute legacy row IDs |
| Source checks | Redesigned reader accepts source text IDs present in its history snapshot | Resolve valid older sources independently so retrieval can reach beyond the visible transcript |
| Prompt projection | Some speech routes deliberately omit historical transcript | Pass selected, relevant, attributed memories to the model when useful; keep simple gratitude compact |
| Diagnostics | Optional selector exceptions retain deterministic ordering | Record whether semantic ranking ran, degraded or was unnecessary |

FAISS indexes vector similarity, not truth or permission. An old offer to inspect can be relevant history while a current SQL fact establishes that the inspection has since finished. Retrieved player reports remain reports; retrieval cannot turn them into verified outcomes.

## Global constraints

- Keep the current Llama model and existing explicit conversation policy bounds.
- Filter by save/game scope, NPC, epoch, visibility, active status and current revisions before ranking. Recheck selected sources before publication.
- No embeddings, index rebuilds or LLM calls while holding a SQL transaction or common game writer lock.
- Never use retrieval to establish consent, execute an action, grant inventory, complete a quest or override a receipt.
- Preserve historical finalized replies and committed operations. Do not reset or rewrite the personal save to implement or test this work.
- An unavailable embedding provider or index degrades memory selection; unavailable authoritative state remains an error.
- Changes to a frozen contract require its normal versioning/conformance process. Prefer internal adapter/value changes where possible.

## Proposed flow

1. Read a consistent, scoped SQL snapshot of current facts, recent finalized turns, memory heads, summaries and their source revisions.
2. Resolve eligible older sources and reject revoked, superseded, invalidated, private or mismatched records. Detach values and release SQL transactions.
3. Reserve the context budget for current input, instructions, operation constraints, required interactions and critical current facts.
4. Embed the current query and rank the eligible older records through FAISS within a bounded retrieval deadline. If unavailable, use deterministic scoped selection.
5. Revalidate selected memory heads/source revisions. Attach only the allowed detached values; index output cannot introduce an unknown record.
6. Include the selected memories, their attribution and uncertainty in the speaker-facing prompt. Current mechanical state takes precedence over historical recollection.
7. Generate and validate the reply through the existing pipeline. Preserve the existing bounded repair, durable request identity, receipt and finalization behavior.

## File map

Existing files to modify:

- `backend/app/services/conversation/application.py`: production assembly and explicit context policy.
- `backend/app/services/conversation/context.py`: query-aware selector input, bounded selection and required fact retention.
- `backend/app/services/conversation/adapters/context_read.py`: scoped older-source resolution and memory eligibility.
- `backend/app/services/prompts/builder.py`: selected-memory projection for relevant speech routes.
- `backend/app/config/settings.py` and `config/playtest.env`: explicit local retrieval switch and bounded retrieval settings.
- `backend/app/database/init_db.py`: integrate any additive persistence migration using repository conventions.

Proposed new files, with names to remain consistent during implementation:

- `backend/app/services/conversation/adapters/semantic_retrieval.py`: query-aware ranking over detached eligible records; reuse `memory/embedding.py` and `memory/index.py`.
- `backend/app/models/conversation_embedding.py`: optional vector/cache metadata for redesigned records, if durable vector reuse is selected.
- `backend/app/services/conversation/adapters/embedding_refresh.py`: bounded post-commit refresh and stale-work rejection.
- `backend/tests/test_conversation_semantic_retrieval.py`: ranking, isolation, degradation and budget tests.
- `backend/tests/test_conversation_retrieval_runtime.py`: actual production wiring and prompt delivery tests.
- A disposable live evaluation runner under `docs/evidence/conversation-memory-retrieval/`.

Do not call legacy `MemoryService.retrieve_relevant_memories` directly from the new runtime without an explicit, tested schema/provenance bridge. Reusing FAISS primitives is different from treating the two memory stores as interchangeable.

## Implementation tasks

### 1. Pin current facts and define query-aware retrieval

- [x] Add failing tests showing current inspection/quest/inventory facts survive pressure from recent history and older memories.
- [x] Define an internal immutable retrieval query containing the turn key, current player text and a bounded deadline. Pass it from the assembler to the selector; do not infer text from a turn ID or shared mutable state.
- [ ] Populate `ContextBudget.critical_evidence_ids` from the actual operation/current-topic requirements in production. Keep required interactions and execution constraints mandatory.
- [x] Add tests for mandatory overflow returning `CONTEXT_BUDGET_EXCEEDED`, complete-value retention, and no silent truncation of attribution.
- [x] Account for the actual serialized prompt and reserved output/schema overhead. Document whether token counting is exact or estimated; the current lexical estimator is not a provider tokenizer.
- [x] Run context and contract conformance checks before advancing.

### 2. Make older-memory provenance usable and scoped

- [x] Add a regression where a valid memory's source is older than the visible transcript; prove it is currently excluded, then resolve its source from scoped finalized SQL records.
- [x] Resolve exact source IDs without loading the entire old transcript into the prompt or remapping an old ID onto current text.
- [ ] Recheck memory/source/correction heads and retain attribution, uncertainty, status and revision. Exclude legacy/unknown lineage until an explicit bridge can verify it.
- [x] Bound SQL candidate selection explicitly. Record candidate limits and any deterministic preselection so evaluation can expose memories lost before FAISS ranking.
- [ ] Test cross-save, cross-NPC, cross-epoch, private, invalidated, retracted, superseded and corrected records, including a clear/new-game race.
- [x] Run SQLite and PostgreSQL source/isolation checks.

### 3. Add FAISS ranking and embedding lifecycle

- [x] Write ranking tests with known vectors and eligible detached candidates, including unknown/duplicate index IDs.
- [x] Implement the new semantic adapter using the existing `EmbeddingService`, `CandidateIndex` and bounded cache. Preserve candidate IDs separately from FAISS positions.
- [x] Make the adapter return ordered eligible IDs; retain deterministic ordering for unranked eligible candidates.
- [x] Persist reusable embeddings separately from authoritative memory content. Key them by game scope, NPC, epoch, record ID/revision, content hash, embedding model/revision and dimensions.
- [x] Add additive migration and idempotent refresh support. A missing/stale vector is recoverable work, not a missing memory or failed game transaction.
- [x] Calculate vectors after commit and outside read/write transactions. Before storing results, recheck scope, source and record revision so delayed work cannot resurrect cleared/corrected memory.
- [x] Key/invalidate index caches by eligible corpus revisions, scope, NPC, epoch, visibility and embedding configuration. Treat indexes as disposable.
- [ ] Bound query embedding latency and refresh batches through explicit settings; choose local values after measurement. Test timeout, malformed vectors, missing model, dimension mismatch and rebuild failure.

### 4. Wire production and deliver retrieved context to the model

- [x] First add a test that constructs the real production runtime and fails unless its configured retrieval adapter is called for a relevant older-memory query. A fake selector tested directly is insufficient.
- [x] Inject the semantic adapter when the retrieval switch is enabled. Keep an explicit off mode for comparison and rollback.
- [x] Add a transport-capture test proving a relevant memory reaches the actual provider prompt with its attribution. Also prove a private or stale memory does not.
- [x] Preserve compact gratitude handling: a simple acknowledgement should not reopen old offers merely because an index found them. A message that genuinely refers to an older conversation must retain the relevant memory context.
- [ ] Ensure memory ranking never suppresses mixed requests, concerns, current facts or operation preconditions.
- [x] Record retrieval mode (`semantic`, `degraded`, `disabled`, `not_needed`), candidate/selected counts, latency, embedding/index identity and degradation reason outside NPC dialogue. Do not expose internal IDs in player-facing text.
- [x] Verify provider/index calls occur with no database transaction/writer lock held.

### 5. Evaluate behavior, then enable the local configuration

- [x] Run paired retrieval-off/retrieval-on trials with the same Llama settings, snapshots and messages. Preserve failures and missing outputs.
- [ ] Include old player preferences, earlier promises, an earlier offer followed by completed inspection, player-claimed delivery versus actual inventory, corrections/retractions, references beyond the recent window, and both NPCs.
- [ ] Include an empty memory corpus and embedding/index outages. Confirm degraded retrieval still yields normal conversation where authoritative context is available.
- [ ] Measure relevance, long-term recall, stale-fact errors, privacy leaks, repeated offers, provider repairs/fallbacks and complete-turn latency. Mechanical tests do not establish semantic quality.
- [x] Run the full backend suite, relevant PostgreSQL runners, and disposable Godot conversation/inspection/gatherer regressions. Never use personal-save resets for verification.
- [x] Review and record actual dialogue samples. Existing human-scoring waiver does not create a semantic score; report unscored results honestly and leave release-wide quality gates open unless separately satisfied.
- [ ] Enable the explicit local switch only after the implementation checks pass and measured behavior supports it. Record selected settings and evidence; retain retrieval-off comparison mode.

## Review focus and acceptance criteria

The implementation is complete only when all of these are demonstrated:

- A production runtime test proves FAISS ranking is actually invoked, and a provider-boundary test proves its selected memory reaches generation.
- A reference older than the visible conversation window can retrieve valid, source-linked memory.
- Current SQL state wins over a conflicting historical memory under both normal and tight context budgets.
- NPC/save/epoch/visibility isolation and correction handling survive stale caches, delayed embeddings, clear/new-game races and restart.
- Embedding or index failure cannot erase memory, change accepted actions, manufacture a receipt, leak private context or block otherwise valid conversation indefinitely.
- The personal save loads unchanged and no finalized history is rewritten.
- Comparative live evidence supports the local adoption decision; no blanket claim of improved dialogue quality is inferred from using FAISS.

## Rollback

Disable only semantic ranking through the new retrieval switch. Keep SQL memories, provenance, embeddings, summaries and conversation/receipt storage intact. Continue scoped deterministic selection and mandatory current-state projection. Preserve the existing conversation runtime policy and pending-turn recovery; disabling retrieval is not the same as disabling the conversation service.
