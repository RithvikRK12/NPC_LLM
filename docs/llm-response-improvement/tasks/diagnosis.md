# Diagnosis task packet

Source of requirements: Stage 3 and Stage 4 of [`../../llm-response-improvement-plan.md`](../../llm-response-improvement-plan.md).

## D01 — materialize packets and establish runtime baseline

Dependencies: none. Owner scope: this planning namespace and evidence diagnosis; runtime files read-only.

- [x] Inspect working tree, applicable instructions, source route, and current client request path. Preserve all existing modifications and historical evidence.
- [x] Materialize workstream progress and task packets without overwriting generic project docs.
- [x] Record effective non-secret settings and available hardware/model/provider evidence; state unavailable facts precisely.
- [x] Reproduce representative personal, mixed practical, recall, and action replies in isolated local sessions if available; record route and output origins. Local endpoint was inaccessible; preserved historical cases and recorded this limitation.
- [x] Publish `docs/evidence/llm-response-improvement/diagnosis.md` with observed facts, hypotheses, unknowns, commands/results, and next task.

Acceptance: actual path/provider evidence is recorded or precisely unavailable; no defaults are presented as active deployment facts; no production state changes. Validation is source/schema inspection and safe isolated measurements only.

Status: verified 2026-10-19. Evidence: [`../../evidence/llm-response-improvement/diagnosis.md`](../../evidence/llm-response-improvement/diagnosis.md).

## D02 — reproduce and resolve structured-output budget ambiguity

Dependencies: D01; E01 before live comparisons. Files are limited to structured generation, necessary callers/contracts/settings, focused tests, and a dated design addendum if a public contract change is needed.

- [x] Use a semantically valid typed response whose final dialogue is within policy while serialized JSON exceeds the dialogue-sized budget; reproduce rejection and token allocation.
- [x] Decide from reproduction whether this violates intended contract. Record explicit units, bounds, compatibility, and migration before any confirmed-defect implementation.
- [x] If confirmed, add focused failing tests and make the smallest bounded fix. Verify dialogue/JSON bounds, token allocation, Unicode, schema failures, and deadlines.
- [x] If not a defect, close no-change with evidence.

Acceptance: budget units are explicit and tested, final dialogue remains within policy, no unbounded output. Run generation adapter, proposal, composition, repair, and touched contract/settings suites.

Current result: `StructuredGenerationAdapter.generate` now receives a named dialogue codepoint limit, uses a separate 2,048 token default and 16,384 JSON-character default, and rejects explicitly invalid/missing bounds before dispatch. Direct local proposal adapter calls were recorded for Llama and Gemma; full durable application-path screening remains unavailable because the current local runtime policy is incomplete and the feature flag is false. See [`../design-addenda/D02-2026-10-19.md`](../design-addenda/D02-2026-10-19.md), [`../../evidence/llm-response-improvement/diagnosis.md`](../../evidence/llm-response-improvement/diagnosis.md), and the test results in master progress.

D02 status: code-level verified 2026-10-19 after user selected defaults of 2,048 generation tokens and 16,384 serialized JSON characters; durable runtime remains disabled.

2026-10-20 correction: the original sandboxed shell path to Ollama loopback was denied, but an approved elevated local command path can access the running local Ollama endpoint. Direct local Llama structured screens and fixture-only full prompt runs are now recorded. This does not enable or verify the disabled durable application route. No hosted inference was used.
