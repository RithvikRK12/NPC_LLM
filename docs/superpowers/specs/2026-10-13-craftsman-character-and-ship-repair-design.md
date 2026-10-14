# Craftsman: character, workshop life, and shipwreck encounter

Date: 2026-10-13  
Status: Design proposal for discussion; gameplay is not implemented by this document.

## 1. Intent and scope

The Craftsman should feel like a person the player can get to know: someone with his own working rhythm, an interest in the player's circumstances, and the ability to act on an offer of help. Crafting and the bow quest remain part of his life, but no longer define every conversation.

The central experience is a small relationship arc. The player meets him in his workshop, tells him about the wreck, leads him down to the shore, watches him assess the damage, and receives a concrete path toward getting home. He then returns to work without requiring the player to escort him back.

### Requested behavior

- Alternate between walking and idling inside the workshop.
- On the first workshop entry, automatically walk the player over to him and introduce him through a cutscene, in the spirit of the fisherman encounter.
- Allow broader, more natural conversation beyond crafting and the bow.
- Respond sympathetically to a request for help with the player's wreck and offer to inspect it.
- Follow the player with physical collision and obstacle-aware movement.
- At the wreck, stage both characters closer to the ship and play scripted dialogue.
- Automatically begin a ship-repair quest with an initial material list.
- Say he is returning to the workshop, walk back, and resume his routine.
- Reserve completion of this overarching quest as the eventual end-of-game milestone.

### Proposed defaults, open to revision

The wreck-and-help request is sufficient to start the outing after the Craftsman's response finishes; an extra confirmation choice is unnecessary. The player can nevertheless say “not now” or ask him to wait. The bow is optional and does not gate ship repair. The Craftsman is warm, practical, curious, and quietly humorous. Following uses a flexible distance band, rather than an absolute geometric constraint.

This design specifies the introduction, outing, inspection, quest activation, return, and conversation changes in detail. Material acquisition, the actual repair sequence, sailing, and the ending cinematic remain later work. Requirements below are proposals, not claims about existing functionality.

## 2. Existing implementation and implications

Paths in this section are relative to the repository root and were inspected while preparing this proposal.

| Existing code or content | Observed behavior | Design implication |
| --- | --- | --- |
| `frontend/godot/scripts/npc.gd` | NPC extends `Area2D`; no movement controller | A sensing area alone cannot provide the requested walking body. Add a physical actor and retain a separate interaction area. |
| `frontend/godot/scripts/player.gd` | Player uses `CharacterBody2D`, speed 180, and `move_and_slide()` | Use equivalent world collision rules for the Craftsman. |
| `frontend/godot/scripts/person.gd` | Supports directional idle/walk frames and derives movement from a `CharacterBody2D` parent | Reuse the existing visual movement system. Additional work gestures are optional. |
| `frontend/godot/scripts/fisherman_encounter.gd` | One-time presentation scoped to the run, local grid routing, collision-aware automatic approach, and input ownership | Reuse the encounter pattern, while giving the Craftsman separate state and dialogue. The fisherman currently cancels on unexpected obstruction; improve recovery for the new encounters. |
| `frontend/godot/resources/building_interiors.json` | Workshop has furniture, a spawn point, and an origin at `(10000, 10000)` | Interior and exterior require explicit portal traversal; they are not adjacent walkable spaces. |
| `frontend/godot/scripts/main.gd` | Coordinates player travel, camera, NPC interaction, dialogue, and bow UI | Add small dedicated controllers; avoid placing every new behavior in this file. |
| `frontend/godot/scripts/world_layout.gd` | Walkability includes furniture, scenery, coast obstacles, and actor-foot clearance | Routing and physical collision must agree on the same geometry. Avoid inflating clearance twice. |
| `backend/app/services/prompts/builder.py`, `context/social.py`, `validation/service.py` | Social conversation is narrowly classified; world answers select facts; social prose rejects many crafting/world terms | Broader character dialogue requires coordinated classification, prompt, context, and validation changes. A personality prompt alone will not work. |
| `backend/app/services/quests/bow.py` | Broad words such as “quest,” “craft,” and “materials” can route to bow dialogue; crafting consumes NPC inventory and later sets him to `available` | Resolve conversation focus before quest routing. Separate movement mode from crafting-job state. |
| `backend/app/services/validation/quest_dialogue.py` | Contains an axe-oriented generic requirements helper | Audit callers and competing responses so “What do you need?” consistently refers to the intended task. |
| `frontend/godot/scripts/quest_panel.gd` | UI is specialized for “Get a bow” | Add a main-quest entry without replacing or resetting the bow quest. |
| `backend/app/models/quest.py`, `models/bow_quest.py` | Legacy quest has one row per player; bow has a dedicated model | A second story quest needs an explicit storage decision; it cannot simply be another legacy row with the same player. |

