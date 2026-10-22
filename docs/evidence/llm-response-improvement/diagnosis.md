# D01 runtime and evidence diagnosis

Inspection: 2026-10-19, Asia/Kolkata. Scope was read-only against runtime/product files. No app startup, database migration, production request, provider generation, or state mutation was performed.

## Checkout and handoff drift

- Handoff planning HEAD and current HEAD both identify `83af36d1541fce21a546b058ef69df591741ec7a` (`Add craftsman and gatherer encounter systems`), branch `master-progress`, tracking `origin/master-progress`.
- The working tree is not the handoff's cleanly understood source snapshot: `git status --short --branch` showed 58 modified tracked files and many untracked files at inspection, including conversation runtime/contracts/context/worker/persistence/diagnostics modules, extensive tests and fixtures, Godot durable conversation client code, and conversation redesign evidence. The exact inventory remains in the initial status output/session; existing files and artifacts were not edited or removed.
- No applicable `AGENTS.md` exists in this repository tree or its parent. A filesystem search found unrelated instructions in sibling projects only; they do not apply.
- Workstream files were absent, so additive packets were created under `docs/llm-response-improvement/`. Generic `docs/proposal.md`, `docs/high-level-design.md`, `docs/detailed-design.md`, `docs/master-progress.md`, and redesign progress were not overwritten.
- A provenance check found an additional source/output mismatch: the frozen fixture SHA-256 matches its replay manifest (`a76b3c…e3bc`), but the archived result records replay-adapter SHA-256 `1f2ee4…3655` while the currently present historical runner hashes to `a05add…387d`. Both historical files are untracked at this checkout and were untouched. The archived 176 outputs remain present, but exact prompt regeneration from the current runner must not be described as reproducing the original baseline. Fresh prompt snapshots and their exact hashes are required for new fixed-context model comparisons.

## Actual request path and configured runtime

1. Current Godot chat UI calls `ConversationGateway.submit`; `build_payload` includes `schema_version`, `request_id`, `game_scope`, `conversation_epoch`, `npc_id`, and `player_message`; `_send_submission` posts it to `/chat`.
2. `backend/app/api/routes/chat.py` branches on whether `request_id` was explicitly supplied. Versioned requests use `request.app.state.conversation_runtime`; they never build the legacy `ConversationPipeline`. Requests without `request_id` use the legacy pipeline.
3. `backend/app/main.py` assembles the durable runtime only when a complete conversation policy is configured. If settings say the durable feature is enabled without that policy, startup fails. `VersionedConversationTransport` returns the durable application's result while disabled to preserve recovery/idempotency; it does not redirect a new versioned request into legacy inference.
4. Safe effective `Settings()` inspection in this environment found: conversation enabled `false`; all durable policy fields other than the new selected output bounds unset; `llm_base_url` configured to localhost; local model setting `llama3:latest`; structured output enabled; timeout 120 seconds. The D02 generation/JSON bounds now default to 2,048/16,384 but do not opt into durable runtime. Thus this checkout's resolved app configuration has no durable runtime and a versioned request cannot be served by the legacy provider path. This describes the inspected environment only; the separately running game/backend container's effective environment was not accessible, so it is not claimed as deployed state.
5. Legacy no-`request_id` path uses `ConversationPipeline` and `LLMService`. With a configured base URL it selects `OpenAICompatibleProvider`; absent URL selects `MockLLMProvider`. Provider/JSON failures are caught and converted to empty raw output, then deterministic validation/fallback/behavior logic forms the displayed response. Known intent, transfer, and inventory questions may bypass inference and use authoritative service output. The database trace records provider class and generation status, but the response itself does not expose a uniform generated/fallback origin field.
6. Durable path proposals and compositions use `StructuredGenerationAdapter`; final origin is represented as generated/repaired/fallback/mock in `AssembledReply` and safe diagnostics. The receipt-first fallback preserves committed operation outcomes.

### Response origins

- Historical T01 replay responses are configured local-model generated outputs; README identifies `llama3:latest` and fixed replay settings. They are dialogue-only replay artifacts, not live production structured-path evidence.
- Current local settings point to a localhost OpenAI-compatible endpoint. Ordinary sandbox calls could not connect, but approved local loopback commands reached Ollama; response origins and pinned model are recorded in the shadow run ledger. No response from the current game/backend route was captured.
- The current Godot request format selects the durable path. Effective settings observed here cannot assemble that path, and provider connectivity prevented an isolated live response. Therefore no claim is made about origin distribution in a live game session.

## D02 — structured-output budget defect reproduced

