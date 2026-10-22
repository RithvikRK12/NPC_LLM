# Dialogue grounding audit — 20 October 2026

The village-name incident is part of a broader dialogue-grounding problem. Server-owned game operations have authority checks, but ordinary generated speech can invent world facts, contradict authored knowledge, promise unsupported services, or report actions that never occurred. Supplying a fact in the prompt does not establish that the accepted answer respects it.

This is an investigation, with reproducible probes and evidence. No production dialogue behavior, model, deployment settings, or personal game save was changed during this audit. The village identity fix from the preceding task is present in the baseline.

The completed live run covered **20 scenarios and 22 turns**: 17 finalized with origin `generated`, and five with origin `fallback`. All twenty isolated worlds retained the original player inventory, no sample produced a transfer receipt, and all had zero persisted player-report memory rows. These origin counts describe the run, not factual-correctness scores. Exact transcripts and failure markers are in [results.md](results.md).

## Method and evidence

- `audit.py` runs the actual production context assembler, generation adapter, coordinator, validator and finalizer, synchronously through the durable worker, against newly seeded temporary SQLite databases. It bypasses HTTP/Godot presentation; it does not bypass dialogue validation or finalization. Each case has an isolated world; multi-turn cases retain only their own history.
- `live.json` contains targeted real-model cases, exact model prompts/responses, input context, final published results and persisted-memory counts. The model is the existing local `llama3:willowbrook`, temperature 0.2, structured output, 8,192-token context policy, 2,048 generation-token bound, and 600-character dialogue bound. `models.json` records installed model digests. No hosted inference or alternative model was used.
- `containment.json` contains twelve **injected** provider-prose cases. These measure the pipeline's ability to contain a bad answer; they are not observed model hallucination frequencies. `injected.json` is the initial eight-case exploratory run.
- `history-ordering.json` reproduces the history/window failure without calling a model. `memory-projection.json` is the initial exploratory version of that probe.
- `results.md` is a compact transcript of the completed live run. These are targeted diagnostic examples, with one run per input, not an estimate of overall quality, latency acceptance, or release readiness.

## Findings, in implementation priority order

### 1. Unsupported expressive speech passes publication checks

**Evidence:** seven of eight deliberately bad injected answers were finalized verbatim with origin `generated`, no degradation, no receipt and no speech evidence dependencies. Examples include “This village is called Willowdale,” “My father died last winter,” “I gave you three axes earlier,” and an offer to teach sword fighting. The real player inventory remained `water, food`: a false transfer claim did not create a transfer.

The existing validator checks a small set of shop/cache/recipe/route patterns, specific ship contradictions, structural IDs/spans and optional canon projections. It does not generally compare factual propositions in expressive prose against authoritative evidence. An empty reference list produces no unknown-reference errors. `ExpressiveSegment` passes through the assembler verbatim and does not establish evidence dependencies. The production validator has no trusted semantic claim extractor configured; production continuity also supplies no generated canon changes.

Sources: [validator](../../../backend/app/services/conversation/validation.py:13), [production validation](../../../backend/app/services/conversation/application.py:158), [expressive assembly](../../../backend/app/services/conversation/composition.py:200), [speech adaptation](../../../backend/app/services/llm/structured.py:136).

**Live reproduction:** asking “Why is this village called Willowdale?” produced an accepted answer describing Willowdale's supposed history and willow trees, despite the exact outbound prompt containing authored `Willowbrook`. The previous fix supplies the missing fact, but does not enforce its use.

The model also asserted sunny weather with a gentle breeze when no weather observation was supplied, and invented settlers as Willowbrook's founders when no founding history was supplied. A question about a previous transfer produced an invented recollection and reversed the transfer direction. These outputs were published as `generated`, with no degradation marker.

**Recommended change:** distinguish factual assertions from expressive reactions at the speech boundary. For authored identity, stock, locations, recipes, progress and completed actions, use server-resolved facts/receipt renderers or an explicitly validated factual projection. Keep warmth, feelings and opinions expressive. Model-generated source IDs alone are not proof that a sentence is supported. Start with bounded factual domains already owned by the game; a general semantic judge would be a separate architecture/latency decision, not an implicit extra model call.

### 2. Shared public knowledge is still missing from the active context

The backend already has a catalog of NPCs, their work, usual locations and known places in `context/village.json`. The active SQL conversation reader currently projects only its village name. `GameReadAdapter.read_facts()` adds inventories and quest/activity state; it does not add the public roster or location catalog.