## 3. Character direction

### Personality

He expresses care through attention and useful action. He hears the distress before discussing repairs. His experience gives him confidence with tools, but he does not promise that a wreck is seaworthy before examining it.

He enjoys understanding how things are made and why people value them. He can talk about patience, repair, work, the player's travels, uncertainty, home, and ordinary village life. His humor should be gentle and occasional. He need not turn every subject into a woodworking metaphor.

Suggested character anchors to author as stable facts:

- He prefers repairing useful things to discarding them.
- He finds familiar workshop sounds comforting.
- He takes pride in careful work more than praise.
- He is curious about places beyond the village but attached to his workshop.
- He dislikes careless promises and will admit when he needs a closer look.

These are proposed characterization, not existing lore. Keep his name as “Craftsman” until a personal name is chosen. Do not invent relatives, major past events, or other villagers ad hoc in generated conversation.

### Voice and conversational behavior

Default to one to three natural sentences. Allow a longer answer when the player asks for a story or explanation; split it into readable dialogue beats if needed. Ask at most one relevant follow-up question, and do not end every response with a question.

Respond to what the player means before offering a task. A frightened player deserves reassurance, not an inventory checklist. A question about his interests deserves an answer, not a bow objective. Relevant remembered details can make later conversations warmer without forcing the player through the same introduction.

| Player | Illustrative response |
| --- | --- |
| “Do you enjoy working here?” | “I do. Something comes in broken, and sometimes it leaves useful again. That's a good day's work to me.” |
| “I don't know if I'll ever get home.” | “That's a heavy thought to carry alone. We can start with what is in front of us—you needn't solve the whole journey tonight.” |
| “What do you do when you're not working?” | “Sometimes I sit here and enjoy the quiet. A workshop sounds quite different when nobody is hammering.” |
| “I miss the sea already.” | “Even after what happened? I suppose a place can frighten you and still feel like home.” |
| “Can you repair my ship?” before inspection | “I'll need to see the damage before I can promise anything. Show me where she came ashore.” |
| “What do you need?” after inspection | Use the authoritative ship-repair list and remaining quantities, with warm introductory wording. |

The sea response requires an established wreck conversation. Do not act as though the Craftsman witnessed the opening sequence or heard the player's conversation with Rowan.

### Freedom with reliable facts

Use three cooperating conversation paths:

1. **Character conversation:** generated language grounded in authored personality, known lore, and relevant memories. Include feelings, work, values, and reflective questions.
2. **World and quest information:** authoritative facts supply requirements, delivered quantities, current location, inspection status, and completion. Natural framing can surround these facts without changing them.
3. **Action requests:** resolve and validate an explicit intent, then execute an allowed command. Generated promises alone never move an NPC, consume an item, or complete a quest.

Mixed messages need mixed responses. “I'm scared, and my ship is wrecked—can you help?” should receive empathy and the inspection offer in one turn. It should not be forced into either a tiny social category or an unrelated bow answer.

Replace coarse topic-word bans with validation that distinguishes harmless craft discussion from unsupported claims about ownership, delivery, action, or completion. Preserve factual grounding, action permissions, and memory provenance. A player saying “I already brought everything” is a claim to check, not a state update.

## 4. Recommended movement and encounter approach

| Approach | Advantages | Limitations |
| --- | --- | --- |
| Fully authored paths for all movement | Predictable staging and simple authoring | Cannot follow arbitrary player detours well; blocked routes become brittle. |
| Fully dynamic navigation everywhere | Flexible following and destination selection | More tuning and less predictable cinematic composition. |
| **Authored destinations and route landmarks with dynamic local routing** | Reliable workshop activity and cutscene staging, flexible following, predictable return | Requires both a small landmark graph and reusable local routing. |