At initial inspection, `ConversationPolicy.output_char_limit` was bounded to at most 600 Unicode code points (`contracts.py`). `ProposalService`, `CompositionService`, and repair passed that integer to `StructuredGenerationAdapter.generate` as `response_budget`. The adapter used it as provider `max_tokens`, described it in the prompt as a response character limit, and rejected when the character length of the entire returned JSON string exceeded the same integer. Whole structured proposal metadata therefore competed with dialogue under both a token bound and a dialogue-sized JSON character bound.

Fake-transport reproduction confirmed the defect: the valid frozen proposal fixture has 917 serialized JSON characters and 11 reply characters. Passing a 600 budget sent `max_tokens=600` and returned `GenerationMalformed` because the full JSON exceeded 600 characters. This violated the intended contract: the final dialogue ceiling should not bound metadata or provider token units.

D02 is now implemented as an additive bounded contract. `output_char_limit` remains the final dialogue Unicode-codepoint ceiling (at most 600). New settings independently bound serialized JSON characters (1–65,536) and generation tokens (1–16,384), with user-selected defaults of 16,384 and 2,048. These defaults do not opt into durable runtime; the rest of the runtime policy remains incomplete and `conversation_enabled=false`. Provider `max_tokens` derives only from the token setting; full serialized content uses the JSON-character bound. Prompt contract version is v4 and structured diagnostics contract version is v2. Focused and adjacent tests passed; see master progress for exact counts. No deployment configuration or routing was changed.

The separately implemented evaluation runner uses independent CLI bounds and labels itself dialogue-shadow-only; it does not constitute evidence for the structured production path.

## Hardware and local provider availability

- `system_profiler SPHardwareDataType` reported Apple MacBook Air, Apple M5, 10 CPU cores (4 performance, 6 efficiency), 16 GB unified memory. Serial/UUID output is intentionally omitted.
- `ollama` 0.34.2 is installed at `127.0.0.1:11434`. Ordinary sandbox calls could not connect (`operation not permitted`), but approved read-only elevated calls later succeeded. Exact installed identities and live local endpoint state are recorded in [`model-inventory.md`](model-inventory.md). No hosted inference was used.
- `sysctl -n hw.memsize` was denied by environment policy. The hardware summary above supplied memory size independently.
- No candidate selection or download was attempted. The existing `llama3:latest` string is a mutable tag, not a verified current model identity.

## Existing failures and controls preserved for later measurement

Use only copies/snapshots for later experiments; source evidence remains untouched:

- `craftsman-01` has a mixed feelings plus rope-purpose request. Historical output makes unsupported pulley/bridge/use and offers a demonstration; review asks whether the game supports that demonstration.
- `craftsman-02` has mixed feelings plus wood purpose; one reviewed candidate acknowledges feelings but does not explain a supported use. Its follow-up/topic-switch turn asks about the workday and receives a fabricated weather forecast. `craftsman-02:t4` states the Craftsman's father is deceased although authored survival is unspecified.
- `gatherer-04:t2` is the fruit recall case; a later turn misattributes the prior fruit preference as company/companionship. Preserve the successful Craftsman recall controls in the full suite.
- Historical reviewer artifacts are one-reviewer evidence for that replay. A second review file is pending; no human score or acceptance is created here.

## Commands and results

| Command/action | Result |
|---|---|
| `pwd` | exit 0; repository root confirmed |
| `git status --short --branch` | exit 0; dirty branch and preserved work inventoried |
| `git log -5 --oneline --decorate` | exit 0; HEAD equals handoff inspection HEAD |
| `find .. -name AGENTS.md -print` | exit 0; found only unrelated sibling-project AGENTS files |
| Safe Python `Settings()` projection (prints no credential) | exit 0; effective non-secret values recorded above |
| `system_profiler SPHardwareDataType` | exit 0; hardware summary recorded, identifiers omitted |
| `sysctl -n hw.memsize` | denied by environment policy; exit 1 |
| `ollama list` | installed CLI could not connect to `127.0.0.1:11434`; exit 1, operation not permitted |
| Source inspection of route, app startup, settings, gateway, legacy and structured paths | completed; files remained read-only |
| Historical fixture/runner provenance comparison | fixture hash matched; current historical runner hash differs from the digest recorded in the archived run. Neither artifact was edited. |

Initial D01 live generations were unavailable in the ordinary sandbox. After D01, approved read-only local access exposed Ollama and fixed-context dialogue-shadow runs were executed; see the evaluation run ledger. Those runs do not test the versioned structured production request, application startup path, or human quality review. No production database, deployment, or game request was touched.

## Next task

D02 is code-level verified with the user's selected settings. E01's local-only shadow runner, records, snapshots, and forms are implemented; fake CLI execution and selected local model runs are recorded. M01 is screening the user-selected local candidate after authorized download. The real versioned structured production request remains unavailable because the durable runtime policy is incomplete. Do not change production routing based on this diagnosis alone.
