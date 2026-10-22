# godot-adapters/T03 handoff

## Task

Centralize revision-aware client snapshot application across durable chat, world, bow quest, legacy inventory reconciliation, Craftsman and Gatherer transport. Preserve shared inventory/quest/NPC/activity state under delayed responses, deduplicate activity presentation without inspecting prose, and preserve exact retry identities.

Implementation is ready for Main Agent review. No backend/API/game adapter files or master/task progress records were edited by this worker.

## Files changed

- `frontend/godot/scripts/revisioned_state.gd` (+ generated `.uid`): shared per-game authoritative revision/value cache. It selects each resource independently, validates nonnegative integral labels, accepts baseline zero, keeps newer cached snapshots and their actual server labels, copies values across the boundary, and never advances a resource from labels alone when that response lacks its fields. NPC social state and NPC inventory have separate keys. The same helper provides scope/resource/local-encounter-revision consumption for existing activity snapshots.
- `frontend/godot/scripts/main.gd`: shares the cache with encounter gateways; filters world, chat and quest state; centrally updates NPC supply UI; rejects obsolete world scopes; treats a same-game loaded `/world` result as resource reconciliation rather than reinitializing active scenes. A world reconciliation blocked by an in-flight chat remains queued. Initial world/new-game restore behavior remains explicit.
- `frontend/godot/scripts/chat_window.gd`: removes the two direct inventory writes from finalized/legacy response handling; the existing `world_changed` path now owns them through the main revision filter. Accepted T01/T02 transport, presentation and paging changes are preserved.
- `frontend/godot/scripts/craftsman_gateway.gd`: filters incoming data through the shared cache; publishes every accepted snapshot separately from once-per-activity presentation delivery; suppresses obsolete local encounter deliveries. A retry of the same request ID reuses the stored complete wire payload and original expected revision.
- `frontend/godot/scripts/gatherer_gateway.gd`: uses the shared filter and the same snapshot/presentation separation; duplicate activity revisions do not repeat presentation. Existing exact-payload retry and conflict/read-only refresh behavior is preserved.
- `frontend/godot/tests/revisioned_state_smoke.gd` (+ generated `.uid`): 25 deterministic behavioral checks using real main/gateway components. Recording subclasses isolate only HTTP dispatch/refresh for retry tests; state application and callback handling remain production code.
- Evidence in `docs/evidence/conversation-redesign-godot-adapters/t03/`.

## Tests run

Godot executable: `/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot` (4.7.2). Final command pattern:

```sh
/Users/rukithnayak/Downloads/Godot.app/Contents/MacOS/Godot --headless --log-file /private/tmp/t03-<name>-final.log --path frontend/godot --script res://tests/<name>.gd
```

| Check | Result | Evidence |
| --- | --- | --- |
| `revisioned_state_smoke.gd` | Exit 0; 25 passed, 0 failed | `t03/revisioned_state_smoke-final.log` |
| `conversation_gateway_smoke.gd` | Exit 0; 19 passed, 0 failed | `t03/conversation_gateway_smoke-final.log` |
| `conversation_presenter_smoke.gd` | Exit 0; 15 passed, 0 failed | `t03/conversation_presenter_smoke-final.log` |
| `gatherer_encounter_smoke.gd` | Exit 0; all five checks PASS | `t03/gatherer_encounter_smoke-final.log` |
| `craftsman_recovery_smoke.gd` | Exit 0; 0 failures | `t03/craftsman_recovery_smoke-final.log` |
| `craftsman_backend_compatibility_smoke.gd` | Exit 0; 0 failures | `t03/craftsman_backend_compatibility_smoke-final.log` |
| `craftsman_activity_smoke.gd` | Exit 0; 0 failures | `t03/craftsman_activity_smoke-final.log` |
| `craftsman_inspection_smoke.gd` | Exit 0; 0 failures | `t03/craftsman_inspection_smoke-final.log` |
| `inspection_objective_smoke.gd` | Exit 0; 0 failures | `t03/inspection_objective_smoke-final.log` |
| Editor import (`--editor --quit`) | Exit 0; no script parse/compile errors | `t03/editor-import-final.log` |
| Focused `git diff --check` | Exit 0 | `t03/diff-check.log` |
| `ui_rework_smoke.gd` | Unavailable: requires live disposable backend at port 8001; observed startup timeout | `t03/ui_rework_smoke-final.log`, `t03/backend-availability.log` |

