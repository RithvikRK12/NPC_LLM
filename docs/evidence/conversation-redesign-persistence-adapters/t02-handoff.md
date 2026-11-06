# persistence-adapters/T02 handoff

Date: 2026-10-18 (Asia/Kolkata)

## Task

- ID: persistence-adapters/T02.
- Owner / model / reasoning effort: persistence_t02 / gpt-6.1-sol / high.
- Status: ready for Main Agent review.
- Scope and dependency versions: accepted persistence-adapters/T01 schema, ports/T02 and turns/T02 contracts/conformance, Detailed design §§5, 6.4, 6.6–6.7, 9–10 and shared invariants. No migration, resource-revision, game-service, master-progress or task-checkbox edits.

## Files changed

- `backend/app/services/conversation/adapters/persistence.py` — new `SQLTurnStore`: atomic scoped admission/deduplication and sequence allocation; oldest-turn claim/fence checks; durable provider attempt ledger/output/assembly; pending, exact status, recovery and receipt lookup; safe infrastructure/uncertain-commit errors. Each method owns/closes its session. Writer order is the existing `lock_player` boundary, stream, then turn.
- `backend/tests/test_conversation_persistence.py` — 23 real-database behavioral checks, including eight concurrent clients, fresh engine recovery, failures before durable writes, lost commit acknowledgements and corrupt receipt scope. SQLite uses a temporary file; explicit test URLs must target disposable `npc_test_*` databases and may not select an arbitrary SQLite file.
- `docs/evidence/conversation-redesign-persistence-adapters/t02-logs/` — exact test outputs.
- This handoff. Shared-file coordination: none; all production changes are confined to the new persistence adapter.

