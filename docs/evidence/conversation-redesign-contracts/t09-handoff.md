# contracts/T09 handoff

Date: 2026-10-18 (Asia/Kolkata)
Owner: Main Agent

## Recorded gap and change

Validation/T01 review found that `ValidatorClaimProjection` binds included propositions to exact final speech but had no field to distinguish a complete extraction from a partial or unavailable one. Added required `coverage_status` with `complete`, `partial`, and `unavailable` values. The validator now emits a blocking `CANON_COVERAGE_INCOMPLETE` finding for partial or unavailable extraction and does not consume the partial proposition list for canon comparisons.

The status is an explicit result supplied by the offline extraction boundary; the validator does not infer completeness from a nonempty list. This contract is an interface and fail-closed gate, not proof that an extractor's semantic attestation is accurate. It grants no game authority.

## Test-first and verification evidence

- Before implementation, the new contract test showed that a claim projection with no coverage outcome was accepted; the validator REDs rejected the new statuses as unknown fields.
- Contract tests: 5/5 pass.
- Validator tests: 13/13 pass, including blocking behavior for partial and unavailable coverage.
- Full conversation suite: 518/518 pass; full backend suite: 986/986 pass.
- `git diff --check`: exit 0.

## Downstream

Validation/T01 now requires a complete coverage outcome before accepting canon comparisons. Any future extraction implementation remains offline and must bind its result to the exact final text; the validator will fail closed when it cannot make that declaration.
