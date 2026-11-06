# Willowbrook UI rework

Status: UI-01 through UI-06 implemented and validated on 2026-10-13.
Created: 2026-10-13.

## Direction

Make Willowbrook feel like a medieval village RPG through blocky lettering, expressive dialogue boxes, and a tactile slot-based inventory. Use warm parchment, dark wood, muted brass, and simple stepped edges. Keep the village visible and give conversations the strongest visual focus when talking.

Confirmed user requests:

- Replace the current font with something blocky.
- Present conversations in typical RPG-style text bubbles.
- Use a portrait and text box along the bottom, with a small speech tail toward the speaker.
- Make the inventory visually closer to Stardew Valley.
- Add Quit Game and move Restart Game into a small menu opened with Escape (Esc).
- Work through this Markdown plan before implementing the redesign.

Proposed details below are defaults for discussion, not additional confirmed requests. Stardew Valley is a reference for compact slots, prominent item icons, and cozy materials; create Willowbrook's own frames and artwork.

## Current implementation

| Area | Current behavior | Implementation location |
| --- | --- | --- |
| Dialogue | Large right-side rounded panel, supplies above a continuous text transcript, free-text input below | `frontend/godot/scripts/chat_window.gd` |
| Inventory | Five-column grid of 96 × 100 item cards; names and counts below icons | `frontend/godot/scripts/item_grid.gd` |
| HUD and satchel | Large lower-left status panel, separate inventory drawer, fixed-position controls | `frontend/godot/scripts/main.gd` |
| Quests | Rounded dark panel with objective and crafting progress | `frontend/godot/scripts/quest_panel.gd` |
| Exit and restart | Restart Game on the HUD; window close saves position before exiting a loaded world | `frontend/godot/scripts/main.gd` |
| Assets | SVG item icons; no bundled custom font found | `frontend/godot/assets/items/` |
| Layout | 1280 × 720 reference viewport with `canvas_items` stretching | `frontend/godot/project.godot` |

The UI is primarily constructed in scripts. Styling is repeated across those scripts, so establish a shared Godot Theme before rebuilding individual controls.

## 1. Typography and shared visual language

Use a readable, blocky pixel-style font throughout the UI. Favor strong square letterforms, open counters, and clear punctuation. Use sentence case for dialogue and item descriptions; reserve uppercase for short headings. Avoid ornate lettering for body copy.

Select the actual font during the first visual sample. Bundle the font and its redistribution license locally. Verify lowercase, numerals, apostrophes, quotation marks, ellipses, arrows, and any symbols used by existing UI strings. Define an explicit fallback for unsupported generated text.

Starting sizes at the reference viewport:

| Use | Proposed size |
| --- | --- |
| Dialogue body and input | 22 px |
| Buttons and item details | 20 px |
| Speaker names and panel titles | 26 px |
| Stack counts and secondary hints | 18 px |

Tune these sizes to the chosen font's native pixel grid. Keep text crisp at the supported window sizes; check font import settings separately from texture filtering. Provide a larger-text option, with wrapping and panel growth rather than clipping.

Starting visual tokens:

| Token | Value | Use |
| --- | --- | --- |
| Ink | `#302419` | Text on parchment |
| Parchment | `#EAD7AB` | Dialogue and details surfaces |
| Parchment shade | `#C4A675` | Inset edges and separators |
| Wood | `#70482C` | Outer frames and buttons |
| Dark wood | `#3A281E` | Outlines and recesses |
| Brass | `#D6AD55` | Selection and small accents |
| Moss | `#68764C` | Secondary accents |
| Error | `#8E352C` | Error text paired with a label/icon |

Use 4 px spacing increments, 16–24 px panel padding, and stepped or square corners. Build reusable frame, button, focus, input, tooltip, and slot styles. Check contrast in the rendered sample before treating these colors as final. Focus and selection must have visible outlines or markers, not just color changes.

## 2. RPG dialogue bubbles

