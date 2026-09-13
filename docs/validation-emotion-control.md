# Validation and Emotion-Aware NPC Control

## Purpose

Implement a stronger validation and behavioral-control layer for NPC conversations.

The current validation layer mostly validates response shape, checks a small action allowlist, detects a curated set of out-of-world topics, and handles item transfers. It does not yet make NPC emotions authoritative over gameplay actions. The implementation in this document must add that behavior without allowing the LLM to mutate inventory, quest state, or rewards directly.

The target behavior is:

- Player words have a noticeably stronger effect on NPC emotion values.
- Emotion changes are smoothed over time so one message does not create an unusable permanent jump, while repeated behavior has cumulative consequences.
- The validation layer blocks actions that are incompatible with the NPC's current emotional state.
- An angry craftsman speaks rudely and refuses to craft the bow.
- Refusal is an authoritative gameplay decision, not merely a generated sentence.
- The player can repair the relationship through later behavior and eventually regain access to blocked actions.
- Existing inventory ownership, quest progression, and server-authoritative rewards remain intact.

This is an implementation prompt/specification. Do not treat generated dialogue as authority. The server must decide whether an action is permitted before applying its effects.

## Existing code to integrate with

Use these files as the starting points:

- `backend/app/services/validation/models.py`
  - Defines `StateUpdate` and `LLMResponse`.
- `backend/app/services/validation/service.py`
  - Parses and validates model output.
  - Rejects unauthorized transfers, unsupported actions, world-state claims, and emotional contradictions.
- `backend/app/services/validation/items.py`
  - Deterministically parses explicit item transfers.
- `backend/app/services/npc/conditioning.py`
  - Currently clamps role-specific aggression and forbids some actions.
- `backend/app/services/state/service.py`
  - Applies state deltas and performs inventory transfers.
- `backend/app/services/pipeline.py`
  - Orders grounding, LLM generation, validation, conditioning, state application, and quest progression.
- `backend/app/services/quests/bow.py`
  - Owns authoritative bow quest progression and crafting completion.
- `backend/app/models/npc.py`
  - Stores NPC emotional values, role, current state, inventory, and pending item.
- `backend/tests/test_npc_pipeline.py`
  - Contains existing behavior and regression tests for transfers, quest behavior, rejected model output, and state deltas.

Read the current implementation before editing. Preserve existing behavior unless this specification explicitly changes it.

## Non-negotiable authority rules

1. The LLM may propose dialogue, intent, emotion labels, actions, and emotion deltas.
2. The LLM may not grant items, consume items, complete quests, start crafting, complete crafting, or change quest phases directly.
3. The server must validate the action against the NPC's current emotional state, role, quest state, and inventory before applying it.
4. A rejected action must have no gameplay effect.
5. A refusal may produce dialogue and a state update, but must not perform the refused action.
6. The bow quest service remains the only authority that consumes bow materials, starts crafting, and grants the bow.
7. The emotional policy must be applied before `maybe_start()` or any other function that can cause an irreversible gameplay transition.
8. A generated sentence claiming that an action happened is not evidence that it happened.

## Desired request flow

Implement the behavior in this order:

```text
Player message
  -> classify player affect and interaction intent
  -> calculate amplified emotion event
  -> apply temporal smoothing to NPC emotion state
  -> generate or construct candidate response
  -> strict response validation
  -> role/action/emotion authorization
  -> convert blocked actions into authoritative refusal
  -> apply allowed state changes
  -> execute authoritative quest/inventory transition only if permitted
  -> persist conversation and emotion audit data
```

The action authorization decision must use the post-message emotional state, not the previous state alone.

## 1. Strengthen the response contract

Update the validation models with strict, typed invariants.

### Strict models

Configure Pydantic models to reject unknown fields with `extra="forbid"`. Unknown fields must become validation failures instead of being silently discarded.

Reject non-finite numeric values. All emotional values and deltas must remain finite and bounded.

### Typed values

Replace free-form action and emotion strings where practical with constrained literals or enums. Keep backward compatibility at API boundaries if necessary, but normalize into typed internal values.

