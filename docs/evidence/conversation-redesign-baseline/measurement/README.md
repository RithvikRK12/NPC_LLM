# baseline/T02 measurement handoff

**Status: baseline/T02 complete (2026-10-18); quality and shipping acceptance remain separate release gates.** The initial 2026-10-14 attempt was blocked by a configured provider `ConnectError`. On 2026-10-18 the existing Ollama service became reachable and the frozen isolated live sessions completed; details follow. The run measures response origins and route latency, not human-rated language quality or a shipping latency budget.

**Sandboxed connectivity probe (2026-10-18, Asia/Kolkata):** `curl --max-time 3 -sS -o /tmp/npc-provider-health.txt -w 'HTTP %{http_code}\n' http://localhost:11434/v1/models` exited **7** (`Failed to connect`); HTTP status was `000`. The sandbox denied localhost access. A subsequent approved local-network check returned HTTP 200 and the live measurement completed, as recorded below. This probe wrote only to `/tmp`.

**Live rerun (2026-10-18, Asia/Kolkata):** The earlier connectivity result was transient: an unsandboxed check returned HTTP 200, `ollama list` showed the configured model, and the exact measurement command below completed with exit 0. The sandbox could not bind or reach localhost; the already installed Ollama service was available through the approved local-network execution. No application provider settings were changed.

```sh
.venv/bin/python docs/evidence/conversation-redesign-baseline/measurement/measure.py | tee docs/evidence/conversation-redesign-baseline/measurement/run-2026-10-18.log
```

The collector ran from `/Users/rukithnayak/Documents/NPC_LLM-1`, using frozen fixture schema 1, SHA-256 `12bbcf23963e8ff3328db62c435862daba55d67027f7e48fa24872265a0c1e3a`, and fresh in-memory SQLite per replay. It completed two seven-turn sessions for each NPC, each repeated twice (28 configured turns total), with 140 credential-redaction checks across all modes. Deterministic mock/controlled/outage replays matched. The configured live gate is complete and had no provider errors.

| Configured live origin | Turns | Count |
| --- | ---: | ---: |
| Generated | 28 | 6 |
| Scripted / server-rendered | 28 | 12 |
| Healthy-provider fallback | 28 | 10 |
| Provider errors | 28 | 0 |
| Explicit mock | 28 | 0 |

| Configured live route | n | p50 | p95 |
| --- | ---: | ---: | ---: |
| Ordinary | 20 | 2.290 s | 4.362 s |
| Action | 8 | 0.019 s | 0.025 s |
| Repair | 0 | unavailable | unavailable |

Repair has no samples because the existing runtime does not make a repair generation; this remains an unavailable baseline, not a zero-latency result. The exact settings and turn-level records are in [results.json](results.json); stdout is in [run-2026-10-18.log](run-2026-10-18.log). The model was `llama3:latest`, Ollama API manifest digest `sha256:365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1` (8.0B, Q4_0); server version was `0.34.2`. Model metadata came from `ollama --version`, `ollama show --modelfile llama3:latest`, and `/api/tags`.

The worktree contained uncommitted application changes during this run; `source_revision` in results identifies `HEAD`, while the task handoff records the live dirty-worktree limitation. No player save or configured embedding service was used.

## Reproduce

Run from `/Users/rukithnayak/Documents/NPC_LLM-1`:

```sh
.venv/bin/python -m unittest discover -s docs/evidence/conversation-redesign-baseline/measurement -p test_measure.py
.venv/bin/python docs/evidence/conversation-redesign-baseline/measurement/measure.py
```

Historical 2026-10-14 exits: initial three-check suite before implementation **1**, expected `ModuleNotFoundError: measure`; four-check suite **0**, 4 passed ([tests.log](tests.log)); first measurement **0**, 113 controlled/live-attempt rows and diagnostic checks ([run.log](run.log)). The configured live gate was false in that historical run. Current 2026-10-18 tests and live measurement are recorded above. [results.json](results.json) contains current settings, source Git revision/fixture SHA-256, per-turn records, origins, actions, inventories, timings, provider-call error classes and p50/p95 denominators. [fixtures.json](fixtures.json) records the unchanged T02 input/state setups; [measure.py](measure.py) is the runner.

## Configuration and isolation

Safely loaded actual settings select `OpenAICompatibleProvider`, `llama3:latest`, base URL `http://localhost:11434/v1`, temperature 0.2, structured output enabled, total HTTP timeout 120 seconds and connect timeout 5 seconds. No provider deadline override was used. The provider sends no max_tokens value. Current dialogue limit is 240 characters, memory top_k 5/candidates 40. The immutable Ollama manifest digest is recorded above and in results. The sanitized whitelist is in results; `.env` contents, API keys, URL userinfo and query strings are not exported.

The runner imports the direct pipeline and asserts neither `app.main` nor `app.database.session` was imported. It creates fresh SQLite `sqlite://` engines per mode/NPC/replay, creates schema and seeds only these in-memory databases, then closes/disposes them. It never opens a player save or application startup path. Opening is marked complete; the Gatherer fixture is deliberately in resolved_helped state. Embedding is patched to deterministic 768-dimensional one-hot vectors before pipeline construction: no embedding HTTP or disk cache is used. The existing memory index cache remains process-local. Only this measurement directory receives evidence writes.

Both seven-turn T02 NPC sessions include greeting, personal/emotional reflection, requested biography, correction, named-item request, purpose confirmation and inventory query. Two identical replays are run independently for each mode. All modes produced equal non-timing records, including visible text and mechanical inventory outcomes. This instrumentation set is separate from T03's 44-scenario evaluation fixture.

