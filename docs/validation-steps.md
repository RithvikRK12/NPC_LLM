# Validation Flow in the NPC LLM Pipeline

This document describes the validation steps that happen in the code before an NPC response is accepted, stored, and used to update game state. The validation logic is spread across the pipeline, the validation service, and the model/schema definitions, and it acts as a safety net between raw LLM output and the in-game world state.

## 1. Where validation happens

The main orchestration is in:

- backend/app/services/pipeline.py
- backend/app/services/validation/service.py
- backend/app/services/validation/models.py
- backend/app/services/validation/control.py
- backend/app/services/validation/knowledge.py
- backend/app/services/validation/items.py

The overall flow is:

1. Build a context for the NPC and the player.
2. Check whether the player message is a valid in-world request or an explicit transfer request.
3. Generate or bypass LLM output.
4. Validate the raw JSON against structural rules.
5. Validate world knowledge boundaries, negotiation rules, and inventory/quest constraints.
6. Check emotion and action compatibility.
7. Reject or repair malformed output with a fallback response.
8. Apply state changes only after the response has passed the checks.

---

## 2. The conversation pipeline starts the gatekeeping

In `ConversationPipeline.chat()`, the system creates a validation context using `make_validation_context(...)` before generating an answer.

This context includes:

- the player input
- player inventory
- NPC inventory
- NPC role
- pending item
- quest phase
- player and NPC IDs

The pipeline also checks for explicit transfer requests before calling the LLM:

- `requested_transfer(player_message)` decides if the input is asking for a concrete item transfer.
- `transfer_answer(...)` resolves item ownership and purpose requirements.
- If the request is grounded in game rules, the system may skip the LLM entirely and respond from deterministic logic instead of trusting a model output.

This is important because item requests are treated as authoritative game rules, not as free-form model decisions.

---

## 3. Knowledge-boundary validation blocks out-of-world content

The file `backend/app/services/validation/knowledge.py` defines the `outside_world()` function.

It scans the player's input or NPC dialogue for modern technology and external-world references such as:

- AI / LLM / OpenAI / ChatGPT
- cloud services / AWS / Azure
- software / programming / internet / websites
- blockchain / cryptocurrency
- Docker / Kubernetes and similar modern-tech language

If the NPC role is `craftsman` or `gatherer`, the system raises a `KnowledgeBoundaryError` when the player message or the output mentions modern technology:

- `ValidationService.validate()` checks:
  - `outside_world(player_input)`
  - `outside_world(str(raw_output.get("dialogue", "")))`
- If the content is outside the setting, the system rejects the result and returns an in-world fallback response via `unfamiliar_topic_response(...)`.

This ensures that the NPC behaves as if it lives in a stylized village world rather than speaking as a modern AI assistant.

---

## 4. Explicit item transfer requests are validated before any transfer

The logic in `backend/app/services/validation/items.py` is a strict gate for transfers.

### 4.1 Request detection

`requested_transfer(question)`:

- lowercases and normalizes the input
- rejects negated phrases such as “do not” or “never”
- extracts item names from the text
- only accepts requests when exactly one item is named
- decides whether the player is offering an item (`receive_item`) or asking for one (`give_item`)

Examples of recognized patterns include:

- “give me wood”
- “can I have a bow”
- “I offer you rope”
- “take my fruits”

### 4.2 Ownership checks

`transfer_answer(...)` validates the transfer against the actual inventories:

- if the NPC is supposed to give an item, the item must exist in `npc_inventory`
- if the player is offering an item, the item must exist in `player_inventory`
- if ownership fails, the NPC responds with a refusal such as “I don’t have any wood left to give you” or “You don’t have that item to give me.”

### 4.3 Purpose confirmation before giving an item

The code enforces a human-readable confirmation pattern:

- If the NPC has a pending item request, it asks for a purpose before handing over the item.
- A request like “give me wood” alone is not enough unless the player explains why they need it.
- The system prompts:
  - “What will you use the wood for? Tell me why you need it, or say cancel.”
