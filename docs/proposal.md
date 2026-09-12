# NPC Closed-Loop Behavior Architecture: Implementation Proposal

## Purpose

This proposal turns the architecture into a coherent, staged implementation
plan. It documents the current codebase, the missing capabilities, and the
contracts that connect each layer. The goal is believable NPC behavior without
giving an LLM authority over game facts or engine execution.

## Target architecture and delivery order

1. **Game Environment + Player Input / Perception** — creates the authoritative
   snapshot of what an NPC knows now.
2. **LLM Reasoning Engine** — turns that snapshot into a grounded decision
   proposal.
3. **State Extraction** — converts proposed relative changes into normalized
   candidate NPC state.
4. **Fuzzy-Symbolic Layer** — derives interpretable behavioral tendencies.
5. **Validation** — resolves constraints and temporal continuity into a
   validated behavior.
6. **Role Conditioning** — applies role permissions, emotional limits, and
   role-specific behavioral bias.
7. **FSEC** — selects an eligible engine action and maps behavior to controller
   parameters.
8. **Game Engine / NPC Controller** — executes commands and reports outcomes.
9. **Persistent Memory** — stores authoritative outcomes and relevant history
   for a later perception snapshot.

The runtime is a loop: engine outcomes feed memory and world state; the next
perception snapshot observes those authoritative changes. The dependency order
above is the implementation order; the detailed sections below group related
work without changing those dependencies.

## Cross-layer invariants

- The backend/game systems, not the LLM or client, own authoritative facts and
  persistent mutations.
- Every handoff is a versioned, typed, traceable object with source IDs.
- A layer may narrow, condition, or reject an upstream proposal; it must not
  invent missing facts to make that proposal valid.
- Hard safety, world, and role constraints override fuzzy preferences and LLM
  suggestions.
- Dialogue about an outcome is emitted only after the corresponding
  authoritative event confirms that outcome.

## Game Environment + Player Input / Perception Layer

### Scope

This layer collects game and player signals, normalizes facts and
interpretations, limits data to what the NPC can know, filters/ranks it, and
produces an immutable `PerceptionSnapshot`. It does not reason, execute, or
persist state changes.

### Design principles

- The game server is the source of truth for positions, inventory, quests,
  factions, world events, combat, and economy.
- The perception layer distinguishes **facts** (observed or authoritative game
  state) from **interpretations** (derived labels such as `nearby`,
  `threatening`, or `quest_relevant`).
- An NPC sees only signals permitted by its location, range, line of sight,
  senses, faction knowledge, and recent interactions.
- The LLM is given an explicit, typed snapshot rather than the full database
  state or raw client claims.
- Every fact should carry source, timestamp, confidence, and visibility scope
  so it can be audited and invalidated.
- Relevance and salience happen before handoff, keeping the snapshot compact
  and predictable.

### What must be added or changed

### 1. Capture authoritative raw signals

Replace the chat-only input boundary with an interaction/event payload. Player
dialogue remains one signal, but it must be accompanied by authoritative game
state recorded by the server.

Add server-owned inputs for:

- **Player interaction:** dialogue text, selected action, intended target,
  interaction type, and client event ID. Treat text-derived intent as an
  interpretation, not an authoritative fact.
- **Spatial state:** player and NPC positions, locations/areas, facing,
  distance, line-of-sight or visibility result, and nearby interactables.
- **Visible items:** stable item IDs, type, quantity, owner, position, and
  visibility/accessibility state. Player and NPC inventories remain distinct
  from ground items.
- **Nearby NPCs/entities:** ID, role, faction, current observable action,
  location, distance, and visibility. Do not expose another NPC's private
  emotions or memories unless a game mechanic reveals them.
- **Quest state:** active quests, phase, objectives, progress, assigned NPCs,
  rewards, and changes since the last snapshot.
- **NPC internal state:** emotional values, current action, goals, role rules,
  relationship values, and cognitive facts/beliefs. Private state should be
  explicitly marked as internal.
- **World events:** event ID/type, location/area, start/end time, severity,
  affected factions/entities, and whether the NPC could observe or has been
  informed of it.
- **Economy/factions/threats:** prices or scarcity, faction reputation and
  relations, hostile entities, hazards, combat state, and urgency.

The Godot client should send only player-originated events. The backend should
look up positions, visibility, inventories, quests, NPC state, and world state
itself. This prevents a client from asserting that an NPC can see an item,
changed a quest, or is in a location.

### 2. Add a world-state and event model

The current data model supports NPC values, player inventory/location, and one
Bow Quest. Add domain models (or an engine adapter with equivalent snapshots)
for:

- `WorldEntity` / `WorldItem`: entity ID, kind, location/position, owner,
  visibility and interaction metadata.
- `WorldEvent`: immutable event records plus lifecycle fields for active
  events; examples include alarm, weather change, attack, trade shortage, and
  quest milestone.
- `Faction` and `FactionRelation`: membership, standings, alliances, and
  hostility.
- `NPCRelationship`: NPC-to-player and NPC-to-NPC social values such as trust,
  familiarity, debt, and reputation.
- `NPCBelief` or `KnowledgeFact`: facts the NPC has learned but cannot
  necessarily currently observe, with source/confidence/expiry.
- Generalized `Quest` / `QuestObjective` records instead of making the context
  depend only on `BowQuest`.
- An explicit spatial representation: named areas are sufficient initially;
  later add 2D/3D coordinates, range checks, and line-of-sight queries.

### 3. Define a normalized signal schema

Introduce typed Pydantic models under `backend/app/services/perception/`.
Raw engine/database records should be translated into one consistent format
before any LLM prompt is built.

Suggested shared envelope:

```json
{
  "id": "event-or-fact-id",
  "kind": "player_speech | visible_item | nearby_npc | quest_update | world_event | internal_state",
  "source": "player | engine | quest_system | memory | npc_state",
  "observed_at": "2026-09-12T12:00:00Z",
  "location": {"area": "village_square", "x": 12.0, "y": 7.0},
  "fact": {"...": "authoritative data only"},
  "interpretation": {"...": "derived labels only"},
  "confidence": 1.0,
  "visibility": "direct | informed | remembered | private",
  "expires_at": null
}
```

Examples:

- A player saying “I need wood” is a `player_speech` fact. “The player wants
  wood” is a lower-confidence interpretation.
- A wolf within line of sight is a direct `nearby_npc`/threat fact. “Dangerous”
  is a derived interpretation with an explicit threat score.
- A rumor retrieved from memory is `visibility: remembered` and must preserve
  its source and confidence rather than being presented as a world fact.

### 4. Implement an NPC-specific sensing stage

Create a `PerceptionCollector` that obtains raw signals for a specific NPC and
decision moment. Its queries should be bounded by the NPC's sensory scope.

Required collectors:

- `PlayerInteractionCollector` for the current dialogue/action payload.
- `SpatialCollector` for NPC/player proximity, area, visibility, nearby items,
  and nearby entities.
- `NPCStateCollector` for private emotional/cognitive/social state.
- `QuestCollector` for only quests relevant to the NPC, player, or current
  interaction.
- `WorldEventCollector` for active and recently changed observable events.
- `MemoryCollector` for semantic memories and recent dialogue.
- `SocialCollector` for relationships and faction knowledge.

The collector must enforce rules such as “only entities within range and line
of sight are directly visible” and “global events require a propagation or
knowledge rule before an NPC knows them.”

### 5. Normalize facts separately from interpretation

Create a `SignalNormalizer` with deterministic transformations. It should:

- convert ORM rows and engine payloads to typed records;
- validate IDs, timestamps, bounds, and allowed enum values;
- deduplicate the same item/entity/event seen through multiple sources;
- attach a stable source and confidence value;
- make derived interpretations explicit and reproducible;
- reject client-provided claims that conflict with server state.

Do not let the LLM perform this normalization. For example, the backend—not the
model—must decide whether an item is visible, whether an NPC is nearby, and
whether a quest objective is complete.

### 6. Add relevance filtering

Create a `RelevanceFilter` that removes signals not useful to this NPC's
current decision. Initial deterministic rules can cover:

- keep the current player interaction and directly visible threats;
- keep events in the NPC's current area or events known through faction/quest
  propagation;
- keep quest facts only when the NPC participates, the player asks about them,
  or they constrain an available action;
- keep items only when visible, actionable, quest-relevant, or mentioned by the
  player;
- keep nearby NPCs only when they are observable or socially relevant;
- keep a small number of retrieved memories that match the player interaction;
- drop stale state, duplicate facts, and distant unrelated background events.

The filter should emit a reason for inclusion/exclusion. That makes debugging
perception decisions possible without exposing irrelevant data to the LLM.

### 7. Rank salience before composing the prompt

Implement a `SalienceRanker` that assigns a deterministic score and a priority
band. A first version can combine:

```text
salience = urgency + recency + player_relevance + spatial_proximity
           + quest_relevance + relationship_relevance + memory_match
```

Recommended ordering:

1. Immediate danger, combat, hard safety constraints, and forced game events.
2. Current player action/speech and directly relevant quest or inventory facts.
3. Nearby visible actors/items and NPC internal emotional/social state.
4. Recent dialogue and matching durable memories.
5. Background world context.

Scores must be reproducible and configurable. Select a token/count budget per
category so an abundance of background events cannot hide a threat or the
current player request.

### 8. Compose a versioned perception snapshot

Replace or wrap `ConversationContext` with a versioned `PerceptionSnapshot`.
The existing fields can remain temporarily for compatibility, but the LLM-facing
object should be grouped by meaning rather than a flat mix of data.

```json
{
  "schema_version": "1.0",
  "snapshot_id": "uuid",
  "observed_at": "2026-09-12T12:00:00Z",
  "npc": {
    "identity": {"id": 1, "name": "...", "role": "..."},
    "internal_state": {"emotion": {}, "cognition": {}, "social": {}},
    "perception_constraints": {"area": "...", "vision_range": 0}
  },
  "current_interaction": {"speech": "...", "action": null, "target": null},
  "direct_observations": {"entities": [], "items": [], "threats": []},
  "relevant_game_state": {"quests": [], "factions": [], "world_events": []},
  "retrieved_memory": {"recent_dialogue": [], "durable_memories": []},
  "salient_facts": [],
  "constraints": ["authoritative state is backend-controlled"]
}
```

Each selected item should include source, visibility, timestamp, confidence,
salience score, and inclusion reason. Keep private implementation diagnostics
out of the production LLM payload if they are not needed for behavior.

