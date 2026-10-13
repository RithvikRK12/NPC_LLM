# Old Fisherman — Static Dialogue Tree

## Purpose

Introduce the village after the player survives the crash, using a traditional NPC with fixed dialogue and exactly two player choices at each dialogue step. This encounter provides a clear comparison with the village's Gen-AI NPCs: the fisherman repeats authored responses, cannot accept free-form questions, and does not remember what the player has already told him.

The fisherman should feel believable on the first conversation. His limitations become apparent when the player follows another branch or speaks to him again.

## Character and encounter

- **Name:** Rowan, the old fisherman (working name).
- **Location:** On the existing fallen log beside the path near the village entrance, sitting with a fishing net across his knees.
- **Personality:** Weathered, plain-spoken, initially surprised, then sympathetic.
- **Movement:** Remains in place; no escort, patrol, or navigation behavior.
- **Introduction:** Entering a 10-meter radius triggers a brief cutscene in which he looks up from his net. The conversation opens at `F00`.
- **Repeat interaction:** The proximity cutscene plays once. Later interactions open `F00` directly.
- **Interaction style:** Two fixed dialogue choices; no text or voice input.
- **Exit:** A separate Close/Back control is always available. Closing is a UI action, not a third dialogue choice.

### Fallen-log seat

Rework the fallen log shown beside the path into a believable seat while preserving its weathered, natural appearance and pixel-art style.

- Thicken the trunk slightly and give its upper surface a broad, relatively level section wide enough for Rowan to sit on.
- Trim the upward-pointing branch at the seating position into a short broken stub away from his body. Keep a few irregular ends and bark details so it still reads as a fallen tree.
- Clear foliage from the seating surface and the space immediately in front of it. Moss and small plants can remain around the ends and behind the log.
- Pose Rowan facing toward the path, with his hips resting on the trunk, knees bent, and feet on the ground in front. His fishing net rests across his lap.
- Layer his torso above the log and his lower legs in front of it; avoid the appearance of standing inside or floating over the trunk.
- Keep the path and player approach clear. The log's collision footprint should cover its grounded trunk without preventing the player from approaching the seated fisherman.
- Rowan remains seated during the introduction and all dialogue. He only looks up or turns his head toward the player; he does not stand or walk.

### Gameplay camera framing

Increase world camera magnification by 50%: change the Camera2D zoom from `(0.5, 0.5)` to `(0.75, 0.75)`. The player and scenery appear 1.5 times as large at the same window size, with approximately two-thirds of the previous world span visible in each dimension. The opening cinematic also uses this world camera, so its shots should be reviewed at the closer zoom.

## Depth and reset rules

**Depth three means three player selections from the opening message.** The opening is depth zero. After the third selection, Rowan delivers a final response; Continue closes the dialogue. Pressing E near Rowan opens the exact opening message and its original two choices again.

```text
F00: opening                                     [selection 1]
├── F10: where am I?                              [selection 2]
│   ├── F20: how to reach the village             [selection 3]
│   │   ├── E01 → Close
│   │   └── E02 → Close
│   └── F21: who lives here                       [selection 3]
│       ├── E03 → Close
│       └── E04 → Close
└── F11: can you help me?                         [selection 2]
    ├── F22: somewhere warm                       [selection 3]
    │   ├── E05 → Close
    │   └── E06 → Close
    └── F23: the wreck                            [selection 3]
        ├── E07 → Close
        └── E08 → Close
```

There are seven choice-bearing nodes and eight final responses. Final responses use a Continue action and do not introduce a fourth dialogue choice. Each new interaction starts its selection count again.

## Dialogue

### F00 — Opening

*Rowan looks up from his fishing net, surprised.*

> "Oh! Didn't hear you coming. Don't know your face, either… You've come up from the shore? You're soaked through."

| Choice | Player says | Next node |
| --- | --- | --- |
| 1 | "Where am I?" | `F10` |
| 2 | "Can you help me?" | `F11` |

### F10 — Where am I?

> "On the coast, just below the village. Follow this path uphill and you'll reach it. You look like you've had a rough landing."

