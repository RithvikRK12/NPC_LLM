# finalization/T02 handoff

Task: `finalization/T02` — durable atomic publication through the existing `Finalizer` and SQL store. Owner: `finalization_t02`. Model/reasoning: `gpt-6.1-sol` / high. Date: 2026-10-18.

**Status: accepted by Main Agent 2026-10-18 after persistence-adapters/T07 GREEN verification.** The worker's initial RED results below are retained as the pre-fix evidence; post-fix results are recorded at the end of this handoff.

## Changes

- `backend/tests/test_conversation_finalization.py`: six new integration tests exercising the real `Finalizer` with `SQLTurnStore`, real game-operation/consent fulfillment, writer transactions, and the existing isolated SQL fixtures. Existing 16 facade tests are preserved.
- `docs/evidence/conversation-redesign-finalization/run_t02_postgres_acceptance.py`: guarded PostgreSQL runner requiring the designated localhost service and `postgres` maintenance database; creates a uniquely named `npc_test_finalization_t02_*` database, installs vector there, runs the focused tests, and drops it in `finally`.
- This handoff and `t02-logs/` record commands/results. `finalization.py` and persistence adapter production files were not modified: observed defects require adapter-owned changes.

## Acceptance evidence

| Expectation | Observed result |
| --- | --- |
| One publication transaction commits transcript, exact text/beats, canon, memory, interaction, terminal result | PASS on SQLite and PostgreSQL: Unicode, combining accent, newline and trailing space preserved; canon/memory/interaction and final result durable together |
| Inject failure after transcript write and before canon write | PASS on both: SQLAlchemy canon `before_insert` event verifies transcript visible inside that transaction, then raises `OperationalError`; transcript/canon/memory/interaction/final result and summary dirty flag all roll back; saved assembly remains recoverable in `finalizing`; clean retry succeeds |
| Exact delivery replay after restart | PASS on both: new SQL store, expired lease, changed resource revisions and different valid caller speech return byte-identical serialized durable result; single transcript/canon/memory rows remain |
| Stale preoperation plan cannot reactivate fulfilled negotiation | Stale revision is rejected, but conflict is nonretryable, so Finalizer cannot refresh the plan and publish receipt-grounded speech; FAIL |
| Fulfilled interaction cannot be reactivated even with matching revision | FAIL on both: real `execute_once` transfers wood, commits receipt and fulfillment at revision 2; a replacement expecting revision 2 reactivates it and incorrectly finalizes |
| Refresh after evidence changes outside SQL transaction | FAIL: nonretryable conflict prevents refresh hook from running. Hook contains pool checkout assertion and replacement evidence/assembly checks for the corrected path |
| Persistent evidence churn returns recoverable conflict without false finalization | FAIL: `EVIDENCE_CHANGED` is returned with `retryable=False`. Test requires two bounded refreshes and no transcript/continuity/result writes |

The six new cases catch lost publication writes, partial publication, replay regeneration or normalization, operation reexecution, terminal negotiation resurrection, callbacks under active SQL transaction, and false finalization during relevant churn. The game operation itself is real; a test-only `execute_once` patch raises if publication attempts to execute it again. All provider work is simulated by a synchronous refresh callback, with no live provider use.

## Required persistence follow-up: persistence-adapters/T07

1. `SQLTurnStore._error` currently excludes `EVIDENCE_CHANGED` from retryable codes. `Finalizer.commit` correctly respects nonretryable errors, so relevant SQL changes never reach its bounded refresh path. Preserve identity/ownership/storage recovery behavior while making publication evidence conflicts recoverable.
2. `SQLTurnStore.commit` requires incoming `reply` to equal previously persisted assembly before its evidence checks. After conflict classification is fixed, the refreshed accepted reply currently appears destined for `IDEMPOTENCY_CONFLICT`. T07 must reconcile refresh with durable assembly while preserving fence/recovery semantics; the integration test requires recovery to contain the published replacement. This second obstruction is identified by source inspection and remains masked in the current runtime RED by item 1.
3. Interaction publication currently checks stored payload revision only. It must reread/validate committed terminal status, preserving operation-fulfilled negotiations even for a supplied replacement with a matching expected revision. The actual real-operation resurrection is reproduced by a RED test. Contract `InteractionPlan.validate_current` alone also does not prohibit terminal-to-active replacement, so invoking it alone will not resolve this case.