- The player can cancel with a phrase such as “cancel” or “never mind.”

This prevents impulsive, under-explained transfers and keeps the item logic grounded in game-specific context.

---

## 5. Pydantic schema validation enforces the response structure

The raw LLM output is expected to match the shape defined in `backend/app/services/validation/models.py`.

### 5.1 `StateUpdate`

`StateUpdate` allows only these fields:

- trust
- fear
- aggression
- curiosity

The model also enforces:

- no extra fields are allowed
- values must be between -1.0 and 1.0
- NaN and infinite values are forbidden

### 5.2 `LLMResponse`

The model requires:

- `intent`: non-empty string
- `emotion`: non-empty string
- `dialogue`: non-empty string, max length 240 characters
- `action`: non-empty string
- `reasoning`: non-empty string, max length 500 characters
- `state_update`: a valid `StateUpdate` object
- `item`: optional, but required when the action is `give_item` or `receive_item`

Cross-field validation is also applied:

- `confirm_transfer` must use `ask_question` as its action
- `cancel_transfer` must not transfer an item
- transfer actions require an item

If the model output is malformed, `ValidationService.validate()` raises a `ValidationError` with the message “Malformed structured JSON.”

---

## 6. Business rules check the meaning and safety of the NPC output

After the schema succeeds, `ValidationService.validate()` runs several semantic checks.

### 6.1 Dialogue length limits

The code rejects output if dialogue exceeds the configured maximum:

- `self._settings.max_dialogue_chars`

This prevents overly long responses from being accepted and stored as NPC dialogue.

### 6.2 Forbidden transfer actions

The system blocks item transfers unless they were explicitly authorized by the deterministic transfer logic:

- if `output.action` is `give_item` or `receive_item`, the system raises a validation error
- this is a safeguard: item exchange is deliberately not left to raw model creativity

### 6.3 Supported actions only

Only the following actions are allowed:

- speak
- idle
- ask_question
- share_memory
- give_item
- receive_item
- craft_axe
- repair_tool
- request_materials
- help_player

If the model tries to trigger an unsupported action, the code rejects it.

### 6.4 Inventory and quest claims are banned in free-form dialogue

The service uses a regex to reject dialogue that claims the NPC has a quest, reward, inventory, or ownership that was not established by the authoritative rules.

This includes phrases like:

- “I have a reward”
- “I completed the quest”
- “I gave you my item”
- “I have wood”
- “you have received a reward”

This is intentionally stricter than a normal chat model would allow, because game state must come from game logic, not from unverified conversational assertions.

---

## 7. Numeric range validation for state updates

The method `_validate_ranges()` checks every emotional delta:

- trust
- fear
- aggression
- curiosity

Each value must remain within the range:

- -1.0 <= value <= 1.0

This prevents the model from arbitrarily pushing the character’s emotional state outside the game’s bounded operational space.

---

## 8. Role-based action validation

The service also checks whether an action is valid for the NPC role.

In `_validate_action()`:

- it checks the action against `SUPPORTED_ACTIONS`
- it blocks role-forbidden actions such as attacking or declaring war for `craftsman` and `gatherer`
- it enforces a crafting rule: crafting an axe requires wood in the inventory or in the NPC’s owned resources

This keeps the NPC’s behavior aligned with the game’s role design and resource economy.

---

## 9. Contradiction validation checks tone versus action/content

`_validate_contradictions()` reads the dialogue for hostile or friendly language and compares it to the emotion and action.

Examples:

- If the NPC’s emotion is `friendly` or `calm` but the dialogue contains terms like “kill,” “attack,” or “destroy,” it is rejected.
- If the NPC is `hostile` or `angry` but the dialogue includes “help,” “repair,” “gift,” or “craft,” and the action is an aggressive action such as `attack` or `declare_war`, it is rejected.

