# ports/T02 implementation handoff

Date: 2026-10-14. Owner: ports_t02. **Bounded implementation is ready for independent review; the main agent owns task/master/graph acceptance.**

## Delivered

Appended the five write/recovery protocols to `backend/app/services/conversation/ports.py`, using frozen contracts/T01–T04 and standard-library typing only. All seven accepted ports/T01 declarations remain unchanged.

| Protocol | Methods / transaction contract |
| --- | --- |
| `TurnStore` | `submit`, `lookup`, `claim_next`, `pending`, `recover`, `record_attempt`, `save_attempt_output`, `save_reply`. Scoped admission uniquely binds request ID/payload and allocates sequence before scheduling. Claims only the earliest nonterminal turn and return `OptionalResult[TurnLease]`; empty/busy is explicit successful absence. All writes check active key/fence/position. Dispatch recording consumes one durable purpose before a provider call, with a single shared repair purpose for `proposal_format` and `final_response`. Output/assembly remains recoverable draft data, isolated from accepted history. |
| `OperationGateway` | `execute_once(turn, fence, decision: ReadyToRecheck)` and `lookup_receipt(turn)`. Writer transaction checks scope/epoch/fence/position, recovers existing receipt before considering execution, rechecks deterministic authority/terms/consent, then atomically commits effect/receipt/resolved phase. Receipt lookup is read-only and exact to the scoped turn. |
| `FinalizationStore` | `commit(turn, fence, reply, continuity_plan)`. Atomically publishes transcript, accepted continuity, immutable final result and terminal status after checking active key/fence/position, actual canon/memory/interaction CAS heads and relevant speech dependencies. It cannot overwrite an operation-committed interaction transition. |
| `LifecycleStore` | `clear(key)` and `new_game(expected_scope)`. Serialized CAS lifecycle operations. Clear advances epoch and deletes conversational payloads/results/drafts/attempts/summaries/reports/interpretations/negotiations while retaining minimal identity/digest/status tombstones, canon origin metadata, authored identity and accepted mechanics/receipts. Reset changes the opaque scope and prevents new-run access to historical receipts. |
| `SummaryStore` | `dirty_keys`, `read_sources`, `lookup_summary`, `publish(summary, expected_revision)`. Durable refresh discovery and scoped finalized source reads, outside mandatory generation. Publication CAS-checks the summary head, active key and source/correction revisions; stale/failed refresh cannot replace the prior record. |

Expected nonoptional results use the design §4 `T | ConversationError` convention. Claims and optional receipt/summary lookups use frozen `OptionalResult[T]`, distinguishing successful `None` from failure. A pending queue read returns an explicit tuple (including an empty tuple), not ambiguous absence.

The missing interface values discovered at initial T02 review are now resolved by the independently reviewed contracts/T04 expansion. No port-local replacement envelopes, ORM sessions, database/provider/framework imports or new shared contract edits were introduced by this worker.

## Reusable conformance and bounded fake

- `backend/tests/conversation_store_conformance.py`: reusable admission, claim, operation, publication, lifecycle/summary and provider-attempt case mixins. Concrete adapter suites can reuse the same expectations with their own clock, fault and audit harness.
- `backend/tests/conversation_store_fakes.py`: test-only in-memory implementation of the five protocols. It stages scripted typed receipts/final results and applies uniqueness, ordering, fence, revision and invalidation expectations. `scenario_*` controls seed detached outcomes, advance time, inject faults and expose test observations; they are not production APIs.
- `backend/tests/test_conversation_store_ports.py`: runs the reusable cases and checks the exact frozen signature types and all five runtime protocol shapes.

Coverage pins same-ID replay/payload conflict; unique per-key sequences; scoped read-only lookup; oldest-only per-NPC claims and independent NPC streams; lease replacement fences; receipt-first recovery across fake adapter restart; stale-write rejection; effect/receipt/phase rollback; transcript/continuity/status rollback; relevant revision recheck with unrelated churn permitted; canon creation CAS collision; preservation of operation-fulfilled interaction status; exact final retry and release of the next queued turn; clear/reset invalidation and receipt/canon lifetime; summary head/source revision CAS; durable dirty-key discovery; consumed provider stages surviving missing output/replacement/restart; the shared repair token; immutable recorded output; historical assembly/attempt fences; and erasure of recovery payloads on clear.

`recover` reads a previously claimed turn; admission recovery discovers unclaimed work via `pending` then claims it, because frozen `TurnRecovery` requires a positive current fence. A recovery observation grants no execution/publication authority.

