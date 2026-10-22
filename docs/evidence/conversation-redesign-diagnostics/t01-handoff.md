# diagnostics/T01 handoff

## Task

- ID: `diagnostics/T01` — structured safe trace projection.
- Owner/model/effort: `main_agent` / gpt-6.1-sol / high.
- Status: ready for Main Agent review.
- Scope: new typed stage event and `TracePort` projection. Sink-failure isolation and scoring export remain T02.
- Dependencies: accepted contracts/T03–T04 and ports/T01.

## Files changed

- `backend/app/services/conversation/diagnostics.py` — immutable `ConversationTraceEvent`, safe scalar projection, and `StructuredTraceSink` adapter.
- `backend/tests/test_conversation_diagnostics.py` — coverage for trace identity, versions, provider settings, sources, decisions/spans, receipts/findings, repair/final origin, credential redaction, invalid timing and cross-turn receipt rejection.
- `docs/evidence/conversation-redesign-diagnostics/t01-handoff.md` — this handoff.

## Tests run

Repository root: `/Users/rukithnayak/Documents/NPC_LLM-1`; Python 3.12.14; `PYTHONPATH=backend` unless stated.

| Check | Command | Exit | Results |
| --- | --- | --- | --- |
| Initial RED before implementation | `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_diagnostics -v` | 1 | 4 expected missing-module failures |
| Follow-up RED for cross-turn receipt scope | `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_diagnostics.ConversationDiagnosticsTests.test_receipt_from_another_turn_cannot_enter_this_turns_trace -v` | 1 | 1 expected assertion failure before guard |
| Focused GREEN | `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_diagnostics -v` | 0 | 5 passed, 0 failed/skipped |
| Trace-port/read-port conformance | `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_diagnostics backend.tests.conversation_port_conformance backend.tests.test_read_ports` | 0 | 21 passed, 0 failed/skipped |
| Legacy trace regression | `PYTHONPATH=backend:backend/tests .venv/bin/python -m unittest backend.tests.test_decision_trace` | 0 | 8 passed, 0 failed/skipped; existing Starlette/httpx and `datetime.utcnow()` deprecation warnings |
| Whitespace validation | `git diff --check` | 0 | clean |

## Acceptance outcomes

- Turn/key/sequence/fence/attempt, injected timing values, policy/prompt/schema versions, scalar provider settings, source IDs, decision codes and span offsets are included in the port event as scalar-safe values.
- Provider credential fields and credential-bearing URL userinfo/query are removed. Hidden reasoning, prompts, raw prose and validation explanations are not accepted as trace fields.
- Authorization and receipt summaries retain safe codes/IDs/outcomes; cross-turn or cross-scope receipt linkage is rejected.
- Validation findings preserve codes, categories, severities, repairability and safe span/evidence references without copying explanations.
- Repair consumption and final response origin are traced.
- Injected timings remain deterministic; nonfinite or negative timings are rejected.
- The sink adapter intentionally propagates port failures; T02 must isolate trace failures from gameplay/finalization.
- T01 does not wire this new conversation trace path into the legacy route/coordinator; application wiring remains an integration task.

## Risks and follow-up

- The concrete TracePort implementation and coordinator event production are not present yet; this task verifies safe projection only.
- `diagnostics/T02` owns best-effort sink failure isolation and evaluation export.
- Application integration must supply every supported nonsecret provider setting and durations measured by the injected monotonic clock.