This prevents the model from creating a personality mismatch between tone, action, and words.

---

## 10. After validation, the system checks emotion control and action authorization

The pipeline continues after `ValidationService.validate()`, but the validation layer is not the end of the safety checks.

### 10.1 Emotion smoothing

`control.py` computes an affect event from the player input and blends it with the model’s emotional delta:

- `classify_player_affect()` detects categories like “respectful,” “insult,” “threat,” “gratitude,” and “neutral”
- `smooth_emotions()` adjusts NPC emotion using:
  - current NPC state
  - player affect
  - LLM-provided delta
  - smoothing constants

This creates a controlled, bounded emotional transition instead of allowing the raw LLM output to swing NPC emotion immediately.

### 10.2 Action authorization

`authorize_action()` decides whether an NPC may execute the requested action.

It blocks actions if:

- the action is not in the supported action set
- the NPC role is not allowed to do it
- the emotional state suggests the NPC should refuse due to aggression or low trust

Examples:

- a `craftsman` or `gatherer` may be blocked from a quest-related or craft-related request if the player is threatening or disrespectful
- if the NPC is too hostile or distrustful, the result becomes a refusal rather than a direct action

### 10.3 Refusal response generation

When an action is blocked, the code returns a refusal response using `refusal_response(...)`.

This creates a deterministic, in-world response instead of letting an invalid action slip through.

---

## 11. Rejection and repair flow

The pipeline wraps validation in `_validate_or_repair()`.

It catches:

- `KnowledgeBoundaryError` → triggers a topic-specific refusal using `unfamiliar_topic_response(...)`
- `ValidationError` → logs the rejection and replaces the output with a safe fallback response

Fallbacks are defined per role:

- gatherer: a safe response about the forest and supplies
- other roles: a general safe response about workshop supplies and help

This means the system never exposes a malformed or off-world NPC response to the user or to game state.

---

## 12. End-to-end summary of the actual validation stack

The code enforces validation in layers:

1. Context and inventory checks before response generation
2. World-boundary knowledge filtering
3. Deterministic transfer resolution and ownership checks
4. Pydantic schema validation for output shape
5. Dialogue and action constraint validation
6. Emotion and state range validation
7. Role-based compatibility checks
8. Contradiction checks between tone, language, and action
9. Emotion smoothing and action authorization
10. Rejection or fallback response generation
11. Only then is the validated output persisted and applied to game state

The important design principle is that game rules and NPC consistency are treated as higher-priority than raw model behavior. The model is allowed to generate a likely reply, but the system actively enforces world consistency before accepting it.

---

## 13. Panel-ready oral explanation

“Validation in this project is not a single check; it is a layered safety system. The first gate is the conversation pipeline, which builds a validation context with the player inventory, NPC inventory, pending item, and quest state. Before the model even speaks, the system screens for explicit transfer requests and item ownership rules, because those are treated as game rules rather than model guesswork.

Then the system validates the raw LLM output against a strict schema. We use Pydantic models that forbid extra fields, enforce non-empty strings, cap dialogue length, and require valid structured fields such as intent, emotion, action, reasoning, and emotional deltas. After that, we do semantic validation: no unsupported action types, no inventory or quest claims in free-form dialogue unless they are backed by the actual game state, and no emotional state values outside a bounded range.

Next, the system checks whether the response respects the NPC’s role. It blocks forbidden actions for certain roles, ensures crafting requires resources like wood, and catches contradictions between the emotional tone and the wording. It also checks whether the player’s tone or attitude would cause the NPC to refuse, and it combines the model’s emotional delta with the player’s affect to produce a smoothed and controlled emotional result.

If any of these checks fail, the code does not silently continue. It logs the rejection and returns a safe fallback response or a world-appropriate refusal. So the system is designed around one principle: the model proposes a response, but the game logic authoritatively decides whether that response is valid, consistent, and safe to execute.”
