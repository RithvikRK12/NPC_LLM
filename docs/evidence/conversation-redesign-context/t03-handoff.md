# context/T03 handoff — locally accepted

## Scope and files changed

- `backend/app/services/conversation/adapters/context_read.py` — concrete `SQLContextReadAdapter` verifies active literal scope, NPC, epoch, and current turn identity; reads current input, finalized prior history, authored NPC profile, active narrative canon, supported scoped memories/reports, current summaries, active/suspended interactions, authoritative game facts and capabilities, and revision labels. All values returned are detached contracts.
- `backend/tests/test_conversation_context_adapter.py` — SQLite/PostgreSQL integration fixtures prove exact `/world` handling, scope/NPC/epoch filters, finalized-only history, profile/canon/summary/report/interaction/fact/capability composition, provenance ID binding, rejection of unknown legacy text IDs, and connection release before optional ranking.
- `docs/evidence/conversation-redesign-context/run_t03_postgres_acceptance.py` — creates a uniquely named disposable PostgreSQL database, runs context and scoped-read tests, and drops the database in `finally`.
- `docs/redesign-tasks/context.md`, `docs/redesign-master-progress.md`, task graph, and `contracts/T08` records updated by the Main Agent.

## Verification

- Initial RED exposed a prerequisite contract conflict: `/world` failed `ConversationKey` validation because game scopes reused the generic `Identifier` pattern. Recorded and completed as contracts/T08 before proceeding.
- Focused SQLite command: `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_game_scope backend.tests.test_conversation_context_adapter backend.tests.test_conversation_context backend.tests.test_conversation_scoped_reads backend.tests.test_conversation_summary_store -v` — exit 0, 28 tests passed, 0 failures/skips. [Log](t03-sqlite.log).
- PostgreSQL 16.15: `CONVERSATION_TEST_ADMIN_URL=... PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-context/run_t03_postgres_acceptance.py` — exit 0, 4 tests passed, 0 failures/skips; disposable database `npc_test_context_t03_b333b1daadb3` dropped. [Log](t03-postgresql.log).
- Conversation test suite: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` — exit 0, 497 passed, 0 failures/skips.
- Full backend suite: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — exit 0, 965 passed, 0 failures/skips. [Log](t03-backend-suite.log).
- `git diff --check` — exit 0.

## Acceptance review

- Literal scope, exact NPC/epoch, current-turn identity and finalized prior-turn boundaries: verified on SQLite and PostgreSQL. `/world` and `world` remain distinct.
- Draft, corrupt, cross-scope, cross-NPC, cross-epoch and unproven legacy history: excluded; only the persistence `read_prior_turns` adapter provides history.
- Player-text IDs: current and historical player strings use the exact deterministic `turn:<sequence>` values used by persisted producers and summaries. Reports with an unknown source ID are omitted.
- Optional ranking: `ContextAssembler` invokes it only after `SQLContextReadAdapter.read_context` returns; pool checkout/checkin assertion observes zero checked-out connections.
- Packet composition: integration fixture covers profile, active canon, persisted summary, attributed report, interaction, game facts and capabilities. Malformed/unavailable stored evidence fails closed by omission or a typed storage/schema error.

## Limitations and follow-up

- `interaction_preconditions` stays empty because no current server-evaluated precondition reader exists at this boundary; omitted status is explicitly unavailable and cannot authorize consent or resume.
- Evidence projection timestamps use adapter read time because the durable canon and contract-memory records do not retain creation timestamps. No age-based policy uses these projected timestamps.
- The concrete reader is not yet wired into a production coordinator/pipeline; that integration remains a downstream task.
- Next recommended task: `coordinator/T01`, the pure orchestration path over the accepted detached ports and policies. Keep API/client adoption behind the existing receipt and lifecycle gates.