## Initial 2026-10-14 attempt and controlled response origins/timings

Counts are final-response origins. Error counts overlap fallback counts because a failed provider call can still yield a successful fallback response. Generated means accepted candidate prose; scripted includes authoritative routing and selected-fact rendering. Fallback is derived from generation failure or validation rejection, not text matching. Connection/timeout error classes are outage fallback; HTTP/provider errors have a separate provider-error fallback; a failed generation with no provider-call exception is decode-or-unknown error fallback because the pipeline combines parsing and generation failures. A malformed JSON response is never assumed to be a transport outage. Explicit mock is never counted as a healthy live provider. Controlled `healthy_valid`/`healthy_rejected` are successful **fake** transport responses, not provider health findings. All underlying trace provider names read `ControlledProvider`; the mode and declared upstream identify the configured adapter versus the test doubles without pretending that wrapper name is the deployed provider.

| Mode | Turns | Generated | Scripted | Fallback | Errors | Explicit mock turns |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Initial configured live attempt (2026-10-14) | 1 | 0 | 0 | 1 | 1 | 0 |
| Explicit MockLLMProvider | 28 | 0 | 12 | 6 | 0 | 16 |
| Controlled accepted candidate | 28 | 10 | 12 | 6 | 0 | 0 |
| Controlled rejected candidate | 28 | 0 | 12 | 16 | 0 | 0 |
| Controlled outage | 28 | 0 | 12 | 16 | 16 | 0 |

Explicit mock turns include 10 accepted mock outputs and 6 rejected mock outputs; its 12 authoritative turns bypass generation. Fallback subtypes in JSON keep these categories separate. Controlled valid responses are intentionally simple fixed prose, and current validation rejects some ordinary inputs even when transport succeeds; this exercises attribution, not quality scoring.

The following are full `pipeline.chat` timings including fake embedding and in-memory persistence, in milliseconds; nearest-rank p50/p95 are used. These controlled timings are **not deployed provider latency**. The configured row is one failed ordinary call from the initial attempt, not an ordinary-play percentile estimate; current live route measurements are reported above.

| Mode | Ordinary n / p50 / p95 ms | Action n / p50 / p95 ms | Repair n / p50 / p95 |
| --- | --- | --- | --- |
| Initial configured live attempt (2026-10-14) | 1 / 29.83 / 29.83 | 0 / unavailable / unavailable | 0 / unavailable / unavailable |
| Explicit mock | 20 / 5.28 / 8.87 | 8 / 7.23 / 19.15 | 0 / unavailable / unavailable |
| Controlled accepted candidate | 20 / 5.29 / 8.46 | 8 / 7.01 / 26.74 | 0 / unavailable / unavailable |
| Controlled rejected candidate | 20 / 5.03 / 7.29 | 8 / 7.14 / 8.17 | 0 / unavailable / unavailable |
| Controlled outage | 20 / 5.25 / 7.50 | 8 / 7.82 / 9.43 | 0 / unavailable / unavailable |

Repair sample count is zero because existing `_validate_or_repair` immediately falls back; it never makes a repair generation. Validation-rejected ordinary turns remain ordinary-route timings. Action samples are the fixture's item negotiation/purpose routes; the stock query is an ordinary factual turn. These do not measure physical encounter completion or redesigned operation receipt latency.

## Diagnostic verification and acceptance

`services/pipeline.py` supplies generation status and authoritative override; `services/decision_trace.py` supplies bounded proposal/validation/configuration fields. It excludes raw prompt, raw prose and reasoning. The runner tests URL credential removal and asserts the actual configured API key (when present), URL password/query, and injected secret sentinel are absent from both decision/grounding traces and the full exported artifact. The sentinel appears only in a fake exception or rejected raw reasoning. The initial run passed 113 checks; the 2026-10-18 rerun passed 140. Free-form exception details and HTTP response bodies are not logged/exported; the current configured live run had no errors.

| T02 acceptance / expectation | Result |
| --- | --- |
| Exact configured provider/model/settings | Recorded whitelist, Ollama 0.34.2 and immutable llama3 manifest digest |
| Representative Craftsman and Gatherer sessions | 28 live configured turns: two seven-turn sessions per NPC, each repeated twice |
| Generated/scripted/fallback/error accounting | Live counts: 6 generated, 12 scripted, 10 healthy-provider fallback, 0 errors, 0 explicit mock |
| Ordinary/action/repair p50/p95 | Live ordinary n=20, 2.290/4.362 s; action n=8, 0.019/0.025 s; repair n=0 unavailable in current runtime |
| Isolated fixtures, no player save | Fresh in-memory SQLite; direct pipeline; fake embedding; startup/session import assertions pass |
| Identical replay | All four controlled modes equal on non-timing records; both live NPC fixtures completed twice |
| Healthy fallback vs outage vs explicit mock | Live healthy fallback is separate from the controlled outage and explicit-mock modes |
| Credential-free diagnostics | 140 current decision/grounding trace checks and full export check passed |

The live measurement gate is satisfied. No model replacement, relaxed validator or timeout change was made. Review transcripts and score them separately during evaluation; provider reachability and baseline origins do not establish quality acceptance.

**Existing follow-up IDs:** `baseline/T03` owns frozen evaluation fixtures/policy candidates; `evaluation-release/T01` owns read-only shadow scoring, and `evaluation-release/T03` owns quality and product latency/readability acceptance. No new follow-up IDs or numeric shipping limits were created. Main Agent owns packet/master status updates.