## Tests run

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1`.

- Expected initial RED: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_conversation_persistence.py -v` — 15 failures, all `T02 SQLTurnStore is not implemented`. [Log](t02-logs/initial-red.log). The development shell wrapper tailed the redirected output, so its reported shell exit was 0; unittest itself failed. Follow-up RED added lost-claim acknowledgement identity (22 tests, 1 failure: missing known turn reference), then receipt-payload scope (23 tests, 1 failure: mismatched receipt was returned). [Claim RED](t02-logs/claim-ack-red.log), [receipt RED](t02-logs/receipt-scope-red.log). Both were fixed and rerun.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_conversation_persistence.py -v` — SQLite temporary file; exit 0, 23 passed, 0 failed/errors/skipped. [Log](t02-logs/sqlite.log).
- `CONVERSATION_TEST_DATABASE_URL='postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/npc_test_t02_20261018' PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p test_conversation_persistence.py -v` — PostgreSQL `16.15 (Debian 16.15-1.pgdg12+2)`; exit 0, 23 passed, 0 failed/errors/skipped. [Log](t02-logs/postgresql.log). Initial sandbox connection failed with `Operation not permitted`; authorized localhost escalation succeeded. Database was created through the `postgres` maintenance database and dropped after the final run; `mvp` and player data were never used. `psycopg` is unavailable; the installed `psycopg2` driver was used.
- `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_store_ports test_conversation_turns test_conversation_persistence_schema -v` — isolated in-memory SQLite and frozen fakes; exit 0, 65 passed, 0 failed/errors/skipped. [Log](t02-logs/adjacent.log).
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` — exit 0, 407 passed, 0 failed/errors/skipped, before the final receipt-corruption case was added. [Log](t02-logs/conversation.log). The final full suite below includes that additional case.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v` — final run, exit 0, 876 passed, 0 failed/errors/skipped. [Log](t02-logs/backend-final.log). The previous broad run overlapped T05 implementation and had 875 tests with 1 failure/4 errors, all in `test_resource_revision_storage`: `test_database_initialization_upgrades_populated_players_idempotently`, `test_populated_migration_preserves_every_existing_field_and_defaults_legacy_rows`, `test_repeated_migration_preserves_existing_revisions_and_scope`, `test_revision_writes_rollback_with_the_callers_player_transaction`, and `test_fresh_model_defaults_to_an_empty_nonnullable_json_ledger`. Those missing migration/model and legacy fixture errors were corrected by the T05 owner; final run has no failures. [Earlier log](t02-logs/backend.log).
- `git diff --check -- backend/app/services/conversation/adapters/persistence.py backend/tests/test_conversation_persistence.py` — exit 0. These files are currently untracked in the shared redesign working tree; the Main Agent must include them when reviewing/integrating.

## Results

- Atomic scoped admission: verified on both engines. Concurrent same ID/payload creates one identity; distinct admissions allocate contiguous unique sequence values; payload changes conflict. Scope, NPC and epoch rejection does not allocate work. Failed admission rolls back sequence allocation; lost commit acknowledgement resolves through exact identity lookup.
- Ordered claims and fence/CAS: verified on both engines. Eight competing claimers produce one lease for the earliest nonterminal turn; busy work never permits skipping it. Replacement advances the durable fence and preserves phase. All write methods compare exact turn/key/sequence, active epoch, earliest position, current fence and lease expiry while holding the common writer boundary. Different NPCs can retain simultaneous leases. SQLite uses `lock_player`'s no-op writer UPDATE before any state read, rather than relying on `FOR UPDATE`.
- Durable provider/repair budgets: verified on both engines. Each purpose is consumed once; repair kinds share one token; three distinct stage calls are the maximum. Exact attempt identity replay does not consume another call. Dispatch without output survives fresh adapter/engine recovery and replacement fence. Rollback and lost budget commit acknowledgements cannot reset consumption. Outputs remain immutable and retain historical fences; old workers cannot persist output or assembly.
- Restart recovery: verified on both engines. Pending scans are scoped/ordered/read-only; submitted payload, preparing/proposed/operation_resolved/finalizing phases, outputs and assembly recover. Receipt/status lookup is exact scoped identity and performs no operation. Final result reads preserve exact Unicode text. Invalidated tombstones expose no recovery payload; active-scope changes reject old recovery. Corrupt receipt payload identity fails closed with `INTERNAL_FAILURE`, never successful absence.
- Transaction boundary: real connection checkout/checkin instrumentation confirms admission, claim, budget commit and read methods release connections before returning; provider dispatch occurs after these calls. This adapter has no provider/embedding/semantic dependency.
- Adjacent integration: 65 frozen store/turn/schema checks and final 876-test backend suite pass. All required T02 SQLite/PostgreSQL checks ran without skips.
- Proposed status update: accept persistence-adapters/T02 after Main Agent diff/evidence review and independent reproduction. Leave T03/T04 and packet/module completion open.

## Risks

- T03 receipt/effect transactions and T04 atomic publication/lifecycle remain separate deliverables. Their writers must follow the same player -> stream -> turn ordering and recheck the current fence/position under that lock.
- The existing turn JSON payload now has documented keys `submission`, `attempts`, `assembled_reply`, and `final_result`. T04 must erase the whole payload on clear/reset, preserve digest/identity tombstones and receipt rows, and write `final_result` atomically with final publication. This task tests seeded final/invalidated/operation-resolved rows; it does not claim those transactions are implemented here.
- Lease timestamps use UTC, persisted as naive UTC for the accepted schema. Production worker clocks must be consistent. Attempt output/assembly recovery preserves original fences and grants no publication authority.
- Infrastructure write failures during commit conservatively return `COMMIT_UNCERTAIN`; callers must resolve durable state before deciding whether to dispatch. A replayed attempt identity is not permission to call the provider again.
- No remaining T02 correctness blocker identified. Main Agent concurrency review is still required.

## Follow-up tasks

- persistence-adapters/T03 — compose operation receipt/effect transactions with the same writer/fence/position boundary; recover receipts before execution.
- persistence-adapters/T04 — consume the documented JSON recovery layout; implement atomic final result, lifecycle erasure and scoped readers.
- game-adapters/T03 and persistence-adapters/T05 — retain their separate shared-resource revision integration ownership; no T02 schema dependency was added.

## Main Agent acceptance addendum

Date: 2026-10-18 (Asia/Kolkata). Main Agent reviewed the final adapter and receipt-scope guard, then independently reproduced:

- Focused SQLite SQLTurnStore suite: 23/23 passed.
- Focused PostgreSQL 16.15 SQLTurnStore suite on disposable `npc_test_resource_revisions_t05`: 23/23 passed.
- Full backend discovery: 876/876 passed.

The initially reported concurrent receipt-scope assertion was the T02 red-phase test while its guard was being implemented; the final test now asserts typed `INTERNAL_FAILURE`, and the final SQLite/PostgreSQL/full-suite runs pass. T02 is accepted locally. T03/T04 remain open.
