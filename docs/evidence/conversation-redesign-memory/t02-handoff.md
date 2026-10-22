# memory/T02 handoff — 2026-10-18

Owner: `memory_t02`; bounded implementation in `backend/app/services/conversation/memory.py` and `backend/tests/test_conversation_memory.py`. Independent review found no remaining facade defect after the revision-zero correction-link fix. Main Agent reproduced the final focused, adjacent and full-backend suites and locally accepted T02; concrete adapters remain unverified.

## Delivered boundary

`SummaryService.refresh(key, source_range, revisions, deadline)` reads detached finalized turns through frozen `SummaryStore` and current attributed records through frozen `MemoryReadPort`. It applies `MemoryPolicy.filter_retrieval`, requires exact source-message/final-speech identities within the requested stream/range, retains unverified report attribution, and publishes a detached `SummaryRecord` with a canonical source revision digest and expected summary revision. The store publication call owns final epoch/source/canon/correction CAS checks after optional slow work has completed.

The optional `summarize` callback selects exact attributed entries; it cannot rewrite record text, source turns, authority, uncertainty or correction metadata. Default selection retains the validated entries. The optional index callback runs after successful publication; exceptions cannot invalidate the summary. Neither callback is passed into a store transaction. No mandatory turn coordinator/route was modified.

`dirty_keys(game_scope)` scans store-backed work, including keys whose in-process notification was missed. Failed refresh leaves that marker intact. A provider exception/error retains a valid prior summary only when its revision heads and exact current entries still match; otherwise a typed failure leaves scoped unsummarized retrieval available. Late source/canon/correction changes, clear/reset and deadline expiry prevent publication.

## Trusted correction metadata boundary

The frozen `MemoryReadPort` returns `MemoryRecord` values and has no `correction_link` field. In particular, `MemoryWrite(expected_revision=None, correction_link=...)` is valid: a revision-zero replacement must not be treated as an uncorrected record. `SummaryService` therefore takes a separate injected trusted `lineage` lookup. It returns `SummaryLineageSnapshot(key, records, revisions, correction_links)` from authoritative persisted memory-write lineage. The result must identify the exact key, complete candidate record values, exact source/canon/correction revision snapshot, and exactly one explicit link or `None` for every candidate ID. The callback must not derive links from provider prose or echo request heads without observing authoritative storage.

The service rejects absent, failed, incomplete, mismatched or unbound lineage lookups. It may return a prior summary only when its current record values/source turns and relevant heads still match, and never publishes on that fallback. Current lineage is preserved for both revision-zero linked replacements and later corrected revisions. Provider selection cannot remove or change a link.

The caller/adapter must supply all relevant source/canon/correction heads in `RevisionSet`; their names and completeness cannot be inferred by this facade. The runtime lineage adapter must read persisted metadata consistent with that exact observed snapshot, and the SummaryStore publication CAS must atomically recheck those same heads. Current-memory retirement/filtering and durable dirty state/finality/CAS are adapter responsibilities. The focused store/lineage doubles model these checks and do not establish SQLite/PostgreSQL durability, restart persistence or transaction lock behavior. No schema or frozen contract/port changed. No live provider or embedding model was used.

## Test-first evidence

Before production edits, the focused command reported `Ran 16 tests ... FAILED (failures=12)` (exit 1), with assertions naming absent `SummaryService`. One initial missing-class direct access was changed to the same explicit feature assertion; the resulting RED run had no fixture errors. Existing five T01 tests passed throughout.

The initial implementation passed 16 tests. Independent review then identified that a valid revision-zero replacement could carry a correction link omitted by `MemoryReadPort`. A regression failed with the missing link; another showed that a bare mapping could contain metadata from a different snapshot. The service now requires a trusted `SummaryLineageSnapshot` bound to the exact key, filtered records, revision map, and complete link-ID set. Missing, failed or stale lineage fails closed or returns only a still-valid prior. The final focused suite passes 22 tests and includes linked revision-zero and changed-revision cases.

## Verification

All commands ran from repository root with the workspace virtualenv:

| Command | Result |
| --- | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_memory.py'` | exit 0; 22 tests |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_store_ports.py'` | exit 0; 32 tests |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_canon.py'` | exit 0; 15 tests |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py'` | exit 0; 70 tests |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | exit 0; 380 tests |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` | exit 0; 843 tests |
| `git diff --check` | exit 0 |

Main Agent reproduced all focused and broad suites after the final lineage change; owned Python whitespace checks and `git diff --check` also pass. Broader runs emitted existing Starlette/httpx and `datetime.utcnow()` deprecation warnings. The backend suite also emitted expected malformed-provider-output diagnostics and the bounded lexical retrieval fallback notice. No failures or skipped PostgreSQL proof are represented as passes. `git diff --check` omits pre-existing untracked module/test paths; tests imported their current content.

T02 is locally accepted as a service/fake conformance deliverable only. The production lineage reader and SummaryStore must still read authoritative persisted metadata, recover dirty keys after restart, scope/finality-filter source turns, and atomically compare all supplied heads.
