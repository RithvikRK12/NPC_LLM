"""Audited game effects for a caller-owned operation transaction.

This is the game participant behind OperationGateway, not that durable port's
implementation. The caller must recover receipts and validate its scope/epoch,
fence and stream position before dispatch. This participant rechecks current
game terms and reloads current consent before calling an effect owner. It
must write the receipt and commit, or roll back all effects on any failure.
This adapter never commits or rolls back the caller transaction, calls a
provider, or owns a Session. Expected denial rolls back only its own savepoint.

Audit: transfers use StateService's existing one-unit ownership/legacy quest
rules and bow.maybe_start's existing material/routine gate. The six Craftsman
commands use apply_command's opening/revision/outing rules and event insertion.
These owners flush only. Gatherer outcomes, physical staging/checkpoints,
inspection completion, pickups, quest start and timed rewards are not eligible.
Their endpoint/transport writers are intentionally not dispatched here.
"""
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Literal, get_args
import json
from types import MappingProxyType
from uuid import NAMESPACE_URL, uuid5

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import NPC, Player, Quest, CraftsmanEncounter, GathererEncounter, BowQuest, ShipRepairQuest
from app.services import craftsman, gatherer
from app.services.conversation.contracts import (
    ActivityResult, CommandId, CommandResult, ItemArguments, NoArguments,
    OperationCandidate, ReadyToRecheck, TransferResult, TurnRef,
    CapabilityDescriptor, ConversationKey, Denied, ItemId, ItemParameterSchema,
    MechanicalFact, NoParameterSchema, PendingInteraction, Precondition, SourceRef,
    TargetReference, TextValue,
)
from app.services.quests.bow import maybe_start, dialogue as bow_dialogue
from app.services.quests.ship_repair import ship_snapshot
from app.services.state.locking import lock_player
from app.services.state.resources import resource_snapshot, revision_labels
from app.services.state.service import StateService
from app.services.validation.models import LLMResponse, StateUpdate


@dataclass(frozen=True, slots=True)
class AuditedCommand:
    command_id: CommandId
    argument_type: type[ItemArguments] | type[NoArguments]
    rule_owner: str
    npc_roles: frozenset[str]


# Explicit allowlist: new HTTP endpoints or additions to CommandId do not
# silently grant conversation execution authority.
AUDITED_COMMANDS = MappingProxyType({
    entry.command_id: entry for entry in (
        AuditedCommand('give_item', ItemArguments, 'app.services.state.service.StateService.apply',
                       frozenset({'craftsman', 'gatherer'})),
        AuditedCommand('receive_item', ItemArguments, 'app.services.state.service.StateService.apply',
                       frozenset({'craftsman', 'gatherer'})),
        AuditedCommand('discuss_bow', NoArguments, 'app.services.quests.bow.dialogue',
                       frozenset({'craftsman'})),
        *(AuditedCommand(command, NoArguments, 'app.services.craftsman.apply_command',
                         frozenset({'craftsman'}))
          for command in ('report_wreck', 'begin_ship_inspection', 'wait', 'resume', 'postpone', 'return')),
    )
})


@dataclass(frozen=True, slots=True)
class GameOperationEffect:
    """Detached effect description, not evidence of a committed receipt.

    Transfers are not idempotent by themselves: the enclosing gateway must
    recover its receipt first. Craftsman also retains its existing command log.
    """
    command_key: str
    result: TransferResult | CommandResult | ActivityResult