### 9. Define the handoff contract

The perception layer's output is data-only. Its contract with the next layer
must ensure that information is not silently converted from a player claim,
memory, or interpretation into an authoritative world fact.

- Mark snapshot data as facts, interpretations, memories, or player claims.
- Retain the source `id` for every salient item so a downstream consumer can
  trace it back to an authoritative record.
- Keep client-provided claims separate from server-observed state when they
  conflict.
- Include a snapshot ID, schema version, and observation time.
- Treat the snapshot as immutable after composition; a later world change
  requires a new snapshot.

### 10. Change the current input-to-snapshot flow

The target flow should be:

```text
Godot player event
  -> API validates client event
  -> backend loads authoritative world state
  -> PerceptionCollector
  -> SignalNormalizer
  -> RelevanceFilter
  -> SalienceRanker
  -> PerceptionSnapshot
  -> handoff to the next architecture layer
```

Specific changes to the existing code:

- Replace `ContextBuilder.build(npc, player, player_input)` with a perception
  builder that accepts a typed interaction event and reads all other state from
  the backend.
- Preserve the current semantic memory service, but place its results under
  `retrieved_memory` and retain source/recency/similarity metadata.
- Generalize the Bow Quest snapshot into a quest collector; do not make it the
  only game-state representation.
- Expand `ChatRequest` into an interaction schema while retaining a simple
  dialogue-only compatibility path for the current UI.
- Update Godot to send an interaction event and to synchronize player position
  or area through a server-authoritative movement/state endpoint.

Prompt construction, LLM generation, output validation, and state execution
should consume this handoff in their own layer-specific proposals; they are not
implementation work for this layer.

### Suggested implementation order

### Phase 1: Establish the boundary and schema

1. Create `services/perception/models.py` with typed signal and snapshot
   models.
2. Convert the existing context fields into `PerceptionSnapshot` sections.
3. Add source, timestamp, visibility, confidence, and salience metadata to
   memories and selected facts.
4. Keep dialogue-only input working while adding an optional typed interaction
   payload.

### Phase 2: Make spatial perception real

1. Add authoritative player/NPC positions or areas.
2. Add nearby entity/item queries and a simple visibility/range rule.
3. Prevent an interaction when the player is not eligible to interact with the
   selected NPC, unless remote communication is explicitly supported.
4. Update the Godot loop to synchronize movement/location through the backend.

### Phase 3: Add filtering and salience

1. Build deterministic relevance rules and inclusion diagnostics.
2. Add a configurable salience scorer and per-category budgets.
3. Ensure threats, active quest blockers, and the current interaction always
   survive truncation.

### Phase 4: Expand game knowledge

1. Generalize quest data.
2. Add world events and event-knowledge propagation.
3. Add faction and relationship state.
4. Add economy and threat providers only when those game systems exist.

### Phase 5: Perception evaluation

1. Log the raw candidate signals, selected snapshot facts, their salience, and
   inclusion/exclusion reasons.
2. Test visibility, stale events, conflicting player claims, salience ordering,
   and memory relevance.
3. Verify that snapshot provenance lets downstream layers distinguish a direct
   observation from a player claim, remembered information, or interpretation.

### Acceptance criteria

The layer is complete enough for this architecture when:

- An NPC receives a compact, typed snapshot containing only facts it can know
  at that moment.
- Player speech, action, nearby visible entities/items, relevant quest state,
  NPC internal state, known world events, and retrieved memory are represented
  separately and with provenance.
- A distant NPC cannot react to an unseen item, unheard dialogue, or unshared
  event.
- Immediate threats outrank generic world context; current interaction outranks
  older memory unless the memory is highly relevant.
- Client requests cannot forge inventory, location, quest, or observation
  facts.
- The snapshot never presents a player claim, memory, or interpretation as an
  authoritative world fact.
- Automated tests cover both what an NPC should perceive and what it must not
  perceive.

### Initial test scenarios

- Player is near the Craftsman, says “I need a bow,” and the snapshot includes
  current dialogue, visible Craftsman, relevant Bow Quest state, and any
  matching memory.
- Player chats with a distant NPC: the backend rejects the interaction or the
  snapshot marks it as a supported remote channel.
- A threat appears in the NPC's visible range: it receives higher salience than
  a five-minute-old memory.
- A global event occurs in another area: it is absent until the NPC observes it
  or receives it through a defined propagation rule.
- The player claims “I gave you wood” without a completed authoritative
  transfer: the claim is labeled player speech, not inventory truth.
- A hundred low-value ambient events do not displace the current player action,
  quest blocker, or immediate threat from the snapshot.

## LLM Reasoning Engine Layer

### Current implementation assessment

The project has a basic LLM generation path, but not a complete LLM Reasoning
Engine as defined by this layer.

| Required capability | Current status | Gap |
| --- | --- | --- |
| Process structured context | Partial | `ConversationContext` is serialized into the prompt, but it is not yet the bounded, versioned perception snapshot defined above. |
| Infer intent from personality and history | Partial | The model emits `intent`; role and retrieved memory are available, but there is no explicit personality/goal profile or evidence that the model must use selected memories. The mock provider ignores memories. |
| Resolve conflicting factors | No | `RuleEngine.evaluate()` labels trust/fear/aggression/curiosity, but its result is discarded by the pipeline and does not influence an LLM decision or a conflict policy. |
| Output structured decisions | Partial | The response has intent, emotion, dialogue, action, and state deltas, but it lacks behavior signals, confidence, alternatives/conflict information, and fact provenance. |
| Consistent, adaptive behavior | Partial | Role constraints and state updates exist, but there is no stable personality contract, deliberation policy, or decision-level evaluation. |

### Scope

This layer starts only after the perception layer has produced an immutable
`PerceptionSnapshot`. It produces a structured **decision proposal** for the
Control and Execution layers. It does not read raw game state directly, change
authoritative state, execute actions, or write durable memory.

```text
PerceptionSnapshot
  -> LLM reasoning and decision composition
  -> StructuredDecisionProposal
  -> Control / validation layer
```

### Required additions and changes

### 1. Consume only the perception snapshot

Replace the current loose `ConversationContext` input to prompt construction
with the versioned `PerceptionSnapshot` from the preceding layer.

- Pass the snapshot ID and schema version through the generation request.
- Do not allow the reasoning engine to query ORM models, game routes, or raw
  client payloads.
- Include direct observations, remembered facts, player claims, and derived
  interpretations as distinct categories; their labels must survive prompt
  serialization.
- Include only the relevance-filtered, salience-ranked facts. The engine should
  not independently reconstruct the world from unbounded conversation history.
- Make the prompt state that a fact is usable only according to its source and
  visibility. A player claim and a memory are not confirmation of current world
  state.

### 2. Define an explicit NPC reasoning profile

The current `role` field is not enough to produce stable personality-driven
intent. Add a typed, server-owned `NPCReasoningProfile` supplied alongside the
snapshot:

```json
{
  "personality": {"warmth": 0.7, "caution": 0.8, "curiosity": 0.4},
  "values": ["protect village", "honor agreements"],
  "goals": [{"id": "keep_workshop_safe", "priority": 0.9}],
  "role_constraints": {"forbidden_behaviors": ["attack"]},
  "dialogue_style": {"tone": "practical", "max_words": 45}
}
```

The profile must be separate from dynamic state. Personality, values, role
constraints, and speaking style change rarely; emotions, current goals, trust,
fear, and relationship context change per snapshot. The engine should be
instructed to explain its decision using the relevant profile and fact IDs,
without treating its explanation as an authoritative state change.

### 3. Add a deliberation input model

Create `ReasoningInput` models under `backend/app/services/reasoning/`:

- `perception_snapshot`: the immutable input from Layer 1;
- `reasoning_profile`: stable personality and role information;
- `decision_policy`: allowed intent/behavior vocabulary and priority rules;
- `response_budget`: maximum candidates, dialogue length, and latency/token
  budget.

Before generation, derive a small `DecisionFrame` from these inputs. It should
name the immediate interaction, salient facts, relevant memories, active goals,
constraints, and detected tensions. This is a deterministic preparation step,
not a second source of world facts.

### 4. Detect and resolve conflicting factors

Conflicts must be explicit rather than relying on the model to notice them
implicitly. Add a `ConflictResolver` that turns competing factors into a small
decision frame, for example:

```json
{
  "tensions": [
    {
      "id": "fear_vs_cooperation",
      "supports": ["retreat", "set_boundary"],
      "opposes": ["cooperate"],
      "evidence_fact_ids": ["threat-42", "relationship-8"],
      "policy": "immediate_safety_overrides_cooperation"
    }
  ],
  "priority_order": ["safety", "hard_role_constraints", "active_goal", "relationship", "preference"]
}
```

Initial resolution policies should be deterministic and server-owned:

1. Immediate safety/threat rules outrank cooperation and conversational goals.
2. Hard role and game constraints outrank personality preferences.
3. Active quest/role goals outrank generic conversation preferences.
4. Relationship and emotional state influence behavior only within the higher
   constraints.
5. Memory can influence trust, tone, and priorities, but cannot override a
   direct current observation or authoritative quest fact.

The LLM uses this frame to choose and phrase a response. A later Control layer
may apply additional fuzzy/rule-based constraints, but it should receive the
conflict evidence and chosen rationale rather than rediscovering the conflict.

### 5. Replace `LLMResponse` with a decision-proposal schema

The current output is structured but too limited for a reasoning handoff. Add
an output model such as `StructuredDecisionProposal`:

```json
{
  "snapshot_id": "uuid",
  "intent": "assist_player",
  "behavior": {
    "primary": "speak",
    "signals": ["reassuring", "cautious"],
    "target_entity_id": "player-1"
  },
  "dialogue": "I can help, but stay close to the path.",
  "emotion_expression": {"tone": "cautious", "intensity": 0.6},
  "confidence": 0.82,
  "grounding": {
    "fact_ids": ["player-message-81", "threat-42"],
    "memory_ids": ["memory-17"],
    "conflict_ids": ["fear_vs_cooperation"]
  },
  "reasoning_summary": "A nearby threat requires a cautious, helpful response."
}
```

Requirements:

- Use closed enums for `intent`, `behavior.primary`, and behavior signals.
- Keep dialogue separate from intent and behavior signals.
- Require snapshot/fact references for any decision that depends on a current
  game fact, quest, threat, item, or remembered interaction.
- Include confidence and a concise, non-authoritative reasoning summary for
  observability.
