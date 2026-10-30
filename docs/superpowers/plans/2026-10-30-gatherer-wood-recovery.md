# Angry Gatherer bow-quest recovery

Implement the user's requested refusal → Craftsman advice → forest gift → restored cooperation flow.

- Store run-scoped recovery flags and collected pickup IDs inside GathererEncounter.state. Existing reset deletes this row; no schema migration is needed. Author three honeycomb pickups in a shared JSON resource, on verified clear forest ground.
- Add a focused quest service owning anger/readiness thresholds, refusal recording, advice unlocking, pickup validation/idempotence, gift effects, and quest projection. Bow phase remains gather while this optional recovery objective is active.
- Use existing local semantic interpretation: a Craftsman capability for Gatherer advice and a player_report target=gatherer route. No phrase parser or additional model call. Add authoritative recovery facts for factual follow-ups.
- Intercept Gatherer wood requests and pending purpose confirmations before transfer. Block angry quest wood despite its existing required-item protection. Once calm/trusting, normal request/purpose/transfer rules resume.
- Add honeycomb to item contracts. A verified player→Gatherer gift applies aggression -.40 and trust +.30 atomically with item removal. Claims of having/giving it have no effect.
- Expose recovery objective/pickups in bow snapshots; add forest pickup sprites, F interaction, icon and current quest text. Reuse chat/bag giving and F8 refresh.
- Regression-test refusal, advice semantics, pickup range/scope/repeat, gift ownership/wrong recipient, cooperation recovery, persistence/reset and normal bow completion. Verify pickup layout and frontend projection, then exercise local-Llama paraphrases through disposable worlds.
