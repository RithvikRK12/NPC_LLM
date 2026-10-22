# Godot adapters T02 handoff

Date: 2026-10-18

## Task

Implemented the ordered finalized-dialogue presenter and connected it to the T01 gateway and existing chat window. The presenter accepts only complete final results for the active scope/epoch, deduplicates turn IDs and sequence numbers, buffers out-of-order results, validates that dialogue beats reconstruct the exact final text, and emits turns in sequence order. Only `/world` rows marked `invalidated` advance an unresolved gap; a `finalized` gap waits for its dialogue in history. World history initializes the cursor after its newest visible sequence, which handles the API's capped latest-50 history.

History refresh supplies per-NPC epoch, transcript history, and terminal metadata. Clear-chat now passes scope and epoch, resets the presenter using the server's returned current epoch, and its copy explains that generated biography and accepted actions remain in this game. New-game copy states that run progress and generated NPC biography reset. The existing History, Supplies, Close, Send, and clear controls and their focus/layout paths were retained.

Narrative text is shown as the complete `final_dialogue`; provided beats are used as readable pages only after exact reconstruction validation. Existing action display continues to read validated output metadata. The presenter does not infer actions, item grants, or animation from story wording.

## Files changed

- `frontend/godot/scripts/conversation_presenter.gd` (new)
- `frontend/godot/scripts/chat_window.gd`
- `frontend/godot/scripts/main.gd`
- `frontend/godot/tests/conversation_presenter_smoke.gd` (new)
- Logs in this evidence directory

Existing T01 gateway changes in `chat_window.gd` and `conversation_gateway.gd` were retained.

## Verification

Godot executable: `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot`, version `4.7.2.stable.official.ed1daf0bf`.

| Command | Exit | Result |
| --- | ---: | --- |
| `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --editor --quit` | 0 | Project import and script parse completed. Godot printed environment diagnostics because the sandbox could not write editor settings under `~/Library/Application Support/Godot`; no script parse errors appeared. |
| `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --script res://tests/conversation_presenter_smoke.gd` | 0 | 15 passed, 0 failed. Covers ordering, duplicates, stale scope/epoch, exact beats, oversized beat pagination, long text, invalidated versus finalized gaps, reset, and latest-50 history startup. |
| `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --script res://tests/conversation_gateway_smoke.gd` | 0 | 19 passed, 0 failed. T01 regression gate. |
| `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot --headless --path frontend/godot --script res://tests/ui_rework_smoke.gd` | 1 | Could not complete: test setup attempted `/world` at `127.0.0.1:8000`, connection failed, then the UI smoke timed out. No backend/provider was available. Log is `ui-rework-blocked.log`. |

Two regressions were run RED before their fixes. Temporarily restoring the prior behavior that skipped both finalized and invalidated rows exited 1 with `a finalized sequence gap waits for dialogue delivery or history` failing (14 passed, 1 failed). The oversized-beat check also failed against a stub that returned unsplit beats (14 passed, 1 failed). Restoring invalidated-only advancement and font-shaped pagination produced the green result above. See `t02/finalized-gap-red.log` and `t02/oversized-beat-red.log`.

Godot also emitted non-fatal macOS certificate lookup and `user://logs` write diagnostics during headless runs. They did not affect the smoke exit codes.

## Results by criterion

- Finalized turns display once in sequence order: **verified** by focused smoke coverage.
- Delayed duplicates and obsolete scope/epoch results are suppressed: **verified** by focused smoke coverage.
- Terminal gap behavior: **verified**; invalidated gaps advance, finalized gaps wait for history/dialogue.
- Exact long-text reconstruction and complete beats: **verified** by focused smoke coverage.
- Oversized individual beats split into viewport pages using the existing font-shaped layout boundaries, while preserving exact text: **verified** by focused smoke coverage.
- Clear/reset drops queued old results: presenter reset behavior **verified**; clear request supplies scope/epoch and reads the returned epoch. End-to-end server clear was not exercised because the backend was unavailable.
- History truncation at 50 turns does not block the next result: **verified** by focused smoke coverage using sequences 51–100.
- Story text does not synthesize action/item metadata: **verified** at the presenter boundary; gameplay state and animation remain outside the presenter.
- Existing controls: **static-only**. Their buttons, focus paths, and container layout were retained; the broader UI runtime smoke could not reach its checks without `/world`.
- Clear/new-game lifetime wording: **static-only** source review.

## Risks and follow-up

- End-to-end clear and live backend delivery remain unverified until a backend is available. The updated clear URL now uses the epoch-aware API route; the existing UI smoke currently attempts world loading before it can exercise that interaction.
- UI-control runtime behavior is not independently verified because the UI smoke timed out on backend connection; control construction and focus wiring were left intact.
- This task does not implement revision-aware application of response state or animation; those remain T03 responsibilities.

## Main Agent review (2026-10-18)

Main Agent inspected the presenter, window integration and RED/GREEN logs, then independently reran the focused checks from the repository root with the same Godot binary:

- `.../Godot --headless --path frontend/godot --script res://tests/conversation_presenter_smoke.gd` — exit 0, 15 passed / 0 failed.
- `.../Godot --headless --path frontend/godot --script res://tests/conversation_gateway_smoke.gd` — exit 0, 19 passed / 0 failed.
- `.../Godot --headless --path frontend/godot --editor --quit` — exit 0, no script parse/compile errors.
- `git diff --check` — exit 0.

Main Agent accepts T02 as locally complete with the backend-dependent UI interaction checks and wording/control review limits above. The `godot-adapters` module remains open pending T03 and adjacent integration.
