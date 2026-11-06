# validation/T01 handoff

Date: 2026-10-15. Implemented locally; integration/release acceptance remains with the coordinator.

## Changed files

- `backend/app/services/conversation/validation.py`: pure deterministic `ResponseValidator`, with whole assembled reply checks for exact span validity, evidence IDs/revisions, private source leakage, canon support spans, event attribution, mechanical contradiction, and narrowly-patterned unsupported world claims. `check_text` accepts small text/evidence/ID projections; it does not access providers, ORM, persistence, or game services.
- `backend/tests/test_conversation_validation.py`: focused behavior cases.

## Follow-up review correction and T06 integration

The first review found that reply dependencies use `SourceRef.source_id`, while the known-ID projection initially indexed only evidence IDs and receipt IDs. Added a regression using a real `MechanicalFact` → `SourceRef` and fixed the detached projection to resolve both ID namespaces. Active narrative canon is also included in that projection.

After contracts/T06 was accepted locally, validation consumes its `ValidatorClaimProjection`, `ValidatorEvidenceProjection`, and `ValidatorComparisonProjection` via optional typed keyword arguments to `check`. Claims are span-validated against the exact assembled reply; projection scope must match the conversation; comparison links must resolve to exact current evidence revisions. Explicit `contradicted` and `unknown` outcomes block. Omitted comparisons for matching subject/predicate slots also block as unknown. If context indicates canon or any T06 projection is supplied but a required projection is absent, validation blocks closed. This implements the T06 checker boundary without changing contracts.

## RED evidence

Command before implementation: `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_validation.py'`.

Exit 1, one loader error: `ModuleNotFoundError: No module named 'app.services.conversation.validation'`. The first attempted command used nonexistent `backend/.venv/bin/python` (shell exit 127); the repository interpreter is `.venv/bin/python`.

T06 integration RED command: same focused unittest command after adding contradiction/unknown comparison cases. Exit 1; 8 tests ran with 2 errors because `ResponseValidator.check` rejected the new `claim_projection` keyword. After implementation, the same command passes 8/8.

## Verification

Exact commands and observed result:

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_validation.py'` — exit 0; 8 passed, 0 failed, 0 skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts_validation.py'` — exit 0; 4 passed, 0 failed, 0 skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition*.py'` — exit 0; 38 passed, 0 failed, 0 skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_proposal.py'` — exit 0; 10 passed, 0 failed, 0 skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_canon.py'` — exit 0; 15 passed, 0 failed, 0 skipped.
- `git diff --check` — exit 0.

## Acceptance mapping and limits

- Whole assembled prose is checked in `check`, including unrelated expressive prose around slots. Mechanical contradictions and unknown dependencies produce blocking `ValidationFinding`s.
- Revision mismatch, server-private source references, invalid exact spans and unsupported continuity supporting spans are blocked.
- Player reports cannot establish first-person witnessed-event claims in this deterministic rule set.
- Harmless “soft spot” and fear idioms pass; explicit unsupported shop/cache/recipe/route existence/location claims fail.
- Projections are detached attributes/maps; implementation is pure and deterministic.
- Evidence dependencies resolve against `SourceRef.source_id` as well as evidence/receipt IDs.
- T06 claim/evidence/comparison projections produce blocking canon contradiction and fail-closed unknown/missing comparison findings.

Free prose grounding outside the T06 typed claim projections remains necessarily conservative and keyword based; this is not semantic proof and avoids treating ordinary idioms as mechanics. Current evidence revisions are compared through the supplied `RevisionSet` keyed by source IDs; receipt and immutable narrative-source revision semantics remain adapter-owned. T06 comparisons are consumed as offline injected results; this task does not activate a runtime semantic judge.

## Follow-up

- validation/T02: concern coverage, speaker identity, repetition and style evaluation hooks, calibrated fixtures, advisory/blocking distinction.
- canon/game adapter integration: supply authoritative evidence resolution and resource revision keys for final publication revalidation.
- coordinator/release integration: wire validator to assembled final replies; measure false positives/negatives for free prose before considering semantic-check activation.


## Main Agent review update (2026-10-15)

Main Agent reproduced validator 6/6, composition 38/38, proposal 10/10, and canon 15/15. Review caught an evidence-key mismatch: reply dependencies use underlying `SourceRef.source_id`, so context projection now recognizes both evidence IDs and their source IDs; the added regression passed. T01 remains incomplete because active canon prose plus assembled spans do not encode typed speech propositions, and string matching would conflict with detailed design §3.4. The proposed versioned contracts/T06 task is recorded in the contracts packet and task graph pending user direction.

## Main Agent review update (2026-10-18)

Contracts/T06 is now locally accepted and the validator consumes typed claim/evidence/comparison projections. Main Agent independently reran focused 8/8, contract 4/4, composition 38/38, proposal 10/10, canon 15/15, full conversation 305/305, and `git diff --check` (all exit 0; 0 failures/skips). The conversation suite emits the existing Starlette/httpx deprecation warning.

An independent read-only review did not accept T01 yet. It found that (1) there is no `check`-level assembled-reply regression proving a correct slot is blocked by contradictory surrounding prose, (2) stale revision and private evidence rejection lack focused tests, (3) the unsupported-world-claim heuristic treats any evidence text containing the same category word as support without matching the claim's subject/location, and (4) typed claim projections are not guaranteed to enumerate every proposition in the reply. The source design forbids treating string matching as full semantic proof, so the heuristic limitations must remain explicit and fail closed where required. T01 remains incomplete; correct these within the existing acceptance boundary or record a separate task before expanding scope. No production edits were made during this review pass.

The bounded correction changed only `backend/app/services/conversation/validation.py` and `backend/tests/test_conversation_validation.py`. Tests now cover a correct receipt-backed transfer span contradicted by surrounding speech, stale/private dependencies, and unrelated route evidence sharing only a category word. Grounding support requires the full claim sentence in detached evidence; this is conservative deterministic matching, not semantic proof. A further Main Agent regression using an actual `OperationReceipt` initially failed because the checker only handled evidence with `kind` and `content`; receipt-aware transfer contradiction detection now blocks it.

Main Agent independently reproduced:

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_validation.py'` — exit 0; 12 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_contracts_validation.py'` — exit 0; 4 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_composition*.py'` — exit 0; 38 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_canon.py'` — exit 0; 15 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` — exit 0; 315 passed, 0 failed/skipped.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — exit 0; 778 passed, 0 failed/skipped.
- `git diff --check` — exit 0.

T01 remains incomplete. The accepted T06 `ValidatorClaimProjection` validates each included claim span but does not attest that every canon-relevant proposition in the assembled reply is included. The checker cannot prove complete canon coverage from the current frozen projection without assuming semantic completeness or broadening string matching in a way the source design rejects. Do not edit contracts under T01; record and schedule a separate contracts/validation task if that guarantee is required. Existing task count remains unchanged.

## Coverage contract follow-up (2026-10-18)

The prior open coverage gap was addressed in recorded `contracts/T09`: `ValidatorClaimProjection` now requires `coverage_status` bound to its exact `text_id`, and ResponseValidator blocks partial or unavailable coverage before evaluating comparisons. The existing T06 fixture declares complete coverage; this records the upstream extraction result and is not independent semantic proof. Validation/T01 was reverified at 13 focused validation, 5 contract-validation, 518 conversation and 986 backend tests; all pass with `git diff --check` clean. See [contracts/T09 handoff](../conversation-redesign-contracts/t09-handoff.md).
