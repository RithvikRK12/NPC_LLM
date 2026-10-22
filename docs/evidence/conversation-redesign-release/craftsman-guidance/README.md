# Accepted Craftsman inspection: close chat and show objective

2026-10-20. Requested flow: once the ship inspection is offered and the player accepts with `yes` or `follow me`, close chat automatically and show `Lead the Craftsman to the boat.` using the island-arrival popup's style and animation.

The client reacts to the accepted activity changing from inactive to active in a current scoped/revisioned server snapshot. A wreck report alone, ordinary conversation, an unrelated yes or a foreign/stale response cannot create this transition. Only the Craftsman's chat is closed; its finalized speech remains in history. Replayed snapshots do not close a later conversation or restart the animation.

The new nonblocking guidance presenter is a second instance of the existing onboarding component. It uses the identical frame, typography, 1.6-second centered hold, 1.1-second smooth shrink/travel, 0.65 dock scale, position and completion checkmark/fade. No art or animation was copied. It does not replay controls or change the initial find-help objective's saved state. Menu pauses and reduced-motion behavior use the same code. Quest/inventory panels obscure it. It completes when the boat encounter begins; an accepted outing restores docked guidance after load without replaying the centered introduction.

## Verification

All four focused Godot scenarios pass (fresh copied logs and `godot-summary.json`):

- `craftsman_guidance_smoke`: report-only and foreign-scope negatives; automatic close; exact popup text; shared presenter; nonblocking input; duplicate delivery; menu pause; docking; 960×540 and 1920×1080 bounds; restoration and completion fade.
- `onboarding_smoke`: the original controls/arrival objective, animation, menu, reload, fresh-run and reduced-motion behavior still pass.
- `craftsman_integration_smoke`: real enabled backend/model, report then **yes**, automatic closure and objective, shared doorway, physical following to boat, inspection, return and reload.
- `craftsman_guidance_follow_smoke`: the same complete physical flow using **follow me**.

The original onboarding fixture was brought up to the existing scope/revision contract: intentional scope replacement, a new revision for changed world data, and `world_loaded=false` to exercise reload rather than background refresh. Early failures are fixture issues encountered during verification, not waived product failures. The final assertions all pass. Native rendering also passes; `center.png` and `docked.png` were visually inspected. The renderer uses a disposable copied project and never the personal save (`run_preview.py`).

No backend or model contract changes were needed. Earlier backend/SQL results remain historical evidence; those suites were not needlessly rerun for this client-only change. The personal game was saved/closed normally and relaunched with its existing save. No reset or transcript rewrite was performed.