- Do not include direct inventory, quest, position, relationship, or state
  mutations; those belong to later layers.

### 6. Update the prompt and provider contract

Update `PromptBuilder` and the OpenAI-compatible provider to:

- accept `ReasoningInput` rather than raw context fields;
- serialize the perception snapshot as data, preserving category and source
  labels;
- provide the reasoning profile, conflict frame, allowed decision vocabulary,
  and required output JSON schema;
- tell the model to select only grounded fact IDs and to state uncertainty when
  facts conflict or are incomplete;
- use strict structured-output validation against
  `StructuredDecisionProposal`;
- preserve recent dialogue as perception-provided history rather than injecting
  it as unclassified messages outside the snapshot.

The mock provider must also consume the same `ReasoningInput`; otherwise local
development and automated tests will not exercise personality, memory, and
conflict behavior.

### 7. Make personality and adaptation observable

Add a `DecisionTrace` for every generation request. It records:

- snapshot ID and schema version;
- reasoning-profile version;
- selected salient fact, memory, and conflict IDs;
- generated decision proposal;
- schema/grounding validation outcome.

This trace measures whether the engine is behaving consistently over time. It
does not itself update emotional state, relationships, or memory; later layers
own those state transitions.

### 8. Integrate with the current pipeline

Replace this part of `ConversationPipeline.chat`:

```text
ContextBuilder -> PromptBuilder -> LLMService -> LLMResponse
```

with:

```text
PerceptionSnapshot -> ReasoningInput/DecisionFrame -> PromptBuilder
  -> LLMService -> StructuredDecisionProposal -> next Control layer
```

`RoleConditioningService` should be split:

- stable role/personality instructions move into `NPCReasoningProfile` before
  LLM generation;
- hard action/state constraints stay in the later Control/Validation layer.

`RuleEngine.evaluate()` should either become the deterministic
`ConflictResolver` input described above or be removed. Its evaluation must not
remain unused.

### Acceptance criteria

- Every reasoning request is tied to exactly one perception snapshot and
  reasoning-profile version.
- The engine derives an intent, behavior signals, dialogue, and grounding
  references in a validated structured proposal.
- Personality and relevant past interactions visibly affect decisions in
  repeatable test cases.
- Safety, hard constraints, and direct observations consistently resolve
  conflicts ahead of lower-priority cooperation or preference signals.
- The engine does not use ungrounded current-world claims or mutate
  authoritative state.
- Mock and configured LLM providers meet the same schema and grounding tests.

### Initial test scenarios

- A normally cooperative NPC with high fear and a visible threat chooses a
  cautious/helpful behavior, cites both the threat and relationship facts, and
  does not claim the threat is gone.
- A high-trust NPC reacts more helpfully to a player request than the same NPC
  with low trust, while remaining within identical hard role constraints.
- A matching memory changes dialogue tone or intent only when it is included in
  the snapshot; an excluded or stale memory has no effect.
- A player claim conflicting with authoritative inventory is not cited as a
  confirmed item fact.
- Generated output with an unknown fact ID, invalid behavior enum, or missing
  snapshot ID fails schema/grounding validation.

## State Extraction Layer

### Current implementation assessment

The project has a partial state-update path, but it does not have a distinct,
complete State Extraction Layer.

`LLMResponse.state_update` carries relative deltas for trust, fear,
aggression, and curiosity. `StateService.apply()` adds them to the persisted
NPC values and clamps the result. It also assigns `output.action` to
`npc.current_state`. This covers a small part of relative-to-absolute emotional
state conversion.

It is incomplete because:

- extraction and persistence are coupled in `StateService` instead of
  producing an explicit state vector for downstream control;
- only four scalar dimensions exist, with no structured behavior state;
- relationships are not modeled or updated;
- `emotion` is an unconstrained output string and is not mapped to a normalized
  emotional state;
- there is no per-field provenance, timestamp, extraction status, or output
  snapshot/version;
- `WorldStateSnapshot` returns inventory and quest information, not a complete
  normalized NPC state;
- the rule engine derives a relationship label but that result is discarded.

### Scope

This layer consumes a validated `StructuredDecisionProposal` from the LLM
Reasoning Engine and the current authoritative NPC state. It emits a
normalized, candidate NPC state for the later fuzzy-symbolic, validation, role
conditioning, and execution layers. It must not directly persist state or
perform inventory, quest, combat, or relationship side effects.

```text
StructuredDecisionProposal + current authoritative NPC state
  -> StateExtractor
  -> NormalizedNPCState
  -> downstream Control layers
```

### Required additions and changes

### 1. Define a complete, typed NPC state model

Create `backend/app/services/state_extraction/models.py` with explicit
separation between current state, relative updates, and extracted state.

Suggested state groups:

- **Emotion:** trust, fear, aggression, curiosity, plus a controlled
  expressed-emotion/tone label derived from the decision proposal.
- **Behavior:** current intent, proposed behavior, behavior signals, target,
  and activity mode (`idle`, `conversing`, `guarding`, `fleeing`, etc.).
- **Social:** relationship values keyed by entity or faction ID, such as trust,
  familiarity, respect, and hostility.
- **Cognitive:** active goal IDs, attention target, and confidence; this layer
  should preserve derived cognitive signals from the decision rather than
  invent new beliefs.

Each numeric dimension needs a canonical range and default. For example,
emotional and relationship dimensions can use `0.0..1.0`; confidence can use
`0.0..1.0`; behavior labels must use closed enums.

### 2. Add relationship persistence and current-state retrieval

The current `NPC` model has only scalar trust/fear/aggression/curiosity fields.
Add an `NPCRelationship` model (NPC ID, subject entity/faction ID, relationship
dimensions, updated time, and revision) or an equivalent authoritative state
store. This enables extraction to resolve and emit relationship updates without
overloading a single global `trust` value.

Add a `CurrentNPCState` loader that reads the relevant NPC, relationship, and
behavior state atomically and returns a version/revision. The state extractor
must operate on this typed object rather than directly modifying ORM entities.

### 3. Make state updates explicit in the decision schema

Extend `StructuredDecisionProposal` with an optional, typed
`proposed_state_delta` field. It should be a proposal from the reasoning layer,
not an already-applied world change.

```json
{
  "emotion": {"trust": 0.03, "fear": 0.15, "aggression": -0.02},
  "behavior": {"activity": "conversing", "attention_target_id": "player-1"},
  "relationships": [
    {"subject_id": "player-1", "trust": 0.02, "familiarity": 0.01}
  ]
}
```

Use closed fields and bounded relative deltas. Do not permit the LLM to submit
an absolute value, arbitrary state key, or direct database mutation.

### 4. Implement a pure StateExtractor

Create `StateExtractor.extract(current_state, decision_proposal)` as a pure,
deterministic service. It should:

1. validate that the decision proposal references the current perception
   snapshot and allowed state dimensions;
2. map allowed behavior/emotion signals into typed state fields;
3. apply relative deltas to current absolute values;
4. resolve one state update per dimension using a documented merge policy;
5. normalize labels and numeric representation;
6. clamp values to their configured ranges;
7. emit `NormalizedNPCState` without mutating the database.

Relative-to-absolute conversion should be explicit:

```text
candidate_absolute = clamp(current_absolute + accepted_relative_delta, min, max)
```

The result should retain `previous`, `delta`, `candidate_absolute`, and
`normalization_notes` per changed field so downstream layers can reason about
both direction and final value.

### 5. Define merge, normalization, and clamp policies

Centralize these policies in configuration rather than scattering them between
Pydantic models, `StateService`, and role conditioning.

- Define ranges, default values, precision, and allowed rate of change for each
  state dimension.
- Limit a single-turn delta and optionally a time-window delta to prevent a
  single response from causing an implausible emotional reversal.
- Resolve duplicate proposals deterministically: hard safety/control input,
  then validated decision proposal, then default/no change.
- Normalize synonymous behavior and emotion labels to a controlled vocabulary;
  reject unknown labels instead of storing free text.
- Preserve the distinction between an internal emotional value (for example,
  high fear) and its external behavioral expression (for example, cautious
  dialogue).
- Emit warnings/errors for invalid, stale, or conflicting values rather than
  silently applying them.

### 6. Define a downstream state handoff

Add a versioned `NormalizedNPCState` output contract:

```json
{
  "schema_version": "1.0",
  "state_id": "uuid",
  "source_snapshot_id": "uuid",
  "source_decision_id": "uuid",
  "state_revision": "current-revision",
  "emotion": {"trust": 0.62, "fear": 0.28, "aggression": 0.05, "curiosity": 0.54},
  "behavior": {"intent": "assist_player", "activity": "conversing", "signals": ["reassuring"]},
  "relationships": [{"subject_id": "player-1", "trust": 0.68, "familiarity": 0.31}],
  "changes": [],
  "diagnostics": []
}
```

This is the consistent state object passed to the downstream control layers.
Those layers decide whether it satisfies fuzzy rules, semantic constraints, and
role conditions; only the approved result is later persisted/executed.

### 7. Split the existing StateService

Refactor `backend/app/services/state/service.py` into distinct responsibilities:

- `StateExtractor`: pure relative-to-absolute extraction and normalization;
- `StateValidator` / later Control layer: applies cross-variable, temporal,
  fuzzy, and role constraints;
- `StateCommitter`: persists only an approved state revision after downstream
  control completes;
- separate game-state services: inventory transfer, quest progression, and
  other world mutations.

Do not set `npc.current_state = output.action` directly. Convert the validated
behavior proposal to a typed activity/behavior state in the extractor, then
allow later control layers to approve or alter it.

The existing `RuleEngine` should consume `NormalizedNPCState` or participate in
the subsequent fuzzy-symbolic layer. Its relationship-mode result must be
included in a downstream contract if it remains part of the system.

### 8. Add extraction traces and tests

Record a `StateExtractionTrace` with source snapshot/decision IDs, current
revision, accepted/rejected deltas, normalization/clamp results, and emitted
state ID. This supports debugging without making the LLM's explanation a state
authority.

Initial tests:

- A fear delta of `+0.15` applied to `0.92` produces `1.0` with a clamp note.
- A negative trust delta and a positive cooperation behavior signal remain
  separate: the extractor records both rather than rewriting one to fit the
  other.
- An unknown emotion/behavior label or unknown relationship subject is
  rejected.
- Two updates for the same relationship dimension use the configured merge
  policy deterministically.
- The extractor returns an identical output for identical current state and
  decision input, and does not modify database rows.