**Live reproduction:** the Craftsman invented a family and village elder when asked who lived here. Asked where the Gatherer was, he suggested an old oak tree or river and offered tracking help. The Gatherer placed the Craftsman near the village center and offered guidance. All were published as generated replies. The catalog identifies the Gatherer's usual place as the forest clearing and the Craftsman's as the workshop; it supplies no navigation routes.

Sources: [catalog](../../../backend/app/services/context/village.json), [world projection](../../../backend/app/services/conversation/adapters/context_read.py:249), [game facts](../../../backend/app/services/conversation/adapters/game.py:233).

**Recommended change:** project the small public roster, work descriptions and known places into mandatory shared authored knowledge. Preserve `usual` versus `current` location explicitly. Supply live positions only from actual encounter observations. No map route should be inferred from a location label. Keep these records distinct from each NPC's private biography and from action capabilities.

### 3. History ordering makes the compact prompt omit the newest conversation

The SQL history reader returns chronological turns. Context budgeting considers newest turns first and returns them in that admission order. The compact prompt then slices `visible_recent_turns[-4:]`, assuming chronological order.

**Deterministic reproduction:** with five finalized prior turns, the assembled order is `[5, 4, 3, 2, 1]`; compact speech receives `[4, 3, 2, 1]`. Turn 5 is missing. Short follow-up profile selection also iterates history as if it were chronological, so the ordering discrepancy affects topic selection as well.

Sources: [SQL history](../../../backend/app/services/conversation/adapters/scoped_reads.py:19), [budget admission](../../../backend/app/services/conversation/context.py:220), [compact history](../../../backend/app/services/prompts/builder.py:128), [profile follow-up](../../../backend/app/services/context/character_profiles.py:88). Evidence: `history-ordering.json`.

**Recommended change:** retain newest turns first for budgeting, then restore chronological order before exposing the packet. Verify both retention under budget pressure and the exact most recent four turns delivered to speech. Include a correction followed by a short follow-up so a test catches stale-topic behavior, rather than checking only array shape.

### 4. The compact speech path loses authored constraints and stable work identity

Full structured prompts carry authored continuity/bounds and `CHARACTER_DIRECTION`. `_speech_prompt()` copies only `core` and selected `details`, omitting those continuity/bounds and the shared direction. The authored statement that the Craftsman's father's survival is unspecified is consequently absent from compact speech unless selected detail happens to repeat it. Receipt reaction prompts also omit general current knowledge/capabilities, relying on the outcome clause and narrow instructions.

Separately, `project_profile()` removes the stable `work` field unless the entire question matches a short list of exact phrasings. “What do you do?” retains the bow-work description; “What is your trade?” and a mixed question do not. The routing classifier also changes the wire contract between those phrases.

**Live reproduction:** “What do you do?” gave the Craftsman's supported bow-work answer. “What is your trade?” went through an unsuccessful action proposal and ended with “Please ask directly for the action you want me to take.” The Gatherer's exact work question produced “You're a skilled gatherer,” assigning the NPC's identity to the player. Asked whether his father was alive, the Craftsman replied only that his father prized speed, leaving the actual question unanswered.

The mixed question “I am scared and lost. What is this village called, and what do you do?” received Willowbrook but no authored bow-work answer, then an unsolicited offer of ship repairs/maintenance. The captured compact prompt explicitly marked `player_ship: not_disclosed`. Its generic instruction text nevertheless includes multiple ship-specific directions on every non-receipt turn. That is a plausible priming contributor, not an isolated experimentally established cause; the unsupported offer passing validation is directly observed.

Sources: [compact prompt](../../../backend/app/services/prompts/builder.py:118), [work removal](../../../backend/app/services/context/character_profiles.py:111), [social routing](../../../backend/app/services/context/social.py:17).

**Recommended change:** keep stable occupation and concise identity constraints in every speaker prompt. Use one shared knowledge/constraint projection across proposal, composition and repair. Test semantic equivalents and mixed questions, including both NPC and player perspective. Avoid solving each paraphrase with another exact question/reply rule.

### 5. Ordinary social disclosures do not create durable recall in this path

The compact `SpeechDraft` adapter constructs proposals with `reports=()`. Its expressive segment also adds no player-message dependencies. `MemoryPolicy.plan()` requires a report plus an accepted final-reply player-message source. The ordinary compact path cannot satisfy that contract. The configured semantic retrieval flag is false, but turning retrieval on cannot recover reports that were never written. The summary service exists as a component; this production runtime does not wire a summary-refresh producer into ordinary turn processing.

