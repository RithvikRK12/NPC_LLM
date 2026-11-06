# Context task packet

Source: Stage 3 and Stage 4 of [`../../llm-response-improvement-plan.md`](../../llm-response-improvement-plan.md).

## C01 — preserve compact identity constraints

Dependencies: D01. Files: Craftsman authored profile/projection and focused tests only if evidence requires.

- [x] Test that father's unspecified survival appears in always-included continuity across greeting, mood, background, and unrelated practical turns.
- [x] Add the missing constraint to authored continuity; do not expand formative lore.
- [x] Preserve detached results, ≤4,200 characters, ≤2 optional cards, unknown-role behavior, and both prompt paths.

Acceptance: invariant is delivered independent of keyword selection. Tests: profile, context adapter, generation adapter. Live compliance is measured separately.

Status: verified 2026-10-19. Changed `backend/app/services/context/characters/craftsman.json` and `backend/tests/test_character_profiles.py`. RED test failed for all four message classes before the projection change. GREEN commands and results are recorded in master progress. Live compliance remains unmeasured.

## C02 — ground practical answers in implemented knowledge

Dependencies: D01. Trace actual item, quest, and command services before proposing any added evidence.

- [x] Audit rope/wood uses and supported commands and record claims the NPC can actually make.
- [x] Add contrasting known/unknown/unsupported-action cases; no existing fact/capability was missing from projection.
- [x] Preserve negative cases for unsupported offers; don't create mechanics or promote dialogue into facts.
- [x] Check stock/location secrecy and operation authorization remain intact against existing adapter contracts/tests.

Acceptance: practical claims have an authoritative source or explicit uncertainty; no code change is an acceptable result when existing projection is sufficient. Run context/game adapter/capability and relevant operation-negative suites.

Status: verified with no runtime code change. Evidence: `docs/evidence/llm-response-improvement/context-audit.md` and focused existing game/capability tests. Live generation remains unmeasured.