Use the third approach. Choose meaningful destinations, find collision-clear paths between them, and physically walk the actors along those paths. A small explicit state machine is sufficient; a general behavior-tree framework is unnecessary for this scope.

The existing local `AStarGrid2D` approach is a useful starting point. For long travel, use a coarse route graph with bounded local searches rather than one huge search across exterior and remote interior coordinates. Exact grid size and search budgets should be measured during implementation.

## 5. Workshop routine

Author a small set of reachable standing points beside the main bench, side bench, shelf, and timber stack. These are interaction positions beside furniture, not furniture centers. Validate each against the current footprint geometry. Keep the door and entrance corridor clear.

Suggested tuning values, all provisional:

| Setting | Initial value |
| --- | --- |
| Idle or work pause | Randomized 5–12 seconds |
| Ambient walking speed | 75 world units/second |
| Destination selection | Weighted toward benches; avoid immediate repetition |
| Conversation distance | Approximately 64–96 world units, with clear approach space |

Idle can initially mean standing and facing his work; tapping, inspecting, or reaching gestures can be added later. He should spend more time appearing settled than pacing. Randomization should vary timing without making him look distracted.

When conversation begins, stop safely, face the player, and suspend ambient destination selection. Resume after dialogue closes, with a short pause before moving. Introduction, following, inspection, and return always override the ambient routine. A global pause freezes movement; ordinary off-camera travel continues.

## 6. First workshop entry

### Trigger and preparation

Trigger after the player's first successful entrance into the workshop, once the travel fade finishes and the world is ready. Scope the flag to the current game run. Do not launch during another cutscene, loading, or a modal interaction.

1. Pause the Craftsman's routine at his current safe position.
2. Select a reachable conversation position near him. If his current position is unsuitable, move him to an authored greeting point first.
3. Acquire encounter control of player movement and camera.
4. Walk the player to the conversation position using physical movement and routing.
5. Turn both actors toward each other, settle the camera, and play the introduction.

Use the fisherman's automatic approach as the interaction precedent, while keeping the Craftsman's free-form conversation available afterward. Do not snap the player across furniture or freeze them indefinitely if the approach fails.

### Suggested introductory beats

**Craftsman:** “Oh—hello there. Come in. Mind the timber by the door.”

*He puts his work aside and turns toward the player.*

**Craftsman:** “You've had a difficult journey, by the look of you. Take a moment. What can I do for you?”

After Continue, hand over to the normal conversation interface. The player can talk about anything; the introduction does not automatically start the bow or ship quest.

Mark the introduction complete after its final beat, or after a deliberate skip. If interrupted by quitting or an unrecoverable route failure before that point, retain it as pending. Skipping restores control and offers ordinary conversation from the current safe position; it does not teleport the player or manufacture story progress. Later workshop visits use normal interaction and never replay the introduction.

## 7. Recognizing the wreck request

The intended trigger is a request for help with the player's damaged ship, including multi-turn context.

Examples that should qualify:

- “My ship wrecked, and I need help.”
- “I washed up on the beach. Can you look at my boat?”
- “The storm broke my ship.” followed by “Could you help me fix it?”
- “Can you come and inspect the wreck with me?”

Examples that should not automatically start following:

- “Do ships often wreck here?”
- “Imagine your boat sank.”
- “My ship wrecked, but I don't want to go back yet.”
- A quotation of somebody else's request.
- A repeated request after the ship has already been inspected.

If the player reports the wreck without asking for help, he can offer to inspect it, but should wait for agreement before following. Explicit requests for help with the wreck authorize the outing by default. Unclear ownership or hypothetical language calls for one short clarification.

### Acceptance line and action

> “Oh no, that's very unfortunate. I'm glad you made it ashore. Can I see the ship so I can work out what I can do? Lead the way.”

Resolve the intent into a proposed `begin_ship_inspection` command. Validate the game scope, NPC identity, conversation, encounter phase, and availability. Persist the accepted outing before displaying an unconditional “Lead the way.” Begin walking once the response has finished and the conversation closes.

