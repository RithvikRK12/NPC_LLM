# canon/T01 handoff

## Delivered

Implemented `CanonPolicy.plan(reply, active_canon, authored_constraints)` in `backend/app/services/conversation/canon.py`. `CanonReply` pairs the frozen `CandidateReply` with its fresh `AssembledReply`. The policy admits only additions. It resolves each candidate's original support span within its exact expressive source segment, checks that the current assembled `segment_spans` entry reproduces the whole source segment in final speech, translates the source offsets, and requires the candidate's final support span to equal that translated span. Proposed content must occur in the original source claim and exact final span.

Admission also requires injected validation hooks to accept the claim. Injected affordance classification and grounding hooks gate claims implying current shops, caches, recipes or other practical affordances. Active authored identity slots and existing active canon heads win. Generated output always carries `origin=generated` and `authority=narrative_only`; this task does not create world entities. T01 skips revisions, which remain T02's responsibility.

## Acceptance mapping

| Acceptance | Evidence |
| --- | --- |
| Only exact validated final-speech spans can support additions | Focused tests cover absent/stale/mispointed spans, checker rejection, and the repeated-sentence reference attack; span-link detail is in `t01-span-link-review.md`. |
| Generated authority remains narrative-only | `test_admits_only_exact_validated_final_speech_additions_as_narrative`. |
| Authored identity wins and accepted biography is not casually overwritten | `test_authored_identity_wins_and_revisions_are_left_to_t02`; policy also skips existing active canon heads. |
| Draft/failed repair and unsupported claims do not persist | Missing final map, injected failed validation, content mismatch, and unsupported-span cases in `test_conversation_canon.py`. |
| Relatives/historical places remain narrative; practical affordances require grounding | `test_allows_relatives_and_historical_places_but_requires_grounding_for_affordances`. |
| No game entity creation or mechanical authority | Output is only a `CanonChange`; narrative authority is fixed. Semantic and affordance decisions remain injected; the module contains no persistence, provider, or game-service dependency. |

## Verification

Commands ran from the repository root. Full output and exit code are recorded in the adjacent logs.

| Command | Exit | Result |
| --- | ---: | --- |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_canon.py' -v` | 0 | 6/6 focused tests pass; `t01-focused.log`. |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_*.py' -v` | 0 | 113/113 conversation tests pass; `t01-conversation-suite.log`. |
| `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_contract_values.py' -v` | 0 | 13/13 dependency tests pass; `t01-contract-dependencies.log`. |
| `git diff --check -- backend/app/services/conversation/canon.py backend/tests/test_conversation_canon.py docs/evidence/conversation-redesign-canon` | 0 | Whitespace check passes. |

The original test-first RED run occurred before `canon.py` existed and failed to import that module; see `t01-red.log`. The subsequent span-provenance review added the repeated-occurrence regression case and its analysis in `t01-span-link-review.md`.

## Limits and handoff

The injected validator must decide semantic support using the authoritative validation result; the policy's exact substring check is only a provenance guard. Affordance recognition and authoritative grounding are also injected and must be wired by the owning validation boundary. No text heuristic in this module proves a factual claim or grants mechanics permission. The policy expects current, scoped active canon and authored constraints from its caller. No database, provider, or player-state calls were used. Contract files and task/progress/graph packets were not changed.

Files changed for T01: `backend/app/services/conversation/canon.py`, `backend/tests/test_conversation_canon.py`, and `docs/evidence/conversation-redesign-canon/t01-*`.
