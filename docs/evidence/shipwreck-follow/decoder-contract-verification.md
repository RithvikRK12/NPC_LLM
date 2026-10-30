# Decoder/validator contract mismatch — 2026-10-30

The latest failed saved input was `yes please`, following an accepted shipwreck report and active inspection offer. It made one interpretation call and no speech call. A fresh raw-model reproduction using a copy of that saved conversation produced operation_request with operation=null, target=null and end=11 for the ten-character input. Local exact-span correction handles the offset; validation then rejects the missing operation as an unsupported capability.

The flat decoder schema previously allowed null operation even on operation_request, null pending-question IDs even on pending_answer, and fields such as purpose on unrelated kinds. Strict application validation rejected combinations that the decoder explicitly permitted.

The decoder now uses typed alternatives: each operation request must select an advertised operation and one of that operation's supported targets; pending answers exist only with a pending question and require its exact ID and an answer type; non-operation kinds cannot produce operation or purpose fields. Application validation, capability membership and authoritative state/consent checks remain intact. No alias guessing or retries were added.

A tiny local-server probe confirmed that both OpenAI-compatible response_format and native format enforce schema enums. The implementation uses the existing OpenAI-compatible endpoint. See [Ollama structured output documentation](https://docs.ollama.com/capabilities/structured-outputs).

Verification:

- Decoder contract regression failed with the old flat schema and passes with typed alternatives.
- 14 focused semantic/HTTP consent tests pass.
- Full POST /chat using separate in-memory copies of the current saved conversation accepts yes please and sure, let's go and starts departure_pending; no thanks does not start the outing. The refusal currently receives a generic clarification, so this does not establish refusal speech quality.
- A fresh disposable-save report/Yes please exchange also passes.
- Every live turn uses one interpretation call. Retries remain disabled. The personal save was not modified.
- Full backend discovery: 579 tests, the same 57 failures and 75 errors as before this change. Failure names are listed in no-retries-verification.md.
- git diff --check passes.

See decoder-contract-live.json. Close the game normally and relaunch ./Play.command to load the changed decoder schema.
