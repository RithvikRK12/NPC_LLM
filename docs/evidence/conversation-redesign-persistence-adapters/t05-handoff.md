# persistence-adapters/T05 handoff

Date: 2026-10-18. Owner: persistence_t05 / gpt-6.1-sol / high.
Status: ready for Main Agent review. No commits or tracker/packet edits.

## Scope and changes

- `backend/app/models/player.py`: additive nonnullable JSON `resource_revisions`, independent ORM `dict` default and database `{}` default. This ledger belongs to the active `game_scope`; it contains storage only.
- `backend/app/database/resource_revision_migration.py`: additive/idempotent upgrade; legacy rows obtain `{}` without rewriting existing columns or existing counters.
- `backend/app/database/init_db.py`: one import and one migration invocation; preserved the preexisting T01 conversation migration wiring and other dirty work.
- `backend/tests/test_resource_revision_storage.py`: five shared SQLite/PostgreSQL acceptance tests covering fresh model/schema/migration, populated legacy data preservation, defaults for subsequent raw inserts, repeatability with nonempty counters, caller-owned rollback, and actual initialization wiring.
- This handoff and `t05-*.log` evidence files are the only documentation additions.

Sources read: T05 packet, redesign prompt, master shared rules, detailed design §§5, 6.4, 6.6–6.7, 9–10; existing Player, initialization/migrations, reset and schema tests. Main Agent clarified reset ownership during implementation: T05 does not modify `reset_world`; T03 owns clearing when scope rotates, resource keys and all revision writes.

## Verification

Working directory for every command: `/Users/rukithnayak/Documents/NPC_LLM-1`.

SQLite uses isolated in-memory databases. PostgreSQL uses PostgreSQL 16.15 at `127.0.0.1:5433`, disposable database `npc_test_resource_revisions_t05`, supplied through `CONVERSATION_TEST_DATABASE_URL`. Tests reject database names outside `npc_test_*`. This dedicated database remains available for review; test setup drops its tables. Administrative access to `mvp` was used only to read server version and create this isolated database; no player save was read or modified. Sandbox TCP access returned Operation not permitted; the PostgreSQL checks succeeded with elevated execution.

1. Test-first red command: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_resource_revision_storage.py' -v`. Run once with no database URL and once with the isolated PostgreSQL URL. Both exit 1: five tests, one failure/four errors because the ledger/migration were absent. An earlier fixture SQL-bind typo was corrected before these captured red runs. Logs: `t05-sqlite-red.log`, `t05-postgres-red.log`.
2. Same focused command after implementation, SQLite and PostgreSQL: both exit 0, 5/5 pass, no skips. Logs: `t05-sqlite-green.log`, `t05-postgres-green.log`. Final focused cases, including an added explicit fresh-migration invocation, were rerun within the adjacent commands below.
3. Final SQLite adjacent command: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_resource_revision_storage test_conversation_persistence_schema test_inventory_migration test_semantic_memory test_opening test_world_inventory test_world_eligibility -v`. Exit 0; 77/77 pass, no skips. Log: `t05-sqlite-adjacent.log`.
4. Final PostgreSQL command with `CONVERSATION_TEST_DATABASE_URL` set to the disposable database: `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_resource_revision_storage test_conversation_persistence_schema -v`. Exit 0; 9/9 pass, no skips. Log: `t05-postgres-adjacent.log`.
5. Latest broad command: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_*.py'`. Exit 1; 876 run, 875 pass, one failure, no skips. Failure: `test_conversation_persistence.SQLTurnStoreTests.test_receipt_payload_cannot_escape_exact_turn_scope`, line 403, expected `ValueError` was not raised. This is in active T02-owned files; Main Agent was notified and those files were not edited. An immediately preceding broad run passed 875/875 before the concurrent new T02 test appeared. Final broad log: `t05-backend.log`. Existing datetime deprecation warnings and expected failure-path diagnostic messages also appear.
6. `git diff --check`: exit 0.

## Acceptance and handoff

The fresh/populated ledger, additive migration, preservation, defaults, portability, idempotence and initialization criteria pass on both engines. Revision edits roll back together with inventory in the caller's transaction; the model has no commit/authority behavior. T05 is ready for review; propose accepting its bounded deliverable after Main Agent reproduction. No packet/master status was changed.

T03 must replace the JSON map on writes (plain SQLAlchemy JSON does not track in-place dict changes), increment under the existing player lock, and clear it in the same transaction as scope rotation. Monotonicity/key semantics are deliberately not implemented here. No additional prerequisite identified. Full integration remains red on the reported concurrent T02 receipt-scope test.

## Main Agent acceptance addendum

Date: 2026-10-18 (Asia/Kolkata). Main Agent reviewed the additive Player field, migration and tests, then independently reproduced:

- Focused SQLite revision-storage suite: 5/5 passed.
- PostgreSQL 16.15 revision-storage plus T01 schema suite on disposable `npc_test_resource_revisions_t05`: 9/9 passed.
- Adjacent SQLite migration/game regressions: 77/77 passed.
- Full backend discovery: 876/876 passed.

T05 is accepted locally. Resource key semantics, increments, coherent snapshots and clearing on scope rotation remain game-adapters/T03.
