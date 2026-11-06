# game-adapters/T03 writer audit and Main Agent acceptance

Date: 2026-10-18 (Asia/Kolkata)
Owner: `game_adapters_t03`, gpt-6.1-sol / high.
Status: accepted by Main Agent 2026-10-18 after implementation review and independent reproduction. The original read-only audit below records the pre-implementation boundary inventory; the implementation and current evidence are appended at the end.

## Existing durable version inventory

| Model / table | Existing version | Coverage / limitation |
| --- | --- | --- |
| `Player` / `players` | None | Inventory, position, opening, salvage, location and map metadata have no ordered resource label. `game_scope` identifies the run, not order within a run. |
| `NPC` / `npcs` | UUID `memory_revision` | Retrieval invalidation and legacy proposal CAS; UUIDs do not order inventory/NPC snapshots. Non-chat inventory writers do not consistently rotate this token. |
| `Quest` / `quests` | None | Legacy status and progress are unversioned. |
| `BowQuest` / `bow_quests` | None | Phase, string pickup and timed reward are unversioned. |
| `ShipRepairQuest` / `ship_repair_quests` | None | Phase/contributions have no monotonic label. `outcome_id` is an event identity. |
| `CraftsmanEncounter` / `craftsman_encounters` | Integer `revision` | Commands/checkpoints increment only this activity's counter; resets to zero when scope changes. Topic updates in `craftsman_intent.dialogue` do not increment it. |
| `GathererEncounter` / `gatherer_encounters` | Integer `revision` | Commands increment the encounter counter. The authored staging migration in `record` changes encounter state and Player position without incrementing it. |
| Conversation persistence T01 | Stream `canon_revision`, pending-interaction revision, summary digest, operation result-revision JSON | These describe other domains or store labels supplied by a caller. There is no generic shared-resource revision table/store. |
| `GameReadAdapter` | SHA256 of public fact content; semantic eligibility digest for capabilities | Digests support equality only, permit ABA, and cannot order delayed Godot snapshots. Capability fingerprints omit quantities and quest state. |

The persistent models above were inspected directly. No existing field provides monotonic inventory/quest/world resource labels across all mutation paths.

## Concrete writer audit

| Entry / owner | Mutations | Current transaction / ordering |
| --- | --- | --- |
| `state/service.py:25`, `StateService.apply` | Player/NPC inventory, legacy quest status/progress, pending item, existing social/current-state fields | Flushes, caller owns transaction. Lower service assumes caller lock. Legacy pipeline and game adapter lock Player before NPC. |
| `quests/bow.py:13`, `get_quest` | Creates default BowQuest | Flushes; invoked from both read-like and write paths. No own writer lock. |
| `quests/bow.py:38`, `dialogue` | `meet -> gather` | Caller transaction/lock. |
| `quests/bow.py:65`, `maybe_start` | Consumes Craftsman wood/string, starts crafting, sets ready time/current state | Flushes; caller transaction/lock. |
| `quests/bow.py:87`, `finish_if_ready` | Grants one bow, marks quest complete, current state, authoritative event/memory | Caller transaction; locks Craftsman after caller Player lock. |
| `api/routes/quests.py:30,49,62` | Quest start; existing one-time Gatherer wood replenishment; string pickup; timed completion | Each route locks Player first; payload flushes and commits. No labels returned. |
| `opening.py:20,35` | Opening/handoff position/location/map metadata; salvage ID and rope grant | `current_run` locks/reloads Player and checks scope; methods commit. No labels returned. |
| `api/routes/world.py:56` | Player position/location/recovery notice | Player lock, optional scope check, commit. No labels returned. |
| `craftsman.py:33` | Creates/rescopes activity record | Caller transaction, no own lock. |
| `craftsman.py:94,132` | Activity state/revision, checkpoint NPC location, intro/inspection Player position, accepted/cancelled activity, ShipRepairQuest creation, authoritative/reported memory | Flushes; routes hold Player lock and commit; conversation adapter holds Player then NPC and caller commits. Direct owner methods assume caller discipline. |
| `craftsman_intent.py:38,65` | Legacy outing dispatch and topic field on encounter JSON | Legacy pipeline holds writer lock at effect time. Topic-only change bypasses encounter revision. |
| `gatherer.py:25` | Creates/rescopes encounter; migrates obsolete authored staging and Player position | No own lock. Called by snapshots, including `/world` GET. Existing migration behavior is covered by `test_relocated_pending_checkpoint_preserves_refusal_outcome`. |
| `gatherer.py:56` | Encounter state/revision, Player position, existing deterministic social consequences, authoritative memory | Flushes only; endpoint locks Player first and commits. Lower owner assumes caller lock. |
| `database/seed.py:51`, `reset_world` | New scope, Player/NPC inventory/state/location, legacy/Bow quest reset, bulk deletes activity/ship/story rows and display/memory rows | Already locks Player then ordered NPCs, flushes; `/world/new-game` commits. Database file is outside this worker's allowed edits. Bulk deletes need explicit revision/reset handling or scope invalidation. |
| `database/inventory_migration.py:6` | Startup additive NPC inventory initialization and Player supplies backfill through raw SQL | Connection transaction during initialization; no runtime writer lock or resource labels. Migration belongs to persistence owner. Baseline label initialization must occur after migration and before serving requests. |

