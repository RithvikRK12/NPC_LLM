# Valid ship report rejected for irrelevant purpose — 2026-10-30

The saved failed message was `my ship wrecked! i'm stranded`. Its trace records one interpretation call, zero speech calls, interpretation_failure, and no accepted interpretation.

A fresh raw-model reproduction using an in-memory copy of the save returned a direct player_report targeting ship, with evidence `my ship wrecked!`. It also returned an incorrect end offset of 10 and the irrelevant purpose `ship inspection`. Exact-offset repair already corrected the offset, but strict validation still rejected purpose on a non-operation concern. The model recognized the report; schema validation discarded it.

The local schema-noise correction now clears purpose only for non-operation concerns, matching its existing handling of irrelevant operation and answer-type fields. Intent, target and modality remain unchanged. Operation purposes still require an exact current-message span, and all capability, consent and ownership checks remain enabled. No retries or phrase routing were added.

Verification:

- Regression using the captured output failed before the fix and passes after it.
- An invented purpose on a give_item operation remains rejected after one provider call.
- 13 semantic-routing/HTTP shipwreck tests pass.
- Three live local-Llama report/consent exchanges pass: the exact lowercase message; Our boat was destroyed in the storm.; My boat sank and I'm stuck here. Each report creates an offer and each Yes please starts departure_pending. See report-purpose-live.json.
- Personal save unchanged. Raw-output reproduction used an in-memory copy; full live exchanges used disposable seeded saves.
- Full unittest discovery: 578 tests, with the same 57 failures and 75 errors as the preceding run. Failure names remain listed in no-retries-verification.md.
- git diff --check passes.

Close the game normally and relaunch ./Play.command to load the fix.
