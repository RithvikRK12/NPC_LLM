# persistence-adapters/T04 handoff — accepted

## Implemented slice

- `SQLTurnStore.commit` atomically writes final transcript/result, canon, interactions, and typed contract-memory revisions. Memory writes validate exact scope/NPC/epoch, compare the active revision, retain correction-link attribution, supersede the previous head, and mark the summary stream dirty. Finalized turns mark summary work dirty even when they produce no memory write.
- Finalization resolves accepted speech dependencies against current resource labels, same-scope finalized/player text, active canon, operation receipts, or active attributed interpretations. Unsupported source kinds fail closed; provider-generated identifiers do not grant evidence authority.
- Clear invalidates old turn payloads, removes old transcript/summary/legacy memory and contract-memory rows, resets summary metadata, and preserves committed receipts/canon. New-game scope rotation clears run-scoped contract memories and rejects late old-scope writes.
- `read_prior_turns` returns detached earlier finalized turns from an exact literal scope/NPC/epoch. It never infers identity from legacy rows with unknown provenance. Player text IDs are deterministically represented as `turn:<sequence>` because `TurnSubmission` stores the accepted text without a producer `TextValue` ID.
- `SQLSummaryStore` supports durable dirty-key scans, contiguous finalized source reads, detached summary lookup, active-memory/correction and canon checks, summary revision CAS, and late-source rejection before clearing the dirty marker. Unsupported source kinds/revision keys fail closed.
- Concurrent new-game/summary publication coverage confirms that a completed reset leaves no active summary in the old scope. A SQLAlchemy pool checkout/checkin assertion confirms detached summary sources reach embedding only after the read connection is returned. Existing finalization tests assert provider/semantic refresh is not performed while its writer is locked.

## Verification

- SQLite lifecycle/publication, summary store, and scoped reads: 24/24.
- PostgreSQL 16.15 disposable database lifecycle/publication, summary store, and scoped reads: 24/24 ([log](t04-postgresql.log)); runner dropped the database.
- Full backend suite: 961/961 passed.
- `git diff --check` passed.

## Follow-on integration (recorded as context/T03)

T04 is accepted for its persistence-owned contracts. Unsupported authored/event sources fail closed because these SQL stores do not own authoritative readers for them. Full `ContextReadPort` packet composition and producer-ID verification require context-owned profile/canon/report/interaction/fact inputs and are recorded as context/T03.

The available SQLite/PostgreSQL results validate the persistence adapter acceptance criteria; context/T03 owns the larger packet-composition integration.