If the player answers “not now,” cancel departure or suspend the outing without starting the repair quest. If a bow-crafting job is already underway, acknowledge the request and wait for that short job to finish before departing. Revalidate availability after waiting.

A network failure must not leave him promising to follow while standing immobile. Retry the command safely, or present a short failure message with control restored. Provide a grounded authored acceptance response if generated dialogue is unavailable.

## 8. Following the player

### Physical actor

Give the Craftsman a `CharacterBody2D` root with a foot collision shape consistent with the player's, plus a child interaction `Area2D`. Preserve his NPC identity and interaction behavior. Walk through the physics movement API; do not animate world position directly through obstacles.

World collision is required for walls, benches, trees, rocks, coastline boundaries, and the hull. Actor-to-actor collision is a separate tuning choice: initially allow player/Craftsman overlap at the collision-mask level, while steering for visible spacing. This avoids making a narrow doorway impossible to cross. Physical blocking between the two can be added later if it improves play.

### Follow distance

An absolute radius cannot always coexist with collision-safe detours: the only route around a large obstacle may briefly take him farther away. Treat the radius as a target and a recovery signal.

| Parameter | Initial proposal |
| --- | --- |
| Desired trailing distance | 64–96 units |
| Stop within | 64 units along an accessible approach |
| Resume pursuit beyond | 96 units |
| Normal follow speed | 180 units/second, matching the player |
| Catch-up speed | Up to 210 units/second when separation exceeds 160 units |
| Separation warning | Beyond 240 units for several seconds |
| Repath cadence | Around 0.4 seconds, or sooner when the route becomes invalid |

These thresholds apply within a navigation space, not across interior/exterior coordinates. Use route distance or reachability as well as straight-line distance; being close through a wall does not mean he has caught up.

Track recent reachable player positions and follow toward an appropriate trailing point. Smooth changes in destination, avoid cutting diagonally through obstacle corners, and replan when a target is stale. Never push either actor through collision to preserve the follow band.

If he falls behind, show a discreet “The Craftsman is catching up” hint. If blocked, replan and try a nearby reachable approach. After repeated failure, have him stop safely and call for the player to return. Preserve the outing; do not silently abandon it, teleport him, or start the inspection remotely.

### Doors and detours

The Craftsman must first walk to the workshop exit. Traverse the existing interior/exterior portal with explicit actor support, then continue following outside. Portal relocation is an authored world transition, not an obstacle-bypassing recovery trick. Use separate clear arrival positions so he does not appear on top of the player.

For workshop departure, briefly stage both actors at the exit and use the travel fade to present a coherent shared transition. For his later solo return, portal traversal must work without moving the player or taking over the player's camera.

During the outing, if the player enters an unrelated cottage, he waits outside its entrance and resumes when they return. The distance check pauses across that portal. If the player returns to the workshop, he may follow back inside; the outing remains pending until resumed or explicitly postponed.

“Wait here” pauses pursuit at a safe nearby location. “Let's go” resumes it. “Go back to your workshop” ends the current outing and starts return travel, with a later opportunity to ask again. Normal dialogue pauses movement; closing it resumes the previous mode.

## 9. Shipwreck cutscene

### Trigger

Add a dedicated inspection arrival area near the existing southern wreck. Do not reuse the opening recovery trigger. The scene may begin only when:

- An inspection outing is active and the wreck has not been inspected.
- Both actors are in the beach navigation space and within the staging area.
- Both can reach their distinct inspection marks.
- No other encounter or modal conversation owns control.

The player arriving alone is insufficient. If the Craftsman is still catching up, keep player control and wait. Re-entering the trigger cannot launch a second instance.

Author markers such as `InspectionArrival`, `InspectionPlayerMark`, `InspectionCraftsmanMark`, and `ReturnRouteStart`. Existing `HullExit`, `ControlHandoff`, and `SafeFallback` markers provide spatial context, but their suitability for a two-person scene must be checked in game. Exact new coordinates require visual staging and collision checks.

### Beat sheet

