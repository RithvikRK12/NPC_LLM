# Integration task packet

Source: Stage 3 and Stage 4 of [`../../llm-response-improvement-plan.md`](../../llm-response-improvement-plan.md).

## I01 — production path and adoption handoff

Dependencies: C01, C02, D02, P01, M02; compatibility review and product latency/resource decision before deployment selection.

- [ ] In isolated state through the full enabled application, test no-operation `proposal.reply`, receipt composition, repair, provider failure, and receipt-safe fallback. Direct adapter checks were isolated and do not replace this gate.
- [ ] Verify exact consent, quoted/hypothetical actions, retry/idempotency, scope/epoch clear, and finalized output. Never replay a committed effect for speech evaluation.
- [x] Run focused and relevant adjacent backend tests; no PostgreSQL/Godot boundary was changed in this workstream, so those gates were not required. Full live-route integration remains unavailable because the current runtime policy/feature flag keeps it disabled.
- [x] Prepare pinned configuration, enable prerequisites, rollback retaining receipts, measured costs, unresolved gates, and recommendation in [`../runbook.md`](../runbook.md).
- [ ] Keep deployment unchanged until required product decisions and adoption gates are satisfied.

Acceptance: adoption is reviewable, bounded behavior is verified, and no unsupported ship claim is made.

Progress: D02 adapter bounds are 2,048 tokens / 16,384 JSON characters / ≤600 dialogue codepoints. Receipt-aware composition now stamps trusted current provenance and appends exactly one server-created receipt slot when absent; focused tests preserve duplicate/mismatch and outcome checks. Local r8 receipt-stage generation still failed strict canon validation, and proposal generation failed an unknown-concern check, while direct composition/repair adapter stages returned typed values. Scripted application/fallback/consent/idempotency/scope tests cover deterministic boundaries. The full enabled local application route cannot be run because current settings leave its feature flag off and durable policy incomplete; do not configure or enable it implicitly. The user waived human reviews, so no semantic quality scores are available. Repeatability runs are complete, but no quality winner or prompt adoption is supported. Deployment remains unchanged pending a product latency/readability decision and the full route gate.
