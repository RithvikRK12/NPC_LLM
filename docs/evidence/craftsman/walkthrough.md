# Craftsman encounter: implementation and verification

Implemented delivery slices 1–5 from the approved design. The bow remains an independent quest. Ship materials, delivery operations, actual repair, sailing and the ending are deferred; inspection starts a gathering quest and never completes the story.

## Play through

1. Start the backend and Godot using the repository README. Existing saves acquire the encounter without resetting inventory or bow progress. Restart Game is optional if you want a fresh opening and both introductions.
2. Enter the workshop. The player walks toward the Craftsman; Continue through his two introductory beats or deliberately Skip. Continue opens his regular conversation. Esc interrupts presentation; an unfinished introduction is eligible on a later workshop entry.
3. Ask about his interests, work, loneliness, home or starting over. Report “The storm broke my ship,” then ask “Could you help me fix it?” A direct “My ship wrecked, and I need help” also accepts the outing. A report alone offers inspection and waits for agreement.
4. Close chat and lead him through the workshop door. He physically approaches the exit before the shared fade. Use “wait here,” “let's go,” “not now,” or “go back to your workshop.” He waits outside unrelated cottages and resumes after you return outside.
5. Follow the southern path to the wreck. If he falls behind, wait or return to him. A blocked route leaves a hint and the accepted outing intact; ask him to resume from clear ground. Neither actor teleports to bypass an obstacle.
6. Both actors must arrive. Continue after recognition, watch both walk closer, and advance through damage, hope and the authoritative recipe. After valid staging, Skip commits the same inspection result. If confirmation fails, Retry resumes the outcome rather than replaying the walk.
7. Confirmed inspection starts **A Way Home**: **12 sound timber planks, 3 coils of rope, 2 bundles of sailcloth, 2 pots of pitch**. Open Quests to see the main quest alongside the bow. Contributions remain zero in this slice.
8. Continue after farewell. The Craftsman walks back independently, crosses into his workshop without moving your camera/player, and resumes his routine. You can speak during return; closing chat resumes the same journey.

## What changed

- A dedicated physical Craftsman with a 24×16 foot collider, a separate interaction area and existing directional art. The stationary Gatherer and Rowan retain their existing actor implementations.
- Weighted workshop activity points, 5–12 second idle pauses, 75-unit ambient speed, conversation suspension, and global-pause handling.
- Bounded collision-clear local routing, breadcrumb following, distance hysteresis, catch-up, safe blocked-route waiting, explicit actor portals and authored return landmarks. Routing includes a 2-unit numerical tolerance beyond WorldLayout's existing foot clearance to prevent sampled corner grazing; the actor footprint is not inflated twice.
- Dedicated introduction/inspection presentation and HTTP gateway controllers. Story state, activity and presentation have separate ownership. Commands are queued behind checkpoint writes, final staging is flushed before outcome commands, and JSON acknowledgements preserve the exact sent snapshot.
- Separate run-scoped encounter/ship-quest tables, monotonic checkpoint revisions, idempotent commands, atomic inspection-plus-quest activation, old-save initialization and New Game reset. A durable story-event model reserves the future deduplicated completion boundary; no repair/completion endpoint exists.
- Broader character classification/profile/prompts/context/validation, authored provider-failure fallback, explicit-topic precedence, contextual wreck intent, quotation/negation/hypothetical exclusions and independent report/agreement/inspection memory provenance. Inventory and quest facts still come from authoritative rules.
- A scrolling main-quest journal beside the bow, integer material counts, current whereabouts, and a confirmed-outcome notification. Inspection framing shows both actors and the hull above the dialogue panel.

## Verification

Tests use an isolated SQLite database at `/tmp/craftsman-playtest-20261013.db` on **port 8001**, with mock language generation and no embedding service. The user's regular database and port-8000 world were not used or reset.

Backend command (from `backend`):

```sh
PYTHONWARNINGS=ignore PYTHONPATH=.. ../.venv/bin/python -m unittest discover -s tests -q
```

**453 tests pass**, including existing inventory, grounding, memory and quest checks plus encounter/recipe defaults, atomic/idempotent inspection, invalid checkpoints, reset/stale scopes, contextual requests, excluded requests, separate memories, character prose, story length, bow overlap and authoritative ship materials.

Godot **4.5.1** was used without an engine migration. Run a headless check from the repository root:

```sh
/private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot \
  --headless --log-file /tmp/craftsman-test.log --path frontend/godot \
  --script res://tests/craftsman_recovery_smoke.gd
```

Passing new checks:

