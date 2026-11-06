# Validation failures: separate speech from server metadata

2026-10-20. The issue was a provider wire contract that asked Llama to generate internal bookkeeping as well as speech. Validation correctly rejected the wrong values, but those values should never have been model-owned.

## Exact reproduced failure

`explain_rejection.py` replays the captured wreck-report output without a provider or database. Its JSON is syntactically valid; the typed errors are:

- `source.policy_versions.authoritative_game_rules`: number `1`, expected a strict string identifier.
- `source.policy_versions.authored_npc_profile`: number `3e4`, expected a strict string identifier.
- Independently, expressive `addressed_concern_ids=["turn:1"]` refers to an invented concern; that deterministic action proposal had no concern IDs.

The adapter had been stamping the actual source metadata **after** validating provider-authored metadata. Invalid model values prevented that step. Composition also did not classify `GenerationMalformed`, so some provider-contract errors appeared as generic `INTERNAL_FAILURE`.

## Change

For action composition, repair and bounded whole-message social conversation, the provider now returns the strict wire value `{"dialogue":"..."}`. Extra fields, forged actions, source metadata, canon additions, blank/non-text/oversized prose and duplicate JSON keys remain rejected. The adapter creates the existing public CandidateReply/TurnProposal, actual dispatch identity, policy versions and empty structural references on the server. Social speech cannot create an operation. Non-social semantic proposals keep their typed interpretation contract; deterministic command/consent checks still authorize effects.

Composition reserves the exact receipt clause's characters in both prompt and provider schema, then appends its trusted slot through the existing assembler. No receipt, quantity, authority, scope, epoch or finalization checks were loosened. The model supplies the personal reaction rather than copying the canonical action clause. A self-contained committed action does not receive unrelated old dialogue as reaction context; ordinary conversation retains recent dialogue. Authored persona and knowledge boundaries remain in use. No model replacement, canned generated reply or public API/schema migration was introduced.

Generation failures are provider-independent boundary errors, so pure composition/proposal modules do not import HTTP/provider infrastructure. Invalid output and provider unavailability are classified separately. Turn-wide attempts and receipt-first recovery remain unchanged.

## Fresh verification

- Full backend: **1,140 tests, zero failures/errors**, exit 0 (`backend-tests.log`). Focused red/green evidence covers the metadata boundary, unknown fields, strict text bounds, exact receipt budget and classified composition failures.
- PostgreSQL: **eight runners / 153 overlapping executions**, all exit 0 (`postgres-runners.log`, copied runner logs).
- Godot: **three freshly rerun scenarios pass**: signal/bootstrap, actual chat UI/gifts, full bow quest (copied logs and `godot-summary.json`). The other earlier client scenarios were not freshly rerun for this change.

Real local Llama screen: **8/8 ordinary/action samples generated with no degradation**, in 1.33–3.21 seconds on this warm local model. These include both NPCs, personal questions, the user's exact stranded message, bow discussion, a purpose-confirmed transfer and a gift. Every exact retry returned the same final response and actions produced one receipt. The exact stranded-message probe completed in 2.78 seconds with origin `generated`, versus the earlier 13.43-second fallback capture. Provider token usage and raw wire response are retained in `live-samples.json`.

The purpose clarification is an intentional deterministic response and is listed separately, rather than counted as a generated model reply. Two deliberate real connection refusals still yield classified fallback without effects. The corrected matrix also asserts that a water gift does not reopen ship/bow/stranded topics. A pre-fix matrix demonstrating stale-topic contamination is preserved under `before-action-context-fix/`.

These samples establish the specific structural repair, not the frozen semantic release thresholds or universal absence of fallback. Prompt prose, persona quality and unsupported factual questions still need broader evaluation. Source hashes, provider wire version and prompt version are in `build-provenance.json`. All live/UI/SQL worlds are disposable; the personal save is only resumed through the normal launcher.

Commands: `PYTHONPATH=backend .venv/bin/python docs/evidence/conversation-redesign-release/validation-contract/run_live.py` and `run_route_matrix.py`; full backend unittest discovery; the standard isolated PostgreSQL runner; `run_godot_checks.py conversation_signal_smoke ui_rework_smoke bow_quest_smoke`.

## Follow-up: report versus accepted following

A read-only check of the user's latest run showed a committed `report_wreck` receipt and `wreck_reported=true`, `offer_pending=true`, `outing_active=false`; no acceptance message had been sent. Reporting alone intentionally waits for agreement. The existing regression freshly passes the exact report followed by `yes please` (11/11 production-graph tests). The full Godot Craftsman integration freshly passes in 35.17 seconds: report waits, contextual help accepts, wait/resume work, both actors leave the workshop, physical following reaches the wreck, inspection completes and solo return/reload work. Zero functional failures; its existing shutdown resource warning remains explicit. No production code or personal save was changed for this diagnosis, and no restart was needed. Close chat after accepting to resume movement.
