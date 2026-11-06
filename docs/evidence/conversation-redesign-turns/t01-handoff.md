# turns/T01 handoff

## Task

- ID: `turns/T01` — submission and retry lookup only.
- Owner / assigned model / reasoning effort: `turns_t01` / `gpt-6.1-sol` / high.
- Status: ready for Main Agent review; packet/master status was not edited.
- Date: 2026-10-15 (Asia/Kolkata).
- Scope: `TurnService.submit` and `lookup`, focused tests, this evidence. Claims,
  leases, recovery, provider dispatch and coordinator wiring remain outside T01.
- Dependencies: accepted contracts/T01–T04 and ports/T01–T02, including the
  frozen `TurnStore` admission/lookup contract and bounded reference fake.

Frozen dependency SHA-256 values at verification:

| File | SHA-256 |
| --- | --- |
| `backend/app/services/conversation/contracts.py` | `4c0a07321d530d68d90dcef4408096b7ef4e1a30c999d615a89c294207a04762` |
| `backend/app/services/conversation/ports.py` | `e7a532ec5007a2e4b5c69ab6f88650068426f4715777bb9ea5d466e75671b96d` |
| `backend/tests/conversation_store_fakes.py` | `c585bfad46cb9edc258e87b9048743166a02e9a7c80fbfe61ac1bcbfa6334c82` |
| `backend/tests/conversation_store_conformance.py` | `ca49d0b66d162a36d1e439432b66a3c7aa6cb38b999e74b110394daafe768527` |

## Files changed

- `backend/app/services/conversation/turns.py` — injected `TurnStore` facade
  for atomic admission and read-only retry resolution.
- `backend/tests/test_conversation_turns.py` — eleven behavioral tests using
  the frozen repository and an observing admission/lookup wrapper. The wrapper
  injects typed storage failures before or after fake admission.
- `docs/evidence/conversation-redesign-turns/t01-handoff.md` — durable handoff
  and command/output evidence.
- No shared contract, port, fake, package initializer, task packet or master
  progress edits were made.

## Boundary decision

`TurnSubmission` and `ConversationKey` are already validated immutable values.
The accepted `TurnStore.submit` contract owns active scope/NPC/epoch checks,
payload deduplication, sequence allocation and durable enqueue in one atomic
operation. The service delegates that operation once. It does not introduce a
separate scope read, payload cache, queue, scheduling call or process mutex.
This boundary was confirmed with the Main Agent before implementation.

The service returns `TurnStatus | ConversationError`, matching the frozen port
and detailed-design §4's definition of `Result[T]` as that union. Typed adapter
errors and known turn references pass through. Unexpected exception mapping
remains the infrastructure adapter's responsibility. `lookup` invokes only
`store.lookup` once; it never admits or processes work. The existing contract's
500-character message bound is preserved without a new service policy.

## Tests run

Python: repository `.venv`, Python 3.12.14. Fixtures: frozen in-memory
`FakeConversationRepository`, scope `run:1`, NPCs 1/2, epoch 0 (epoch 1 after
clear). No live provider or player database was needed by the focused cases.

Root cwd: `/Users/rukithnayak/Documents/NPC_LLM-1`.

| Check | Exact command (from root unless stated) | Exit | Pass / fail / error / skip | Full local log |
| --- | --- | --- | --- | --- |
| RED, before implementation | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_turns.py' > /private/tmp/conversation-turns-t01-red.log 2>&1` | 1 | 0 / 11 / 0 / 0 | `/private/tmp/conversation-turns-t01-red.log` |
| GREEN, focused | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_turns.py' > /private/tmp/conversation-turns-t01-green.log 2>&1` | 0 | 11 / 0 / 0 / 0 | `/private/tmp/conversation-turns-t01-green.log` |
| Adjacent frozen write/store conformance | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_store_ports.py' > /private/tmp/conversation-turns-t01-store-ports.log 2>&1` | 0 | 32 / 0 / 0 / 0 | `/private/tmp/conversation-turns-t01-store-ports.log` |
| Conversation regression suite | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' > /private/tmp/conversation-turns-t01-conversation.log 2>&1` | 0 | 163 / 0 / 0 / 0 | `/private/tmp/conversation-turns-t01-conversation.log` |
| Documented backend suite, cwd `/Users/rukithnayak/Documents/NPC_LLM-1/backend` | `PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -v > /private/tmp/conversation-turns-t01-backend.log 2>&1` | 0 | 626 / 0 / 0 / 0 | `/private/tmp/conversation-turns-t01-backend.log` |

