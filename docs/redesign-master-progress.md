# NPC conversation redesign — master progress

Updated: 2026-10-20 (Asia/Kolkata).

## Overall status

**Ready for local playtesting.** Run [`../Play.command`](../Play.command), or double-click it in Finder. It starts the enabled conversation backend and Godot against the existing save. Closing the game normally saves and stops the backend. See the [play and rollback runbook](conversation-redesign-runbook.md) for controls and settings.

The engineering integration is complete: **1,150 backend tests pass, all eight isolated PostgreSQL runners have passing recorded results (153 test executions), and 21 Godot scenarios have passing recorded results.** The final live screen and configuration are recorded in the [release evidence](evidence/conversation-redesign-release/t03/). These checks cover both NPCs, crafting, purpose-bound stock requests, gifts, encounter progression, persistence, durable retries, recovery, clear/reset and revision-aware UI delivery.

**71/73 task gates are closed or explicitly waived.** T01's human-scoring requirement is waived by the user's previously recorded instruction; T02 passes. T03 remains open for the numerical dialogue-quality and product-latency gate. T04's runbook and receipt-safe rollback tests are complete, but its broad rollout approval depends on T03. Local play does not depend on broad rollout approval. No semantic scores or release acceptance have been invented.

The 21 design modules are integrated and mechanically verified; the table below records that engineering status separately from quality acceptance. The baseline supporting packet is complete; evaluation-release is open. Historical local handoffs and the previous 69/73 tracker are preserved in the [pre-closeout archive](evidence/conversation-redesign-release/t02/master-progress-before-closeout.md).

Sources: [Proposal](npc-conversation-redesign-proposal.md), [Detailed design](npc-conversation-redesign-detailed-design.md), [mechanical handoff](evidence/conversation-redesign-release/t02/handoff.md). Confirmed design decisions still govern: per-NPC queues, no timer/turn negotiation expiry, and clarification before selecting among multiple supported actions.

Proposed follow-up: [FAISS memory retrieval implementation plan](superpowers/plans/2026-10-20-faiss-memory-retrieval.md). The active runtime still lacks the FAISS adapter connection; existing selector/component tests do not establish production semantic retrieval. This integration remains proposed, not completed.

## Module status

The rows describe integration evidence, not an assertion that live language meets the shipping quality thresholds.

| Module | Engineering status |
| --- | --- |
| [contracts](redesign-tasks/contracts.md) | Integrated; pure, API and SQL gates pass |
| [ports](redesign-tasks/ports.md) | Integrated; pure, API and SQL gates pass |
| [turns](redesign-tasks/turns.md) | Integrated; pure, API and SQL gates pass |
| [context](redesign-tasks/context.md) | Integrated; authored profiles and bounded live context pass; semantic quality gate open |
| [capabilities](redesign-tasks/capabilities.md) | Integrated; pure, API and SQL gates pass |
| [proposal](redesign-tasks/proposal.md) | Integrated; pure, API and SQL gates pass |
| [interactions](redesign-tasks/interactions.md) | Integrated; pure, API and SQL gates pass |
| [operations](redesign-tasks/operations.md) | Integrated; pure, API and SQL gates pass |
| [composition](redesign-tasks/composition.md) | Integrated; pure, API and SQL gates pass |
| [validation](redesign-tasks/validation.md) | Integrated; fail-closed authority/receipt checks pass; measured semantic quality gate open |
| [fallback](redesign-tasks/fallback.md) | Integrated; pure, API and SQL gates pass |
| [canon](redesign-tasks/canon.md) | Integrated; pure, API and SQL gates pass |
| [memory](redesign-tasks/memory.md) | Integrated; pure, API and SQL gates pass |
| [finalization](redesign-tasks/finalization.md) | Integrated; pure, API and SQL gates pass |
| [lifecycle](redesign-tasks/lifecycle.md) | Integrated; pure, API and SQL gates pass |
| [diagnostics](redesign-tasks/diagnostics.md) | Integrated; pure, API and SQL gates pass |
| [persistence-adapters](redesign-tasks/persistence-adapters.md) | Integrated; pure, API and SQL gates pass |
| [game-adapters](redesign-tasks/game-adapters.md) | Integrated; pure, API and SQL gates pass |
| [coordinator](redesign-tasks/coordinator.md) | Integrated; pure, API and SQL gates pass |
| [api-adapter](redesign-tasks/api-adapter.md) | Integrated; pure, API and SQL gates pass |
| [godot-adapters](redesign-tasks/godot-adapters.md) | Integrated; 21 recorded Godot scenarios pass; latest full inspection/gratitude flow passes |