At minimum, define explicit internal vocabularies for:

- Emotion dimensions: `trust`, `fear`, `aggression`, `curiosity`.
- Actions: `speak`, `idle`, `ask_question`, `share_memory`, `give_item`, `receive_item`, `craft_axe`, `repair_tool`, `request_materials`, `help_player`, and any existing supported actions.
- Refusal reasons: `emotion_blocked`, `role_forbidden`, `missing_materials`, `quest_not_ready`, `item_unavailable`, and `validation_rejected`.

### Cross-field invariants

Add model or service validation for combinations such as:

- `give_item` and `receive_item` require a non-empty `item`.
- Transfer actions can only be created by deterministic transfer logic after an explicit player request.
- `confirm_transfer` must use `ask_question`.
- `cancel_transfer` must not transfer an item.
- `craft_axe` must not be created for a role without that capability.
- Refusal output must not retain the blocked action as the final action.
- A response that says an item was granted must not be accepted unless the authoritative transition is being executed in the same transaction.

Do not use the LLM's `reasoning` field as authorization evidence. Treat it as untrusted diagnostic text, limit its length, and avoid making gameplay decisions from it.

## 2. Add a typed validation context

Replace broad `context: object | None` plus `getattr()` calls with a small typed context owned by the validation/control layer.

The context should contain only trusted facts needed for authorization, for example:

```python
@dataclass(frozen=True)
class ValidationContext:
    player_input: str
    player_inventory: tuple[str, ...]
    npc_inventory: tuple[str, ...]
    npc_role: str
    pending_item: str | None
    quest_phase: str | None
    player_id: int
    npc_id: int
```

Use immutable collections in the context. The context must be a snapshot. Validators must not mutate ORM objects or inventories while evaluating a candidate.

## 3. Classify player affect deterministically

Add a focused player-affect classifier. It may be implemented as a pure service under the validation/control area, or as a separate service if that matches the repository architecture.

The classifier should produce a typed result, not only a boolean:

```python
@dataclass(frozen=True)
class AffectEvent:
    trust: float
    fear: float
    aggression: float
    curiosity: float
    intensity: float
    category: str
    evidence: tuple[str, ...]
```

The category should distinguish at least:

- `respectful`
- `neutral`
- `insult`
- `threat`
- `coercion`
- `apology`
- `gratitude`
- `cooperation`
- `helpful_explanation`
- `unknown`

Use normalized text and explicit evidence tokens. Avoid a single broad regex that treats every occurrence of `bad`, `give`, or `I have` as hostile.

The first implementation may use deterministic lexical rules. Keep the classifier behind an interface so a stronger classifier can be introduced later without changing authorization code.

### Suggested affect mapping

Use a table-driven policy rather than scattering constants across conditionals. The following values are starting points and should be tuned through tests and playtesting:

| Category | Trust | Fear | Aggression | Curiosity | Intensity |
|---|---:|---:|---:|---:|---:|
| respectful | +0.12 | -0.03 | -0.08 | +0.04 | 0.35 |
| gratitude | +0.16 | -0.04 | -0.10 | +0.05 | 0.45 |
| apology | +0.20 | -0.06 | -0.16 | +0.03 | 0.55 |
| cooperation | +0.10 | -0.02 | -0.06 | +0.08 | 0.30 |
| insult | -0.18 | +0.03 | +0.20 | -0.02 | 0.60 |
| threat | -0.28 | +0.16 | +0.32 | -0.04 | 0.90 |
| coercion | -0.22 | +0.12 | +0.26 | -0.03 | 0.80 |
| neutral | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

These are emotion deltas before amplification and smoothing. Do not blindly copy them if the existing game balance indicates different values; preserve the relative behavior and document any tuning changes.

### Amplification requirement

Player affect must be stronger than the current LLM-provided state deltas. Apply a configurable amplification factor to player-derived events before smoothing. Start with:

```text
amplified_delta = raw_player_delta * 1.75
```

Then clamp each dimension to `[-1.0, 1.0]`.

