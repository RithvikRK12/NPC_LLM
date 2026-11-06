# Repeatable NPC AI demonstration

This demonstrates the existing grounded conversation, fuzzy/FSEC behavior, authoritative transfers and scoped memory retrieval. D3 memory-driven state influence and authored mandatory-refusal recovery remain disabled/deferred. No release-quality threshold has been agreed.

## Live API demonstration

Run from the repository root with the configured local generation and embedding providers available:

```sh
PYTHONPATH=backend .venv/bin/python backend/tests/run_decision_demo.py \
  --output docs/evidence/decision-demo-NEW --attempts 2
```

Always choose a new output directory. The runner creates and deletes its own SQLite world, uses production routes through an in-process HTTP client, and omits production startup hooks. It does not connect to the player's gameplay server or reset saved data. No generation or embeddings are mocked. It reads provider settings without exporting credentials or endpoint URLs.

The 13 saved steps in `backend/tests/decision_demo_scenarios.json` run twice. Initial helpful state and later cautious/distrustful states are explicit controlled fixtures, not changes caused by remembered experience:

1. Ask for the Gatherer's usual location, follow up with “Where can I find him?”, and ask for directions. Location is sourced; missing directions remain explicit.
2. Ask about the unknown Moon Castle. The NPC clarifies instead of inventing lore.
3. Claim “I gave you wood”, then ask what was actually delivered. The claim is remembered with its source/status while current delivery state remains authoritative.
4. Ask for rope and explain its purpose. Inspect cooperation, actual ownership-count evidence and the resulting memory/source IDs.
5. Repeat the rope request. Inventory stays at one transferred rope.
6. Under a controlled cautious state, ask for the owned hammer and inspect clarification; cancel the request.
7. Under a controlled distrustful state, ask for the optional saw and inspect refusal. Required quest cooperation remains protected without authored recovery.
8. Switch to the Gatherer and verify that the Craftsman's retrieved memories do not leak.

For each step, inspect `decision_trace`: context source IDs; memory status/scope and retrieval bounds; the safe proposal projection; validation status; candidate state, fuzzy rule strengths and tendencies; eligible/scored candidates and selection; and durable outcome identity. The trace excludes raw model prose/reasoning, prompts, credentials, arbitrary rejected references and unrelated private NPC state. The ordinary local conversation audit still retains its original raw proposal separately.

The runner writes incremental `evidence.json` and `transcript.md`. The JSON includes per-case expectations, authority checks, trace checks, configuration, installed Ollama model digests when available, implementation/fixture fingerprints, attempts, rejections and measured API latency. Exit status is nonzero if any demonstrated scenario or trace invariant fails. Passing scores are bounded scenario evidence, not a general natural-language truth guarantee.

## Recorded backup

Open the final recorded transcript linked from the E checkpoint in `ai-delivery-plan.md`. It contains the actual player messages, NPC answers and decision traces produced by the API demonstration. It is a saved transcript, not live execution, a Godot playthrough or a screen recording. Present it as recorded evidence if the local provider is unavailable. Do not relabel prior evidence or hide failed attempts.

Fresh [rendered Godot screenshot walkthrough](evidence/godot-decision-rendered-v1/walkthrough.md) is now available for the current application code: 334/334 live-flow checks and 22/22 separate provider-failure checks. It is recorded automated gameplay evidence, not manual play or continuous video. All screenshots were visually inspected. Earlier artifacts remain historical with their original fingerprints and limits.

## Live rendered Godot verification

```sh
PYTHONPATH=backend .venv/bin/python backend/tests/run_godot_grounding.py \
  --godot /private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot \
  --output docs/evidence/godot-decision-NEW --behavior-fixtures --rendered

PYTHONPATH=backend .venv/bin/python backend/tests/run_godot_grounding.py \
  --godot /private/tmp/npc-godot-runtime/Godot.app/Contents/MacOS/Godot \
  --output docs/evidence/godot-decision-failure-NEW --provider-failure --rendered
```

Use new output directories. This runner reserves its own backend listening socket, overrides the database before production startup, imports a temporary copy of the Godot project, drives real controls/HTTP parsing, and deletes its temporary world after capture. Its reset and process restart apply only to that disposable world. `--rendered` opens a native Godot window and saves viewport PNGs; omitting it performs headless checks without screenshot evidence. Failure mode uses an unreachable generation endpoint and is distinct from D2 embedding-outage verification.

The live path includes both NPCs' grounded scenarios, optional refusal/cooperation, wood transfer, string pickup, partial material delivery, timed crafting, exactly one bow, scene relaunch, full backend/Godot restart and reset. Godot checks parse decision identities, recipient/run, eligible/scored FSEC selection and retrieval bounds. The Python capture links each saved decision trace to its durable source and validates memory provenance. Use `decision-traces.json` for shareable implementation evidence; `conversations.json` and full response logs remain separate local audits. No trace UI was added to the game.

## Failure demonstrations and regression

```sh
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_decision_trace.py'
PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests
PYTHONPATH=backend .venv/bin/python backend/tests/run_memory_retrieval_live.py \
  --output docs/evidence/memory-retrieval-NEW.json
git diff --check
```

Decision-trace tests use deterministic generation/embedding fixtures and cover rejected malformed/private proposals, real persisted trace identities, provider-failure zero-effect behavior, accepted legacy label redaction, transfer memory provenance, current-state precedence and unique timed reward receipts. They are not live generation-quality evidence. The D2 runner uses real embedding transport failure, restores the actual endpoint and explicitly reindexes only disposable data; it does not exercise generation.

Before release, agree on the required model/configuration, accepted quality threshold and final presentation format; choose whether a continuous/narrated video is required beyond the recorded screenshot walkthrough. Preserve the two D1 social-generation rejections in the historical results. Story facts and mandatory recovery must come from approved authored content, and D3 needs its own bounded/idempotent integration slice.