def encounter_command_id(turn: TurnRef, operation: OperationCandidate) -> str:
    """Stable encounter identity, independent of proposal/speech retry IDs.

    All TurnRef fields and exact command/arguments/target terms are included.
    Candidate identity, source spans and wording cannot mint a different key.
    """
    if not isinstance(turn, TurnRef) or not isinstance(operation, OperationCandidate):
        raise TypeError('encounter identity requires typed turn and operation')
    turn = TurnRef.model_validate(turn.model_dump(mode='json', warnings='none'))
    operation = OperationCandidate.model_validate(operation.model_dump(mode='json', warnings='none'))
    terms = dict(turn=turn.model_dump(mode='json'), command_id=operation.command_id,
                 arguments=operation.arguments.model_dump(mode='json'),
                 target=operation.target.model_dump(mode='json'))
    canonical = json.dumps(terms, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return str(uuid5(NAMESPACE_URL, 'npc-conversation:game-operation:v1:' + canonical))


@dataclass(frozen=True, slots=True)
class ConsentSnapshot:
    """Loaded by server storage in the caller transaction, never by the model.

    Texts must contain exactly the persisted current question and separately
    admitted answer text identities, and
    expected_answer the exact selected answer text. Operation must come from
    the server-owned current terms, independently of the submitted decision.
    The loader remains behind
    the gateway's authoritative interaction/epoch/fence boundary.
    """
    interaction: PendingInteraction
    operation: OperationCandidate
    texts: Mapping[str, str]
    expected_answer: str

    def __post_init__(self):
        object.__setattr__(self, 'texts', MappingProxyType(dict(self.texts)))


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()


def _load(db, scope, npc_id):
    # Refresh identity-map values: the caller may retain objects from an older
    # read transaction. Read paths never call record()/get_quest() creators.
    def one(model, predicate):
        return db.scalar(select(model).where(predicate).execution_options(populate_existing=True))
    player = one(Player, Player.id == 1)
    if player is None or player.game_scope != scope:
        return None
    npc = one(NPC, NPC.id == npc_id)
    if npc is None:
        return None
    rows = {}
    for model in (CraftsmanEncounter, GathererEncounter, BowQuest, ShipRepairQuest):
        row = one(model, model.player_id == player.id)
        if row is not None and hasattr(row, 'game_scope') and row.game_scope != scope:
            row = None
        rows[model] = row
    return player, npc, rows


def _eligibility(db, player, npc, rows, command):
    entry = AUDITED_COMMANDS[command]
    if player.opening_state != 'complete' or npc.role not in entry.npc_roles or gatherer.chat_blocked(db, player, npc):
        return False
    if entry.argument_type is ItemArguments:
        stock = npc.inventory if command == 'give_item' else player.inventory
        return any(item in get_args(ItemId) for item in (stock or []))
    if command == 'discuss_bow':
        quest = rows[BowQuest]
        return quest is not None and quest.phase == 'meet'
    row = rows[CraftsmanEncounter]
    state = row.state if row else craftsman.defaults()
    return craftsman.conversation_command_available(command, state)


def _descriptor(db, player, npc, rows, command):
    entry = AUDITED_COMMANDS[command]
    target = TargetReference(reference_id=f'npc:{npc.id}', entity_kind='npc', entity_id=str(npc.id))
    available = _eligibility(db, player, npc, rows, command)
    # Resource labels identify proposal dependencies. A changed label causes
    # current deterministic rules to be rechecked; semantic fingerprints, exact
    # ownership and selected terms decide availability, rather than version churn.
    terms = dict(scope=player.game_scope, npc=npc.id, role=npc.role, command=command,
                 opening_complete=player.opening_state == 'complete',
                 story_blocked=gatherer.chat_blocked(db, player, npc), eligible=available)
    fingerprint = _digest(terms)
    labels = revision_labels(db, player)
    dependencies = [('encounter', 'world'), ('encounter', f'npc:{npc.id}'),
                    ('encounter', 'encounter:gatherer')]
    if entry.argument_type is ItemArguments:
        dependencies.extend((('inventory', f'inventory:npc:{npc.id}'),
                             ('inventory', 'inventory:player'), ('quest', 'quest:bow')))
    elif command == 'discuss_bow':
        dependencies.append(('quest', 'quest:bow'))
    else:
        dependencies.append(('activity', 'activity:ship_inspection'))
    checks = tuple(Precondition(precondition_id=f'{command}:{resource}',
        source=SourceRef(kind=kind, source_id=resource, revision=labels[resource],
            game_scope=player.game_scope, npc_id=npc.id,
            attribution='authoritative_game_rules', visibility='public'),
        fingerprint=fingerprint) for kind, resource in dependencies)
    if entry.argument_type is ItemArguments:
        stock = npc.inventory if command == 'give_item' else player.inventory
        allowed = tuple(item for item in get_args(ItemId) if item in (stock or []))
        # Frozen schema requires a nonempty item domain even when unavailable.
        schema = ItemParameterSchema(kind='single_item', allowed_items=allowed or get_args(ItemId))
    else:
        schema = NoParameterSchema(kind='none')
    return CapabilityDescriptor(command_id=command, parameter_schema=schema,
        allowed_target_references=(target,), available=available,
        safe_unavailable_reason=None if available else 'That action is not available right now.',
        relevant_preconditions=checks, supported_speech_acts=('request', 'offer', 'accept', 'question'))


def _same_preconditions(checked, current):
    # Revisions identify the evidence that must be refreshed; they do not make
    # unrelated quantity/version churn a changed consent term by themselves.
    def semantic(value):
        return value.model_copy(update={'source': value.source.model_copy(update={'revision': 0})})
    return (tuple(sorted(map(semantic, checked), key=lambda value: value.precondition_id)) ==
            tuple(sorted(map(semantic, current), key=lambda value: value.precondition_id)))


class GameReadAdapter:
    """Detached, public-only WorldReadPort and CapabilityReadPort projections.

    The existing role, story, inventory, activity and quest owners supply state.
    These descriptions do not authorize effects, create owner records, finish a
    timed quest or expose raw ORM state, private denial reasons or social scores.
    """
    def __init__(self, db: Session) -> None:
        self._db = db

    def read_capabilities(self, game_scope: str, npc_id: int,
                          visibility: Literal['public', 'npc_private']) -> tuple[CapabilityDescriptor, ...]:
        if visibility not in {'public', 'npc_private'}:
            raise ValueError('Unsupported game view visibility')
        player = self._db.get(Player, 1)
        if player is None or player.game_scope != game_scope:
            return ()
        snapshot = resource_snapshot(self._db, game_scope)
        data = _load(self._db, game_scope, npc_id)
        if data is None:
            return ()
        player, npc, rows = data
        return tuple(_descriptor(self._db, player, npc, rows, command) for command in AUDITED_COMMANDS)

    def read_facts(self, game_scope: str, npc_id: int, epoch: int,
                   visibility: Literal['public', 'npc_private']) -> tuple[MechanicalFact, ...]:
        ConversationKey(game_scope=game_scope, npc_id=npc_id, epoch=epoch)
        if visibility not in {'public', 'npc_private'}:
            raise ValueError('Unsupported game view visibility')
        player = self._db.get(Player, 1)
        if player is None or player.game_scope != game_scope:
            return ()
        snapshot = resource_snapshot(self._db, game_scope)
        data = _load(self._db, game_scope, npc_id)
        if data is None:
            return ()
        player, npc, rows = data
        now = datetime.now(timezone.utc)
        values = []
        def add(kind, source_id, value):
            content = json.dumps(value, sort_keys=True, ensure_ascii=False)
            revision = snapshot['state_revisions'][source_id]
            source = SourceRef(kind=kind, source_id=source_id, revision=revision,
                               game_scope=game_scope, npc_id=npc_id,
                               attribution='authoritative_game_rules', visibility='public')
            values.append(MechanicalFact(kind='mechanical_fact', evidence_id=f'game:{npc_id}:{epoch}:{source_id}',
                          content=content, sources=(source,), created_at=now))
        for owner, inventory in (('player', player.inventory), (f'npc:{npc.id}', npc.inventory)):
            add('inventory', f'inventory:{owner}', dict(owner=owner, quantities=dict(Counter(inventory or []))))
        quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id).execution_options(populate_existing=True))
        add('quest', 'quest:legacy', dict(status=quest.status if quest else 'not_started', progress=quest.progress if quest else 0))
        bow = rows[BowQuest]
        add('quest', 'quest:bow', dict(phase=bow.phase if bow else 'available'))
        if npc.role == 'craftsman':
            row = rows[CraftsmanEncounter]
            state = row.state if row else craftsman.defaults()
            activity = {key: state[key] for key in ('outing_active', 'inspection_complete', 'mode', 'wreck_reported', 'offer_pending')}
            if state['inspection_complete']:
                activity['inspection_findings'] = 'Split planking and leaking seams; the hull needs repair.'
            add('activity', 'activity:ship_inspection', activity)
            ship = ship_snapshot(self._db, player)
            add('quest', 'quest:ship_repair', {key: ship[key] for key in ('phase', 'materials', 'availability_note')})
        if npc.role == 'gatherer':
            row = rows[GathererEncounter]
            state = row.state if row else gatherer.defaults()
            add('encounter', 'encounter:gatherer', dict(status=state['status']))
        return tuple(values)