Confirmed layout: a portrait and text box along the bottom, with a small speech tail pointing toward the speaker. Use a speaker nameplate and a parchment surface with a stepped border. This gives long generated responses a predictable readable area.

Position the tail along the upper edge toward the active speaker's screen position, clamped away from panel corners. Keep it short so it suggests direction without crossing the village view. Update the portrait and name together whenever the active utterance changes speaker; hide the directional tail for system notices or when the speaker is off-screen.

Proposed bottom-box layout at 1280 × 720:

- 24 px safe margin around the screen; approximately 220–260 px tall during conversation.
- Portrait/emblem area around 80 × 80 px, speaker name above the text.
- One active utterance with wrapped text; long replies continue over readable pages.
- A compact reply input and Send button beneath the utterance.
- History, Supplies, and Close controls as secondary actions.

Conversation flow:

1. Approach a villager and press E. Open the conversation and clearly identify that NPC.
2. Type freely as today. Enter submits only when the input has focus and a request is not pending.
3. Display the submitted player message with a player label. While waiting, show a restrained “Waiting for [name]…” status rather than fabricated NPC speech.
4. Present the returned NPC response in the active bubble. Optional typewriter reveal runs locally after the full response arrives, with an instant-text setting.
5. A dedicated Continue control reveals the rest of a page, then advances to the next page. Do not consume typing or submit another request while advancing text.
6. History opens a scrollable view of labeled player/NPC bubbles for this NPC. Restored history appears instantly without replaying animations.
7. Escape opens the game menu above the conversation, preserving the current page and unsent reply. Resume or Escape returns to the conversation and restores focus.

Show system notices and failures as distinct notices, not as NPC utterances. Retain a failed message for manual retry; never automatically repeat a transfer. Move Clear chat into the history view and retain its existing explanation about clearing conversation and memories.

Supplies opens a compact inventory overlay associated with the active speaker. Requesting an item retains the current purpose-confirmation conversation; gifting retains its current immediate transfer behavior. Keep the speaker's identity pinned while a conversation is open so nearby-NPC detection cannot silently change the recipient.

Pause player movement while conversation, history, or inventory controls own input. Backend requests and crafting timers continue. Closing a view must not cancel or duplicate a transaction; its eventual response still updates the correct NPC and world state.

## 3. Stardew-inspired inventory

Replace captioned cards with a framed grid of square slots. Emphasize icons, small stack counts in the lower-right corner, and a clear selected-slot outline. Use a recessed warm slot fill inside a wood frame. Put the full selected item name and action in a details area beneath the grid; show names on hover and keyboard focus as well.

Proposed starting layout:

- Centered satchel panel with title, Close button, slot grid, and selected-item details.
- Eight columns of 64 × 64 px slots with 8 px gaps at the reference viewport.
- Two visible rows initially, including decorative empty slots; scroll for additional rows.
- One slot per distinct item type, preserving current duplicate-item stacking.
- 48 × 48 px icon area inside each slot; count only when greater than one.
- Unknown items receive a placeholder icon and their readable name.
- Empty slots cannot be selected. They do not imply a new inventory capacity limit.

Use the same slot component for player inventory and NPC supplies. The NPC view can use fewer columns to fit its overlay. Keep ordering stable across refreshes and preserve selection while the selected item remains owned. Clear selection and disable the action when the last copy disappears.

Actions remain explicit: “Give Wood to Craftsman” or “Request Wood.” Show the recipient beside the action. Disable unavailable or pending actions with an understandable reason. Update quantities only from authoritative responses; no visual reward before confirmation.

First pass retains current item artwork so layout can be reviewed independently. A follow-up art pass can replace smooth SVG illustrations with original pixel-style icons using a consistent grid, outline, palette, and scale. Do not assume nearest-neighbor filtering alone makes the existing artwork pixel art.

Drag/drop, equipment, a usable hotbar, sorting, item splitting, and capacity rules are outside this first pass. They would introduce additional behavior beyond the requested visual redesign.

