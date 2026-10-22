# canon/T02 handoff

Implemented the bounded accepted-correction policy in `backend/app/services/conversation/canon.py` and appended nine focused tests to `backend/tests/test_conversation_canon.py`. Shared contracts/ports, T01 tests, task packets, master progress, and graph files were not changed by this worker.

## Boundary extension

`CanonReply` now accepts optional `corrections: tuple[CorrectionCandidate, ...]` and `correction_texts: Mapping[str, str]`. Defaults preserve T01 callers; absent correction inputs cannot authorize a revision. The wrapper snapshots the tuple and message mapping. Correction targets must already be resolved to canon IDs. Message texts must come from exact accepted player input and are keyed by the `player_message` source IDs in `AssembledReply.evidence_dependencies`; they are not provider-rewritten transcripts.

`CanonRules.validated_correction(candidate, correction, head, final_text, span_text, correction_texts, evidence) -> bool` is the new injected semantic hook. The supplied correction texts are exact resolved source-span slices in order. The hook must establish explicit NPC acceptance and semantic linkage between the attributed challenge, old head, replacement, and this exact final support span. A missing hook, exception, rejection, or non-boolean truthy result rejects revision. An attributed challenge alone never becomes acceptance. There are no wording heuristics or provider calls in this module.

## Acceptance mapping

- Revision requires a single matching active generated narrative head, exact expected revision, a unique explicit correction link, and correction target equal to the head canon ID. Stale/concurrent head versions and ambiguous multiple active heads reject.
- Each correction source span must resolve in the injected accepted texts and match a scoped, attributed `player_message` source dependency. Wrong provenance kind, attribution, scope, NPC, missing texts, out-of-range spans, or missing evidence reject. A message source with no NPC is allowed when scoped to the same game; an explicitly different NPC is rejected.
- Both additions and revisions use T01's full source-segment to fresh assembled-final mapping and translated candidate span. A rebuilt final ID/offset is accepted only with the fresh matching map; draft offsets reject. The replacement content must occur in the exact supporting span, and injected claim validation/affordance grounding still apply.
- An active authored constraint/head for the same subject/predicate prevents revision. Ordinary later additions cannot replace a generated head.
- Output is frozen `ReviseCanonChange`: existing `canon_id`, `expected_revision`, subject, predicate, category, generated/narrative-only authority, exact final support span, and explicit correction link. Existing `CanonRecord` values, including superseded history, remain untouched. The persistence owner must atomically compare the expected head revision, preserve the superseded record and create the next record with lineage; this pure planner performs no write and cannot eliminate a race after planning.
- Contradiction-only input yields no canon change and retains its attributed correction value. Report persistence remains the memory owner's responsibility; the canon policy does not manufacture or promote reports into events.

The hand-checked accepted-versus-contradiction inputs are in `t02-correction-fixtures.json`. The two final speeches contain the same proposed replacement; only the accepted speech passes the injected semantic decision.

## Test-first evidence

`t02-red.log` records the initial missing constructor API. After adding only the detached input fields, `t02-behavior-red.log` records two expected assertion failures (`0 != 1`) because the existing policy skipped revisions. Implementing revision admission made those cases pass. T01's six tests remain unchanged; nine T02 tests cover the acceptance matrix.

## Verification

| Command | Exit | Evidence |
| --- | ---: | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_canon.py' -v` | 0 | 15/15, `t02-focused.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest backend/tests/test_contract_values.py backend/tests/conversation_port_conformance.py backend/tests/conversation_store_conformance.py -v` | 0 | 17/17 collected dependency/conformance tests, `t02-dependencies.log` |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` | 1 | 139 tests, one concurrent composition fixture error, `t02-conversation.log`; combined rerun pending coordinator after both workers freeze |
| `git diff --check -- backend/app/services/conversation/canon.py backend/tests/test_conversation_canon.py docs/evidence/conversation-redesign-canon` | 0 | `t02-diff-check.log`; tracked diff clean |

The exact unrelated error is `test_conversation_composition_service.CompositionServiceTests.test_unknown_fact_and_renderer_fail_closed`, line 204: constructing `ReceiptSlot` raised `ValueError: renderer does not match receipt speech act` before the test reached composition service code. Composition files are owned by the parallel T02 worker and were not changed here. The coordinator explicitly requested preserving this transient failure and deferring the full combined rerun until both workers finish.

The canon implementation and test files are currently untracked in the shared worktree, so supplemental `git diff --no-index --check /dev/null FILE` inspections are also recorded. They emitted no whitespace errors and returned 1 for the intentional file additions. A standalone owned-artifact whitespace check is recorded in `t02-artifact-check.log`.

No live database/provider calls were made. Full legacy backend discovery was not run under this pure task's no-database/no-provider constraint. Persistence CAS, retained superseded records, downstream summary invalidation and real semantic validation wiring remain adjacent integration responsibilities, not claims of this planner deliverable.