- Inventory and quest payloads cannot be changed through a state-extraction
  proposal.

### Acceptance criteria

- Every accepted LLM state proposal is converted into typed, bounded relative
  values and resolved absolute values.
- Emotional, behavioral, and relationship state are represented separately.
- All numeric values are normalized and clamped under one documented policy.
- The result is a versioned, complete `NormalizedNPCState` suitable for later
  control layers, with provenance and diagnostics.
- Extraction is deterministic and side-effect free; persistence occurs only
  after downstream control approves the candidate state.

## Fuzzy-Symbolic Layer

### Current implementation assessment

No complete fuzzy-symbolic layer exists today. The existing `RuleEngine` uses
hard thresholds to label four values as `LOW`, `MEDIUM`, or `HIGH`, then selects
one of `friendly`, `hostile`, or `neutral`. This is symbolic bucketing, not
fuzzy inference:

- a value belongs to exactly one category instead of having degrees of
  membership in overlapping categories;
- there are only two hard-coded two-variable rules;
- no rule weight, activation strength, aggregation, or defuzzification exists;
- behavior tendencies are not produced; and
- the pipeline computes the evaluation but discards it.

### Scope

This layer consumes `NormalizedNPCState` from State Extraction and produces an
interpretable `BehaviorShapingResult` for the later validation, role
conditioning, and execution layers. It does not read raw LLM text, decide quest
or inventory facts, persist NPC state, or execute behavior.

```text
NormalizedNPCState
  -> fuzzification
  -> weighted IF-THEN rule inference and aggregation
  -> behavior shaping / defuzzification
  -> BehaviorShapingResult
  -> later Control and Execution layers
```

### Required additions and changes

### 1. Define fuzzy variables and membership functions

Create `backend/app/services/fuzzy/` with typed definitions for input and
output variables. Initial input variables should include at least:

- `fear`, `trust`, `aggression`, and `curiosity` from normalized NPC state;
- `threat_level` and `relationship_trust` when present in the state/snapshot;
- optional `goal_urgency` and `cooperation_signal` from the decision proposal.

For every `0.0..1.0` input define overlapping LOW, MEDIUM, and HIGH membership
functions. Triangular or trapezoidal functions are sufficient initially and
must be configurable, for example:

```text
LOW    = trapezoid(0.00, 0.00, 0.20, 0.45)
MEDIUM = triangle (0.25, 0.50, 0.75)
HIGH   = trapezoid(0.55, 0.80, 1.00, 1.00)
```

At `fear = 0.40`, the NPC may simultaneously have LOW fear at `0.20` and
MEDIUM fear at `0.60`. Do not use the current exclusive `bucket()` function
for fuzzy evaluation.

Membership definitions, ranges, and labels must live in versioned configuration
or typed data files, not inline conditional statements. Validate that each
function has ordered points and maps inputs to `0.0..1.0`.

### 2. Define controllable output variables

The layer should shape behavior rather than directly choose or execute an
action. Start with normalized output tendencies such as:

- `cooperation_tendency`;
- `caution_tendency`;
- `assertiveness_tendency`;
- `avoidance_tendency`;
- `dialogue_warmth`;
- `dialogue_directness`.

Each output has LOW/MEDIUM/HIGH membership sets and a final numeric value in
`0.0..1.0`. Later layers combine these tendencies with hard role rules and
engine constraints to select a permitted action.

### 3. Add a declarative weighted IF-THEN rule set

Store rules as data (JSON, YAML, or Pydantic-loaded Python configuration) with
stable IDs, descriptions, antecedents, consequent(s), weight, enabled status,
and version. Example:

```yaml
id: fear_high_trust_high_be_cautiously_helpful
when:
  all:
    - {variable: fear, is: HIGH}
    - {variable: trust, is: HIGH}
then:
  - {variable: caution_tendency, is: HIGH}
  - {variable: cooperation_tendency, is: MEDIUM}
weight: 0.90
```

Initial rules should cover competing combinations, not only friendly/hostile
labels:

- high fear + high trust: cautious cooperation;
- high fear + low trust: avoidance/boundary setting;
- low fear + high aggression + low trust: assertive behavior;
- low fear + high trust: warm cooperation;
- high threat: elevate caution/avoidance regardless of background preference;
- high curiosity + low threat: elevate information-seeking/directness.

Rules must be editable without a code deployment and reviewed as game-design
content. A rule change should increment a ruleset version attached to every
result.

### 4. Implement fuzzification, inference, and aggregation

Create a pure `FuzzyInferenceEngine.evaluate(normalized_state)` service.

1. **Fuzzify:** compute each input's membership degree for LOW/MEDIUM/HIGH.
2. **Evaluate antecedents:** use a documented operator, initially `min` for
   `all` and `max` for `any`.
3. **Apply rule weight:** `activation = antecedent_degree * rule.weight`.
4. **Apply consequents:** clip each output membership set by its activation.
5. **Aggregate:** combine contributions to each output label using `max`.
6. **Defuzzify:** compute one numeric tendency per output, initially centroid
   defuzzification over the `0.0..1.0` domain.

The choice of operators must be configurable and captured in the output
metadata. Do not let an LLM calculate memberships or rule activations.

### 5. Return an interpretable behavior-shaping contract

Add a versioned `BehaviorShapingResult` model:

```json
{
  "schema_version": "1.0",
  "source_state_id": "uuid",
  "ruleset_version": "v1",
  "input_memberships": {
    "fear": {"LOW": 0.0, "MEDIUM": 0.35, "HIGH": 0.65}
  },
  "tendencies": {
    "cooperation_tendency": 0.58,
    "caution_tendency": 0.84,
    "avoidance_tendency": 0.42
  },
  "dominant_labels": {"caution_tendency": "HIGH"},
  "rule_contributions": [
    {"rule_id": "fear_high_trust_high_be_cautiously_helpful", "activation": 0.59, "consequents": []}
  ],
  "diagnostics": []
}
```

The result must retain every active rule's contribution—not merely the winning
label—so designers can explain why a behavior was shaped. Add a minimum
activation threshold for trace readability, while retaining full details in
debug mode.

### 6. Integrate it into the control pipeline

Replace the unused call to `RuleEngine.evaluate(npc)` with the sequence:

```text
StructuredDecisionProposal
  -> StateExtractor
  -> NormalizedNPCState
  -> FuzzyInferenceEngine
  -> BehaviorShapingResult
  -> Validation / Role Conditioning / Execution
```

The existing `RuleEngine` can be retired after its simple labels are represented
as fuzzy memberships and declarative rules. It must not run in parallel as an
untracked source of behavior decisions.

Role conditioning remains a later hard-constraint layer: fuzzy tendencies may
suggest assertiveness but cannot authorize a forbidden action. The fuzzy result
may adjust permitted behavior selection, animation/dialogue tone, pacing, and
other engine parameters only after validation.

### 7. Add designer controls and safety limits

- Provide a ruleset validation command/test that detects invalid memberships,
  unknown variables, out-of-range weights, duplicate IDs, and unreachable
  rules.
- Permit rules to be enabled/disabled and weights tuned through versioned game
  configuration.
- Define safe fallback tendencies when no rule activates or the ruleset fails
  validation; never reuse stale output without marking it.
- Bound every defuzzified output to `0.0..1.0` and record clamping or fallback
  diagnostics.
- Separate hard constraints from fuzzy preferences so game designers cannot
  accidentally use a weight change to bypass safety or role restrictions.

### Acceptance criteria

- Numeric inputs map to overlapping LOW/MEDIUM/HIGH membership degrees rather
  than an exclusive threshold bucket.
- Multiple state signals activate weighted IF-THEN rules and contribute to the
  same behavior tendency.
- The engine produces bounded numeric behavior tendencies and interpretable
  contribution traces.
- Rule configuration is versioned, validated, and adjustable without modifying
  inference code.
- The result is consumed by a downstream control layer; it is never silently
  calculated and discarded.
- Identical state and ruleset inputs produce identical behavior-shaping output.

### Initial test scenarios

- At the LOW/MEDIUM and MEDIUM/HIGH boundaries, membership degrees overlap and
  remain within `0.0..1.0`.
- High fear, high trust, and a nearby threat activate both caution and
  cooperation contributions; caution dominates without eliminating cooperation.
- High aggression and low trust activate assertiveness, but a later role rule
  still rejects a forbidden attack action.
- Increasing one rule's weight increases only its documented contribution and
  predictably changes the affected tendency.
- An invalid or disabled rule cannot influence output; an empty valid ruleset
  returns the documented fallback result.

## Role Conditioning Layer

### Current implementation assessment

The project has a partial `RoleConditioningService`, but not a complete role
conditioning layer. It currently defines constraints for only `craftsman` and
`gatherer`, replaces `attack`/`declare_war` with `speak`, and caps the proposed
**aggression delta**. Validation separately rejects some role-forbidden actions.

This is insufficient because:

- roles do not have complete allowed-action sets, required permissions, targets,
  or context preconditions;
- unknown roles default to no restrictions;
- capping a delta does not cap the NPC's final absolute aggression;
- fear, trust, curiosity, behavior tendencies, dialogue tone, and relationship
  responses have no role-specific policy;
- no role-driven weights/multipliers influence fuzzy behavior shaping;
- silently replacing an action with `speak` loses the rejected-action reason;
- there is no versioned role profile or conditioned-state handoff.

### Scope

Role Conditioning consumes the validated behavior, normalized NPC state, and
fuzzy behavior-shaping result. It applies the NPC's immutable or
slow-changing role policy and emits a role-aligned candidate for execution. It
does not create role definitions from LLM output, bypass hard game constraints,
or persist/execute the candidate.

```text
DecisionProposal + NormalizedNPCState + BehaviorShapingResult + RoleProfile
  -> RoleConditioner
  -> RoleConditionedBehavior
  -> final Control / Execution layers
```

### Required additions and changes

### 1. Define versioned role profiles

Replace the in-code `ROLE_CONSTRAINTS` dictionary with validated, versioned role
profiles under `backend/app/services/roles/` or game-design configuration.
Every NPC references one profile by stable role ID and profile version.

Each `RoleProfile` should define:

- allowed, denied, and required action/behavior sets;
- valid targets and prerequisites for each allowed behavior;
- hard absolute caps/floors for emotional and relationship dimensions;
- role emotional baseline and allowed expression vocabulary;
- behavior-tendency multipliers and caps;
- dialogue tone/style constraints;
- role goals and non-negotiable duties;
- safe fallback behavior when a proposal is denied.