| Choice | Player says | Next node |
| --- | --- | --- |
| 1 | "Where should I go in the village?" | `F20` |
| 2 | "Who lives here?" | `F21` |

### F11 — Can you help me?

> "Depends what you need. I can point you toward shelter. If it's trouble out at sea, these old legs won't be much use."

| Choice | Player says | Next node |
| --- | --- | --- |
| 1 | "I need somewhere warm." | `F22` |
| 2 | "My boat crashed on the rocks." | `F23` |

### F20 — Directions

> "Keep to the path until you reach the houses. Someone there can help you find a place to rest."

| Choice | Player says | Final response |
| --- | --- | --- |
| 1 | "Will you come with me?" | `E01` |
| 2 | "What if they don't want a stranger there?" | `E02` |

### F21 — The villagers

> "Ordinary folk. People working, trading, getting on with their day. They'll notice a new face soon enough."

| Choice | Player says | Final response |
| --- | --- | --- |
| 1 | "Who should I speak to first?" | `E03` |
| 2 | "Do you get many strangers here?" | `E04` |

### F22 — Shelter

> "Then head into the village. Get out of those wet clothes and ask for somewhere to sit by a fire. Sea wind cuts right through you."

| Choice | Player says | Final response |
| --- | --- | --- |
| 1 | "I don't have any money." | `E05` |
| 2 | "Can I rest here for a moment?" | `E06` |

### F23 — The wreck

> "The rocks below the path? Nasty stretch of coast. You're fortunate you made it ashore. Leave the wreck alone until you've got your strength back."

| Choice | Player says | Final response |
| --- | --- | --- |
| 1 | "Could you help me recover my things?" | `E07` |
| 2 | "Is there anyone in the village who could help?" | `E08` |

## Final responses

Show the selected response, then close the dialogue when the player presses Continue. Do not automatically skip past the response. The next E interaction starts at `F00`.

| ID | Rowan says | After Continue |
| --- | --- | --- |
| `E01` | "No, I'll stay with my nets. You can see the roofs from here. Keep walking uphill." | Close |
| `E02` | "Tell them you washed ashore. Someone will hear you out." | Close |
| `E03` | "Start with someone by the houses. Ask where a traveler can rest, and take it from there." | Close |
| `E04` | "A few. Most arrive a good deal drier than you." | Close |
| `E05` | "Ask anyway. A place by the fire needn't cost a fortune." | Close |
| `E06` | "Catch your breath, then. But don't sit in the wind too long. The village is warmer." | Close |
| `E07` | "Can't do that for you. Ask in the village, and mind those rocks if you go back." | Close |
| `E08` | "Perhaps. Ask around the village. You'll have better luck there than with an old man and a torn net." | Close |

## Deliberately fixed behavior

- Every new visit repeats `F00` word for word, including his surprise at an unfamiliar face. Completed branches close after Continue.
- Choices remain available after they have been selected. No visited markers or alternative wording.
- Rowan never remembers the crash, the request for help, or a previous conversation.
- No relationship changes, generated responses, inventory grants, quest changes, or promises that require him to act.
- He gives useful initial directions, but cannot answer follow-up questions beyond the authored choices.
- The one-time cutscene flag records presentation only; it does not change his dialogue.

## Demo walkthrough

1. Approach from the shore and trigger the introduction.
2. Select "Can you help me?" → "My boat crashed on the rocks." → "Is there anyone in the village who could help?"
3. Read his final reply and press Continue.
4. The dialogue closes. Press E again: Rowan repeats his opening surprise, despite having just heard about the wreck.
5. Close the conversation and continue to a Gen-AI NPC for comparison.

For the comparison, give the Gen-AI NPC the same crash information and follow up on it. Look for a relevant response that uses the conversation context; dynamic dialogue quality should be demonstrated through behavior.

## Review checks

- Every choice-bearing node has exactly two choices.
- All eight paths reach a final response after exactly three player selections.
- Every final response closes after Continue; the next E interaction opens `F00`.
- Closing and reopening starts at `F00`.
- Completing a branch does not replay the introduction cutscene or trap the player in the conversation.

This document defines the encounter and dialogue only; game implementation is a separate step.