## 4. HUD, quests, and layout

Shrink the persistent satchel status into a compact Bag control with count. Keep Quests and the nearby interaction prompt small enough that exploration remains the main view. Apply the shared theme to quest progress, restart confirmation, tooltips, loading states, and error notices.

Anchor controls to viewport edges and use containers for internal sizing. Avoid retaining the current collection of absolute panel coordinates. Conversation occupies the lower screen; inventory/history/supplies overlays must not obscure its active input unexpectedly. Allow only one such overlay at a time and restore focus to its opener when closed.

Check 1280 × 720, 1920 × 1080, and a compact 960 × 540 window. At compact sizes, reduce grid columns and allow vertical scrolling. At larger text sizes, reserve enough room for the input and actions; paginate dialogue based on available space. Mouse and keyboard should support every existing action; controller support is a separate scope decision.

### Escape game menu

Move Restart Game out of the persistent HUD into a small centered menu, opened with Escape. Add Quit Game alongside it. Use the shared wood/parchment frame, blocky font, and a lightly dimmed background.

Menu order:

1. **Resume** — close the menu and restore the previous view and keyboard focus.
2. **Restart Game** — open the existing confirmation explaining that quests, inventories, chats, and NPC memories will reset. Cancel returns to the menu; a successful restart dismisses the menu and returns to the fresh world.
3. **Quit Game** — save and exit the application through the same shared shutdown flow as the window-close control.

Escape opens this menu directly from exploration, dialogue (including a focused reply input), inventory, supplies, history, or quests. Preserve the underlying view and unsent text. Escape while the menu is open resumes; Escape inside restart confirmation cancels that confirmation first. Handle each key press once, ignore key-repeat events, and prevent input from reaching underlying controls. Panel Close buttons remain available for dismissing individual panels. Update the HUD hint to “Esc Menu.”

Focus Resume by default and support mouse, arrow/Tab navigation, and Enter activation. Block player movement and gameplay actions while the menu is open. Let backend requests, saves, and crafting deadlines continue; this menu does not pause authoritative world time.

Keep Restart Game disabled while loading, quitting, or an operation is pending, preserving existing restart protections. Quit Game enters a single shutdown state: block additional actions, show “Saving…” or “Finishing current action…”, wait for pending mutations, save the latest position, then exit. Repeated clicks must not duplicate requests. If saving fails, keep the application open and show a visible error in the menu with Retry and Back actions. Do not automatically retry an item transfer. Handle quitting during initial loading or connection failure without waiting indefinitely for a world that has not loaded; any already-dispatched mutation must still settle before exit.

Implementation should extract/reuse the existing window-close save flow in `main.gd` so both exit paths share pending-operation and save-failure behavior. Ensure the error remains visible in the menu instead of only in the underlying satchel label.

## 5. Implementation sequence

- [x] **UI-01 — Visual sample and assets.** Choose and license the blocky font. Build a sample with the confirmed bottom portrait/text box and directional speech tail, a reply input, and filled/empty/selected inventory slots. Review font readability, portrait treatment, and materials together.
- [x] **UI-02 — Shared theme.** Add a reusable Theme and frame assets; apply typography, buttons, inputs, tooltips, and focus styles across existing controls. Remove conflicting local overrides as each control migrates.
- [x] **UI-03 — Dialogue presentation.** Introduce reusable bubble presentation, active utterance/pages, history, and pending/error states. Preserve free-text submission, per-NPC history, transfer callbacks, and clear-chat behavior.
- [x] **UI-04 — Inventory slots.** Rework `item_grid.gd`, satchel layout, and NPC supplies around shared slot visuals. Preserve stacking, item identity, selection, and request/give actions.
- [x] **UI-05 — HUD and input integration.** Rework anchors, overlay coordination, movement gating, focus restoration, and quest styling in `main.gd` and `quest_panel.gd`. Add the Escape menu with Resume, Restart Game, and Quit Game; remove the HUD restart button, retain restart confirmation, and share the save-before-exit flow with window close.
- [x] **UI-06 — Validation and polish.** Capture representative screenshots, check compact/large-text layouts, and run the relevant gameplay smoke checks against a disposable world. Record results and any remaining visual issues here.