Main Agent expanded T07 to cover publication refresh and conflict classification. Re-run these six SQL integration cases on both databases after T07, then run the complete focused/adjacent/backend suites before considering T02 accepted. No production fix or GREEN claim is made here.

## Exact verification commands and results

All commands ran from `/Users/rukithnayak/Documents/NPC_LLM-1`.

1. `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_finalization.py' -v > docs/evidence/conversation-redesign-finalization/t02-logs/sqlite-red.log 2>&1`

   Exit **1**; **22 tests, 18 pass, 4 failures, 0 errors/skips**. [SQLite RED log](t02-logs/sqlite-red.log).

2. `CONVERSATION_TEST_ADMIN_URL='postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/postgres' PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-finalization/run_t02_postgres_acceptance.py > docs/evidence/conversation-redesign-finalization/t02-logs/postgresql-red.log 2>&1`

   Initial sandbox TCP access returned `Operation not permitted`; the same command succeeded in reaching PostgreSQL with approved escalation. Test exit **1**; PostgreSQL **16.15**, disposable database **npc_test_finalization_t02_21360b98e6c1**, **22 tests, 18 pass, same 4 failures, 0 errors/skips**. Runner confirmed database dropped. Only `postgres` maintenance and the newly created disposable test database were accessed; no player database/save was used. [PostgreSQL RED log](t02-logs/postgresql-red.log).

3. `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest test_conversation_persistence_lifecycle test_conversation_contracts_interfaces test_conversation_canon test_conversation_interactions test_conversation_store_ports test_conversation_memory -v > docs/evidence/conversation-redesign-finalization/t02-logs/adjacent.log 2>&1`

   Exit **0**; **126 tests pass, 0 failures/errors/skips**. [Adjacent log](t02-logs/adjacent.log).

4. `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v > docs/evidence/conversation-redesign-finalization/t02-logs/backend.log 2>&1`

   Exit **1**; **975 tests, 971 pass, 4 failures, 0 errors/skips**. These are exactly the same four new focused failures, listed below; no additional backend failures. [Backend log](t02-logs/backend.log).

5. `git diff --check` — exit **0**.

Failing names in SQLite, PostgreSQL and full backend runs:

- `DurableFinalizationTests.test_persistent_sql_evidence_churn_never_publishes_or_marks_terminal`
- `DurableFinalizationTests.test_refresh_replacement_publishes_after_sql_transaction_is_released`
- `OperationFulfilledFinalizationTests.test_matching_revision_cannot_reactivate_a_terminal_negotiation`
- `OperationFulfilledFinalizationTests.test_stale_preoperation_plan_cannot_reactivate_committed_negotiation`

`initial-red.log` records an earlier development run before correcting the test receipt source revision from zero to its durable argument digest. It is retained for transparency; `sqlite-red.log` is the authoritative fixture-corrected RED. Existing datetime `utcnow()` deprecation warnings appear in SQLite/backend logs.

## Proposed ledger update for Main Agent

Keep T02 unchecked/incomplete. Record six new real SQL cases, atomic rollback/exact replay passing on both databases, four reproduced integration failures, and follow-up `persistence-adapters/T07`. Acceptance of previously completed T01/T04 is not changed by this handoff; T02 durable integration remains open. Main Agent owns task packet/master ledger edits.

## Post-fix GREEN verification

Persistence-adapters/T07 updated the SQL store to return retryable relevant evidence conflicts, accept and persist the refreshed validated reply with its continuity plan, and reject transitions that would replace terminal interactions. The finalization facade itself required no production change.

- SQLite finalization integration: 22/22 pass; [log](../conversation-redesign-persistence-adapters/t07-logs/sqlite-green.log).
- PostgreSQL 16.15 finalization integration: 22/22 pass; disposable database dropped; [log](../conversation-redesign-persistence-adapters/t07-logs/postgresql-green.log).
- Adjacent finalization and persistence-lifecycle tests: 36/36 pass; [log](../conversation-redesign-persistence-adapters/t07-logs/adjacent-green.log).
- Full backend suite: 975/975 pass; [log](../conversation-redesign-persistence-adapters/t07-logs/backend-green.log).
- `git diff --check`: exit 0.

All six SQL integration tests that initially exposed the retryability, replacement-reply and fulfilled-interaction failures pass after T07 on both databases. Atomic rollback and exact replay continue to pass. T02 is locally accepted; coordinator wiring and module-level integration remain downstream.
