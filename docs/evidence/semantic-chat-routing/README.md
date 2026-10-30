# Semantic chat routing evaluation

The held-out evaluation ran 23 turns through the real `/chat` route with local
`llama3:willowbrook` at temperature 0. Each NPC scenario used a disposable
in-memory SQLite database. Neither personal `mvp.db` was used. The frozen
fixture and complete per-turn audit are in
`backend/tests/fixtures/semantic-routing-heldout-v1.json` and `report.json`.

## Results

| Measure | Result | Design target |
| --- | ---: | ---: |
| Complete interpretation accuracy | 3/23 (13.0%) | >=90% |
| Gatherer interpretation accuracy | 3/12 (25.0%) | >=90% overall gate applies |
| Craftsman interpretation accuracy | 0/11 (0%) | Both NPCs are represented |
| Operation accuracy | 1/3 (33.3%) | Component of complete interpretation |
| Fact reference accuracy | 0/4 (0%) | Component of complete interpretation |
| Target accuracy | 0/1 (0%) | Component of complete interpretation |
| Modality accuracy | 2/5 (40.0%) | Component of complete interpretation |
| Pending answer type accuracy | 0/3 (0%) | Component of complete interpretation |
| Unnecessary fallback on non-clarification turns | 11/20 (55.0%) | <5% |
| Grounding rejection | 13/23 (56.5%) | Reported; no target |
| Mixed-concern coverage | 0/7 (0%) | >=90% |
| Unauthorized mutations | 0/23 (0%) | 0 |
| Expected state changes completed | 2/7 (28.6%) | Reported; no target |
| Interpretation model calls | 46/23 turns; 23 extra correction calls | Reported |
| Speech and repair calls | 12 total | Reported |
| Interpretation latency | p50 15.080s, p95 34.023s (23/23) | No threshold specified |
| End-to-end latency | p50 30.359s, p95 59.462s (23/23) | No threshold specified |

The run met the zero-unauthorized-mutation condition but missed routing,
fallback, and mixed-concern targets by a wide margin. It does not establish
generalization. Two purpose-bearing item turns completed transfers. The original
wellbeing exchange and one reworded social continuation were interpreted as
social. Several Craftsman encounter requests and factual
turns were classified incorrectly or failed span validation. Failures degraded
without state changes. Accidental repetition and consistency targets were not
measured in this fixture and remain unproven.

The report's confusion table and each turn's classification, reply,
before/after state, fallback classification, calls, and timings provide the
per-case evidence. Interpretation accuracy requires the exact expected concern
kinds and checks the expected operation, fact, target, modality, and answer
type where specified. It does not measure universal safety.

## Test baseline

Before editing, the full unittest discovery run had 562 tests and failed with
20 failures and 53 errors. This included imports for absent legacy conversation
modules, personal-history/render failures, and tests requiring the missing
conversation contracts. The same command after implementation had 573 tests,
57 failures, and 75 errors in the restricted environment; tests that attempted
the configured localhost model received `ConnectError` and degraded. A second
full run with Ollama access was stopped after legacy behavior tests began making
slow real-model calls and did not produce a complete suite result.

The focused contract and deterministic HTTP integration checks passed:

```sh
PYTHONPATH=backend .venv/bin/python -m compileall -q backend/app backend/tests
PYTHONPATH=backend .venv/bin/python -m unittest backend.tests.test_semantic_routing -v
cd backend/tests
PYTHONPATH=..:.. ../../.venv/bin/python -m unittest \
  test_grounded_chat.GroundedChatTests.test_mixed_social_and_factual_concerns_keep_both_grounded_segments \
  test_grounded_chat.GroundedChatTests.test_quoted_item_request_is_interpreted_but_never_executed \
  test_npc_pipeline.NPCPipelineTests.test_request_waits_for_reason_and_can_be_cancelled -v
```

## Re-run live evaluation

Start Ollama with the configured local `llama3:willowbrook` model, then run from
the repository root:

```sh
PYTHONPATH=backend .venv/bin/python backend/tests/run_semantic_routing_live.py \
  --output docs/evidence/semantic-chat-routing/report.json
```

The runner refuses a different model and creates disposable in-memory SQLite
worlds. It does not use either personal save database.
