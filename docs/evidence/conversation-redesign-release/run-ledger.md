# Local play closeout decisions — 2026-10-20

- Scope: finish practical integration and launch the local game. No shared deployment, publication or original-save reset.
- Preserve the existing Llama 3 preference and human-review waiver recorded in `docs/llm-response-improvement/runbook.md`. Do not request reviewer 2 or claim unmeasured scores.
- Use `llama3:willowbrook`, an 8192-context alias of installed Llama 3 weights; no replacement model. `config/playtest.env` holds all explicit pilot bounds. Alias creation reuses local weights.
- Pure/SQL/API/Godot mechanical gates pass. The final backend count is 1,129; PostgreSQL has 153 overlapping executions; Godot has 16 functional scenarios. See T02 handoff and logs.
- Preserve red logs and earlier live screens. A schema-capable provider receives the schema through response_format; the prompt does not duplicate it. Strict decode and deterministic authorization are retained.
- Three fixture-only shutdown resource warnings remain documented. No gameplay invariant failure is waived.
- T01 closes with explicit scoring waiver; T02 closes with mechanical evidence. T03 numerical quality/latency remains open. T04 runbook/rollback tests are implemented but broad rollout approval remains dependent on T03. Count 71/73 formally closed or waived tasks, rather than checking unproven release gates.
- Local play can proceed through `Play.command`. The launcher resumes the configured existing save and stops only the backend it starts. Do not use clear/reset to roll back receipts.

Actual launcher/UI verification completed: village loaded from the existing save, with the final game left open. Saved pending requests now allow initial world context and retain the usual background refresh guard; focused Godot regression passes. Final live screen: 3/4 ordinary generated, 1/4 fallback, 3/3 actions receipted with server-rendered fallback narration, 2/2 intentional outages correctly classified. No broad quality acceptance.