## Test-first and final verification

All commands ran from the repository root. Evidence logs contain complete output, including expected-red assertions. Expected-red runs contain no import/collection errors. During implementation a summary-source fixture mapping exposed the frozen `VisibleTurn` text wrappers; the fake was corrected to return `TextValue` player/final text values before green verification.

| Check | Exact command | Exit | Result / log |
| --- | --- | ---: | --- |
| Initial expected red | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_store_ports.py'` | 1 | 12 expected missing-boundary/fake assertions; `t02-red.log` |
| Dependent-interface expected red | Same focused command after adding claim/publication/lifecycle/summary cases | 1 | 26 tests, 30 expected missing-method/interface assertions; `t02-dependent-red.log` |
| Dependent-interface green | Same focused command | 0 | 26/26; `t02-dependent-green.log` |
| Attempt/recovery expected red | Same focused command after adding attempt cases | 1 | 32 tests, 29 expected missing-attempt-method assertions; `t02-attempt-red.log` |
| Attempt/recovery green | Same focused command | 0 | 32/32; `t02-attempt-green.log` |
| Final focused | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_store_ports.py'` | 0 | 32/32; `t02-green.log` |
| Full conversation | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 0 | 91/91; `t02-conversation.log` |
| Frozen conversation contract dependencies | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py'` | 0 | 59/59; `t02-contracts.log` |
| Existing read ports | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_read_ports.py'` | 0 | 12/12; `t02-read-ports.log` |
| Frozen T01 port conformance / import hygiene | `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest conversation_port_conformance` | 0 | 4/4; `t02-t01-conformance.log` |
| Existing contract dependency | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py'` | 0 | 13/13; `t02-dependency-contracts.log` |
| Full backend | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | 0 | 554/554; `t02-backend-suite-final.log` |
| Diff and owned-file whitespace | `git diff --check` plus a Python check of every owned source/test line against `line.rstrip()` | 0 | `t02-diff-check.log` |

The full backend log includes existing Starlette/HTTPX and naive-UTC deprecation warnings and scripted rejection/retrieval-fallback diagnostics. It reports no failures or skips.

Historical snapshot: the first broad run occurred during contracts/T04's concurrent red phase and exited 1 (531 tests, 41 errors), recorded in `t02-backend-suite.log`. All errors belonged to `test_conversation_contracts_interfaces.ConversationInterfaceContractTests` before its implementations were added: `test_all_interface_values_roundtrip_and_reject_extra_fields`, `test_continuity_rechecks_only_dependencies_and_exact_final_spans`, `test_interaction_plan_cannot_overwrite_a_committed_transition`, `test_lease_rejects_replaced_fence_expiry_and_wrong_stream_position`, `test_memory_corrections_require_link_and_expected_head`, `test_nested_data_is_detached_and_immutable`, `test_optional_success_none_is_distinct_from_failure_and_missing_branch`, `test_rejected_shared_fixtures`, and `test_summary_rechecks_epoch_correction_revisions_and_source_range`. The final 554/554 run supersedes that transient snapshot.

## Explicit limits

The protocol declarations specify atomic transaction responsibility; they do not implement persistence. Pure fake rollback cases prove only the fake's staged observable behavior and the reusable expectation. They **cannot prove SQL atomicity, SQLite `lock_player`/ignored `FOR UPDATE` behavior, PostgreSQL isolation/row locking, concurrent worker races, real crash durability, or lost commit acknowledgement**. Sharing recorded fake state with a new adapter object is a recovery fixture, not process/disk durability.

Receipts, publication metadata and authoritative revision snapshots are deliberately scripted/injected in the fake. The fake does not implement or prove existing game rules, role/ownership/consent authority, semantic canon admission, provider behavior, the complete authored-identity/relationship/encounter deletion matrix, or a concrete summary scheduler. Canon fake storage exercises head CAS; complete durable revision-history storage remains an adapter responsibility. Clear/reset protocol documentation preserves those responsibilities without claiming a real adapter or application integration exists.

No provider calls or player database are used by the focused/conversation port conformance. The broad backend command runs the existing isolated regression suite; it does not add T02 SQL adapters or satisfy future persistence acceptance. Both isolated SQLite and PostgreSQL adapter conformance, including race/atomicity/lifecycle tests, remain mandatory integration gates. No task/master/graph ledger was edited by this worker.