## Completed work

- [x] Post-inspection gratitude now uses compact dialogue/current-state context; perspective, copied offers, completed-inspection reoffers and unfinished-repair contradictions are checked. Repair receives the actual findings. [Evidence](evidence/conversation-redesign-release/post-inspection-dialogue/README.md): 1,150 backend tests, six live generated variants, real Llama correction and complete Godot escort/gratitude flow.
- [x] Natural inspection consent such as “Sure! That would be helpful.” now accepts the pending offer and triggers the existing chat-close/escort objective. [Evidence](evidence/conversation-redesign-release/natural-inspection-consent/README.md): 1,144 backend tests and the exact-phrase full Godot escort pass.
- [x] Fixed this Mac’s terminal-launch NPC chat 503 by persisting the existing pilot policy in ignored `backend/.env`; ordinary startup now enables the required conversation runtime. [Evidence](evidence/conversation-redesign-release/chat-service-startup/README.md).
- [x] Gatherer help now shows the shared animated boar objective only after accepting; both dead boars trigger its checkmark immediately. Declining never shows guidance, including the later corpse scene. [Evidence](evidence/conversation-redesign-release/gatherer-guidance/README.md): four fresh Gatherer combat/integration and Craftsman/arrival regression scenarios pass.
- [x] Accepted ship inspection now automatically closes Craftsman chat and shows “Lead the Craftsman to the boat.” through the original arrival objective presenter. [Evidence](evidence/conversation-redesign-release/craftsman-guidance/README.md): four fresh Godot scenarios, both yes/follow-me physical flows, original onboarding, replay safety and native centered/docked visual checks.

- [x] Provider validation contract corrected: speech-only wire for composition/repair/social chat; server-owned provenance and structural IDs; unchanged authority/receipt checks. [Evidence](evidence/conversation-redesign-release/validation-contract/README.md): backend 1,140/1,140; eight PostgreSQL runners; three fresh Godot scenarios; 8/8 sampled ordinary/action replies generated in 1.3–3.2 seconds, with purpose clarification and deliberate outages reported separately. Broad semantic release quality remains open.

- [x] Wreck-disclosure fallback now uses the authored Craftsman reaction instead of internal report-bookkeeping text. Exact-message regression verifies no automatic inspection and consent on the next turn. [Evidence](evidence/conversation-redesign-release/wreck-reaction/README.md); full backend 1,135/1,135.

- [x] Fresh-save greeting correction: undisclosed ship state is excluded from speaker generation, and greetings use a compact typed prompt. [Evidence](evidence/conversation-redesign-release/greeting-knowledge/README.md): five regressions; backend 1,134/1,134; four isolated real-model greetings in 5.3–6.8 seconds. Wider dialogue quality/latency remains unproven.

- [x] All 69 previously accepted implementation/replay tasks remain accepted; packet-level handoffs preserve their evidence.
- [x] evaluation-release/T01: frozen read-only replay and dependency isolation complete; human calibration waived on 2026-10-20. Scores remain unmeasured.
- [x] evaluation-release/T02: full mechanical adoption gate complete. Fresh logs, executable runners and the detailed-design crash/error coverage map are in [T02](evidence/conversation-redesign-release/t02/handoff.md).
- [x] Play launcher, explicit local policy, both NPC profiles, deterministic request/consent adapters and receipt-safe rollback runbook delivered.
- [x] Actual integration defects fixed: final-reply signal wiring, typed revision envelopes, clear sequence continuation, saved-pending startup bootstrap, durable gift path, stock-purpose producer, current-answer choice provenance, Craftsman activity projection, context-overflow completion and queued-work recovery.

## In-progress work

- [ ] evaluation-release/T03: prove the final configuration's relevance ≥90%, mixed-concern coverage ≥90%, canon consistency ≥95%, healthy-provider fallback <5%, accidental repetition <2%, and accepted latency/readability. The small live functionality screen does not establish these proportions. The user waived human review and retained Llama 3; do not request a second reviewer or substitute another model on that basis.
- [ ] evaluation-release/T04: approve broader rollout after T03. Runbook and deterministic rollback/replay checks are delivered; broad rollout remains gated.

## Dependencies and sequencing