The LLM-proposed `StateUpdate` must not be allowed to erase or reverse a strong player affect event in the same turn. Combine the two sources explicitly, for example:

```text
combined_delta = amplified_player_delta + bounded_llm_delta * llm_influence
```

Use a configurable `llm_influence` lower than the player influence, such as `0.25` to `0.50`. Document and test the chosen value.

## 4. Implement temporal smoothing

Emotion values are persistent state, so the system must avoid both instant emotional whiplash and unbounded accumulation.

Use a deterministic smoothing function. One acceptable starting design is:

```text
amplified_event = clamp(player_delta * player_gain, -1, 1)
llm_delta = clamp(model_delta * llm_gain, -1, 1)
raw_target = clamp(current_emotion + amplified_event + llm_delta, 0, 1)
smoothed = current_emotion + alpha * (raw_target - current_emotion)
next_emotion = clamp(smoothed, 0, 1)
```

Where:

- `player_gain` defaults to `1.75`.
- `llm_gain` defaults to a smaller value, such as `0.35`.
- `alpha` defaults to a responsive value such as `0.65`.
- All persisted emotion values remain in `[0, 1]`.

The existing `StateUpdate` currently behaves like a direct delta. Decide explicitly whether to preserve that public meaning or introduce a separate internal `EmotionEvent` and `EmotionSnapshot`. Do not silently reinterpret existing callers.

### Required smoothing behavior

- A neutral message must not change emotions.
- One insult must create a noticeable change but must not permanently force maximum aggression.
- Repeated insults must cross the angry threshold.
- Repeated respectful or apologetic messages must reduce aggression and restore trust gradually.
- A single apology must not instantly erase a history of threats.
- Emotion values must remain bounded after any number of messages.
- Smoothing must be deterministic and testable without wall-clock timing.

### Time-based recovery

If the design uses time between messages, inject a clock rather than calling time directly in business logic. Otherwise, use message-based smoothing only and document that choice.

For time-based recovery, define per-dimension recovery rates and test with a fake clock. Recovery must not bypass a current refusal in the same turn.

## 5. Define emotion thresholds and action policy

Create an explicit policy table. Do not hide emotional authorization inside dialogue generation.

Use hysteresis so an NPC does not alternate between allowed and blocked behavior at a boundary. Define separate block and release thresholds.

Suggested initial policy for the craftsman:

| Condition | Effect |
|---|---|
| `aggression >= 0.65` or `trust <= 0.20` | Refuse bow crafting and non-essential repair/help actions |
| `aggression >= 0.45` | Use curt or rude dialogue; require a respectful interaction before cooperation |
| `fear >= 0.75` | Refuse risky actions and avoid escalating dialogue; do not attack unless explicitly supported by role policy |
| `aggression <= 0.50` and `trust >= 0.30` | Release the bow-crafting refusal, subject to quest/material rules |
| `trust >= 0.65` and `aggression <= 0.35` | Normal cooperative behavior |

Tune thresholds after tests, but preserve the key requirement that an angry craftsman cannot craft the bow.

Represent policy decisions as typed results:

```python
@dataclass(frozen=True)
class ActionDecision:
    allowed: bool
    requested_action: str
    effective_action: str
    reason_code: str | None
    refusal_tone: str | None
```

Examples:

```text
requested_action = craft_axe
allowed = False
reason_code = emotion_blocked
refusal_tone = rude
```

Do not convert every blocked action into a generic fallback. The player should receive a role-appropriate refusal that communicates the current relationship state without exposing internal thresholds.

## 6. Craftsman bow refusal behavior

Implement the concrete scenario end to end.

When the player has angered the craftsman past the configured refusal threshold:

1. The player's current message is classified and the craftsman's emotion state is updated.
2. The bow-crafting request is evaluated against the post-message state.
3. If blocked, the request does not advance the bow quest.
4. No materials are consumed.
5. No crafting timer starts.
6. No bow is granted.
7. The final response has a rude or curt but bounded tone.
8. The final action is a safe conversational action such as `speak` or `ask_question`, not `craft_axe` or another crafting action.
9. The response records a typed refusal reason for diagnostics and memory classification.
10. The refusal itself may create a conversation record, but it must not create a false quest-completion or item-transfer event.

