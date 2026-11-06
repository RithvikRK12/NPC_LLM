# proposal implementation tasks

**Goal:** Deliver the `proposal` responsibility in the NPC conversation redesign.
**Status:** T01–T02 locally verified; 2/2 local tasks complete. Provider/coordinator runtime wiring remains downstream.
**Sources:** [Proposal](../npc-conversation-redesign-proposal.md), [Detailed design](../npc-conversation-redesign-detailed-design.md). Relevant sections: Detailed design §§4,6.2; Proposal §16.
**Owned files / integration targets:** backend/app/services/conversation/proposal.py; backend/app/services/prompts/builder.py; backend/app/services/llm/*; backend/tests/test_conversation_proposal.py.
**Architecture:** In-process modules with injected narrow contracts. Mechanical authority remains in existing deterministic game services; conversational narrative never grants gameplay permissions.
**Stack:** Python/FastAPI/Pydantic/SQLAlchemy backend; Godot/GDScript client where applicable.
**Module dependencies:** [baseline](baseline.md), [contracts](contracts.md), [ports](ports.md). Task-level gates below govern sequencing; pure tests may use frozen contract doubles before concrete adapters exist.

## Execution rules

- Assign one task ID to one worker. Read this packet, its cited source sections, [shared rules](../redesign-master-progress.md#shared-implementation-rules), and direct dependency contracts/fixtures; full-system context is needed only for coordinator and release integration.
- File paths below are ownership targets, not claims that files already exist. Coordinate edits to shared existing files with their owning adapter packet. Freeze shared contract fixtures before parallel implementation.
- Each task is a separate reviewable deliverable. First add the named behavioral tests, confirm the expected failure, implement, then run focused checks. Use fakes for pure boundaries; no live provider or player database for deterministic tests.
- A task is complete only when every subtask below and its acceptance/test expectations pass. Record commands, exit codes, evidence paths and any limitations. Change the master module checkbox only after all local tasks and adjacent integration expectations pass.
- Planning completion is not runtime completion. Existing related features/tests are reusable foundations, not checked-off redesign work.

## Task checklist

### proposal/T01: Implement shared prompt and strict proposal decoding

- [x] **Task complete locally** — frozen typed generation boundary honored; prompt/provider adaptation remains T02.

**Depends on:** ports/T01; contracts/T03.
**Acceptance criteria:** ProposalService.propose(context, deadline) makes exactly one call through the frozen `GenerationPort` and validates its typed `TurnProposal` against the supplied context, including T05 cue references. The shared character-data prompt contract is implemented by the generation/provider adapter in proposal/T02, whose tests cover multiple concerns, references, reports, corrections, modalities, interaction links and canon candidates for both NPC profiles. Do not add raw-JSON/provider seams to this domain task.
**Test expectations:** Typed scripted outputs cover mixed emotion/request, direct/quoted/hypothetical/negated/ambiguous intent, unknown IDs, invalid Unicode spans, unsupported commands and extra fields; assert one frozen-port call. Provider prompt parity, malformed JSON, timeout and mock/outage mapping are proposal/T02 checks.

- [x] Add focused failing behavioral tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused checks and adjacent contract/conversation checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

### proposal/T02: Adapt providers and author both NPC profiles

- [x] **Task complete locally** — provider adapter and shared prompt contract are implemented; runtime coordinator wiring remains downstream.

**Depends on:** proposal/T01; baseline/T01.
**Acceptance criteria:** Provider adapter accepts purpose, contract, deadline and response budget; classify timeout/cancellation/unavailable/malformed/version errors separately. Supply lightweight authored Craftsman/Gatherer traits from existing content. Explicit mock reports origin=mock; no silent outage substitution.
**Test expectations:** Scripted transport tests exact call count, deadline and output bounds; shared prompt parity for both NPCs; provider/config diagnostics are accurate and redacted; no new authored identity requirements invented.

- [x] Add focused failing behavioral tests and capture expected failures.
- [x] Implement the bounded deliverable through the owned interface; preserve shared invariants.
- [x] Run focused and adjacent adapter/legacy checks; record evidence.
- [x] Review acceptance criteria and update task/master progress.

## Verification and handoff

Backend deterministic checks use `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py'`; narrow the pattern to the packet test file during development. Preserve and run existing mechanical regression checks at adapter/release gates. Persistence tests must explicitly exercise isolated SQLite and PostgreSQL databases; a skipped PostgreSQL suite does not satisfy acceptance. Client checks use `godot --headless --path frontend/godot --script res://tests/<implemented-conversation-test>.gd` (resolve the installed executable during baseline). Test filenames are proposed targets, not currently runnable implementation claims. Baseline/quality tasks instead record their exact replay/measurement commands and conditions.

| Task | Owner / state | Verification command and evidence | Handoff / blockers |
| --- | --- | --- | --- |
| T01 | proposal_t01 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed and reproduced | [Handoff/red-green evidence](../evidence/conversation-redesign-proposal/t01-handoff.md); focused+adjacent 52/52, conversation 213/213, full backend 676/676; diff check clean | One call through frozen GenerationPort; typed proposal, references, operations and T05 cue spans validated against ContextPacket; raw JSON/provider/shared prompt implementation belongs to T02 |
| T02 | proposal_t02 / locally accepted 2026-10-15; gpt-6.1-sol / high; Main Agent reviewed and reproduced | [Handoff/red-green evidence](../evidence/conversation-redesign-proposal/t02-handoff.md); adapter/proposal/composition/context/interface checks 66/66 pass; broad conversation/backend run currently has two independent SQLite persistence fixture errors | Shared provider prompt and typed adapter; no mock substitution on outage; T01 failure mapping added narrowly; coordinator wiring remains pending |