| Beat | Movement and framing | Scripted dialogue or effect |
| --- | --- | --- |
| Recognition | Pause following; frame both actors and the damaged hull | “There she is. Let's have a closer look.” |
| Approach | Acquire control; walk both actors toward separate clear marks nearer the ship | Let the line lead into visible movement. Wait for both arrivals before the assessment. |
| Inspection | Player stops; Craftsman faces the hull and pauses | “The planking's split, and those seams won't keep the sea out. But there's something here worth saving.” |
| Hope | Craftsman turns partly toward the player | “I think I can make her seaworthy again. It'll take sound timber, rope, and something to seal the hull.” |
| Requirements | Present the authoritative material list | “Bring me twelve sound planks, three coils of rope, two bundles of sailcloth, and two pots of pitch. That should give us a start.” |
| Quest activation | Commit the inspected state and new quest together; show a small quest notification on success | **A Way Home — Gather the ship-repair materials.** |
| Departure | Craftsman turns toward the inland route | “I'll head back to my workshop now. Bring what you find there—we'll take this one step at a time.” |
| Handoff | Release player and camera control; begin independent return travel | Player can stay at the wreck, follow, or explore. |

Dialogue advances on Continue, not a short forced reading timer. The material sentence should be formatted from the same recipe data as the quest UI so later tuning cannot produce conflicting numbers.

### Interruption and skip

If staging fails, restore control and leave the inspection pending. If the scene is skipped after valid staging, commit the same inspection result and material list, show the quest notification, and proceed to return travel. Skipping presentation must not skip the story state change.

At the quest-activation beat, a failed request restores control and leaves a resumable pending completion. Do not announce quest success before confirmation. A retry continues from the outcome beat rather than replaying the whole walk. If the server committed but the reply was lost, fetch the existing outcome and continue without creating a second quest.

## 10. Overarching quest: A Way Home

### Initial definition

| Field | Proposal |
| --- | --- |
| Quest ID | `ship_repair` |
| Display title | A Way Home |
| Category | Main story |
| Start | Automatically upon committed ship inspection |
| Initial objective | Gather the materials and bring them to the Craftsman's workshop |
| Eventual completion | Ship repair finishes; emit a one-time story-completion signal |

Use a separate encounter record for the journey before inspection. An escort hint can say “Lead the Craftsman to your ship” without prematurely creating the material-gathering quest.

### Provisional materials

| Item ID | Display name | Quantity | Purpose | Proposed future source |
| --- | --- | ---: | --- | --- |
| `ship_plank` | Sound timber plank | 12 | Replace damaged hull boards | Timber gathering and processing, or salvage |
| `rope` | Coil of rope | 3 | Replace damaged rigging and lashings | Beach salvage plus additional supplies |
| `sailcloth_bundle` | Bundle of sailcloth | 2 | Patch the sail | Recoverable cloth or a later village supply interaction |
| `pitch_pot` | Pot of pitch | 2 | Seal hull seams | A later resource or crafting interaction |

The quantities are deliberately arbitrary starting values. The beach already has a rope salvage point, but the full sources, yields, and three new item types are not implemented by this proposal. Do not tell the player an unimplemented source exists. Before making the quest completable, guarantee that sufficient materials can be obtained and that losing an item cannot permanently exhaust the world's supply.

Use ship-specific planks to reduce accidental overlap with bow wood. The Craftsman's starting rope and tools do not automatically count as player contributions. A source must transfer an owned quantity through a real operation; conversation about giving something is insufficient.

### Quest lifecycle

`not_started → gathering_materials → ready_for_repair → repairing → completed`

Only `gathering_materials` needs to be reached by the encounter work. The later states reserve a clear contract for future development. Possessing the full list is not the same as completing repair or ending the game.

When deliveries are implemented, persist contributed counts per item. Atomically remove the accepted quantity from player inventory and add it to this quest's contribution ledger. Cap contributions at the remaining requirement and leave excess items with the player. Duplicate requests must not consume items twice.

The current inventory representation uses string lists, so quantities need an explicit adapter or count-aware inventory change. Do not silently mix new dictionary quantities with consumers expecting strings. General transfer into NPC inventory must not accidentally feed both bow crafting and ship repair.

The final repair-completion transaction should mark the quest complete and emit a durable, deduplicated `main_story_completed` event. The ending presentation consumes that event later. It should not exit the application or trigger from an LLM claim, a full inventory, or the inspection itself.

### Coexistence with the bow