Example:

```yaml
role_id: craftsman
version: v1
actions:
  allowed: [speak, ask_question, trade, request_materials, repair_tool, craft_item]
  denied: [attack, declare_war, steal]
emotion_policy:
  aggression: {max_absolute: 0.20, delta_multiplier: 0.35}
  fear: {max_absolute: 0.70, delta_multiplier: 0.80}
behavior_modifiers:
  cooperation_tendency: {multiplier: 1.15, max: 0.95}
  assertiveness_tendency: {multiplier: 0.60, max: 0.35}
safe_fallback: {behavior: speak, signal: practical_boundary}
```

Profiles are authoritative design data. The LLM may be prompted with a concise
role description, but cannot alter a profile or request an unlisted privilege.

### 2. Enforce action permissions and preconditions

Implement a `RolePermissionEvaluator` before the final execution handoff. It
must validate:

- whether the proposed intent/behavior is allowed for this role;
- whether the selected target type is allowed;
- whether role-specific conditions are met (for example, a craftsman must have
  access to a workshop and valid materials before a crafting behavior can be
  considered);
- whether an action conflicts with non-negotiable duties or faction alignment.

Return a typed decision: `allowed`, `conditioned`, `denied`, or `fallback`,
with the matching profile rule ID and reason. Do not silently turn an invalid
action into `speak`; use the declared safe fallback only when the product policy
permits it, and record why.

### 3. Condition emotions using absolute caps and bounded modifiers

Role policy should shape emotional response without erasing the state extracted
from the decision. For each role-controlled dimension:

```text
role_adjusted_delta = clamp(proposed_delta * role_multiplier, min_delta, max_delta)
role_adjusted_absolute = clamp(current_absolute + role_adjusted_delta, role_floor, role_cap)
```

Apply this to fear, trust, aggression, curiosity, and role-specific social
dimensions where appropriate. Store both the original and conditioned values.
This corrects the current implementation, which only limits an aggression delta
and can still leave final aggression above a role's intended maximum.

The profile must separately constrain **expression** (tone, animation,
assertiveness) from internal emotion. A peaceful gatherer may feel high fear
but should express it through retreat, caution, or a request for help—not an
out-of-role attack.

### 4. Apply role-driven fuzzy-output modifiers

Use the `BehaviorShapingResult` as an input to a deterministic
`RoleConditioner`. For each permitted behavior tendency:

```text
conditioned_tendency = clamp(fuzzy_tendency * role_multiplier, role_min, role_max)
```

Examples:

- a guard profile may raise alertness/assertiveness within a defined cap;
- a healer profile may raise cooperation and reduce aggression expression;
- a craftsman may favor practical/helpful interaction and lower combat
  tendencies;
- a gatherer may favor avoidance when threat is high and exploration when it is
  low.

Hard denials always override multipliers. Role multipliers should adjust fuzzy
preferences, not grant a forbidden action or bypass a safety/control rule.

### 5. Emit a role-conditioned handoff object

Add a `RoleConditionedBehavior` model:

```json
{
  "schema_version": "1.0",
  "source_state_id": "uuid",
  "source_behavior_shaping_id": "uuid",
  "role_id": "craftsman",
  "role_profile_version": "v1",
  "permission": {"status": "allowed", "rule_id": "craftsman.speak"},
  "conditioned_behavior": {"primary": "speak", "signals": ["practical", "cautious"]},
  "conditioned_state": {"aggression": 0.18, "fear": 0.31},
  "applied_modifiers": [],
  "diagnostics": []
}
```

The result must show every applied cap, multiplier, fallback, and denied
proposal. It is the final role-aligned candidate passed to later execution
mapping; it is not a committed NPC state.

### 6. Integrate with the control sequence

Refactor the current ordering so role policy evaluates typed, normalized data
rather than a raw `LLMResponse`:

```text
StructuredDecisionProposal
  -> StateExtractor
  -> FuzzyInferenceEngine
  -> ControlValidationService
  -> ValidatedBehavior
  -> RoleConditioner
  -> RoleConditionedBehavior
  -> FSEC
```

Move stable role personality/style data into the LLM Reasoning profile as a
hint for coherent generation, but retain the `RoleConditioner` as the
authoritative post-generation enforcement point. Remove duplicated role action
lists from `ValidationService` after the role permission evaluator owns them,
or make validation delegate to the same profile source so policies cannot
diverge.

### 7. Add profile validation and tests

- Validate that every role has a safe fallback, a finite set of actions, and
  ranges/multipliers within allowed bounds.
- Reject role profiles that allow behaviors unavailable in the engine mapping.
- Version and log every profile used for a conditioned result.
- Test each denied action and precondition, not only the happy path.

Initial tests:

- A craftsman or gatherer can never emit an executable attack/war behavior,
  even when the LLM proposal and fuzzy aggression are high.
- A role cap limits final aggression after relative-to-absolute conversion, not
  only a single update delta.
- Identical fuzzy state produces different but predictable conditioned behavior
  for a guard, healer, craftsman, and gatherer profile.
- High fear for a peaceful role produces an allowed cautious/avoidant behavior
  and role-aligned emotional expression.
- A denied proposal records its role rule and safe fallback rather than being
  silently changed.

### Acceptance criteria

- All executable behavior is checked against one versioned, authoritative role
  profile.
- Role profiles constrain permissions, targets, preconditions, emotional state,
  emotional expression, and fuzzy behavior tendencies.
- Final absolute emotion values respect role caps/floors after all modifiers.
- Forbidden behavior cannot be reintroduced by an LLM proposal, fuzzy rule, or
  later mapping error.
- Conditioned results are traceable to the input state, fuzzy result, and role
  profile version.

## FSEC (Fuzzy State Engine Controller) Layer

### Current implementation assessment

No FSEC layer currently exists. The backend returns a validated dialogue/action
field, while the Godot client updates an NPC label with four state values and
displays dialogue. It does not receive an executable NPC command, select among
actions with utility scoring, drive NPC movement/animation, or report command
outcomes back to the backend.

The current chat response is therefore a dialogue UI response, not a bridge
between the behavioral-control stack and the game engine.

### Scope

FSEC consumes a `RoleConditionedBehavior` that has passed Control Validation
and maps it to a selected,
engine-neutral NPC controller command. It may use authoritative engine state to
check action feasibility, but it does not regenerate LLM decisions, alter fuzzy
rules, or directly change game facts. The game engine executes the command and
reports the outcome through a separate authoritative feedback path.

```text
RoleConditionedBehavior + current engine capability state
  -> candidate actions
  -> utility scoring and selection
  -> parameter mapping
  -> NPCControllerCommand
  -> Godot NPC controller
  -> execution outcome feedback
```

### Required additions and changes

### 1. Define engine capabilities and a controller-action vocabulary

Create a shared, versioned action contract between backend and Godot. Start
with only actions the Godot NPC controller can actually perform, for example:

- `idle`;
- `speak`;
- `face_target`;
- `move_to` / `approach_target`;
- `retreat_from_target`;
- `interact`;
- `play_animation`.

Each action definition must declare allowed target types, required parameters,
preconditions, cancellation behavior, expected duration, and outcome events.
Game-specific actions such as trade, crafting, quest reward, combat, or item
transfer must remain separate authoritative game-system operations; FSEC can
request an interaction but cannot fabricate their success.

Add an engine capability snapshot for each NPC/controller (position, navigation
availability, animation set, current command, movement limits, interactable
targets, and blocked/unavailable status). FSEC should not select `move_to` if
the controller lacks a reachable target or navigation capability.

### 2. Generate eligible action candidates

Implement an `FSECController` service under `backend/app/services/fsec/`.
It converts the role-conditioned behavior into a finite candidate set before
scoring it.

- Apply hard eligibility first: role permission, target existence, distance,
  navigation path, action cooldown, animation support, and current controller
  lock/interruptibility.
- Map behavior signals to candidates: `cautious` may add `face_target` and
  `retreat_from_target`; `reassuring` may add `speak` with a calm animation;
  `practical` may add `approach_target` only when interaction range is needed.
- Keep dialogue as a payload of `speak`, not an engine action that implies
  movement or an inventory change.
- Record every rejected candidate and its eligibility reason.

### 3. Add utility-based action selection

Create a deterministic `UtilityScorer` that scores only eligible candidates.
The score should combine normalized signals from the prior layers:

```text
utility(action) =
  goal_alignment * w_goal
  + role_fit * w_role
  + fuzzy_behavior_fit * w_behavior
  + safety * w_safety
  + interaction_relevance * w_interaction
  + feasibility * w_feasibility
  - interruption_cost * w_interrupt
```

Rules for selection:

- hard safety and role denials exclude an action rather than merely lowering
  its score;
- weights are versioned configuration, with role-specific overrides within
  safe bounds;
- use a deterministic tie-breaker (priority, then action ID) so identical
  input produces identical commands;
- allow controlled stochasticity only when explicitly configured, seeded, and
  logged for replay;
- select a safe `idle`/`speak` fallback when no candidate is eligible.

Return each candidate's component scores, total score, selected status, and
ruleset/configuration versions for designer inspection.

### 4. Map behavioral state to engine parameters

Add declarative mapping tables from `RoleConditionedBehavior` and
`BehaviorShapingResult` to engine-neutral controller parameters.

Initial mappings should cover:

| Input signal | Engine parameter examples |
| --- | --- |
| `caution_tendency` | preferred distance, retreat threshold, turn speed, cautious animation blend |
| `assertiveness_tendency` | approach distance, movement speed cap, posture/animation blend |
| `cooperation_tendency` | interaction willingness, facing target, warm dialogue tone tag |
| emotional expression | animation state, voice/dialogue tone tag, idle variation |
| selected target | target entity ID, navigation destination, facing direction |
| role profile | permitted animation set, movement speed/range caps, interaction set |

The mappings must be bounded and validated. For example, a high fear tendency
can increase a preferred distance but cannot produce an invalid negative speed
or route an NPC through blocked geometry. Keep visual tone parameters separate
from authoritative simulation parameters.

### 5. Define an idempotent NPC controller command schema

Create a versioned `NPCControllerCommand` model that is independent of Godot
implementation details:

