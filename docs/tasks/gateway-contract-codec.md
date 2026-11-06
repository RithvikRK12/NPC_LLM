# gateway.contract_codec

## Scope and contract

`decode_command(payload) -> CommandResult`; validate version, timeline, vocabulary and finite parameters.

Source: [Detailed design](../detailed-design.md), 6.3 Godot modules; [proposal](../proposal.md). The confirmed detailed-design ordering overrides conflicting proposal examples.

**Status:** T01-T04 complete; target module complete. **Owner:** Main Agent. Whole-module completion is tracked in [master-progress](../master-progress.md#module-status).

## Dependencies and sequencing

- **Start:** Common envelope/types from [contracts.core](contracts-core.md). Use frozen fixtures and fake ports; upstream production implementations are not required for T01–T03 unless a task explicitly says otherwise.
- **Integration gate:** [contracts.core](contracts-core.md)
- Execute local task IDs in order; T04 requires T01–T03 and the direct integration dependencies. A dependency means consume its documented output, not edit its implementation.
- Work against dependency fixtures until those outputs are available. Record a blocked task with its exact missing contract/content; do not mark unrelated local work blocked.

## Assignment boundary

Own this module's implementation, module-local DTOs and focused tests. Common envelope changes belong to `contracts.core`; shared repository/schema changes belong to `adapters.persistence`. Do not rename other modules or rewrite the global pipeline as part of this packet. Return changed files, test command/result and any unresolved dependency when handing off one task.

Use fake transport/controller collaborators for unit checks. Real navigation/render checks are separate; headless tests must not wait for render-only events.

## Task checklist

- [x] **T01 — Define the module contract and fixture boundary.**
  - **Acceptance:** Publish the public input/output/error types above, with owned domain fields and shared envelope references. Supply a valid fixture and one rejected fixture; expose no ORM/session or node object in the handoff.
  - **Tests:** Round-trip or construct the valid fixture, reject missing required fields and unsupported variants, and prove input fixtures are not mutated. Decode the shared command fixture in Godot.
  - **Depends on:** Start contracts above. Do not wait for full runtime integration.

- [x] **T02 — Implement the primary behaviour.**
  - **Acceptance:** Decode and validate versioned commands and outcome/display records into typed Godot values without applying gameplay changes.
  - **Tests:** Use the valid T01 fixture and a focused fixture for each successful branch named in this acceptance criterion; assert exact result/state/effect identity rather than generated prose. Use a fixed clock and IDs where relevant.
  - **Depends on:** T01; use immutable upstream result fixtures.

- [x] **T03 — Enforce failures and invariants.**
  - **Acceptance:** Reject old timelines, unknown commands, missing parameters and non-finite values; preserve IDs and backend constraint ranges.
  - **Tests:** Unknown version/action, missing target, old timeline, non-finite values. Assert typed rejection/fallback and absence of unintended effects, not merely that an exception occurred.
  - **Depends on:** T02. Failure injection must remain local to this module and its ports.

- [x] **T04 — Verify adjacent handoff and publish evidence.**
  - **Acceptance:** Consume fixtures produced by each direct dependency and show this module's result satisfies the next documented handoff without changing upstream policy or schema implicitly. Record test evidence and unsupported capabilities.
  - **Tests:** One focused adjacent-module contract check plus the module regression suite; include a mismatched source version/timeline where applicable. Do not run the full game unless this is an engine adapter check.
  - **Depends on:** T01–T03 and the direct Integration gate above. Until those dependencies are ready, record this task as waiting without blocking local unit work.

## Completion rule

Check the whole-module box in master-progress only when every applicable unchecked task above is complete, public contracts and focused tests pass, the adjacent integration gate is satisfied, and evidence is recorded below. Existing baseline B01 is not permission to check the whole module.

## Execution record

- Assigned task/owner: Main Agent completed T01-T04 on 2026-10-12.
- Current task state: complete.
- Test evidence for new work:
  - `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_gateway_contract_codec.py'` — 14 tests passed on 2026-10-12.
  - `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests` — 361 tests passed on 2026-10-12.
  - `/opt/homebrew/bin/godot --headless --path frontend/godot --script res://tests/gateway_contract_codec_smoke.gd` — fixture smoke passed on 2026-10-12; Godot emitted local log/certificate warnings but exited 0 and printed the pass message.
- Implemented files: `backend/app/gateway/contract_codec.py`, `backend/app/gateway/__init__.py`, `backend/tests/test_gateway_contract_codec.py`, `backend/tests/fixtures/gateway/contract-codec-t01-valid.json`, `backend/tests/fixtures/gateway/contract-codec-t01-rejected.json`, `frontend/godot/tests/gateway_contract_codec_smoke.gd`.
- Unsupported capabilities recorded: this module decodes and validates transport payloads only; it does not apply gameplay changes, schedule controller work, perform HTTP handling or grant outcome authority.
- Adjacent handoff: focused tests prove decoded `CommandResult` values satisfy a `controllers.lifecycle` input boundary and reject mismatched timeline evidence.
- Blocker: none.