`state/locking.py:6` performs a no-op Player UPDATE before SELECT FOR UPDATE, so SQLite acquires a real writer lock. It refreshes the Player identity-map value. Repeatedly introducing this function into lower owners can discard dirty Player values when the production session has `autoflush=False`; do not add indiscriminate nested refresh calls. The revision/writer design must preserve caller transaction ownership and dirty values.

## Hidden snapshot writes and coherence

- `/world` reads Player/quest/NPC/history first, then calls Gatherer and Craftsman snapshots. Both call record creators; Gatherer may migrate state and position. It currently takes no Player writer lock.
- Legacy pipeline context calls Craftsman encounter snapshot before provider generation, then rolls back its read transaction. The final payload may also call record creators after its mechanics commit.
- A future labelled snapshot must bind copied values and revisions to one coherent boundary. Sequential unlocked ORM reads under PostgreSQL READ COMMITTED can combine values and labels from different commits.
- Content hashes cannot replace durable revisions. Relevant version mismatch requires current deterministic precondition revalidation; it must not automatically substitute terms or expire a negotiation solely due to unrelated churn.

## Minimal persistence coordination requested

Proposed new persistent store contract (requires Main Agent task recording and persistence ownership):

- Key: `(game_scope, resource_id)`; exact nonnegative monotonic integer revision. Missing key reads as zero.
- `read(game_scope, resource_ids) -> RevisionSet`: detached current labels, no record creation or commit.
- `bump(game_scope, affected_resource_ids)`: atomic increment/first insert in the caller's transaction while the common Player writer lock is held. Rollback restores labels with effects; unchanged retries create no effect/revision.
- Stable candidate IDs: `inventory:player`, `inventory:npc:<id>`, `quest:legacy`, `quest:bow`, `quest:ship_repair`, `activity:ship_inspection`, `encounter:gatherer`, `world`; `npc:<id>` if a complete NPC projection containing social/location/current-state fields is versioned independently.
- The game layer owns the mapping from existing mechanical writes to affected resource IDs; persistence owns schema/migration/store implementation. No generated game capability is introduced.
- Reset changes scope, invalidating every prior resource label and current-scope publication. Preserve historical scope labels as necessary for receipt recovery; new scope initializes its own labels. Define explicit reset handling before touching the forbidden reset owner.

## Checks run

Working directory: `/Users/rukithnayak/Documents/NPC_LLM-1`. Existing Python venv; disposable file SQLite fixtures created by the test suite; no provider, player save or PostgreSQL connection used.

| Command | Exit | Result / evidence |
| --- | --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_game_adapters.py' > /private/tmp/conversation-game-adapters-t03-baseline.log 2>&1` | 0 | 29 baseline tests pass, 0 failures/errors/skips. This verifies accepted T01–T02 baseline only; no T03 acceptance is claimed. |

No RED test or implementation check has been run because the missing durable boundary is under coordination. T03's non-chat/proposal race, cross-NPC contention, cancellation/reset and monotonic snapshot tests remain required on isolated SQLite and PostgreSQL. No packet/master checkboxes were edited.

## Original audit follow-up (superseded by acceptance below)

- T03 remains incomplete: every-write revision discipline and ordered snapshots are not implemented.
- Main Agent must record/assign the minimal persistent resource store expansion, freeze its interface, and coordinate reset/migration ownership.
- Then resume `game-adapters/T03` for test-first game writer integration, coherent projections and both-engine race evidence.
- Consumers remain `persistence-adapters/T03–T04` (receipt/publication and lifecycle), `api-adapter/T02` (transport labels), and `godot-adapters/T03` (scope/revision-aware application). Confirm exact API task ownership before editing schemas/legacy pipeline payloads.

## Implemented deliverable and Main Agent verification

The game-owned revision boundary is implemented in `backend/app/services/state/resources.py`. It serializes game writers on Player, snapshots detached values and labels coherently, increments only changed resources in the caller transaction, and clears counters when a new game scope is installed. Existing game owners and route writers now use this boundary for inventory, quests, activities, world position/opening state, and reset. Snapshot-triggered staging migrations/topic writes are labelled; operation/cancellation/reset races and refresh of stale clean ORM objects are covered. No new gameplay capability or relationship scoring was introduced.

Single-offer consent paths consume the `contracts/T07` typed binding. The persistence gateway independently reloads stored terms and admitted answer text. The current answer candidate/source span is kept separate from the original stored offer span.

Main Agent reviewed the production diff and reproduced:

- SQLite `test_conversation_game_adapters.py`: 48/48 passed. [Log](t03-sqlite.log)
- PostgreSQL 16.15 `GameResourceRevisionTests` on disposable `npc_test_game_t03_*`: 19/19 passed. [Runner](run_t03_postgres_acceptance.py), [log](t03-postgresql.log)
- Full backend suite: 935/935 passed. [Log](../conversation-redesign-persistence-adapters/t03-logs/backend-final.log)
- `git diff --check`: passed.

The PostgreSQL runner creates and drops a fresh test database and confines `vector` setup to that database. It never uses `mvp` for game revision acceptance. API and Godot application of published revision labels remain downstream tasks.
