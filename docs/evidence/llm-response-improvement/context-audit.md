# C01/C02 context and capability audit

Date: 2026-10-19 Asia/Kolkata. Scope: read-only source audit plus existing focused tests. No gameplay was added.

## C01 — identity projection

The authored Craftsman JSON already stated in its full authoring contract that relatives' survival is unspecified. The always-included compact `continuity` list instead said only that Father had no established name, present whereabouts, or service. Since `project_profile` emits `core`, `continuity`, and compact `bounds` for greetings and unrelated requests, the survival constraint was absent on those turns.

Updated the compact continuity sentence to explicitly leave survival unspecified. No father status, name, service, disaster, or formative lore was invented. Added a failing projection test covering greeting, mood, father/background, and unrelated rope questions. It also verifies no living/deceased assertion and the 4,200-character ceiling. The test now checks both legacy and structured prompts receive the constraint.

## C02 — practical facts and capabilities

### Supported facts and actions

- `backend/app/services/context/village.json` says the Craftsman makes the bow from wood and string; the Gatherer gathers supplies and can share wood when in stock.
- `backend/app/services/quests/bow.py` implements the bow phases, names wood and string as requirements, directs the player to Gatherer wood and string near the well, and starts/crafts only under existing quest/activity conditions.
- `GameReadAdapter.read_facts` projects current player/NPC inventory quantities, bow phase, and role-specific activity/quest state. It does not publish an inventory-derived generic use for rope.
- `GameReadAdapter.read_capabilities` derives transfer availability from current stock and opening/story gates. The explicit allowlist contains `give_item`, `receive_item`, and the Craftsman's existing inspection outing controls. It exposes no rope-use, pulley, bridge repair, demonstration, training, or generic crafting command.
- Final operations recheck current scope, target, ownership, command parameters, conditions, and exact consent in the owning deterministic services. A visible capability is not consent.

### Claims that remain unknown or unsupported

- The displayed rope may be described as currently stocked only when current inventory evidence supplies it. The game does not define what this rope is useful for.
- The game does not support the Craftsman offering to inspect the player's rope, demonstrate uses, train, fix a bridge, or make an arbitrary tool/shelter from available wood.
- Current stock may support an exact item transfer after the existing request/consent rules; stock does not imply use or a new activity.
- Supported bow material/quest facts may be explained from current phase and exact supplied evidence. No other material recipe or location is implied.

The existing `craftsman-01` mixed rope request and unsupported demonstration offer remain a negative evaluation case. `craftsman-02` wood query remains a contrast for genuinely supported bow requirements versus unsupported generic wood uses. No new projection was justified by this audit.

## Verification

- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_game_adapters.py' -v`: exit 0, 48 tests passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_capabilities.py' -v`: exit 0, 13 tests passed.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_character_profiles.py' -v`: exit 0, 10 tests passed.

These are deterministic contract checks, not proof that a live model will obey the boundary. P01/M02 must score actual local outputs separately.