Example user-visible behavior, subject to the project's dialogue style:

```text
"Not after the way you've spoken to me. Come back when you can show some respect."
```

Do not hard-code this exact sentence as the only response. Use deterministic refusal templates or a constrained response composer so the tone is reliable and the gameplay outcome cannot be overridden by the LLM.

When the player's behavior later improves the craftsman's state below the release threshold, crafting may become available again if all ordinary quest and material requirements are satisfied.

## 7. Pipeline ordering changes

Update the pipeline so emotional authorization occurs before irreversible quest actions.

The current sequence validates/conditions output, applies state, and then calls `maybe_start()`. That is unsafe for emotion-aware gating because `maybe_start()` can begin bow crafting based on inventory and quest phase.

The new sequence must be equivalent to:

```text
1. Load locked NPC/player/quest state.
2. Build immutable validation context.
3. Classify player affect.
4. Compute smoothed post-message emotion state.
5. Resolve deterministic transfer and quest responses where applicable.
6. Generate LLM output only when the interaction is not fully grounded.
7. Strictly validate the candidate response.
8. Authorize the requested action against post-message emotion and role policy.
9. Replace blocked actions with an authoritative refusal response.
10. Apply the approved emotion state and approved conversational state.
11. Call bow quest progression only when the action decision allows it.
12. Apply inventory and quest mutations in the same transaction.
13. Persist audit data and commit.
```

Preserve the existing lock order and rollback behavior. A failed memory write or later persistence error must not leave emotional, inventory, or quest state partially applied.

## 8. Role-aware dialogue composition

Add a constrained refusal/dialogue policy rather than asking the LLM to infer all tone from raw numeric values.

At minimum support these tone modes:

- `friendly`
- `neutral`
- `curt`
- `rude`
- `fearful`
- `apologetic`

Tone selection must use authoritative emotion values and action decisions. The model may supply wording only within the selected tone and permitted action.

For an emotionally blocked craftsman:

- State the refusal.
- Do not claim that materials were consumed.
- Do not claim that crafting started or completed.
- Do not threaten violence unless the role policy explicitly allows it.
- Do not include hidden thresholds or internal implementation details.
- Keep dialogue within the configured maximum length.

If the LLM output conflicts with the selected refusal tone or claims the action occurred, discard it and use the deterministic refusal response.

## 9. Persistence and schema considerations

Determine whether existing NPC emotion columns are sufficient for the selected smoothing design.

If message-based smoothing is used, existing fields may be sufficient, but add audit fields if useful:

- `last_emotion_event_category`
- `last_emotion_event_at` or a revision counter
- `emotion_policy_version`
- `action_refusal_reason`

If time-based decay or richer emotional memory is used, add a migration and document defaults for existing rows.

Do not store unbounded raw player text in emotion state. Store compact categories, magnitudes, and evidence only where needed for diagnostics.

Ensure new fields are reset by the existing new-game/reset flow and survive normal restarts as intended.

## 10. Validation errors and observability

Replace generic string-only failures where practical with stable error codes. Examples:

- `MALFORMED_RESPONSE`
- `UNKNOWN_RESPONSE_FIELD`
- `ACTION_NOT_ALLOWED_FOR_ROLE`
- `ACTION_BLOCKED_BY_EMOTION`
- `TRANSFER_NOT_EXPLICIT`
- `ITEM_NOT_OWNED`
- `QUEST_CLAIM_NOT_AUTHORITATIVE`
- `KNOWLEDGE_BOUNDARY`
- `EMOTION_OUT_OF_RANGE`
- `INCONSISTENT_RESPONSE`

Log structured fields, not only prose:

- NPC id and role.
- Player message classification.
- Previous emotion snapshot.
- Amplified player event.
- Model delta.
- Smoothed next snapshot.
- Requested action.
- Effective action.
- Refusal reason.
- Quest phase before and after.
- Whether an inventory mutation occurred.