All runtime logs include the environment's macOS certificate startup diagnostic (`get_system_ca_certificates`, `ret != noErr`). Final editor import additionally reports that sandboxed editor settings cannot be saved outside the workspace. The existing inspection/objective smoke reports two ObjectDB instances and one resource still in use at exit despite its zero assertion failures; this is recorded, not hidden. Initial runs also showed the default user-log directory was unwritable; subsequent commands explicitly directed engine logs to `/private/tmp`.

### RED/GREEN sequence

- `red.log`: original production paths produced 2 passing / 8 failing assertions for delayed shared state, central NPC inventory, narrative-only state, scope and duplicate Gatherer delivery. One initial activity assertion had an incomplete fixture (the Craftsman gateway scope was unset); the fixture was corrected before GREEN. The actual delayed-world activity behavior is checked separately in the final suite.
- `red-edges.log`: 19 passing / 2 failing; obsolete `/world` scope replacement and retained values carrying the incoming stale label. Fixed by explicit scope replacement rules and retaining the matching cached server labels.
- `red-retry.log`: 21 passing / 1 failing; same-ID Craftsman retry changed payload/expected revision after disconnect. Fixed by resending the exact saved payload.
- `red-world-delivery.log`: 22 passing / 1 failing; duplicate world reset the active Gatherer scene. Fixed by the loaded-world resource reconciliation path.
- `red-deferred-refresh.log`: 23 passing / 1 failing; reconciliation was dropped while another chat was pending. Fixed by retaining a queued read-only refresh.
- `red-independent-resources.log`: 24 passing / 1 failing; duplicate activity delivery suppressed newer independent inventory state. Fixed by publishing snapshots independently of deduplicated activity presentation.
- `green.log` and `revisioned_state_smoke-final.log`: 25 passing / 0 failing after the final implementation.

## Results by acceptance criterion

1. **Shared revision application:** Main chat/world/quest paths and both encounter gateways use the same cache in the running scene. Complete label maps do not advance resources absent from a response. Different-NPC stale inventory, late quests, late world inventory/quest/activity and independent NPC inventory labels are covered.
2. **No repeated inventory deltas:** The client assigns detached authoritative snapshots; it adds/removes no items based on narrative or receipts. Missing state fields no longer clear inventory through a default empty list.
3. **Verified activity deduplication:** Gateway `updated` delivery is consumed once per server game scope, activity resource and existing local encounter revision. Every snapshot still reaches resource application through `snapshot_received`, including newer unrelated inventory in a duplicate-activity refresh. Repeated same-game `/world` no longer resets active presentation. No identity is derived from dialogue/beat content, and no server event fields were invented.
4. **Disconnect/retry safety:** Gatherer exact pending request survives transport failure; successful read-only refresh adopts the committed branch and clears pending without dispatching another command. Craftsman exact saved request ID/payload/expected revision survives retry even when local physical staging and the gateway's current revision have changed.
5. **Text-only narrative safety:** A reply describing giving a bow and walking to the ship changes neither actual inventory nor actor position. Missing authoritative state is not interpreted as an empty inventory or new activity.

## Risks and contract limitations

- `/world/beach/salvage` currently returns only `player_inventory` and `salvage_ids`; legacy `/inventory/transfer` uses `ChatResponse`, whose schema has no resource labels. These were reported to Main Agent during implementation. The client refuses those unversioned shared-state fields and requests authoritative read-only `/world` reconciliation. No backend change is required for this fallback. The focused suite checks that neither result overwrites known inventory and that reconciliation is requested.
- Public encounter snapshots expose local `revision` and durable activity/attempt/outcome state, but not a general public event-ID stream. Presentation deduplication therefore uses the existing verified activity identity (scope + resource + local encounter revision); it does not invent an event schema. There is no new animation driven by chat receipts or prose.
- Existing backend-required UI/integration suites are not claimed as passing. The checks above use real client components with deterministic callback inputs, not a complete mock HTTP server or a live provider.
- Full repository/backend suites were not rerun for this client-only bounded task. The Main Agent owns independent integration/release acceptance.

## Follow-up tasks

- Main Agent independently reruns the focused/adjacent checks and reviews the shared-cache and retry changes, then updates the task and master progress records.
- Run the existing UI/live conversation/encounter integration suites against an isolated disposable backend when port 8001 is available.
- If direct application of legacy transfer/salvage response state is desired later, add authoritative `game_scope`/`state_revisions` to those response contracts upstream; the current read-only reconciliation remains safe without it.
