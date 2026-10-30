# Stronger emotional changes — 2026-10-30

At the user's request, meaningful social reactions are now ten times stronger than the initial policy. This supersedes the .05 cap and small numeric changes recorded in verification.md/live.json; those remain historical test evidence.

| Interpreted conduct | Trust | Fear | Aggression | Curiosity |
| --- | ---: | ---: | ---: | ---: |
| Conciliatory | +.20 | -.10 | -.20 | +.10 |
| Antagonistic | -.30 | 0 | +.30 | -.10 |
| Intimidating | -.30 | +.30 | +.20 | -.10 |
| Engaging | 0 | 0 | 0 | +.20 |
| Neutral | 0 | 0 | 0 | 0 |

Combined per-turn changes are capped at ±.40 per dimension, with final saved values clamped to [0,1]. The server-owned reaction policy is applied after role conditioning so legacy caps on model-proposed aggression deltas do not blunt these changes. Role action restrictions remain intact. Input meaning still comes from the existing LLM intent call; no added model calls, retries or phrase matching.

Verification: updated persistence, per-turn cap and aggression-cap regressions failed before the change and pass afterward. Twelve focused feedback/tone/editor/context tests pass. A Gatherer starting at trust .10 and aggression .90 reaches .30/.70 after conciliatory conduct; a Gatherer at aggression .30 reaches .60 after antagonistic conduct. Neutral and quoted-conduct exclusions remain tested. Full discovery: 591 tests, unchanged 57 failures and 75 errors, no new failure names; the existing list is in verification.md. git diff --check passes.

Restart ./Play.command to load the stronger policy. The player's real save was not altered by the tests.