Do not log secrets, API keys, or unnecessary full prompts.

## 11. Tests required before completion

Add focused unit tests for pure logic and integration tests for the pipeline.

### Model and schema tests

- Unknown response fields are rejected.
- Missing required fields are rejected.
- Non-finite or out-of-range emotion values are rejected.
- Transfer actions require items.
- Invalid action/intent combinations are rejected.

### Affect classifier tests

- Respectful wording produces positive trust and reduced aggression.
- Insults produce negative trust and increased aggression.
- Threats produce a stronger response than insults.
- Apologies reduce aggression but do not erase all prior anger.
- Neutral text produces zero affect.
- Similar wording with different context does not trigger accidental transfer or hostility.

### Smoothing tests

- Values remain bounded after 1, 10, and 1,000 events.
- A single insult has a noticeable but bounded effect.
- Repeated insults cross the angry threshold.
- Repeated respectful messages eventually release the refusal.
- One apology does not immediately restore full trust.
- Identical input and state produce identical output.
- Fake-clock tests pass if time-based recovery is implemented.

### Authorization tests

- A craftsman below the refusal threshold can craft when quest/material rules allow it.
- An angry craftsman refuses to craft.
- The refusal does not consume wood or string.
- The refusal does not start the crafting timer.
- The refusal does not grant a bow.
- A gatherer and craftsman follow distinct role policies.
- An LLM response requesting a blocked action cannot bypass the policy.
- A deterministic quest response cannot bypass the policy either.
- The policy evaluates post-message emotion, including the emotion caused by the current insulting message.

### Regression tests

Preserve existing tests for:

- Explicit item transfer and cancellation.
- Missing inventory items.
- Modern-topic rejection.
- Hallucinated quest rewards.
- Bow quest progression and one-time reward behavior.
- Transaction rollback on memory persistence failure.
- Signed state deltas and role conditioning.

Add an end-to-end scenario:

```text
1. Start with a neutral craftsman and an available/gathering bow quest.
2. Player sends repeated insulting or threatening messages.
3. Assert trust decreases and aggression increases substantially.
4. Ask the craftsman to craft the bow.
5. Assert rude refusal and no quest/material mutation.
6. Send several respectful/apologetic messages.
7. Assert emotions recover gradually.
8. Once below the release threshold, provide valid materials and request crafting.
9. Assert crafting begins only then.
10. Advance the timer and assert one bow reward.
```

## 12. Acceptance criteria

The implementation is complete only when all of the following are true:

- Player affect changes emotions more strongly than the current LLM-only deltas.
- Emotion changes use a documented, deterministic temporal smoothing model.
- Emotion state is bounded and persisted correctly.
- Action authorization is separate from dialogue generation.
- The craftsman refuses bow crafting while emotionally blocked.
- The refusal is rude/curt but does not create unsafe threats or false world claims.
- Blocked actions have no inventory, quest, timer, or reward effects.
- Recovery is gradual and allows future cooperation after respectful behavior.
- The LLM cannot bypass emotional or role policy through action fields or dialogue claims.
- Existing authoritative bow, inventory, and rollback behavior remains intact.
- Tests cover both pure emotional policy and full pipeline behavior.
- Error codes and structured logs make blocked actions diagnosable.
- The implementation does not rely on wall-clock time in tests.

## Implementation discipline

Keep the first implementation narrow. Do not introduce a general-purpose emotion AI system, sentiment API, or large framework unless the repository already uses one.

Prefer:

- Pure functions for affect mapping, smoothing, threshold evaluation, and policy decisions.
- Immutable typed snapshots at validation boundaries.
- Existing Pydantic, SQLAlchemy, and service patterns.
- Server-side deterministic authority for inventory and quests.
- Small migrations with reset/restart coverage.
- Focused tests before broad refactoring.

At handoff, report:

- Changed files.
- New configuration values and defaults.
- Any database migration.
- The exact smoothing formula and threshold table.
- Test commands and results.
- Any behavior intentionally left unsupported.
