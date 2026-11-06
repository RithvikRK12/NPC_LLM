# api-adapter/T02 handoff

Date: 2026-10-18 (Asia/Kolkata)
Owner: Main Agent

## Deliverable

- Versioned `DELETE /chat/{npc_id}` accepts required `game_scope` and `conversation_epoch` query values, delegates to the lifecycle service, returns the incremented key and explains which conversational/game state remains. Old unversioned clients retain their existing clear route during migration.
- Versioned `POST /world/new-game` accepts a strict `expected_scope`, delegates to the lifecycle service, returns a 409 on stale scope, and includes the replacement scope plus the existing world snapshot fields. Empty-body legacy calls retain the existing reset response.
- `GET /world` now returns the active scope and each NPC's current epoch, revision labels, and terminal/invalidated sequence markers. History is filtered by active scope and epoch. Legacy history without a trustworthy scope/epoch is visible only while that current scope has no redesigned stream; reset clears those legacy rows before scope rotation.

## Test-first and verification evidence

- New route/projection tests initially failed because lifecycle dependency bindings and the projection fields were absent.
- `PYTHONPATH=backend .venv/bin/python -m unittest discover -s backend/tests -p 'test_conversation_api*.py'`: 18/18 pass.
- Conversation suite: 516/516 pass; [log](t02-logs/conversation.log).
- Full backend suite: 984/984 pass; [log](t02-logs/backend.log).
- `git diff --check`: exit 0.
- Lifecycle SQL transaction semantics and facade integration were independently accepted in [lifecycle/T02](../conversation-redesign-lifecycle/t02-handoff.md), with SQLite and PostgreSQL 16.15 22/22 each.

## Scope and remaining work

`api-adapter/T03` still owns coordinator binding and final transport/error behavior. Godot consumption of active epochs and terminal sequences is a separate client task. Unscoped legacy rows cannot prove their historical run identity; they are hidden once a redesigned stream exists and reset removes them during run rotation.