Suggested new resources under `frontend/godot/`: `themes/medieval_ui.tres`, `assets/fonts/`, `assets/ui/`, and reusable UI scenes/scripts where useful. These paths are proposals, not existing resources.

This is a presentation plan alongside [ui.dialogue_presenter](../tasks/ui-dialogue-presenter.md) and [ui.world_presenter](../tasks/ui-world-presenter.md). Completing this redesign does not complete those broader architecture task packets or introduce their future contracts implicitly. No backend schema or endpoint changes are planned.

## 6. Acceptance and verification

- [x] All player-facing controls use the blocky font or the defined fallback; no clipped names, counts, input text, or buttons.
- [x] Conversations read as RPG dialogue, with clear speaker identity, readable long replies, and accessible per-NPC history.
- [x] Active dialogue uses the confirmed bottom portrait/text box, with a short tail toward the visible speaker and no tail on system notices.
- [x] The satchel reads as an inventory grid: consistent square slots, prominent icons, corner counts, visible empty slots, and clear selection.
- [x] Hover, keyboard focus, selection, disabled, and pending states are distinguishable.
- [x] Typing movement keys or pressing Enter inside dialogue never moves the player or triggers unrelated world actions.
- [x] Opening/closing overlays, switching NPCs, and responses arriving after closure preserve the correct history and recipient.
- [x] Escape opens the small game menu from exploration and every UI view, including focused text input; Resume restores the prior view, unsent text, and focus without triggering world actions.
- [x] Restart Game appears in the menu, retains confirmation and pending-operation protection, and resets the world only after confirmation.
- [x] Quit Game and window close both wait for pending mutations and save the latest position before exiting; save failure keeps the game open with a visible retry path. Verify initial-loading exit and repeated quit inputs as well.
- [x] Request wood, explain its purpose, pick up string, give materials, craft the bow, and receive the reward all still work exactly once.
- [x] Saved inventory and histories restore after relaunch; clear-chat and restart retain their existing distinct effects.
- [x] Empty inventories, missing icons, large stacks, long item names, multi-page replies, connection failure, and failed transfers remain usable.
- [x] Screenshots cover exploration, conversation, history, inventory, NPC supplies, crafting, the Escape menu, restart confirmation, and an error state at the supported sizes.

Existing checks to revisit: `bow_quest_smoke.gd`, `persistence_smoke.gd`, and `grounded_chat_smoke.gd` under `frontend/godot/tests/`. Some directly read `dialogue_log.get_parsed_text()`; if the new UI replaces that widget, update the tests to inspect displayed conversation content through a stable presentation accessor. Retain assertions for restored text, responses, and restart clearing rather than removing them.

Use a disposable backend for mutation tests as described in the [README](../../README.md). Run rendered checks as well as automated checks: headless success cannot establish font readability or layout quality.

## Decisions still to refine

| Decision | Draft default |
| --- | --- |
| Overall mood | Warm, cozy medieval parchment and wood |
| Font | Bundled Pixelify Sans under OFL 1.1, explicit OS font fallback |
| Text reveal | Instant text with dedicated Continue pagination; typewriter deferred |
| Portrait artwork | Original block portraits, with speaker-specific coat colors and a system emblem |
| Inventory | Up to eight columns, two decorative rows, responsive scrolling |

## Implementation progress and evidence

Completed 2026-10-13. See [validation record and reproduction commands](../evidence/ui-rework/README.md).

