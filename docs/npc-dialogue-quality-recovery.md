# NPC Dialogue Quality Recovery Plan

## Executive summary

The current NPC dialogue quality problem is not a single bug; it is a system-level issue caused by a combination of:

- overly narrow conversational routing,
- a small deterministic fallback surface,
- validation that rejects many natural replies,
- and a lack of diversity in the socially grounded response patterns.

The project already contains the right building blocks to fix this: a conversation pipeline, grounded context, memory, validation, and authorial personality scaffolding. The main problem is that the system currently collapses many useful player inputs into a small set of safe or generic responses, which makes NPCs feel repetitive and shallow.

This document identifies the root causes, outlines the likely failure modes, proposes several concrete solution paths, and ends with a phased recommendation for implementation.

---

## 1. Symptom description

The gameplay is starting to feel good, but the NPC conversations lack the flexibility to feel like real social interaction. The main symptoms are:

- NPCs repeat the same lines across different prompts.
- Different player intents collapse into the same response shape.
- NPCs answer the same way when the player asks about mood, history, work, fear, or circumstance.
- The response usually feels “safe” but not “alive.”
- Mixed or nuanced messages often get flattened into generic acknowledgements or fallback replies instead of a contextual answer.

This creates a conversation loop where players stop exploring because they quickly learn the NPC is not really listening.

---

## 2. Where the repetition is coming from in this codebase

The issue is visible in several parts of the current implementation.

### 2.1 Fallback selection is intentionally narrow

The pipeline has a fallback path that is aware of role and context, but it is still very small. See [backend/app/services/pipeline.py](../backend/app/services/pipeline.py):

- it attempts a provider call,
- validates the result,
- and if rejected, falls back to a function that produces a generic response.

The fallback for Craftsmen is implemented in [backend/app/services/pipeline.py](../backend/app/services/pipeline.py) and uses [backend/app/services/context/craftsman_profile.py](../backend/app/services/context/craftsman_profile.py).

That fallback is helpful as a safe default, but it is not broad enough to sustain varied social play. It contains a very small set of likely phrases and patterns, which makes the NPC sound repetitive once the player asks more than a few things.

### 2.2 The mock provider is deterministic and limited

The mock LLM provider in [backend/app/services/llm/mock.py](../backend/app/services/llm/mock.py) hard-codes a few responses for social messages.

Examples:

- social messages get a response shaped by `character_fallback(player_input)`,
- non-social requests may fall back to generic workshop introduction text,
- some craft and item prompts are answered with a few shallow “safe” responses.

This is useful for dev and tests, but it also means the system can easily converge on a tiny response menu when the provider is in a mock or degraded mode.

### 2.3 The social detector is regex-based and brittle

The social classifier in [backend/app/services/context/social.py](../backend/app/services/context/social.py) relies on keyword patterns. That works for a few obvious phrases, but it is weak against:

- mixed requests,
- slightly paraphrased emotional speech,
- quoted remarks,
- hypotheticals,
- layered concerns (“I’m scared, and my ship is wrecked — can you help?”),
- and follow-ups that require remembering prior context.

When a message is misclassified as “not social” or “not world fact,” it may be sent to a route that is too generic or too restrictive. That is a common source of stale, repetitive replies.

### 2.4 Validation is stricter than the conversation model

The validation layer in [backend/app/services/validation/service.py](../backend/app/services/validation/service.py) allows only certain kinds of output. This is important, but it creates a very sharp boundary between “safe enough” and “rejected.” If the model has to keep producing ever more generic text to satisfy validation, the resulting NPC speech becomes bland.

This is especially visible with social/promotional text that mentions work, home, fear, uncertainty, or values. The system tries to preserve safety by rejecting claims about ownership, completion, or new facts. That is correct, but the reply surface becomes narrower than the underlying character should support.

### 2.5 Prompting is supportive but still too constrained

The prompt builder in [backend/app/services/prompts/builder.py](../backend/app/services/prompts/builder.py) tries to encourage personality, but it remains tied to a narrow “natural reply” contract and to minimal world context. It says to speak briefly, naturally, and within tight character limits, but it does not give the model enough structured content to develop a richer relationship arc.

That means the model can say something pleasant, but it does not have a strong enough “conversation memory + personality plan” to produce individually distinctive replies over time.

---

## 3. Why this produces same-message behavior

The repetition is not arbitrary. It is a predictable outcome of the current architecture:

1. The input is classified into a coarse bucket.
2. The system routes it toward a small list of safe answer patterns.
3. Validation rejects or narrows replies that feel too broad.
4. A fallback response pattern is used when the model cannot produce a valid answer.
5. Because the fallback itself is a tiny set of preset lines, repeated interactions converge on the same language.

This is common in constrained conversational systems: the “safe path” becomes the default path, and the default path starts sounding identical.

The larger issue is not just a bad prompt. It is that the system currently has no robust way to distinguish:

