# Mechanical adoption handoff

2026-10-20, macOS, Python 3.12.14, Godot 4.7.2, PostgreSQL 16.15 (pgvector Docker service). The existing dirty redesign workspace was preserved. Tests used temporary SQLite databases, disposable `npc_test_*` PostgreSQL databases and copied Godot projects with isolated client caches. No acceptance runner uses the personal save.

## Results

| Gate | Final result | Evidence |
| --- | --- | --- |
| Full backend | 1,129 tests, zero failures/errors, exit 0 | `backend-tests-final.log` |
| PostgreSQL | Eight runners, all exit 0; 153 executions (overlapping suites) | `*-postgres_acceptance.log`, `run_postgres_checks.py` |
| Godot | 16 functional scenarios, all exit 0, zero assertion/script failures | `godot-summary.json`, individual `.log` and `-turns.json` |
| Shell / whitespace | `bash -n Play.command`, `git diff --check`, exit 0 | final closeout commands |

Commands are in [the runbook](../../../conversation-redesign-runbook.md). [Crash/error mapping](coverage-map.md) names the behavioral tests for detailed-design §5.4 and §8. The full backend command is `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -v`.

## Integration corrections

The live adoption gate found gaps missed by pure boundaries. Final speech now reaches the Godot presenter through the correct signal signature. Typed revision envelopes update inventories/quests/activity. Clear retains monotonically increasing stream sequences. Gifts share durable chat identity and keep unsent drafts. Explicit stock requests create a durable purpose question; choice consent preserves immutable offered terms and exact current-answer provenance. Craftsman activity projection matches the existing controller. A restored pending conversation no longer blocks the initial world fetch needed to validate its scope; background reconciliation still waits for in-flight turns. The focused bootstrap regression failed before this fix and passes afterward. Context overflow becomes a terminal safe reply, and a coalesced periodic worker scan recovers pending streams without mutating status reads.

The production gateway rechecks deterministic intent rather than accepting generated action guesses. Provider syntax is constrained to current capabilities, personal conversation suppresses invented actions/canon, redundant prompt schema/fingerprints are removed, and Llama uses an explicit 8192-context alias of the existing weights. The strict public decoder, consent validation and receipt transaction remain authoritative.

The bow, Craftsman wreck/solo return, Gatherer combat/retry/reload/decline/success, doors, persistence, fullscreen and pending shutdown paths pass. Route checks use actual segmented navigation and actor positions; fixture reloads actually recreate scenes. Provider waits permit cold local processing without asserting playable latency.

## Limitations and review

Craftsman integration, persistence and fullscreen fixtures print resources-still-in-use warnings at teardown. Their functional assertions pass; `shutdown_resource_warning` is explicit in the summary. The runner still fails other engine errors, script errors, FAIL assertions or nonzero exits. Fixture teardown cleanup is deferred and is not called a clean engine shutdown.

A read-only review identified signal wiring, missing purpose production, context-budget recovery and obsolete route-check assumptions. These were corrected and regression-tested. Subsequent changes received self-review and final suite verification; no second independent review is claimed.

The small live route screen is separate from this mechanical gate. It cannot close semantic-quality thresholds or product acceptance of latency. Human calibration was waived by the user's existing instruction. T03 remains open; T04's runbook/tests are delivered while broad approval awaits T03.

## Actual local launch

`./Play.command` started the backend on 127.0.0.1:8000 and Godot against the configured existing save. Native UI inspection verified the loading label disappeared, the player/village rendered and the bag showed two items. A pre-existing saved pending request exposed the bootstrap deadlock; the first instance was restarted after the focused red/green regression. The final game instance was left open for the user. Backend health and world/checkpoint requests returned 200. No reset was performed.
