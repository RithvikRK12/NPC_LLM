# Post-inspection dialogue: perspective, stale offers and repair

The reported persisted turn confirms the screenshot: “Thanks for looking at my ship!” produced a generated reply that echoed the player, copied old NPC sentences and offered an already-completed inspection again. The authoritative encounter was already complete and no operation receipt was appended on this turn. This was generated speech contamination, not another inspection or a client concatenation bug.

## Causes and changes

- Whole-message gratitude with a complement missed social routing, sending a courtesy acknowledgement through the large extraction schema. Gratitude now uses the bounded dialogue-only wire. Mixed messages containing another request retain extraction/action handling.
- Prompt v9 explicitly separates player ownership, inspection completion, observed hull damage, and unfinished repair. Authored inspection findings enter the speaker context only after the inspection completes. Gratitude uses compact current-state facts rather than a transcript of earlier offers; the original authoritative history is retained.
- Narrow blocking checks now detect echoed player gratitude, player-ship ownership reversal during gratitude, new inspection offers after completion, copied long historical sentences during gratitude, and claims that the unfinished hull repair is complete. They do not claim general semantic understanding; arbitrary narrative evaluation remains an open quality gate.
- The production repair hook used to discard validation findings. It now sends their safe explanations as per-attempt authored correction directions, retaining original authoritative evidence, bounded repair allowance and operation authority. The real Llama repair check verifies this produces a corrected answer rather than defaulting to fallback.

## Verification

- Failing regressions were recorded before each repair. The full backend suite now passes **1,150 tests**. Existing dependency deprecation warnings and bounded lexical embedding recovery remain visible in the log.
- Six live gratitude variants against a disposable SQLite backup of the reported save all produced **generated**, brief replies with no fallback or renewed offer, in **1.848–2.409 seconds**. For the exact exclamation-mark message: “You're welcome, glad I could help you take a closer look at your ship.”
- A deliberately invalid initial draft was corrected by the actual local Llama provider: **repaired**, no fallback, no operation receipt. Final samples are in `live-results.json`. Intermediate live outputs that exposed optimistic condition claims and historical priming are preserved in `before-history-projection.*`; these are not treated as passing final outputs. An initial verification-script assertion used the internal legacy_projection key against the flattened HTTP response and was corrected to the public craftsman_encounter field.
- `craftsman_post_inspection_smoke` passes the complete real-model flow: disclose wreck, natural consent, automatic chat closure, objective, physical following through doors, inspection at ship, gratitude, no repeated objective, solo return and reload. Its existing teardown resource warning is recorded; all assertions pass and there are no script errors.

The personal database was read only for reproduction and backed up into a temporary test database. The personal game was closed normally and relaunched with its save preserved. No history, accepted action, receipt or inspection outcome was rewritten. PostgreSQL acceptance was not rerun for these prompt/pure-validation changes; previous results remain historical. This fixes the observed classes of errors without claiming the outstanding release-wide semantic quality gate has passed.
