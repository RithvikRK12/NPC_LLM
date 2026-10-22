# diagnostics/T02 handoff

## Task

- ID: `diagnostics/T02` — isolate trace failures and produce reproducible evaluation rollups.
- Owner/model/effort: `diagnostics_t02` / gpt-6.1-sol / high.
- Status: locally verified; ready for Main Agent review.
- Dependencies: `diagnostics/T01` structured trace projection.
- Scope kept bounded: no coordinator/route wiring, no live generation, no inferred quality or provider-health claims.

## Files changed

- `backend/app/services/conversation/diagnostics.py` — trace exception isolation, detached evaluation sample/manifest types, deterministic JSON export.
- `backend/tests/test_conversation_diagnostics.py` — sink outage and export coverage.
- `docs/evidence/conversation-redesign-diagnostics/t02-handoff.md` — this handoff.

## Behavior

- `StructuredTraceSink.emit` treats projection and `TracePort.record` exceptions as best effort. `emit_trace_best_effort` also isolates failures from arbitrary injected sinks. The helper returns no status that application code could use to change gameplay, finalization, or receipt recovery.
- `EvaluationSample` requires explicit route, origin, and provider-health labels; provider health defaults to `unknown`. Token usage is counted only when observed tokens are explicitly supplied. No generation health or quality rate is inferred.
- `build_evaluation_export` emits canonical sorted JSON with the manifest's dataset/version/fixture digest/policy/model identifiers and allowlisted scalar provider settings; safe scalar sample rows; total, scenario, route, origin, provider-health, and fallback-by-health counts; available-token sample count and sum; repetition counts; route-specific p50/p95 and sample counts; percentile method; plus caller-supplied retention/access policy IDs, retention seconds (nullable if unspecified), and access roles.
- Percentiles use inclusive linear interpolation at rank `q * (n - 1)`. Empty route buckets retain a sample count of zero and null percentiles. Duplicate sample IDs, malformed fixture digests, invalid scalar measurements, and invalid metadata fail closed.
- Export includes identifiers and numeric evaluation facts only; it does not contain prompt text, conversation prose, hidden reasoning, credentials, or provider configuration values.

## Tests run

Repository root: `/Users/rukithnayak/Documents/NPC_LLM-1`; Python 3.12.14; `PYTHONPATH=backend`.

| Check | Command | Exit | Results |
| --- | --- | --- | --- |
| Initial RED | `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_diagnostics.ConversationDiagnosticsTests.test_sink_outage_is_best_effort_and_does_not_escape_emit_boundary backend.tests.test_conversation_diagnostics.ConversationDiagnosticsTests.test_evaluation_export_is_reproducible_and_reports_route_counts_percentiles_and_metadata backend.tests.test_conversation_diagnostics.ConversationDiagnosticsTests.test_evaluation_export_does_not_infer_token_usage_or_healthy_provider_state -v` | 1 | 3 expected missing-API import errors before implementation |
| Focused GREEN | `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_diagnostics -v` | 0 | 9 passed, 0 failed/skipped |
| Trace/read-port adjacency | `PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_conversation_diagnostics backend.tests.conversation_port_conformance backend.tests.test_read_ports` | 0 | 25 passed, 0 failed/skipped |
| Whitespace | `git diff --check` | 0 | clean |
| Broader conversation discovery during parallel implementation | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` | 1 | 219 discovered; 2 import errors from concurrently incomplete sibling modules: `test_conversation_generation_adapter` could not import `app.services.llm.structured`, and `test_conversation_memory` could not import `app.services.conversation.memory`. Diagnostics tests passed. |
| Broader conversation discovery after sibling modules landed | `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'` | 0 | 235 passed, 0 failed/skipped |

## Risks and follow-up

- The outage check proves the diagnostics boundary does not propagate exceptions; no concrete coordinator/finalizer is wired to this new module yet. Integration must call the safe boundary at operation, finalization, and recovery observation points.
- The exporter labels results only from explicit inputs. Upstream evaluation collection must determine route/origin/provider health and token availability; `unknown` remains a valid outcome.
- Retention and access values are reported from caller-supplied metadata. This module does not enforce storage deletion or authorization.
- Healthy-generation/fallback rates and quality targets require representative evaluation evidence; this task makes no such claim.