```json
{
  "schema_version": "1.0",
  "command_id": "uuid",
  "npc_id": 1,
  "source_state_id": "uuid",
  "source_role_conditioned_id": "uuid",
  "controller_revision": 12,
  "kind": "approach_target",
  "target": {"entity_id": "player-1", "position": null},
  "parameters": {
    "arrival_distance": 48.0,
    "max_speed": 110.0,
    "animation": "walk_cautious",
    "dialogue_tone": "reassuring"
  },
  "issued_at": "2026-09-12T12:00:00Z",
  "expires_at": "2026-09-12T12:00:03Z",
  "interrupt_policy": "replace_lower_priority"
}
```

Commands require an ID, source IDs, expiry, controller revision, and explicit
interrupt policy. The game client must treat repeated command IDs as
idempotent, reject stale revisions, and never execute arbitrary commands that
do not validate against the shared vocabulary.

### 6. Build the backend-to-Godot bridge

Add a command-delivery mechanism instead of relying on chat responses alone.
Choose one transport appropriate for the game's update rate:

- an initial polling endpoint such as `GET /npc/{id}/commands?after=...`; or
- a WebSocket/server-sent-event channel for low-latency commands and outcomes.

Godot should add a real NPC controller script (movement/navigation,
animation-player integration, facing, interaction range) that:

1. receives and validates `NPCControllerCommand`;
2. performs the mapped movement/animation/interaction presentation;
3. acknowledges acceptance, rejection, completion, interruption, or failure;
4. reports authoritative observed outcomes and final position to the backend.

The backend must verify outcome reports against the active command and current
world state before emitting any new world event. Client acknowledgement is not
proof that an inventory transfer, quest update, or combat result occurred.

### 7. Add command lifecycle and feedback records

Persist or reliably queue command lifecycle data:

```text
issued -> acknowledged -> running -> completed | failed | cancelled | expired
```

Each transition records command ID, NPC ID, time, controller revision, and
reason. Feed completed/failed outcomes to the later persistent-memory and
perception/event systems as authoritative engine events. This closes the loop
without letting the FSEC layer itself write memories or mutate unrelated state.

### 8. Integrate the full handoff sequence

The target sequence is:

```text
PerceptionSnapshot
  -> LLM Reasoning Engine
  -> State Extraction
  -> Fuzzy-Symbolic Layer
  -> Control Validation
  -> Role Conditioning
  -> FSEC candidate selection and utility scoring
  -> NPCControllerCommand
  -> Godot NPC controller / engine outcome
```

The existing `ChatResponse.validated_output.action` should be retained only as
a temporary dialogue compatibility field. It must not be treated as the final
engine command once FSEC is introduced. Expose command status separately so the
UI can render pending movement, animation, failures, and completed interactions.

### 9. Add replayable tests and observability

Record an `FSECTrace` containing candidate eligibility, component utility
scores, selected command, parameter mapping, and command lifecycle IDs.

Initial tests:

- Given identical conditioned behavior, engine capability state, and utility
  configuration, FSEC always selects the same command.
- An unavailable/blocked path makes `approach_target` ineligible and selects a
  safe alternative.
- High caution increases preferred distance and selects retreat/facing behavior
  when safety rules permit it.
- A role-denied action never becomes a candidate, even with the highest raw
  utility.
- Replayed command IDs do not cause duplicate movement or interaction.
- A stale command revision or expired command is rejected by Godot and recorded
  as such by the backend.

### Acceptance criteria

- Role-conditioned behavioral state becomes one explicit, engine-neutral
  controller command rather than only a dialogue/action string.
- Eligible candidates are selected through versioned, interpretable utility
  scoring with hard constraints applied first.
- State and fuzzy tendencies map to bounded movement, animation, interaction,
  and dialogue-tone parameters.
- Godot executes only validated, idempotent commands and reports their
  lifecycle/outcomes.
- Command outcomes can re-enter the perception/event loop as authoritative
  engine facts.

## Validation Layer

### Current implementation assessment

The existing `ValidationService` is a useful first-pass response validator, but
it is not sufficient as the architecture's Validation Layer or as a reliable
decision-making aid. It currently validates JSON shape, dialogue length, a
small action allowlist, selected inventory/quest claims, per-turn delta bounds,
and a few keyword-based contradictions. It also has a fallback response path.

Missing capabilities include:

- no validation of the proposed decision against a versioned perception
  snapshot, state-extraction result, fuzzy contributions, or role profile;
- no general conflict detection/resolution across fear, trust, aggression,
  intent, behavior, and action;
- no temporal smoothing, rate limiting, cooldown validation, or prevention of
  abrupt behavioral flips;
- no cross-variable semantic constraints beyond a few dialogue keywords;
- no unified, versioned `ValidatedBehavior` handoff with rejection/repair
  diagnostics; and
- no way for validation results to constrain downstream action selection other
  than rejecting a raw LLM response.

### Scope

Validation is a Control-layer gate. It consumes the structured decision,
normalized candidate state, and fuzzy behavior-shaping result. It produces a
validated, smoothed, constraint-compliant behavior for Role Conditioning. It
does not create facts, re-run LLM reasoning, persist state, or execute engine
commands.

```text
DecisionProposal + NormalizedNPCState + FuzzyResult
  -> structural / semantic / temporal validation
  -> ValidatedBehavior
  -> Role Conditioning
```

### Required additions and changes

### 1. Split response schema checks from control validation

Keep a narrow `DecisionProposalValidator` immediately after LLM generation to
validate JSON structure, closed enums, required snapshot/fact references, and
basic numeric types. Replace the current broad `ValidationService` as the sole
gate with a separate `ControlValidationService` for later-layer validation.

This prevents raw dialogue checks, item-transfer special cases, role policy,
and temporal behavior control from being mixed in one class. Inventory, quest,
and ownership operations should continue through their own authoritative game
services.

### 2. Validate structural and provenance consistency

The Control Validation Layer must reject or repair candidates when:

- source snapshot, state, fuzzy-result, role-profile, or ruleset IDs do not
  match the current decision chain;
- a referenced fact, memory, target, or relationship is absent or stale;
- behavior/action/target parameters are not in the shared contracts;
- a role-conditioned permission is denied or lacks its required preconditions;
- values are non-finite, out of canonical range, or missing required
  provenance.

These checks should return explicit machine-readable codes rather than relying
on matching dialogue words such as `attack` or `gift`.

### 3. Add semantic constraints and conflict resolution

Implement declarative cross-variable constraints over the typed inputs and
candidate behavior. Examples:

- high `caution_tendency` cannot result in an unprotected close-approach
  command toward a known threat;
- a behavior targeted at an entity must have a matching, visible/reachable
  target in the source perception snapshot;
- `cooperation` and `retreat` can coexist as tendencies, but the selected
  behavior must define a coherent safe-distance policy;
- a peaceful role with high aggression may express firm boundaries, but cannot
  select a role-denied violent behavior;
- a stated intent, behavior signals, dialogue tone, and selected action must
  agree or provide a declared conflict/fallback reason.

Use a deterministic precedence order for unresolved conflicts:

```text
safety and authoritative-world constraints
  > role permissions and hard game constraints
  > temporal/controller feasibility
  > active intent and goal alignment
  > fuzzy preferences and dialogue presentation
```

The validator may narrow parameters, select a declared safe fallback, or reject
the candidate. It must record which constraint won; it must not invent a new
quest, relationship, item, or world fact to make a candidate pass.

### 4. Add temporal smoothing and continuity rules

Introduce a per-NPC `BehaviorHistory` / control-state record containing the
last approved state, behavior, command, timestamps, cooldowns, and active
interrupt policy. Apply smoothing after state extraction and before FSEC:

```text
smoothed_value = alpha * candidate_value + (1 - alpha) * prior_approved_value
```

Use per-dimension `alpha`, maximum rate-of-change, and hysteresis thresholds.
Examples:

- fear and trust cannot jump from LOW to HIGH in one ordinary conversational
  turn without an urgent observed event;
- behavior selection requires a utility advantage above a switch threshold
  before interrupting a currently valid action;
- animation/movement parameters interpolate over a configured duration rather
  than snapping each update;
- immediate threat/safety events can bypass normal smoothing, with an explicit
  `emergency_override` diagnostic.

Smoothing must use prior **approved** state, not an unvalidated LLM proposal or
client report.

### 5. Centralize ranges, constraints, and repair policy

Create versioned control-policy configuration for:

- numeric min/max values, delta/rate limits, and smoothing parameters;
- target distance and movement/interaction safety bounds;
- behavior compatibility matrices and intent-to-action mappings;
- role-independent hard safety rules;
- repair choices: parameter clamp, safe fallback, reject/retry, or idle.

Use one source of truth for bounds currently duplicated across Pydantic fields,
`StateService`, role conditioning, and FSEC mappings. Every automatic repair
must retain the original candidate and a diagnostic explaining the correction.

### 6. Emit a validated-behavior handoff

Add a `ValidatedBehavior` model for FSEC:

```json
{
  "schema_version": "1.0",
  "validation_id": "uuid",
  "source_snapshot_id": "uuid",
  "source_state_id": "uuid",
  "source_fuzzy_result_id": "uuid",
  "source_role_conditioned_id": "uuid",
  "status": "approved | repaired | fallback | rejected",
  "intent": "assist_player",
  "behavior": {"primary": "speak", "signals": ["cautious", "reassuring"]},
  "parameters": {"preferred_distance": 96.0},
  "smoothed_state": {},
  "applied_constraints": [],
  "diagnostics": []
}
```

FSEC receives only an approved, repaired, or declared fallback object. A
rejected result must stop command creation and trigger the system's configured
safe response path.

### 7. Integrate validation at the correct stages

The target pipeline becomes:

```text
LLM DecisionProposal
  -> DecisionProposalValidator
  -> State Extraction
  -> Fuzzy-Symbolic Layer
  -> Role Conditioning
  -> ControlValidationService (semantic + temporal + constraints)
  -> ValidatedBehavior
  -> FSEC utility selection and engine command mapping
```

Move raw-output fallback handling next to `DecisionProposalValidator`. The
later validation layer should reason over typed candidate state/behavior and
can provide constraint-aware parameters or a safe fallback to FSEC.

### 8. Add traces and test suites

Record a `ValidationTrace` with input IDs, policy versions, constraint
evaluations, original values, smoothing calculations, repairs, final status,
and fallback reason.

Initial tests:

- A candidate approach toward a visible high-threat entity is repaired to a
  safe-distance/retreat behavior according to the precedence policy.
- Alternating LLM proposals cannot cause NPC behavior to flip between approach
  and retreat unless utility/safety thresholds are met.
- An urgent observed threat bypasses smoothing and records an emergency
  override.
