# Prompt task packet

Source: Stage 3 and Stage 4 of [`../../llm-response-improvement-plan.md`](../../llm-response-improvement-plan.md).

## P01 — minimal current-turn and recall revision

Dependencies: E01, C01, C02; apply D02 result for structured-path measurements. Freeze baseline prompts/profiles and preserve historical variants.

- [x] Materialize one compact candidate direction covering early substantive answers, attributed recall from visible speech, answering topic switches, evidence-bounded offers, explicit unknowns plus one useful question, grounded current world/biography, and clean bounded endings in [`../candidate-guidance.md`](../candidate-guidance.md). The tested prompt snapshot remains the actual variant under comparison.
- [x] Test evidence delivery at current-turn, recall, identity, and capability seams through the frozen failing exchanges, successful controls, and non-scored artifact spot checks. Human semantic scoring was waived; no rubric scores or pass rates are claimed.
- [x] Complete three validated 24-turn fixed-context controls and three validated 176-turn fixed-context controls with the pinned baseline Llama model at active context 4096. Outputs and metrics are recorded in the run ledger.
- [x] Complete blind human review for practical response, recall, topic switch, offers, endings, and continuity; **waived by the user on 2026-10-20**. No human scores or semantic pass rates are entered. Agent spot checks are documented separately and are not rubric scoring.
- [x] Retain/revise based on observed results and keep neutral or negative outcomes. Retain the current deployed prompt; candidate remains unelected due to unsupported world claims and cutoff signals.

Acceptance: frozen variants and evidence are traceable; no unsupported quality claims. Tests: profile, generation adapter, replay/experiment suites plus live local review when available.

Progress: no new response prompt has been adopted. Llama t04, updated_profiles, and improved_guidance each completed the full 176 turns twice with all six denominators. Cutoff-suspected counts across repetitions were t04 52/67, updated_profiles 108/106, and improved_guidance 82/83. Non-scored artifact spot checks show corrected Gatherer recall but persistent unsupported current-world assertions and cutoffs under improved_guidance. User chose only the existing Llama due to Gemma resource cost. Focused runs and closed-loop smoke outputs remain preserved; the incomplete Gemma full run is excluded. Human reviews are waived; blind forms remain unscored provenance artifacts.
