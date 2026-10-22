# Wreck disclosure: NPC reaction instead of bookkeeping

2026-10-20. User message: `my ship just wrecked and i'm stranded!`. Read-only inspection of the saved turn confirmed a committed wreck-report receipt, followed by a failed composition attempt and `PROVIDER_INVALID_OUTPUT` fallback. The fallback literal was `I recorded the wreck report.` This was authored renderer text, not an intended in-world bureaucratic role or an invented player request.

The problem was player-facing language in the exact receipt catalog. The same catalog is used by successful composition slots and provider-failure fallback, so changing only the model prompt would leave the bad line reachable.

The report acknowledgement now uses the existing authored Craftsman reaction: `I'm glad you made it ashore. I can take a look at the damage with you, if you'd like.` The receipt remains internal, and durable retry still returns the exact finalized result. Recording the wreck sets `wreck_reported` and `offer_pending`; it does not start or complete inspection. A separate affirmative response accepts the offered outing.

The regression first failed on the old literal (`red.log`), then passed through the enabled production graph with composition deliberately failing (`green.log`). It verifies the user's exact message, the natural fallback, one receipt, unchanged result on retry, no automatic outing/completed inspection and subsequent `yes please` acceptance. Full backend: 1,135 tests pass (`backend-tests.log`). This was a wording change to the receipt renderer, not a change to storage, consent or provider validation. Model composition can still fail; this does not certify overall dialogue quality.

The isolated live harness completes arrival before exercising the report command. An initial harness probe omitted that prerequisite and therefore tested ordinary pre-arrival chat instead; its failed assertion/log is retained as `harness-before-opening-fix.log`. The corrected live run and raw provider output are in `live.log` / `live-samples.json`. No personal save is used or reset by these checks.

Corrected live run: exit 0, 13.43 seconds, natural receipt-safe fallback, exactly one receipt, no automatic outing or completed inspection, exact retry preserved. Raw provider output still contained malformed/internal source metadata and an invented addressed-concern ID; generation reliability is not fixed by this wording change. The saved game was closed normally and relaunched with the updated renderer; no reset or transcript rewrite was performed.