- A role-allowed behavior with an invalid target or missing provenance is
  rejected before FSEC command generation.
- Values at bounds, just outside bounds, and non-finite values receive the
  configured clamp/reject treatment with diagnostics.
- An intent/dialogue/action mismatch is caught using typed behavior fields, not
  a brittle keyword-only check.

### Acceptance criteria

- Validation checks structural, provenance, semantic, temporal, and
  cross-variable consistency—not only raw JSON and keywords.
- Conflicting signals are resolved by documented precedence rules, with a
  traceable repair/fallback when needed.
- Ordinary state and behavior changes are smoothed, rate-limited, and
  hysteresis-controlled; safety events can explicitly override them.
- All final values and parameters meet one versioned constraint policy.
- FSEC receives a consistent, validated behavior object or no command at all.

## Game Engine / NPC Controller Layer

### Current implementation assessment

No Game Engine / NPC Controller Layer exists today. Godot NPCs are `Area2D`
nodes used for proximity interaction and labels; they have no movement,
navigation, controller state machine, animation state machine, command queue,
or command-outcome reporting. The only `CharacterBody2D` movement implementation
belongs to the player. Backend actions are displayed as chat/UI data rather
than executed controller behavior.

### The action–dialogue synchronization dilemma

NPC dialogue must remain true at the moment the player hears it. A controller
cannot safely display “I gave you the wood,” “I reached the gate,” or “the path
is clear” merely because an LLM or FSEC command proposed it. Movement may fail,
the target may disappear, the NPC may be interrupted, or an authoritative game
system may reject the interaction.

Use three explicit dialogue timing classes:

- **Immediate expression:** a statement of current internal expression that can
  occur at command start, such as “Stay close; I am nervous.”
- **Commitment / intent:** an in-progress, non-completion claim, such as “I’ll
  come with you” or “Let me check the workshop.” It may be shown only after the
  command is accepted and must be cancelled/updated if the command fails.
- **Authoritative outcome:** a claim about a completed movement, interaction,
  transfer, quest, combat, or world fact. It may be displayed only after the
  engine and relevant authoritative game service report success.

This distinction keeps NPC responses aligned with action without making the UI
feel silent while an NPC moves. The controller may speak immediate expression
while starting movement, but the backend/game system owns outcome statements.

### Scope

This layer consumes `NPCControllerCommand` from FSEC and executes it in Godot.
It controls physics, navigation, animation, interactions, and dialogue timing;
it reports observed outcomes. It does not select utilities, reinterpret fuzzy
state, create game facts, or independently decide actions.

```text
NPCControllerCommand
  -> Godot NPC command queue and state machine
  -> movement / animation / interaction / speech events
  -> authoritative outcome acknowledgement
  -> backend event and perception feedback
```

### Required additions and changes

### 1. Replace the display-only NPC with a controllable actor

Refactor `frontend/godot/scripts/npc.gd` and NPC scene construction so each
NPC is a controllable physics actor:

- use `CharacterBody2D` for mobile NPCs, with a child `Area2D` reserved for
  player interaction detection;
- add `CollisionShape2D`, navigation support (`NavigationAgent2D` plus a
  `NavigationRegion2D`/navigation map), facing direction, velocity, and
  movement limits;
- retain the visual/body and label as children of the controller actor;
- give stationary roles a controller that still supports facing, animation,
  dialogue, interaction, and interruption even when movement is disabled;
- maintain an engine-side NPC registry mapping authoritative `npc_id` to the
  controller node.

The backend remains authoritative for game identity and command issuance; the
scene must not infer NPC role, permissions, or state changes from visual names.

### 2. Implement a controller state machine

Build an explicit, testable `NPCControllerStateMachine` in Godot. Initial
states should include:

```text
Idle
  -> ReceivingCommand
  -> FacingTarget
  -> Navigating
  -> Arrived
  -> Interacting
  -> Speaking
  -> Completing
  -> Idle

Any active state -> Interrupted | Failed | Cancelled
```

Each transition requires a named event and must record the active command ID.
For example, `Navigating -> Arrived` occurs only within arrival distance;
`Interacting -> Completing` occurs only after the relevant engine/game-system
acknowledgement. Commands must define whether they can interrupt an existing
state and which states they are allowed to replace.

Avoid setting animation or velocity directly from a chat response. All changes
go through this state machine so the visual state, physics state, command
lifecycle, and backend outcome stay consistent.

### 3. Execute movement through navigation and physics

For `move_to`, `approach_target`, and `retreat_from_target` commands:

- validate that the target/position is present and still valid;
- calculate navigation paths through `NavigationAgent2D` rather than moving in
  a straight line through walls;
- steer with bounded velocity and `move_and_slide()` so collisions use Godot
  physics;
- observe arrival distance, path failure, blocked movement, target movement,
  timeout, and stuck detection;
- replan only under a configured cadence/budget; report failure after bounded
  retries rather than looping indefinitely;
- use FSEC parameters such as preferred distance and speed only after clamping
  them to controller/role capabilities.

For non-mobile NPCs, return a structured `unsupported_capability` outcome
instead of pretending to move.

### 4. Drive animation through a separate animation state machine

Add `AnimationTree`/`AnimationPlayer` integration or a small explicit adapter
that maps controller states and FSEC parameters to available clips/blends:

- `idle`, `walk`, `walk_cautious`, `face_target`, `talk_calm`, `talk_firm`,
  `interact`, `retreat`, and `failure` are an initial vocabulary;
- controller state chooses the base animation; role and behavior tone choose
  only a permitted variation/blend;
- movement speed drives walk blend/playback rate within safe visual bounds;
- animation completion/notifies gate interactions that require a visible
  gesture;
- absent animation assets fall back to a declared safe clip and produce a
  diagnostic rather than breaking the command.

The existing procedural `person.gd` visual can remain temporarily, but it must
receive controller-state signals rather than infer walking solely from whether
its parent happens to be a `CharacterBody2D`.

### 5. Model interactions as authoritative requests

`interact` commands should identify an interaction type and target but not
apply outcomes locally. The controller must:

1. verify local range, target presence, and controller state;
2. play the interaction/facing animation;
3. send an interaction-attempt event containing command ID, NPC ID, target ID,
   position, and controller revision;
4. wait for backend/game-system acknowledgement;
5. present the approved outcome or failure through the state machine.

Inventory transfer, crafting completion, quest advancement, and combat results
are especially important: they must be confirmed by their authoritative service
before the controller plays completion dialogue or effects.

### 6. Implement dialogue as controller events

Extend `NPCControllerCommand` with an optional dialogue event:

```json
{
  "dialogue": {
    "text": "I will take a look.",
    "timing": "on_command_accepted | on_arrival | on_interaction_success | on_failure",
    "kind": "expression | commitment | outcome",
    "tone": "cautious"
  }
}
```

The controller displays dialogue only when its timing condition is satisfied.
For `outcome` text, require a corresponding authoritative outcome ID; reject
the display request if it is absent. When a commitment command is cancelled,
emit a follow-up controller event so the backend can decide whether a truthful
interruption line should be generated.

The chat UI should subscribe to controller dialogue events rather than display
`final_dialogue` immediately for every nontrivial action. Maintain a temporary
dialogue-only compatibility path for `speak` commands whose only precondition
is command acceptance.

### 7. Build a reliable command bridge and feedback protocol

Implement a command gateway between backend and Godot (polling for the MVP,
then WebSocket if latency/scale requires it). The protocol should support:

- command delivery with cursor/acknowledgement;
- idempotent receipt keyed by `command_id`;
- ordered per-NPC command streams using `controller_revision`;
- cancellation and interruption messages;
- controller events: accepted, started, arrived, interaction_attempted,
  dialogue_emitted, completed, failed, cancelled, and expired;
- reconnect/replay behavior that restores active commands without duplicating
  effects.

Backend endpoints validate command/event ownership, NPC/controller revision,
expiry, target identity, and permitted transitions. The client must never be
trusted to issue a command or claim a completed authoritative outcome without
server verification.

### 8. Keep controller state and world state synchronized

Define separate data categories:

- **Controller presentation state:** position, velocity, animation, facing,
  active command, and local progress. Godot reports this frequently enough for
  observation and recovery.
- **Authoritative game state:** inventory, quests, combat, relationships,
  world events, and approved NPC state. The backend/game systems own it.

Reconcile them at command boundaries and on failure. A final NPC position is
accepted only if it is plausible under the active command/navigation rules;
otherwise the backend marks the command failed and requests a fresh perception
snapshot before another decision.

### 9. Develop incrementally

1. Implement `speak`, `face_target`, `idle`, and command acknowledgements.
2. Convert NPCs to `CharacterBody2D`; add walking and safe `move_to` with
   navigation, arrival, and failure events.
3. Add `approach_target`/`retreat_from_target` and animation-state mapping.
4. Add server-confirmed interaction attempts and outcome-timed dialogue.
5. Add cancellation, recovery, reconnect/replay, and richer role-specific
   animations/interactions.

This ordering lets the project prove command semantics and dialogue truthfulness
before adding complex navigation or game-changing interactions.

### Acceptance criteria

- Every FSEC command has one controller lifecycle with explicit success,
  failure, cancellation, or expiry outcome.
- NPC movement uses navigation and physics and cannot pass through blocked
  geometry or claim arrival without satisfying distance/path rules.
- Animation, facing, movement, interaction, and dialogue are driven by the
  same controller state machine.
- Dialogue about completed actions is emitted only after an authoritative
  outcome; immediate expression and commitments follow their declared timing.
- The backend and Godot remain synchronized through idempotent commands,
  revisions, acknowledgements, and verified outcome events.

### Initial test scenarios

- An NPC commanded to approach the player walks through a valid navigation path,
  faces the player at arrival distance, then emits its arrival-timed line.
- A blocked or missing navigation path yields `failed` and never emits “I am
  here” or an outcome dialogue.
- An inventory-transfer interaction plays its gesture, waits for the backend
  result, and only then displays the completion line and UI inventory change.
- A new higher-priority retreat command interrupts an approach command, stops
  its movement/animation, and emits only dialogue valid for the interruption.
- Duplicate delivery of a completed command does not replay movement,
  interaction, dialogue, or game effects.

## Persistent Memory Module

### Current implementation assessment

The project already has a meaningful selective semantic-memory implementation,
but it is not yet a complete persistent-memory feedback module for evolving NPC
behavior.