| Task | Delivered | Evidence |
| --- | --- | --- |
| UI-01 | Pixelify Sans + OFL license, original block portraits, bottom parchment bubble/tail, slot sample | [Dialogue](../evidence/ui-rework/dialogue-1280.png), [slots](../evidence/ui-rework/inventory-1280.png), `assets/fonts/` |
| UI-02 | Reusable runtime Godot Theme in `scripts/medieval_theme.gd`: frames, focus, buttons, inputs, tooltips, progress, fallback font | Rendered samples at all three sizes; font fallback [sample](../evidence/ui-rework/dialogue-960-fallback.png) |
| UI-03 | Active utterance with font-measured pages, Continue, portrait/name/tail, labeled scrollable history bubbles, distinct pending/notices, retained failed input | [History](../evidence/ui-rework/history-1280.png), [chat error](../evidence/ui-rework/chat-error-1280.png); UI smoke and live chat suite |
| UI-04 | Shared 64px slots, stable alphabetical ordering and selection, corner counts, decorative empties, unknown placeholder, explicit give/request actions | [Supplies](../evidence/ui-rework/supplies-960.png), [large stack/unknown item](../evidence/ui-rework/inventory-edge-cases-1280.png); bow and UI smoke |
| UI-05 | Compact HUD, anchors, above-dialogue overlays, movement gating, pinned gift recipient, menu focus trap/restore, Resume/Restart/Quit, shared window-close shutdown/recovery | [Menu](../evidence/ui-rework/menu-1280.png), [restart](../evidence/ui-rework/restart-960-large.png), [save error](../evidence/ui-rework/save-error-1280.png); process exit tests |
| UI-06 | Rendered checks at 960×540, 1280×720, 1920×1080 plus larger text; gameplay, persistence and provider failure regression | 424 backend tests; 301/301 live grounded-chat checks; 22/22 provider-failure checks; 29/29 rendered UI assertions; bow, persistence and process-exit smoke checks passed |

Validation details:

- The rendered UI smoke checks actual Escape dispatch from focused input, inventory, history, supplies and quests; arrow navigation stays inside the menu. Resume restores focus and unsent input. Escape cancels restart confirmation before closing the menu.
- Long replies retain every character through pagination. Large stacks (1234), unknown icons, long names, empty slots, fallback glyphs, selection retention and selection removal were exercised. History is keyboard-scrollable; grids follow focused slots.
- A late gift response after closing its conversation updated that NPC's history and world inventory exactly once without changing the other NPC's unsent reply. Responses while the menu is open retain menu focus.
- Both exit paths use `_begin_shutdown()`. A real in-flight gift completed before exit, repeated quit/close inputs caused no duplicate gift, and read-only DB checks confirmed saved position (73,83). Actual failed position save kept the process open, with visible Retry/Back; Retry subsequently saved and exited. Initial loading quit cancels only the read-only GET and exits promptly.
- Bow checks retained purpose confirmation, F pickup, two immediate gifts, five-second crafting, and one reward. Persistence and live-provider checks retained restored histories and restart-clearing assertions using `conversation_text()`.
- Visual QA found and fixed pale input placeholders, container-stretched overlays, unsupported fallback glyphs, underlying HUD hints showing below dialogue, and menu Tab/arrow focus escaping to underlying controls.
- Screenshot coverage includes exploration, dialogue, history, inventory, supplies, crafting, completion, menu, restart confirmation and failures. The main panels have compact/reference/large captures; crafting is captured at reference size. [Larger-text compact sample](../evidence/ui-rework/dialogue-960-large.png).
- A preliminary mock-provider grounding run failed provider-dependent fact assertions; the configured llama3:latest rendered rerun passed all 301 checks. The mock run is not counted as grounding evidence.

No backend schema/endpoints or broader architecture packet status changed. The existing SVG item art remains deliberately unchanged. Instant text is the shipped default; optional typewriter reveal and a future bespoke item-art pass are deferred. OS fallback coverage depends on installed fonts; tested macOS fallback renders accented Latin, arrows and Chinese. No remaining blocking visual issues were found in the supported rendered layouts.
