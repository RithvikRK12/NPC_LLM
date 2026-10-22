# Godot adapters T01 handoff

Date: 2026-10-18

## Changes

- Added `frontend/godot/scripts/conversation_gateway.gd` for versioned chat submissions, request identity, retry, pending polling, persisted pending payload recovery, scope/epoch suppression, stale-key world refresh, and finalized-turn delivery.
- Integrated chat submissions in `chat_window.gd`; inventory transfer and clear-chat continue to use their existing request path.
- Added `frontend/godot/tests/conversation_gateway_smoke.gd` covering fresh IDs, payload contract, pending response recognition, and scope/epoch comparison.
- A follow-up regression guard makes `invalidate("", ...)` a no-op until `/world` supplies an initialized scope, preserving restored requests during startup. The smoke test asserts that a pending `scope:1` / epoch `2` request survives an empty-scope invalidation.
- Pending records now use `user://conversation_gateway_pending_npc_<npc_id>.cfg`; chat_window assigns the NPC ID before adding the gateway child, so each window restores and persists only its own turn. The smoke test asserts NPC 1 and NPC 2 produce different storage keys.
- Startup restoration now waits until a nonempty world scope/epoch arrives. A matching key resumes the saved ID by status lookup or exact-payload redelivery; a stale scope/epoch clears that NPC's record and refreshes `/world` without resubmitting. A final response received before key initialization is held until the key can be checked. The smoke test covers the empty-key preservation guard plus current/stale restored-key comparisons.
- Initial pending-record persistence is required before POST dispatch; a save failure clears in-memory pending state and returns no request ID. Failure to save a later status URL emits a warning but retains the in-memory request identity and continues status polling; after a crash, the original persisted payload can be safely re-delivered with the same ID if its record remains available. The smoke test checks the dispatch gate for successful and failed save results.
- Clearing a pending record is now durable-first: the gateway writes the empty per-NPC record before clearing memory or emitting a finalized response/failure. If that save fails, it retains the same identity and outcome, then retries clearing at 2-second intervals up to five times. It never publishes the finalized response or reports the turn cleared while the write fails. After the bounded retries, it leaves the record pending for a later manual retry/restart. Stale invalidation and 404/409 paths use the same clear gate and defer world refresh/reporting until persistence succeeds. The smoke test checks the clear-success publication gate.

The gateway writes one active pending request per NPC to `user://conversation_gateway_pending_npc_<npc_id>.cfg`. A recovered pending request uses the persisted status URL when present, otherwise it re-delivers the exact persisted request ID and payload. The status endpoint is only called with GET. It is never treated as a new submission. Pending API responses do not expose draft dialogue; only a final response with `final_dialogue` is emitted to the window.

## Verification

Expected command:

```sh
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --script res://tests/conversation_gateway_smoke.gd
```

Attempted once before implementation (red reproduction) and once after the initial implementation. Both invocations exited `137` with no stdout/stderr. `Godot --version` also exited `137`, so the installed runtime cannot start in this environment; the final smoke assertions added during review could not be run. This is a runtime/environment blocker, not a passing test claim.

Static independent review approved the final source after fixes for startup key validation, per-NPC storage collisions, save-before-POST, and durable clearing before final/stale events. It also confirmed that `retry()` has no dedicated chat-window control; timed polling and restart recovery remain wired. Static review does not substitute for the unrun headless smoke or timer/file integration behavior.

## Integration limits / findings

- api-adapter/T02 now exposes conversation epoch in `/world`, and api-adapter/T03 binds versioned submit/status to the durable service with final compatibility projections. The remaining acceptance blocker for this task is a runnable Godot executable for the headless smoke suite.
- The gateway persists only the active pending request, not a turn history. Its pending request survives application restart through Godot `user://` storage; this does not promise recovery if that storage is removed or inaccessible.
- Scope/epoch invalidation suppresses old publication, cancels local polling/request delivery, and asks `/world` for an authoritative refresh. It does not create another action.

## Main Agent runtime verification (2026-10-18)

A runnable Godot binary was found at `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot` (Godot `4.7.2.stable.official.ed1daf0bf`). The previously referenced `/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot` still exits 137. The `Downloads` binary was used for these checks from the repository root:

- `.../Godot --headless --version` — exit 0; version recorded in `t01-runtime/version.log`.
- `.../Godot --headless --path frontend/godot --editor --quit` — exit 0; no GDScript parse or compile errors after the type annotation fix; output in `t01-runtime/editor-import.log`.
- `.../Godot --headless --path frontend/godot --script res://tests/conversation_gateway_smoke.gd` — exit 0; 19 passed, 0 failed; output in `t01-runtime/gateway-smoke.log`.

The first project import exposed a compile error at `chat_window.gd:325`: Godot could not infer the return type from the gateway held as a `Node`. The local fix annotates `request_id: String`. The smoke runner also now records failed checks and explicitly exits nonzero, instead of relying on bare `assert()` behavior; it frees the gateway node before exiting.

The binary logs benign environment diagnostics: macOS certificate lookup reports `ret != noErr`, and the sandbox prevents Godot from writing its default `user://logs` / editor settings under the user's Library. These did not change process exit codes or the smoke result. The smoke asserts the gateway's ID/payload helpers, pending-response predicate, scope/epoch guards, startup restoration guard, per-NPC storage path, and persistence/clear gates. It does not simulate every HTTP delivery/poll/restart lifecycle against a mock server; the lifecycle implementation remains covered by the prior static independent review recorded above, so this is a focused client runtime gate rather than exhaustive integration evidence.

T01 is locally accepted for the runtime unblock. `godot-adapters/T02` is now dependency-ready (T01 and api-adapter/T02 complete); `baseline/T02` remains blocked on provider availability.