- a simple greeting,
- a personal question,
- a sentimental question,
- a fact request,
- a mixed emotional + practical request,
- a relationship-building follow-up,
- a sensitivity check,
- a direct action request,
- or a repeated question requiring continuity.

When those are not separated, the NPC responds like a generic assistant instead of an NPC with a personality.

---

## 4. Detailed failure modes

### 4.1 Same opening line repeated forever

If the social classifier doesn’t recognize the intent, the fallback can repeat the same empathetic line. This is especially common for emotionally loaded prompts like:

- “I’m scared.”
- “I don’t know if I’ll ever get home.”
- “Do you enjoy working here?”
- “What do you do when you’re not working?”

These should not all map to the same emotional phrase. They should trigger different conversational branches based on content and relationship context.

### 4.2 Mixed requests flatten into one response

A message like:

> “I’m scared, and my ship is wrecked — can you help?”

should be able to trigger both empathy and a useful next action. Instead, the system can collapse to a single narrow branch or a generic helper message if the intent routing is too simplistic.

This is a sign the NPC is not “integrating” the issue; it is only selecting a single allowed category.

### 4.3 Short-term memory is not effective enough

The system does have memory and context retrieval, but it still does not reliably shape the response with recent continuity. If a player discusses the wreck, then asks a follow-up question, the NPC should respond as if it remembered the situation. Without that, conversations feel repeatable and disconnected, even when the game state is correct.

### 4.4 Hypothetical and edge-case prompts are usually rejected too early

The design documents specifically acknowledge the importance of distinguishing direct requests from quoted, hypothetical, or non-authoritative statements. That is good — but if the model and the classifier are too blunt, the NPC may answer the wrong thing or give a generic social line instead of a meaningful response.

This is especially relevant when the player says something like:

- “Imagine my ship sank.”
- “Do ships often wreck here?”
- “He said ‘help me repair my ship.’”

These are not the same as “My ship wrecked, and I need help.”

---

## 5. What the project already gets right

This is not a broken design from the ground up. Several parts are already structured correctly:

- The conversation pipeline separates generation from validation and action execution: [backend/app/services/pipeline.py](../backend/app/services/pipeline.py)
- Social context is intentionally separated from world facts: [backend/app/services/context/social.py](../backend/app/services/context/social.py)
- The system already distinguishes state-authoritative actions from conversational narrative: [backend/app/services/validation/service.py](../backend/app/services/validation/service.py)
- The design spec calls for broader character conversation and richer emotional grounding: [docs/superpowers/specs/2026-10-13-craftsman-character-and-ship-repair-design.md](superpowers/specs/2026-10-13-craftsman-character-and-ship-repair-design.md)
- The project already defines a character profile with meaningful anchors: [backend/app/services/context/craftsman_profile.py](../backend/app/services/context/craftsman_profile.py)

In other words, the architecture is close to a solid NPC conversation system. The need is not a full redesign, but better use of those existing pieces.

---

## 6. Potential solution paths

### Option A: Improve route classification and context routing

This is the lowest-risk improvement with a high payoff.

#### What it does

Instead of a single coarse “social vs. world” label, the system breaks conversations into categories such as:

- greeting,
- personal question,
- emotional disclosure,
- story request,
- world fact question,
- quest/inventory question,
- action request,
- mixed request,
- repeated follow-up.

#### Why it helps

It prevents different intents from collapsing into the same response branch. It also allows the NPC to choose a more appropriate response style for each message.

#### Implementation notes

- Build a small intent classifier using regex plus a few structured features.
- Keep it deterministic and explainable.
- Prefer “multi-intent detection” over binary classification.

This would address a large portion of the repetition problem without changing the generation model dramatically.

### Option B: Add a richer personality response bank

This is a content-authoring solution.

#### What it does

Create a library of validated response patterns for the NPC, keyed by intent, mood, relationship state, and topic. Examples:

- “work values” responses,
- “loneliness / uncertainty” responses,
- “home / departure” responses,
- “practical help” responses,
- “gentle humor” responses,
- “quiet reflection” responses.

#### Why it helps

It makes the NPC sound less robotic even if the model stays constrained. It also keeps grounded, safe responses.

#### Implementation notes

- Keep the response bank small but varied.
- Store them as structured templates rather than raw free text.
- Use recent conversation state to select the appropriate one.
- Ensure each template avoids forbidden claims about world state or action authority.

### Option C: Add conversation continuity and memory-aware response templates

This is the best improvement for perceived intelligence.

#### What it does

The NPC should remember and refer to recent relevant facts:

- the player’s fear, shock, or uncertainty,
- whether they mentioned the wreck,
- whether they asked for help before,
- whether they paused or declined earlier,
- what kind of emotionally loaded topic came before.

#### Why it helps

This prevents the “generic NPC” feeling. The player feels listened to.

#### Implementation notes