**Deterministic reproduction:** six accepted ordinary conversation turns, starting with a personal disclosure, produced zero `ConversationMemoryRevision` rows and no selected memories. The original disclosure can appear temporarily in raw history; that is transcript recall, not durable semantic memory. The window-ordering bug above further makes that temporary recall stale.

Sources: [speech adaptation](../../../backend/app/services/llm/structured.py:143), [memory policy](../../../backend/app/services/conversation/memory.py:43), [production continuity](../../../backend/app/services/conversation/application.py:254), [playtest configuration](../../../config/playtest.env). Evidence: `history-ordering.json`, plus per-case memory counts in the live results.

**Recommended change:** give ordinary accepted disclosures a bounded, attributed memory-production path with exact accepted player-message provenance. Preserve uncertainty and correction/retraction lineage. Test disclosure → enough unrelated turns to leave the visible window → recall, and NPC/epoch isolation, through the production graph. Existing tests of manually seeded memory retrieval cannot establish that live conversation creates those memories.

### 6. The narrow word-pattern guard also rejects safe dialogue

The shop/cache/recipe/route guard treats particular keywords plus nearby verbs as an unsupported claim, then requires an exact sentence substring in evidence. It does not distinguish uncertainty, figurative speech or a supported paraphrase.

**Deterministic reproduction:** both “I don't know where the shop is” and “The way I see it, mistakes are how we learn” triggered repair and ended in generic fallback when the injected provider repeated them. The deliberately unsupported “The shop is behind the inn” was correctly contained. Correct Willowbrook and explicit weather uncertainty controls passed.

Source: [world-claim patterns](../../../backend/app/services/conversation/validation.py:38). Evidence: `containment.json`.

**Recommended change:** retain strict checks around supported factual domains while distinguishing assertions from explicit uncertainty and ordinary figurative language. Do not expand a keyword blacklist as a substitute for broader grounding; it already both misses fabricated facts and blocks harmless speech.

### 7. Authoritative server state and NPC knowledge are conflated

Every supported NPC receives the player's complete inventory as a public mechanical fact. This is reliable server state, but the projection does not establish whether this NPC has seen the player's bag or been told its contents. Public catalog omissions and player-inventory exposure therefore coexist: speakers lack ordinary village knowledge while receiving privileged state.

**Live reproduction:** asked what the player was carrying, the Craftsman answered “a saw, hammer, and rope,” which were the **Craftsman's** tools in the supplied facts. The player's actual inventory was `water, food`. The ownership contradiction passed final validation. Both owner IDs were in the prompt; this is an attribution failure in addition to the epistemic-policy question.

Source: [inventory projection](../../../backend/app/services/conversation/adapters/game.py:256), [speaker projection](../../../backend/app/services/prompts/knowledge.py:18).

**Recommended change:** define an explicit epistemic policy: public authored knowledge, personal authored knowledge, witnessed/disclosed events, attributed player claims and server-only execution state. Keep execution state available to rule checks without automatically making it something the NPC can assert knowing. Whether player inventory is intentionally visible to villagers is a product decision, so this audit records the current behavior rather than assuming the desired policy.

## Recommended next work

1. Fix chronological packet output and retain stable speaker identity/constraints. These are bounded context bugs with deterministic regressions.
2. Project public world knowledge, with epistemic labels and explicit unknowns, consistently across all speech stages.
3. Enforce factual support at final speech publication for the game's bounded domains, including false-premise questions, false past-action claims and unsupported offers. Keep expressive prose available for personality.
4. Restore accepted attributed memory production and prove recall beyond the visible transcript window.
5. Re-run the targeted live cases and the existing frozen scenario suite. Report actual model failures, validation rejections, repairs and fallbacks separately. A green mechanical/unit suite does not establish broad prose grounding.

## Reproduction

From `backend`, use the existing virtual environment. Every output path must be new; the scripts refuse overwrite.

```sh
PYTHONPATH=.:tests ../.venv/bin/python ../docs/evidence/dialogue-grounding-audit-2026-10-20/audit.py --live --output /private/tmp/new-live-grounding.json
PYTHONPATH=.:tests ../.venv/bin/python ../docs/evidence/dialogue-grounding-audit-2026-10-20/audit.py --output /private/tmp/new-containment-grounding.json
PYTHONPATH=.:tests ../.venv/bin/python ../docs/evidence/dialogue-grounding-audit-2026-10-20/projection_checks.py --output /private/tmp/new-history-grounding.json
```

The live command requires access to local Ollama. It verifies the endpoint/model before making inference requests. These scripts use fresh temporary databases, not either existing `mvp.db`.
