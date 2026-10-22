# contracts/T06 handoff

Date: 2026-10-15. Local contract and fixture work complete; validation/runtime integration remains with the coordinator.

## Changed files

- `backend/app/services/conversation/contracts.py`: added versioned immutable `ValidatorClaimProjection`, `ValidatorEvidenceProjection`, and `ValidatorComparisonProjection` values, plus nested claim/comparison values. Claim spans must point into the exact `AssembledReply` text ID and resolve within its final text. Evidence requires active public canon claim heads with scoped game/NPC identity, canonical IDs/revisions, and `narrative_only` authority. Comparisons carry explicit `supported`, `contradicted`, or `unknown` outcomes, can be checked against claim/evidence projections, and default omitted pairs to `unknown`; only explicit support reports consistent.
- `backend/tests/test_conversation_contracts_validation.py`: adds JSON round-trip, bad span, scope/ID/revision mismatch, private/authority rejection, unknown/contradicted outcome, immutability and missing-outcome cases.
- `backend/tests/fixtures/conversation/contracts-t06-valid.json`: shared valid projections and assembled reply fixture.

## Red/green evidence

- Before implementation, with the fixture present: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts_validation.py'` — exit 1; 4 tests errored because `ValidatorClaimProjection`, `ValidatorEvidenceProjection`, and `ValidatorComparisonProjection` were not defined.
- After implementation: same focused command — exit 0; 4 passed.

## Verification

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts*.py'` — exit 0; 70 passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_validation.py'` — exit 0; 6 passed.
- `PYTHONPATH=backend .venv/bin/python -c "from app.services.conversation import contracts; print(contracts.ValidatorClaimProjection.__name__)"` — exit 0; pure module import printed `ValidatorClaimProjection`.
- `git diff --check` — exit 0.
- Broader `test_conversation_*.py` discovery — exit 1; 285 tests ran, 12 failures all in unrelated `test_conversation_operations.py` because `OperationPolicy` is absent in this shared worktree. The other discovered tests passed.

## Limits and boundaries

The contract represents offline semantic extraction and comparison results; it does not implement either checker, infer meaning from prose, or connect to providers. A projection's IDs, revisions, scope, public visibility and declared narrative authority are validated structurally; the owning server adapter must still prove that those values came from its current authoritative read set. Canon evidence remains narrative-only and cannot authorize gameplay. Missing comparisons map to `unknown`, and `unknown` is not consistent. No schema, database, API, validation implementation, or gameplay requirements were changed.