Keep the bow independently playable. While following or returning, he can discuss it, but new hands-on crafting waits until he reaches the workshop. An existing short crafting job finishes before departure. Crafting completion must not overwrite escort or return state with a generic `available` value.

“What materials do you need?” follows the active conversational topic. If both quests are plausible and neither is in focus, ask “For the bow, or for your ship?” Explicit “ship” and “bow” requests always select the named quest.

## 11. Returning to the workshop

After the farewell, select a fixed chain of authored route landmarks: wreck approach → inland beach route → village approach → workshop exterior entrance → workshop interior arrival → preferred work position. Validate the actual connections against the current map before assigning coordinates.

Each segment uses collision-aware routing, so a fixed route defines destinations rather than allowing him to walk through anything between them. He walks at approximately normal player speed, without a follow-distance constraint. He does not reverse direction to chase the player after saying goodbye.

Return continues when he is off camera. If the player speaks to him along the way, pause, face them, answer, and resume the same journey afterward. On arrival, enter the workshop through the portal, walk to a work point, and resume the idle/walk rhythm. The player need not accompany him.

If blocked, replan the current segment and try an alternate reachable landmark. If no path exists, wait safely and expose his current whereabouts through the journal or interaction hint. Never claim he has arrived while his actor remains stranded. A map-load recovery may relocate an invalid saved position to a documented safe point, but routine navigation failures do not justify visible teleportation.

## 12. State, ownership, and persistence

Separate three kinds of state:

- **Story progression:** introduction completion, outing acceptance, inspection completion, ship quest and contributions.
- **Activity:** ambient work, following, waiting, returning, or a crafting job.
- **Presentation:** camera framing, input ownership, current line, and temporary staging paths.

Suggested encounter states:

| State | Entry | Exit |
| --- | --- | --- |
| `workshop_routine` | Initial load or completed return | Introduction, conversation, or accepted outing |
| `workshop_intro` | First eligible workshop entry | Complete/skip to conversation; failure leaves intro pending |
| `departure_pending` | Accepted outing with dialogue or work still active | Following when ready; postponement returns to routine |
| `following_player` | Departure ready or wait resumed | Wait, inspection staging, or explicit return request |
| `waiting_for_player` | Player asks him to wait or enters unrelated interior | Resume follow or return |
| `inspection_staging` | Both reach arrival area | Inspection dialogue, or recoverable route failure |
| `inspection_dialogue` | Both reach valid marks | Committed quest outcome and return |
| `returning_to_workshop` | Inspection farewell or outing postponed away from home | Workshop routine |

Conversation is a temporary overlay that retains the previous activity. A single encounter owner controls input and camera; ambient routines, player input, and scripted movement must never independently drive the same actor in the same frame. Release ownership on every success, skip, failure, load, and cancellation path.

Persist run scope, story phase, introduction flag, NPC navigation space and safe position, movement mode, waiting location when relevant, return landmark index, inspection outcome ID, quest phase, and contributed counts. Use stable markers and recompute paths on load; do not persist fragile path arrays. The backend owns durable quest/encounter outcomes; the frontend owns moment-to-moment movement and reports validated transition checkpoints.

Commands should carry run scope and an idempotency key. Reject stale responses after New Game. Validate encounter prerequisites and reported actor locations before recording inspection completion. Commit inspection completion and quest activation atomically.

On load, restore a safe actor position and resume the saved activity. An interrupted introduction restages if not complete. An interrupted inspection resumes its uncommitted beat; a committed inspection resumes return without replaying quest activation. New Game resets all Craftsman flags and quest state with the existing game scope.

Record separate memories for “player reported a wreck,” “Craftsman agreed to inspect,” and “Craftsman inspected the ship.” Only the latter establishes firsthand knowledge of damage. Durable state takes precedence over remembered dialogue when they disagree.

## 13. Suggested implementation boundaries

These are proposed responsibilities, not existing APIs or a step-by-step implementation plan.