Play locally now. Before any wider release, evaluate the final prompt/model/policy against the frozen scenario denominators, record results and product acceptance, then close T03 and approve T04. Historical replays used earlier prompt/settings and cannot certify the final runtime. [Task graph: 73 tasks / 23 packets](evidence/conversation-redesign-schedule/task-graph.json).

## Shared implementation rules


- Domain modules depend on contracts/ports and pure policies, never FastAPI, ORM sessions or concrete provider constructors. Reuse existing immutable values only through explicit semantic adapters; do not assume game_id/timeline_id equals scope/epoch.
- Only deterministic services authorize gameplay. Generated canon is narrative_only; player reports and interpretations retain attribution/uncertainty. Current state and authored constraints override stale memories/generated conflicts.
- Persist turn admission/order before context. Only earliest nonterminal turn per NPC can proceed; different NPCs may generate concurrently. Shared state rechecks serialize through the same writer boundary.
- At most one mutating operation per turn. Multiple supported requests require a choice and do not queue unselected commands. Quoted/hypothetical/negated/ambiguous requests cannot execute. Consent binds exact current question, answer span, terms and preconditions.
- Negotiations never expire by clock or turn count. Relevant precondition failure, explicit cancellation, clear and reset end them. Topic shifts suspend; bare yes cannot select a suspended request.
- One ordinary proposal attempt; action composition may add a call; one repair token shared across proposal-format and final-speech recovery. Persist attempts/repair consumption before dispatch. Summaries are outside the mandatory path.
- No provider, embedding or semantic-check call under DB transaction/lock. Operation effects and receipt commit atomically; final dialogue and accepted continuity commit atomically in a separate transaction. Writer order and fences apply on SQLite and PostgreSQL.
- Receipt recovery precedes execution; HTTP timeout does not discard admitted work. Only durable final dialogue is displayable; delivery retry returns identical final speech. Accepted activity is not completed activity.
- Validate whole assembled replies and fallbacks, including prose around exact slots. Critical quantities/outcomes remain server-rendered. No silent truncation; readable beats partition full dialogue. Semantic checks begin offline and never grant authority.
- Clear advances epoch and removes conversational payloads/drafts/results while preserving generated canon, authored identity and accepted mechanics/receipts; retain minimal invalidation tombstones. New game changes scope and resets run-specific state/canon. Every read/cache/async publish checks scope and applicable epoch/revisions.
- Keep the current 500-character request bound unless separately changed. Policy controls output/context/deadline/queue/lease/summary/retention limits consistently across provider, Pydantic, composer and client. Numeric shipping latency/length and model replacement are not selected by this plan.
- Run deterministic pure tests with fake clock/token counter/provider, adapter tests on isolated SQLite/PostgreSQL, and API/headless Godot lifecycle/retry tests. Mechanical invariants must all pass; live wording is scored, not exact-string asserted.
- Release quality: relevance ≥90%; mixed-concern coverage ≥90%; canon consistency ≥95%; healthy-provider fallback <5%; accidental identical consecutive replies <2% excluding purposeful mechanical repetition. Freeze ≥40 scenarios, generally 4–8 turns, across both NPCs, report counts/model/config and ordinary/action/repair p50/p95. Product acceptance of playable latency/readable limits remains a shipping gate.

## Blockers and risks

- Broad release quality is unproven. Live dialogue may fall back and provider processing may take tens of seconds. A completed mechanical turn is not proof of natural or relevant prose.
- Three Godot fixtures report resources still in use during test shutdown; all functional assertions pass. They are explicitly marked in `godot-summary.json`; teardown cleanup remains a minor follow-up, not a concealed invariant failure.
- Generated canon remains fail-closed without a trusted semantic claim producer. The conservative deterministic request adapter can request clarification for unsupported phrasing.
- A Way Home currently stops at material gathering. Ship repair, sailing and an ending are beyond the conversation redesign, as documented in README.
- Existing user changes and saves were preserved. All acceptance worlds/databases are disposable. The launcher resumes the configured existing save; it does not reset progress.

## Next action

**Play the game with `Play.command`.** T03/T04 are broader release follow-ups, not local launch prerequisites. Record awkward dialogue or blocked interactions with the NPC and exact wording so the next change can address a reproducible case.

## Progress update procedure

Attach fresh evidence before changing a gate. Keep local play readiness, mechanical integration and numerical release-quality acceptance distinct. Never count a waiver as a measured quality pass.
