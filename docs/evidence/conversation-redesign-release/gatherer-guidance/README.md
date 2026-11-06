# Gatherer help objective

2026-10-20. Accepting the Gatherer's help choice now shows “Help the Gatherer defeat both boars.” using another instance of the existing arrival objective presenter: identical style, centered hold, shrink/travel to the corner, checkmark drawing and completion fade. It does not block gameplay. The normal pause, overlay obscuring and reduced-motion behavior are shared.

The popup starts only after the gateway confirms acceptance. The accepted combat branch completes it as soon as both boars die, before sending the durable victory command. Killing one boar is insufficient. Refusing help never starts the objective, and the refused branch's staged corpses never complete it. Restarting an attempt clears guidance until the player chooses help again. Reloading thanks does not replay the popup/checkmark; accepted-combat reload retains the existing behavior of resetting the attempt and presenting the choice again.

## Verification

The added integration assertion first failed because the objective presenter did not exist (`before.log`). After implementation, four focused Godot scenarios pass against a disposable copied project, temporary SQLite save and local test backend:

- Gatherer integration: acceptance, no popup before choice or on refusal, dead-boar refusal route, retry, one-boar negative, both-boars checkmark before victory save, failed-save recovery, successful combat, reload and completion.
- Gatherer combat: existing damage/attack behavior.
- Craftsman guidance: the existing objective behavior and layout checks.
- Original onboarding: controls, arrival objective, pause, reload and reduced motion.

Fresh logs and summary are adjacent. Onboarding retains its existing resource-at-exit warning; all assertions passed and the other three scenarios exited without that warning. No backend or model behavior changed. Tests never used the personal save.