| Component | Responsibility |
| --- | --- |
| Craftsman activity controller | Workshop routine, follow/wait/return modes, safe interruption and resumption |
| Shared actor routing helper | Walkable paths, physical progression, stuck detection, arrival reporting |
| Portal traversal support | Interior/exterior transition for either actor, including solo NPC travel |
| Craftsman encounter controller | Workshop introduction, wreck staging, scripted beats, input/camera ownership |
| Character profile and conversation context | Stable personality, knowledge, relevant memories, current topic |
| Intent and command handling | Validate inspection, waiting, resuming, and return requests |
| Ship-repair domain service and storage | Atomic inspection outcome, material requirements, future contributions and completion |
| Quest presentation | Main quest alongside bow, escort hint, material counts, and current Craftsman whereabouts |

Keep structured movement outcomes separate from dialogue text. Update NPC location facts and the current hard-coded “Workshop” label when he is on the road or beach. Existing proximity, direction, and interaction checks must use the actor's real position.

## 14. Delivery slices

1. **Workshop presence:** physical NPC movement, safe activity points, idle/walk animation, interruption by conversation.
2. **First meeting:** one-time automatic approach, introduction, skip and recovery.
3. **Broader character dialogue:** profile, topic handling, grounded conversational freedom, contextual wreck intent.
4. **Outing:** accepted departure, following, obstacle routing, portals, wait/resume, and independent return.
5. **Inspection and quest:** two-actor staging, authored dialogue, atomic quest activation, journal presentation, restart recovery.
6. **Later story completion:** material sources and counted deliveries, repair sequence, completion signal, ending presentation.

Each slice should preserve the prior playable experience. This document does not require building the final ending now.

## 15. Acceptance and review scenarios

| Scenario | Expected result |
| --- | --- |
| Observe workshop for two minutes | Several natural pauses and walks; no furniture clipping or blocked entrance. |
| First entry while he is moving | Routine yields; player walks to a reachable conversation position; introduction plays once. |
| Re-enter or reload after introduction | Normal interaction; no repeated forced approach. |
| Skip or fail introduction staging | Control and camera restore; skip marks seen, failure leaves it pending. |
| Ask about his interests, then discuss loneliness | Relevant character conversation without an unsolicited bow pitch. |
| Report wreck and ask for help across two turns | He connects the context, responds sympathetically, and follows after dialogue. |
| Mention a hypothetical wreck or say “not now” | No unwanted departure. |
| Repeat an accepted inspection request | No second outing or duplicate command effect. |
| Lead around bench, trees, rock, and coastline | Actual physical walking; routes avoid obstacles and corner clipping. |
| Leave workshop, enter cottage, then return outside | Correct portal handling; he waits outside the unrelated cottage and resumes. |
| Outrun or obstruct him | Catch-up/replanning and useful feedback; no forced teleport or remote inspection. |
| Reach wreck without him | Cutscene waits until both actors are eligible. |
| Reach wreck together | Both auto-walk closer, remain outside hull collision, and receive the full scene. |
| Skip inspection or lose activation response | Exactly one quest outcome; safe retry/load behavior. |
| Leave him after farewell | He reaches workshop independently and resumes his routine. |
| Talk during return | Conversation pauses travel; closing resumes return. |
| Request ship materials while bow is active | Correct quest focus and consistent requirements. |
| Bow job completes around departure | No lost reward and no movement-state overwrite. |
| Claim all materials were delivered | No inventory, contribution, or completion change without verified transfer. |
| Reload during follow, inspection, or return | State resumes coherently with no duplicated introduction or quest. |
| Start New Game while a request is pending | Old response cannot modify the new run. |

For implementation, combine focused state/command tests with in-game observation of animation, collision, camera framing, and long-route recovery. Exercise the full path from first workshop entry to his return; backend tests alone cannot verify the encounter feels right.

## 16. Topics for the next character discussion

No answer is needed to use this document as the initial proposal. The most useful refinements are:

- Whether his warmth should feel fatherly, companionable, or reserved until trust grows. Current proposal: companionable and practical.
- Whether he should have a personal name and a modest authored backstory. Current proposal: retain “Craftsman” and use the character anchors above.
- Whether the player should explicitly say “follow me” after his offer. Current proposal: a direct wreck-and-help request starts the outing; a bare report waits for agreement.
- Whether the repair should feel like a short final objective or a long journey through the island. Current proposal: preserve the overarching role and postpone balance and ending details.

The test for the character is simple: after this encounter, the player should remember a person who listened, came along, and helped them find a way forward.