- `craftsman_navigation_smoke.gd`: clear routed segments, rejected furniture/portal gaps, physical actor masks, numerical corner tolerance and valid door arrival.
- `craftsman_activity_smoke.gd`: actual workshop movement and conversation pause. Its initial work-point choice is controlled so a random 16-unit first walk cannot invalidate a 20-unit displacement assertion.
- `craftsman_intro_smoke.gd`: first-entry approach, actual player movement, input ownership, interruption/pending status, no replay and help-objective completion.
- `craftsman_inspection_smoke.gd`: no player-only trigger, recognition before approach, two physical staging paths and distinct collision-clear marks.
- `craftsman_recovery_smoke.gd`: latest staging flush before queued outcome, exactly-once dispatch after acknowledgement, explicit wait across a door, released player control on activation failure, pending-outcome reload, and recovered farewell ownership.
- `craftsman_presentation_smoke.gd`: hull above dialogue, journal bounds at 960×540 and 1280×720, whole-number counts.
- `craftsman_integration_smoke.gd`: real HTTP and full physical route from introduction through contextual agreement, wait/resume, shared departure, cottage detour, inspection, quest activation, independent return and reload; **0 failures headless and rendered**.
- `CRAFTSMAN_RECOVERY_RUN=1` with the integration script: actual reloads during follow, the visible inspection beat and independent return; staged Skip commits the quest; conversation during return preserves the activity; **0 failures**.
- `craftsman_routine_render.gd`: two-minute rendered observation with three distinct idle positions and no nonwalkable positions. A separate headless two-minute run observed five positions. Captures are under `/tmp/craftsman-routine`.

Passing existing regressions: `bow_quest_smoke.gd` (one real timed bow reward), `building_interiors_smoke.gd` (all three rooms and reloads), `persistence_smoke.gd`, `fisherman_integration_smoke.gd`, and `opening_lifecycle_smoke.gd`. The interior smoke now deliberately finishes the new first-entry introduction before testing furniture and exit controls; its existing assertions remain intact.

The full existing `ui_rework_smoke.gd` still reports **three failures at 1920px**: dialogue bounds, supplies bounds and menu bounds. Running the identical script on an untouched archive of base commit `fe42df4` reproduced exactly those three failures. They were not broadened into an unrelated UI refactor. The new journal/inspection checks pass at their tested viewport sizes.

## Visual evidence and limits

These are actual Godot render captures, inspected after the complete physical playthrough:

- [Workshop introduction](screenshots/01-introduction.png)
- [Shared departure](screenshots/02-shared-departure.png)
- [Both actors inspecting the wreck](screenshots/04-inspection.png)
- [Authoritative requirements](screenshots/05-requirements.png)
- [Main quest beside the independent bow quest](screenshots/07-main-quest.png)

The rendered routine showed the Craftsman beside different work areas while the entrance corridor remained clear. Rendered inspection was adjusted after review to keep the hull visible above dialogue. Physical headless assertions complement these captures; backend tests alone were not used to claim movement or framing works.

Free-form prose was checked with mocked proposals, authored fallback and the mock provider; quality from a particular live LLM remains provider-dependent. Trusted action recognition is a bounded English adapter; unfamiliar wording may need clarification. Routing has bounded searches and safe waiting rather than a guarantee of recovering from every arbitrary obstruction or distant detour.

Some existing Godot tests emit exit-time ObjectDB/resource warnings; the baseline fisherman integration does too. Headless macOS runs also emit the system-certificate diagnostic. Import/parse completed, but the sandbox prevented the editor from saving its global settings outside the workspace; no project parse error was reported. Native UI inspection was unavailable, so visual verification used rendered in-game captures.

## Review decisions

A fresh read-only whole-change review found five Important issues. Each was reproduced before fixing: recovered farewell ownership, queued final staging, explicit waiting at workshop departure, bow-topic precedence after wreck context, and negated/quoted/hypothetical commands. Follow-up tests also exposed and fixed JSON acknowledgement type differences and immediate arrival checkpoint timing.

Implementation stayed in the requested non-main development checkout to preserve the authorized working location. The dedicated physical Craftsman avoids changing the stationary Gatherer's collision behavior; this leaves small identity/display adapters in both scripts. No merge, push, deployment or user-save reset was performed.

### If the introduction buttons appear stuck

An older backend can still serve the village while omitting the newer Craftsman
encounter snapshot. This previously left the final introduction command silently
unsent. The compatibility regression now verifies that both Continue and Skip
surface a clear recovery message and restore control when encounter initialization
is missing. Restart the backend with this checkout's code and reopen the game;
**New Game is unnecessary**. Existing inventory, quests and chat history are kept.