| Requirement | Current implementation | Gap |
| --- | --- | --- |
| Store structured past interactions/events | Partial | `Memory` stores event text, importance, emotion, timestamp, embeddings, event type, and optional quest ID; `Conversation` stores every dialogue turn. It lacks source-event IDs, participants, location, fact/claim status, visibility, outcome linkage, and relationship targets. |
| Retrieve relevant memory from context | Yes, with limitations | Per-NPC semantic retrieval uses the player message as the query; the context builder also includes the latest six exchanges. Retrieval does not yet use the full perception snapshot, active intent, visible entities, current location, or target. |
| Use relevance, recency, importance | Yes | Candidate ranking uses `0.65 * similarity + 0.20 * importance + 0.15 * recency`, with metadata prefilters and exact-duplicate consolidation. It lacks configurable per-memory-type policies, hybrid lexical fallback, and salience-aware retrieval budgeting. |
| Update NPC state and relationships over time | No | Memories can influence an LLM prompt, but no trusted memory effect updates NPC emotional state, goals, or relationships. There is no relationship model. |
| Evolving consistent behavior | Partial | Durable preferences, commitments, quest progress, and transfers can be retrieved. Contradictions, corrections, decay, outcome reconciliation, and long-term state evolution are not implemented. |

Strengths already present include importance-gated writes, player-claim labeling,
semantic embeddings, FAISS candidate retrieval, relevance/importance/recency
reranking, transaction-aware cache invalidation, reindexing support, and tests
for semantic-memory behavior. These should be preserved rather than replaced.

### Scope

The Persistent Memory Module receives authoritative completed interaction/world
events plus approved conversation outcomes. It stores and retrieves
NPC-scoped memory records, derives bounded memory influence, and supplies
selected memories to the Perception Layer. It does not accept raw LLM text as
world truth, directly execute actions, or bypass State Extraction/Validation
when a memory affects behavior.

```text
authoritative interaction / engine outcome / approved conversation event
  -> memory classification and write
  -> lifecycle, contradiction, and effect processing
  -> retrieval for PerceptionSnapshot
  -> bounded MemoryInfluence for later state evolution
```

### Required additions and changes

### 1. Replace free-text memory records with provenance-rich event memories

Keep the existing human-readable `event` summary and semantic embedding, but
expand the memory model (or add linked `MemoryEvent`/`MemoryFact` tables) with:

- stable source event ID and idempotency key;
- source system (`engine`, `quest`, `interaction`, `conversation`, `player_claim`);
- participant/entity IDs, subject/object roles, and optional faction ID;
- location/area and game-time/world-time;
- epistemic status: `authoritative_fact`, `direct_observation`,
  `player_claim`, `npc_inference`, `rumor`, `correction`, or `retraction`;
- confidence, visibility/knowledge channel, and expiry/retention policy;
- outcome/command ID for engine-backed events;
- relation to a quest, goal, item, threat, or prior memory;
- lifecycle state (`active`, `superseded`, `retracted`, `archived`).

Do not convert an NPC/LLM statement into an authoritative memory merely because
it appears in a conversation. Authoritative transfers, quest outcomes, engine
command completions, and world events should be ingested from their owning
services with source IDs.

### 2. Add a memory ingestion pipeline

Replace the chat-specific `classify(player_input, output, ...)` as the only
write path with a `MemoryIngestionService` that accepts typed domain events.

Required inputs:

- completed or failed FSEC/controller command outcomes;
- authoritative quest, inventory, trade, combat, and world-event transitions;
- approved player interactions and explicit player claims;
- approved dialogue/commitments, stored at their proper epistemic status;
- relationship changes approved by State Extraction/Validation.

The ingestion service should classify importance, select affected NPCs, create
one idempotent memory event per recipient, create embeddings, and enqueue any
allowed memory influence. A repeated delivery of the same engine outcome must
not create a second memory.

Conversation history can remain a short-term record, but long-term memory
writes should no longer depend solely on a regular-expression scan of the
player's chat message.

### 3. Make memory relevance depend on the perception snapshot

Replace `retrieve_relevant_memories(npc, player_message)` with a request model
that receives the current `PerceptionSnapshot` and, when applicable, the active
intent/target. Build a retrieval query from:

- current player speech/action and referenced entities;
- NPC area/location, visible threats/items/entities, and active quest;
- role goals and relationship subject;
- current conversation topic and behavior/decision context.

Apply strict metadata filters before semantic search: NPC knowledge scope,
visibility, lifecycle state, expiration, participant, location, quest, target,
and event type. A memory about a different person or an inaccessible rumor
should not become a generic NPC fact just because it is semantically similar.

Return selected memories to the perception layer with their provenance,
epistemic status, source timestamp, retrieval score, and inclusion reason.

### 4. Improve retrieval with configurable multi-factor ranking

Preserve the existing semantic/importance/recency ranking as a baseline, but
make its components explicit and configurable by memory type:

```text
memory_score = semantic_relevance
             + importance
             + recency
             + participant/relationship match
             + location match
             + quest/goal match
             + current-threat or action relevance
             - uncertainty/staleness penalty
```

Use a per-category budget so recent dialogue, durable commitments, relationship
memories, quest facts, and critical event memories cannot starve one another.
High-importance authoritative memories may be included through a deterministic
priority path even when semantic candidate retrieval misses them.

Add a hybrid fallback for embedding outages or lexical identifiers (names, item
IDs, quest IDs), while keeping the current behavior of never fabricating
embeddings. Log whether a memory was selected semantically, lexically, by
authoritative priority, or by recency.

### 5. Handle contradictions, corrections, and consolidation

Exact duplicate handling exists, but semantic contradiction and correction
handling is missing. Add a `MemoryReconciler` that:

- links a correction/retraction to the memory it supersedes;
- marks facts stale or superseded instead of deleting historical evidence;
- preserves conflicting player claims as separate claims with provenance;
- uses authoritative outcomes to supersede incompatible unverified claims;
- consolidates stable facts/preferences only when their subject, predicate,
  provenance, and confidence rules permit it;
- prevents both sides of a resolved contradiction from being presented as equal
  current facts in the same perception snapshot.

Do not rely on embedding similarity alone to identify negation or truth. The
reconciler should use typed event fields and authoritative references wherever
possible, escalating ambiguous conflicts to “uncertain” rather than guessing.

### 6. Add retention, decay, and memory lifecycle policy

The current memory and conversation tables are unbounded, and new-game reset
erases all memories. Define explicit policies by memory type:

- permanent/auditable: quest completion, major world event, contract, or
  authoritative relationship milestone;
- long-lived but decaying: preferences, rumors, ambient observations;
- short-lived: temporary threats, intent, pending requests, and controller
  failures;
- short-term only: routine dialogue.

Separate retrieval salience decay from historical deletion. Store decay/expiry
metadata and run a scheduled maintenance/review job that archives expired
records, refreshes summaries only under provenance-safe rules, and reindexes
when needed. Decide explicitly whether a “new game” starts a new memory
timeline, archives the old one, or intentionally clears it; do not call the
module persistent if memories are silently lost across the intended game scope.

### 7. Create bounded, trusted memory effects on state and relationships

Memory should influence evolving behavior through typed effects, not by giving
the LLM unrestricted authority over stored text. Add `MemoryInfluencePolicy`
rules such as:

- a verified helpful interaction can propose a small trust/familiarity increase
  for that player–NPC relationship;
- an authoritative betrayal or threat outcome can propose a bounded trust
  decrease/fear increase;
- a fulfilled commitment can update commitment status and relationship
  reliability;
- an unverified player claim affects belief/confidence but does not directly
  alter trust or world facts without a corroboration rule.

Emit a `MemoryInfluenceProposal` with source memory IDs, target relationship or
state dimensions, relative delta, policy ID, and confidence. Route it through
State Extraction, Fuzzy-Symbolic, Role Conditioning, and Validation; do not
have the memory service directly mutate `NPC` fields. Add the `NPCRelationship`
model described in State Extraction before applying relationship effects.

### 8. Protect the memory-to-LLM boundary

Memory summaries are untrusted historical data, particularly player claims and
dialogue. The perception snapshot must serialize each memory as data with its
source/status and never allow its content to function as an instruction.

- strip or neutralize instruction-like content for prompt presentation;
- label claims, rumors, and inferences clearly;
- do not retrieve memories outside the NPC's knowledge scope;
- limit token/count budgets and redact fields unnecessary for the decision;
- log selected memory IDs, scores, and the snapshot in which they were used.

### 9. Update the feedback-loop integration

The target memory loop is:

```text
validated controller/game outcome
  -> MemoryIngestionService
  -> durable memory + optional MemoryInfluenceProposal
  -> approved state/relationship evolution
  -> future PerceptionSnapshot retrieval
  -> LLM reasoning and later control layers
```

The current `MemoryService` can remain the embedding, index, and retrieval
adapter beneath this pipeline. Refactor its API to accept typed memory events
and retrieval requests rather than free-text event strings and only a player
message query.

### 10. Add observability and tests

Create a `MemoryTrace` containing source event ID, recipient NPC IDs,
classification/importance result, embedding/index status, consolidation or
reconciliation actions, retrieval candidates, selected memories, and generated
influence proposals.

Initial tests:

- A completed engine-backed item transfer is stored once with its command/event
  ID and is retrievable for the involved NPC, while a duplicated outcome is
  idempotently ignored.
- An explicit player preference is stored as an unverified claim and can affect
  dialogue context but cannot overwrite inventory or quest facts.
- A corrected authoritative outcome supersedes the related claim in current
  retrieval while retaining the historical record.
- A relevant older quest commitment survives a semantic candidate miss through
  the authoritative-priority path; an unrelated high-importance memory does
  not displace the current threat/player context.
- Embedding unavailability falls back to permitted lexical/recency retrieval
  with trace diagnostics, not a fabricated vector.
- A verified relationship memory produces a bounded influence proposal that is
  only applied after State Extraction and Validation approve it.
- Expired temporary threat memory is omitted from retrieval while the archived
  event remains available for audit.

### Acceptance criteria

- Every durable memory has provenance, epistemic status, lifecycle, and
  recipient/knowledge scope in addition to semantic content and importance.
- Retrieval uses full current perception context and balances relevance,
  recency, importance, and game-specific metadata under explicit budgets.
- Contradictions and corrections are represented and reconciled without
  silently rewriting history or treating claims as facts.
- Memory effects evolve NPC state and relationships only through bounded,
  traceable proposals approved by the control stack.
- Engine/controller outcomes and authoritative game events close the feedback
  loop, producing consistent behavior over time.