class _TermsChanged(ValueError):
    pass


class GameOperationAdapter:
    """Caller-owned transaction participant with final safe authority checks.

    Expected owner rejections become fixed public Denied values, with any
    attempted effects rolled back to a savepoint. Infrastructure failures still
    propagate for full caller rollback. Scope/epoch/fence and durable receipt
    recovery remain the gateway's responsibility.
    """

    def __init__(self, db: Session, *,
                 consent_loader: Callable[[TurnRef, str], ConsentSnapshot | None] | None = None) -> None:
        self._db = db
        self._consent_loader = consent_loader

    def execute(self, turn: TurnRef, decision: ReadyToRecheck, *,
                expected_encounter_revision: int | None = None) -> GameOperationEffect | Denied:
        if not isinstance(turn, TurnRef) or not isinstance(decision, ReadyToRecheck):
            raise TypeError('game execution requires typed turn and selected operation')
        if not self._db.in_transaction():
            raise ValueError('Game effects require a caller-owned transaction')
        # Materialize SQLite's deferred outer transaction before SAVEPOINT.
        # Releasing a first-statement savepoint would otherwise commit effects.
        lock_player(self._db)
        try:
            # A rule owner may reject after changing tracked values. Roll back
            # its whole attempted effect before returning a normal denial.
            with self._db.begin_nested():
                return self._execute(turn, decision, expected_encounter_revision=expected_encounter_revision)
        except _TermsChanged:
            return Denied(kind='denied', reason_code='TERMS_CHANGED',
                          safe_explanation='The request has changed. Please confirm the current request again.')
        except (ValueError, HTTPException):
            # Never project exception detail, entity data, private scores or SQL.
            return Denied(kind='denied', reason_code='NOT_AVAILABLE',
                          safe_explanation='That action is not available right now.')

    def _execute(
        self, turn: TurnRef, decision: ReadyToRecheck, *,
        expected_encounter_revision: int | None = None,
    ) -> GameOperationEffect:
        if not isinstance(turn, TurnRef) or not isinstance(decision, ReadyToRecheck):
            raise TypeError('game execution requires typed turn and selected operation')
        # Revalidate even typed objects: model_construct/copy are unvalidated
        # escape hatches and are not suitable external decoding boundaries.
        turn = TurnRef.model_validate(turn.model_dump(mode='json', warnings='none'))
        decision = ReadyToRecheck.model_validate(decision.model_dump(mode='json', warnings='none'))
        operation = decision.operation
        entry = AUDITED_COMMANDS.get(operation.command_id)
        if entry is None or type(operation.arguments) is not entry.argument_type:
            raise ValueError('Unsupported conversation command or parameters')
        if not self._db.in_transaction():
            raise ValueError('Game effects require a caller-owned transaction')
        if (expected_encounter_revision is not None and
                (type(expected_encounter_revision) is not int or
                 not 0 <= expected_encounter_revision <= 9007199254740991)):
            raise ValueError('Encounter revision must be an exact nonnegative integer')
        if operation.target != TargetReference(reference_id=f'npc:{turn.key.npc_id}',
                                               entity_kind='npc', entity_id=str(turn.key.npc_id)):
            raise ValueError('Operation target must be the current conversation NPC')

        # Existing shared writer order: Player before NPC. No transaction is
        # opened/closed here; the lock is held through the caller's receipt.
        player = lock_player(self._db)
        if player is None or player.game_scope != turn.key.game_scope:
            raise ValueError('Operation is not in the current game')
        if player.opening_state != 'complete':
            raise ValueError('Finish arriving first')
        npc = self._db.scalar(select(NPC).where(NPC.id == turn.key.npc_id).with_for_update()
                              .execution_options(populate_existing=True))
        if npc is None or npc.role not in entry.npc_roles:
            raise ValueError('This NPC cannot perform that command')
        if gatherer.chat_blocked(self._db, player, npc):
            raise ValueError('Finish the current encounter before talking')
        data = _load(self._db, turn.key.game_scope, turn.key.npc_id)
        if data is None:
            raise _TermsChanged('Current scope or target missing')
        player, npc, rows = data
        current = _descriptor(self._db, player, npc, rows, operation.command_id)
        if not _same_preconditions(decision.checked_preconditions, current.relevant_preconditions):
            raise _TermsChanged('Current game preconditions differ')
        if operation.pending_question_id is not None and decision.consent is None:
            raise _TermsChanged('Pending request requires current consent')
        if decision.consent is not None:
            binding = decision.consent
            snapshot = (self._consent_loader(turn, binding.interaction_id)
                        if self._consent_loader is not None else None)
            if not isinstance(snapshot, ConsentSnapshot) or binding.answering_turn != turn:
                raise _TermsChanged('No current consent')
            try:
                interaction = PendingInteraction.model_validate(snapshot.interaction.model_dump(mode='json'))
                current_operation = OperationCandidate.model_validate(snapshot.operation.model_dump(mode='json'))
                if (current_operation.command_id, current_operation.arguments, current_operation.target, current_operation.pending_question_id, current_operation.modality) != (
                        operation.command_id, operation.arguments, operation.target, operation.pending_question_id, operation.modality):
                    raise ValueError('Current selected operation terms differ')
                if not _same_preconditions(binding.checked_preconditions, current.relevant_preconditions):
                    raise ValueError('Current game preconditions differ')
                if (binding.answer_span.text_id == interaction.question_id or
                        set(snapshot.texts) != {interaction.question_id, binding.answer_span.text_id}):
                    raise ValueError('Answer span must identify the separately admitted current answer')
                binding.validate_against(interaction, snapshot.texts, expected_answer=snapshot.expected_answer)
                question = TextValue(text_id=interaction.question_id, text=snapshot.texts[interaction.question_id])
                interaction.validate_question(binding.question_turn, question)
                if binding.answer_span not in operation.source_spans:
                    raise ValueError('Consent answer is not the selected source')
            except (ValueError, KeyError):
                raise _TermsChanged('Consent terms no longer match') from None
        if isinstance(operation.arguments, ItemArguments):
            source = npc.inventory if operation.command_id == 'give_item' else player.inventory
            if operation.arguments.item not in (source or []):
                raise ValueError('Exact one-unit ownership is required')
        command_key = encounter_command_id(turn, operation)

        if isinstance(operation.arguments, ItemArguments):
            # Constructed exclusively from the audited typed terms. Model prose,
            # biography and state deltas never enter the legacy rule boundary.
            output = LLMResponse(
                intent='transfer', emotion='calm', dialogue='Authoritative item transfer.',
                action=operation.command_id, item=operation.arguments.item,
                reasoning='Gateway-authorized exact typed item terms.', state_update=StateUpdate(),
            )
            quest = self._db.scalar(select(Quest).where(Quest.player_id == player.id).with_for_update())
            StateService(self._db).apply(npc, player, quest, output)
            maybe_start(self._db, player, npc, output)
            result = TransferResult(kind='item_transfer', item=operation.arguments.item, quantity=1,
                                    direction='to_player' if operation.command_id == 'give_item' else 'to_npc')
        elif operation.command_id == 'discuss_bow':
            quest = self._db.get(BowQuest, player.id)
            if quest is None or quest.phase != 'meet':
                raise ValueError('The bow materials discussion is not available')
            output = bow_dialogue(self._db, npc, 'bow', player)
            maybe_start(self._db, player, npc, output)
            result = CommandResult(kind='command', changed=True)
        else:
            row = craftsman.record(self._db, player)
            is_replay = command_key in row.commands
            if (operation.command_id == 'begin_ship_inspection' and not is_replay
                    and not craftsman.conversation_command_available(operation.command_id, row.state)):
                # The owner intentionally no-ops these requests. They cannot
                # produce a receipt claiming a newly accepted activity. Exact
                # replay still recovers its historical acceptance below.
                raise ValueError('No new inspection outing can be accepted')
            revision = row.revision if expected_encounter_revision is None else expected_encounter_revision
            craftsman.apply_command(self._db, player, npc, operation.command_id,
                                    command_key, revision, {})
            if operation.command_id == 'begin_ship_inspection':
                result = ActivityResult(kind='activity', activity_id=command_key, stage='accepted')
            else:
                # The owner returns its saved result before applying any
                # mutation on exact command-key replay.
                result = CommandResult(kind='command', changed=not is_replay)
        self._db.flush()
        return GameOperationEffect(command_key=command_key, result=result)
