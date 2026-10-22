# contracts/T07 Main Agent acceptance

Date: 2026-10-18 (Asia/Kolkata)
Status: accepted by Main Agent after integration review.

## Delivered boundary

`PendingInteraction.authorized_operation` stores an optional exact direct operation for a single item/activity offer. Legacy records without that field remain readable and fail closed. Interaction and operation policies compare command, arguments, target, modality, and current question while preserving the current answer's candidate identity and source span in consent and `ReadyToRecheck`. Candidate ID and original source spans are not treated as semantic command authority. Action-choice continues to retain inert alternatives and binds only the selected exact option.

The SQL gateway independently loads the stored operation and current question/answer from persistence before effect dispatch. That storage recheck is implemented and tested under persistence-adapters/T03.

## Verification reproduced

- Contract, interaction, operation, persistence, and game-adapter focused tests passed after the answer-provenance correction.
- Full backend: 935/935 passed. [Log](../conversation-redesign-persistence-adapters/t03-logs/backend-final.log)
- PostgreSQL persistence adapter: 47/47 passed on isolated PostgreSQL 16.15. [Log](../conversation-redesign-persistence-adapters/t03-logs/final-postgresql.log)
- `git diff --check` — passed.

No item/activity interaction creation or gameplay rule was added. Consent remains subject to current server preconditions and gateway revalidation.
