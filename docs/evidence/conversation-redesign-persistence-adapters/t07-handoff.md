# persistence-adapters/T07 handoff

Date: 2026-10-18 (Asia/Kolkata)
Owner: Main Agent

## Recorded acceptance gap

Finalization/T02 integration first reproduced four failures: relevant `EVIDENCE_CHANGED` errors were marked nonretryable; a bounded refresh replacement could not be committed or recovered; a stale pre-operation plan could not reach refresh; and an interaction fulfilled by the atomic operation commit could be reactivated by finalization with a matching revision.

## Changes

- `SQLTurnStore._error` now marks relevant evidence changes retryable, allowing `Finalizer` to invoke refresh only after the SQL transaction closes.
- `SQLTurnStore.commit` accepts a replacement reply only after validating its turn/fence, continuity plan, current evidence and revisions. On successful publication, it persists the accepted reply beside the durable final result for recovery/replay.
- Publication reloads scoped interaction rows under lock and validates current plan state. Terminal interactions (`fulfilled`, `cancelled`, `expired`) cannot be replaced, including a replacement whose expected revision matches the committed terminal head.

No game or product behavior was expanded. The `finalization/T02` integration tests supplied the failing behavior and both database acceptance gates.

## Test-first and verification evidence

- Before the adapter fix, `test_conversation_finalization.py` failed on four cases. See the corrected SQLite [RED log](../conversation-redesign-finalization/t02-logs/sqlite-red.log) and PostgreSQL [RED log](../conversation-redesign-finalization/t02-logs/postgresql-red.log).
- Finalization SQL integration: SQLite 22/22 pass; [log](t07-logs/sqlite-green.log).
- PostgreSQL 16.15 finalization SQL integration: 22/22 pass on `npc_test_finalization_t02_0c21264a99e9`; runner dropped the disposable database; [log](t07-logs/postgresql-green.log).
- Adjacent finalization and lifecycle suite: 36/36 pass; [log](t07-logs/adjacent-green.log).
- Full backend suite: 975/975 pass; [log](t07-logs/backend-green.log).
- `git diff --check`: exit 0.

## Limitations

The SQL store cannot independently verify that an external refresh callback used a provider; architecture confines that callback to `Finalizer` outside storage calls. Context precondition projection and overall coordinator wiring remain separate tasks. This task closes the persistence publication behaviors required by finalization/T02 only.