The logs above are local temporary files. The relevant output is preserved
below so this handoff remains evidence if temporary files are removed.

RED: the tests were written first, and the absent module was handled by the
test harness so each case reported the missing feature as an assertion failure:

```text
AssertionError: unexpectedly None : T01 TurnService is not implemented
Ran 11 tests in 0.000s
FAILED (failures=11)
```

Fresh post-implementation summaries, in table order after RED:

```text
Ran 11 tests in 0.001s
OK

Ran 32 tests in 0.005s
OK

Ran 163 tests in 0.242s
OK

Ran 626 tests in 5.636s
OK
```

## Acceptance evidence

| Criterion | Outcome / test evidence |
| --- | --- |
| Validate scope/epoch through the atomic port | Verified typed `STALE_SCOPE`, `STALE_EPOCH` and `UNKNOWN_NPC` rejections, with no sequence consumed: `test_store_rejects_stale_scope_epoch_and_unknown_npc_before_admission`. Exactly one admission call per request; no separate active-scope read. |
| Same key/request/payload returns existing status/ref | Verified serialized-value replay returns the original queued status, leaves one pending entry and allocates the next new request sequence 2: `test_same_payload_replays_the_original_status_without_allocating_sequence`. Final and invalidated replays are also covered. |
| Changed payload conflicts | Verified whitespace-changing payload returns `IDEMPOTENCY_CONFLICT`, the original turn ref, and preserves original status/queue: `test_changed_payload_conflicts_without_replacing_the_original`. |
| Store allocates and queues sequence | Verified shared store sequence 1/2/3 across two services and fake restart: `test_separate_services_use_store_owned_sequence_after_restart`. Per-NPC identities independently start at sequence 1: `test_same_request_id_is_independent_for_each_npc_stream`. This is sequential fake evidence only. |
| Lookup returns pending/final/invalidated without generation or mutation | Each phase asserts exactly one `lookup` call. Pending lookup preserves queue/effect count. Final lookup returns the exact complete persisted response/beats and preserves transcript. Clear lookup exposes no response or recoverable payload. Tests: `test_pending_lookup_calls_only_lookup_once_and_preserves_queue`, `test_final_lookup_and_resubmission_return_exact_durable_response`, `test_clear_lookup_and_same_payload_replay_return_erased_tombstone`. The observing wrapper supplies only submission/lookup methods. |
| Missing/scoped lookup never creates a turn | Verified typed missing/stale errors, one lookup call each, empty queue and next sequence 1: `test_missing_lookup_does_not_admit_and_rejects_other_scopes`. |
| Admission/enqueue failure remains typed/recoverable | Before admission, `STORAGE_UNAVAILABLE` has no turn, no queue entry and same-ID retry can admit sequence 1. After fake admission, the typed error retains the turn, service makes no automatic retry, and lookup finds one queued nonfinal turn. Tests: `test_failure_before_admission_stays_typed_and_same_id_can_be_retried`, `test_failure_after_admission_is_not_retried_or_finalized_and_lookup_is_pending`. |
| Adjacent conformance/regression | All 32 frozen write/store cases and all 163 conversation cases passed, including lifecycle tombstone/identity and scoped admission conformance. Full documented backend suite passed 626 tests. |

## Risks and limitations

- No T01 implementation blocker identified.
- The service intentionally relies on the accepted atomic store contract.
  Fake sequencing, shared-state restart and scripted fault injection do not
  prove database concurrency, durable transactions, actual lost acknowledgments
  or writer ordering. SQLite/PostgreSQL atomic admission and clear/reset races
  remain persistence-adapter gates; these checks were not run for this pure
  service task.
- The reference fake preserves invalidated identities before stale-key
  rejection. Delegation preserves that required tombstone retry behavior.
- Claims/phase recovery and provider work are not implemented by T01.
- Main Agent must inspect the files and independently reproduce focused
  verification before accepting the task.

## Proposed status and follow-up tasks

- After Main Agent review, mark `turns/T01` complete, update turns to 1/2 local
  tasks complete, and remove the T01 active assignment from master progress.
  Keep the overall turns module unchecked pending T02 and integration gates.
- `turns/T02`: add ordered claims, fences, attempt/repair persistence and phase
  recovery against the same frozen `TurnStore`; extend the owned module/tests.
- `persistence-adapters/T02`: exercise atomic admission, uniqueness, sequence
  allocation and lifecycle contention on isolated SQLite and PostgreSQL.
- `coordinator/T01`: consume the typed submission/lookup facade with injected
  store dependencies; provider/operation generation belongs to coordinator
  processing and must not enter retry lookup.