- Add a recent-turn summary to the model prompt.
- Feed in not just raw memory but also a conversation summary: “Player reported a wreck, is scared, is asking for help.”
- Add a small “do not repeat the exact same opening phrase” guard.
- Use continuity tags like: `empathy`, `goal`, `delay`, `topic`, `recent_question`, `loaded_context`.

### Option D: Build a structured social state machine

This is the most architecture-heavy option, but also the most robust.

#### What it does

Represent the social relationship as a small state machine:

- neutral,
- warmed-up,
- concerned,
- trusted,
- hesitant,
- in-the-middle-of-help.

Then every social reply is selected based on:

- relationship state,
- emotional tone,
- recent topic,
- current task or encounter state,
- player’s recent asks.

#### Why it helps

It makes the conversation feel dynamic and consistent, not random. It also gives the NPC a recognizable voice pattern over time.

### Option E: Upgrade the generation path without abandoning safety

This is the biggest quality win, but also the most expensive.

#### What it does

Use a stronger model or better prompt structure specifically for social conversation, while keeping the world-authoritative layer strictly deterministic.

#### Why it helps

This allows the NPC to carry natural social detail, while the rules layer still prevents invalid game-state claims.

#### Caveat

This is not a full replacement for validation. The system still needs rule-based guardrails. The key is to give the social layer enough space to be expressive without allowing it to pretend to have authority over the game world.

---

## 7. Recommended approach: layered fix, not single magic prompt

The right solution is not “rewrite the prompt and hope.” The best path is a layered fix:

### Phase 1: Diagnose the true failure path

- Log which route is being used for a given message: provider, fallback, rule engine, validation rejection.
- Measure repeated reply text frequencies.
- Track the most common phrases that repeat.

This helps separate a model problem from a conversation routing problem.

### Phase 2: Narrow the repetition sources

Fix the top offenders:

- generic fallback response bank,
- overly broad social classifier,
- lack of recent-context aware prompt assembly,
- poor differentiation among emotional, practical, and relationship conversation.

### Phase 3: Add conversation-state awareness

The system should know whether:

- the player is scared,
- the player reported a wreck,
- the NPC already responded to the same issue,
- the player is asking about the same topic again,
- the player is asking a different, more personal question.

This is where the NPC starts to feel real.

### Phase 4: Improve authored response diversity

Add a small library of interpersonal response patterns that are still safe and grounded.

### Phase 5: Measure quality

Set conversation quality targets, such as:

- fewer than X% of replies come from fallback lines,
- fewer than Y% of social responses repeat the same opening phrase,
- repeated prompt families produce distinct follow-ups,
- more than Z% of messages include some direct acknowledgement of the player’s actual concern.

---

## 8. What to test in the short term

It is important to move from vague “the dialogue feels bad” to concrete system behavior.

### Conversation test cases

- greeting + question
- emotional disclosure + practical request
- direct question about work or values
- meta/story request
- hypothetical or quoted story
- repeated follow-up after previous topic
- direct command or request with the same NPC
- player asks for help after previously declining
- player switches topics mid-conversation

### Quality checks

- Is the NPC responding to the actual content of the message?
- Is the response consistent with the NPC’s personality?
- Does it avoid duplicate phrasing from the last turn?
- Does it avoid claiming game-world authority it shouldn’t have?
- Does it still feel grounded and believable?

---

## 9. Recommended implementation plan

### Sprint 1: reduce repetition at the system boundary

- improve intent classification,
- add conversation-state tagging,
- add “do not repeat last reply” logic,
- fix fallback bank diversity.

### Sprint 2: improve continuity and memory usage

- summarize recent dialogue,
- provide structured context to the model,
- track openings, feelings, tasks, and unresolved topics.

### Sprint 3: enrich personality and response variation

- create a small authored response library,
- add mood and topic-specific variants,
- add voice/pacing constraints.

### Sprint 4: quality metrics and regression checks

- collect repeated-response data,
- regression test common social phrases,
- ensure safety boundaries remain intact while variety improves.

---

## 10. Suggested guiding principle

The highest-leverage principle is this:

> Social dialogue should be expressive, but world-changing claims must remain authoritative and deterministic.

If the project holds to that boundary, the NPC can feel emotionally rich without becoming unsafe or game-breaking. The issue is not that NPCs are too “creative”; it is that the creative layer is being forced into a tiny safe subset of expressions.

---

## 11. Bottom line

The conversation quality issue is real, but it is not caused by a single bad string. It is caused by a combination of:

- conversational routing too coarse,
- fallback responses too narrow,
- validation too restrictive,
- and insufficient continuity between turns.

The best fix is a layered recovery plan: improve intent detection, add recent-context awareness, diversify safe fallbacks, and make the social layer more expressive while keeping the authoritative layer strict.

That combination should produce NPCs that feel less like repeated canned lines and more like coherent people with a stable voice.
