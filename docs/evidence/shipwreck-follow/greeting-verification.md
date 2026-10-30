# Greeting interpretation — 2026-10-30

Fresh reproduction without retries returned a valid social concern for hello followed by seven concerns copied from context fact text. The evidence for those extra concerns was absent from the actual message, so validation correctly rejected the entire output.

The interpretation request previously contained only a system message with instructions and embedded context. It now includes the current player input as a separate final user message, and explicitly limits classification/evidence to that message. Reference facts remain available. No concerns are silently dropped, no greeting phrase allowlist was added, and retries remain disabled.

Verification:

- Provider request regression failed before the change and passes after it.
- 14 focused tests pass, including no-retry and shipwreck consent regressions.
- Local llama3:willowbrook through POST /chat returns a valid greeting in 10.329 seconds with one interpretation call and one speech call. Interpretation alone took 6.242 seconds. This is one observed run, not a latency guarantee.
- The live wreck report and Yes please regression also passes with retries disabled.
- Both live runs use disposable saves; the personal save was not changed.
- Full unittest discovery: 576 tests; the same 57 failures and 75 errors as before this change. Failure names are listed in no-retries-verification.md.
- git diff --check passes.

See greeting-first-call.json for live results. Close the game normally and relaunch ./Play.command to load the changed backend.
