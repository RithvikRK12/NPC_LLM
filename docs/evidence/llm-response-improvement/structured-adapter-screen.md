# Local structured proposal adapter screen

Date: 2026-10-19 Asia/Kolkata. This was a direct single-stage invocation of the production `StructuredGenerationAdapter` against a frozen `t05-valid.json` context fixture and the local Ollama OpenAI-compatible endpoint. It did not call the conversation application, durable stores, game state, or an enabled production route. The durable runtime is not configured/enabled in current local settings.

Both calls used the selected bounds (2,048 max generation tokens, 16,384 serialized JSON characters, and a 600-codepoint dialogue ceiling), JSON Schema structured output, and a 120-second monotonic deadline. No API key was supplied; endpoint was loopback only.

| Model | Full digest | Result | Detail |
|---|---|---|---|
| `llama3:latest` Q4_0 | `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1` | Typed `TurnProposal` accepted | Serialized output 288 characters; zero reply segments. A full proposal validator/composition pipeline could still reject or require repair. |
| `gemma3:12b-it-q4_K_M` Q4_K_M | `b92b218582c521ba287f38f1d6057dcd3c6cbff036f13cac97b5d861f5e58ec3` | `GenerationMalformed` | Provider returned JSON, but strict Pydantic validation rejected it because a span text reference did not exist. No mock fallback occurred. |

The Llama check exited 0. The Gemma check exited 1 with the expected categorized validation failure. An initial harness invocation exited 1 because it omitted the required deadline clock; that was a harness setup error and was corrected before both recorded calls.

## Follow-up: reply-less proposal regression

On 2026-10-20, the current checkout was inspected after the Llama result above was flagged. Its `TurnProposal.reply` field already has `min_length=1`, the generated JSON Schema contains `minItems: 1`, and `StructuredGenerationAdapter` strictly validates provider JSON before returning. This conflicts with the earlier Llama observation; the exact source/runtime revision used for that call is not recoverable from its screen record. The current source was reproduced with the production array-to-tuple conversion and rejects `reply: []` as `GenerationMalformed`.

A regression test now covers the adapter boundary and asserts the emitted schema minimum. A proposal-service test also constructs a reply-less typed model via `model_copy`; its strict round-trip validation returns `PROVIDER_INVALID_OUTPUT`. Focused adapter/proposal/coordinator/composition-service tests passed 68/68. Adjacent contract/application/fallback/validation tests passed 74/74.

The original inability to call Ollama was caused by the restricted command sandbox, not a stopped local service. The normal sandbox command `ollama ps` was denied access to loopback, while the same read-only query succeeded through the approved elevated local command route. Using that route, one fresh direct proposal call through `StructuredGenerationAdapter` with `llama3:latest` returned `TurnProposal` with 1 reply segment; diagnostics reported generated origin, structured output, 2,048 token limit, and 16,384 JSON-character limit. The command exited 0. Follow-up `ollama ps` showed only Llama loaded, 5.0 GB, 100% GPU, context 4096. An initial harness attempt exited 1 because it omitted the required deadline clock; it made no request and was corrected. The original zero-segment screen result remains preserved as historical evidence. The enabled durable application path remains separately unavailable under current settings.

## Proposal, composition, and repair repeat screen

To make the stage check reproducible, [`screen_structured_stages.py`](screen_structured_stages.py) verifies the installed Llama digest/quantization, provider version, and active 4096 context, then sends one request for each adapter purpose using only the frozen fixture context. It writes summary metadata and categorized outcomes without storing generated prose or touching application/game/database state.

| Screen record | Proposal | Composition | Repair | Process result |
|---|---|---|---|---:|
| `runs/llama3-structured-stages-screen-r1.json` | `GenerationMalformed` | `CandidateReply`, 1 segment | `CandidateReply`, 1 segment | exit 1 |
| `runs/llama3-structured-stages-screen-r2.json` | `TurnProposal`, 1 segment | `CandidateReply`, 1 segment | `CandidateReply`, 1 segment | exit 0 |
| `runs/llama3-structured-stages-screen-r3.json` | `TurnProposal`, 1 segment | `CandidateReply`, 1 segment | `CandidateReply`, 1 segment | exit 0 |

All records pin `llama3:latest`, digest `365c0bd3c000a25d28ddbf732fe1c6add414de7275464c4e4d1c3b5fcb5d8ad1`, Q4_0, Ollama 0.34.2, 2,048 tokens, 16,384 JSON characters, and 600 dialogue code points. Each observed 5,003,804,671 resident bytes and context 4096. A separate one-off proposal call before this three-stage screen also returned one segment. The isolated sample therefore shows a malformed proposal in one of three repeat calls; strict validation remains fail-closed. Composition and repair were typed in all three calls. This is a schema-stage compatibility screen, not an end-to-end production turn.

This confirms the adapter's actual local parsing/typed-validation behavior for one proposal per model. It does not establish complete durable production-path readiness, composition/repair compatibility, acceptance behavior, or a model quality winner. Do not enable deployment based on these calls.

## Receipt-aware composition follow-up

On 2026-10-20, an isolated local screen was extended through `CompositionService.compose` with a detached committed-receipt fixture. The screen revealed that model-authored `ReplySource` policy provenance can be stale even when the segment schema is valid. The adapter now stamps source origin, turn ID, schema version, and policy versions from the current trusted request context after strict candidate validation. This does not relax validation of reply segments or canon candidates.

The receipt-aware service also now appends one deterministic `ReceiptSlot` from the already-verified `OperationReceipt` when the model omits it. Existing model-supplied slots must still match the exact receipt ID, outcome, and renderer; duplicates and mismatches fail closed. Prompt contract version v5 directs the model to provide only optional grounded prose while the server owns the committed outcome slot. This preserves deterministic receipt rendering and prevents the model from upgrading acceptance to progress/completion.

The current local Llama r8 screen (`runs/llama3-structured-stages-screen-r8.json`) did not reach normalization: its receipt-composition generation was rejected as `GenerationMalformed` because an addition canon candidate carried revision lineage. The proposal stage also failed an unknown-concern reference; direct composition and repair returned typed one-segment candidates. This remains an observed strict-contract failure, not a passing live receipt-path result. The preceding r7 attempt hit the same malformed canon error before the harness captured evidence; the harness now records stage exceptions. Focused deterministic receipt tests pass for server insertion, exact outcome rendering, duplicate rejection, wrong IDs/outcomes, and activity safety.

The direct local screen is still isolated from the application, durable stores, and game state. It does not establish enabled full-route readiness.
