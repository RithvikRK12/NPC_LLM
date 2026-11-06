"""Bounded in-memory reference fake for the five T02 write/recovery protocols.

The fake stages deterministic scripted receipts/final results and applies the
protocol's scoped uniqueness, fencing, CAS and invalidation expectations.
``scenario_*`` methods are test-harness controls, never production APIs. There
are no game rules, providers, databases, SQL isolation or real crash simulation.
"""
import hashlib
from datetime import datetime, timedelta, timezone

from app.services.conversation.contracts import (
    CanonRecord, ClearResult, ConversationError, ConversationKey, FinalTurnResult,
    OperationReceipt, OptionalResult, ReadyToRecheck, RecoveredReply, RevisionSet, TurnLease,
    TextValue, TurnRecovery, TurnRef, TurnStatus, TurnSubmission, VisibleTurn, WorldResult,
)


def _identity(key, request_id):
    return key.game_scope, key.npc_id, key.epoch, request_id


def _error(code, stage, turn=None):
    return ConversationError(code=code, stage=stage, retryable=code in {
        'LEASE_LOST', 'STORAGE_UNAVAILABLE'}, turn=turn, safe_detail=code)


class FakeConversationRepository:
    def __init__(self, state=None):
        self._state = state if state is not None else {
            'scope': 'run:1', 'epochs': {1: 0, 2: 0}, 'next_sequence': {},
            'turns': {}, 'identities': {}, 'receipts': {}, 'outcomes': {},
            'effects': 0, 'fail_receipt': False,
            'clock': datetime(2026, 10, 14, tzinfo=timezone.utc),
            'canon': {}, 'memories': {}, 'interactions': {}, 'transcripts': {},
            'publications': {}, 'summaries': {}, 'dirty': set(), 'revisions': {},
            'fail_publication': False,
            'next_scope': 1,
        }

    def _key_error(self, key, stage, turn=None):
        if key.game_scope != self._state['scope']:
            return _error('STALE_SCOPE', stage, turn)
        if key.npc_id not in self._state['epochs']:
            return _error('UNKNOWN_NPC', stage, turn)
        if key.epoch != self._state['epochs'][key.npc_id]:
            return _error('STALE_EPOCH', stage, turn)
        return None

    def submit(self, submission: TurnSubmission) -> TurnStatus | ConversationError:
        identity = _identity(submission.key, submission.request_id)
        digest = hashlib.sha256(submission.model_dump_json().encode('utf-8')).hexdigest()
        existing_id = self._state['identities'].get(identity)
        if existing_id is not None:
            row = self._state['turns'][existing_id]
            if row['digest'] != digest:
                return _error('IDEMPOTENCY_CONFLICT', 'admission', row['status'].turn)
            return row['status']
        error = self._key_error(submission.key, 'admission')
        if error is not None:
            return error
        stream = (submission.key.game_scope, submission.key.npc_id, submission.key.epoch)
        sequence = self._state['next_sequence'].get(stream, 1)
        turn = TurnRef(turn_id=f'turn:{len(self._state["turns"]) + 1}',
                       request_id=submission.request_id, key=submission.key, sequence=sequence)
        status = TurnStatus(turn=turn, phase='queued')
        self._state['turns'][turn.turn_id] = {
            'digest': digest, 'submission': submission, 'status': status,
            'fence': 0, 'lease_active': False,
        }
        self._state['identities'][identity] = turn.turn_id
        self._state['next_sequence'][stream] = sequence + 1
        return status

    def lookup(self, key: ConversationKey, request_id: str) -> TurnStatus | ConversationError:
        turn_id = self._state['identities'].get(_identity(key, request_id))
        if turn_id is not None:
            return self._state['turns'][turn_id]['status']
        error = self._key_error(key, 'lookup')
        return error if error is not None else _error('INVALID_INPUT', 'lookup')

    def _write_row(self, turn, fence=None):
        row = self._state['turns'].get(turn.turn_id)
        if row is None or row['status'].turn != turn:
            return _error('INVALID_INPUT', 'operation', turn)
        if row['status'].phase == 'invalidated':
            return _error('TURN_INVALIDATED', 'operation', turn)
        error = self._key_error(turn.key, 'operation', turn)
        if error is not None:
            return error
        pending = [candidate['status'].turn for candidate in self._state['turns'].values()
                   if candidate['status'].turn.key == turn.key and
                   candidate['status'].phase not in {'finalized', 'invalidated'}]
        if not pending or min(pending, key=lambda value: value.sequence) != turn:
            return _error('LEASE_LOST', 'operation', turn)
        if fence is not None and (not row['lease_active'] or row['fence'] != fence or
                ('lease' in row and self._state['clock'] >= row['lease'].expires_at)):
            return _error('LEASE_LOST', 'operation', turn)
        return row

    def claim_next(self, key, worker_id, lease_policy):
        error = self._key_error(key, 'claim')
        if error is not None:
            return OptionalResult.failure(error)
        rows = [row for row in self._state['turns'].values()
                if row['status'].turn.key == key and row['status'].phase not in {'finalized', 'invalidated'}]
        if not rows:
            return OptionalResult.success(None)
        row = min(rows, key=lambda value: value['status'].turn.sequence)
        if row['lease_active'] and self._state['clock'] < row['lease'].expires_at:
            return OptionalResult.success(None)
        row['fence'] += 1
        row['lease_active'] = True
        if row['status'].phase == 'queued':
            row['status'] = TurnStatus(turn=row['status'].turn, phase='preparing')
        row['lease'] = TurnLease(turn=row['status'].turn,worker_id=worker_id,fence=row['fence'],
            phase=row['status'].phase,claimed_at=self._state['clock'],
            expires_at=self._state['clock'] + timedelta(seconds=lease_policy.lease_duration_seconds))
        return OptionalResult.success(row['lease'])

    def pending(self, key):
        error = self._key_error(key, 'pending')
        if error is not None:
            return error
        return tuple(sorted((row['status'] for row in self._state['turns'].values()
            if row['status'].turn.key == key and row['status'].phase not in {'finalized','invalidated'}),
            key=lambda value:value.turn.sequence))

    def _read_row(self, turn, stage):
        if turn.key.game_scope != self._state['scope']:
            return _error('STALE_SCOPE', stage, turn)
        row = self._state['turns'].get(turn.turn_id)
        if row is None or row['status'].turn != turn:
            return _error('INVALID_INPUT', stage, turn)
        return row

    def recover(self, turn):
        row = self._read_row(turn, 'recovery')
        if isinstance(row, ConversationError):
            return row
        if row['fence'] == 0:
            return _error('LEASE_LOST', 'recovery', turn)
        return TurnRecovery(status=row['status'],fence=row['fence'],submission=row.get('submission'),
            attempts=tuple(row.get('attempts', {}).values()),receipt=self._state['receipts'].get(turn.turn_id),
            assembled_reply=row.get('assembled_reply'))

    def lookup_receipt(self, turn):
        row = self._read_row(turn, 'receipt_lookup')
        if isinstance(row, ConversationError):
            return OptionalResult.failure(row)
        return OptionalResult.success(self._state['receipts'].get(turn.turn_id))

    @staticmethod
    def _same_dispatch(left, right):
        return (left.turn,left.attempt_id,left.fence,left.purpose,left.repair_kind,left.dispatched_at) == (
            right.turn,right.attempt_id,right.fence,right.purpose,right.repair_kind,right.dispatched_at)

    def record_attempt(self, turn, fence, attempt):
        row = self._write_row(turn, fence)
        if isinstance(row, ConversationError):
            return row
        if attempt.turn != turn or attempt.fence != fence or attempt.status != 'dispatched':
            return _error('INVALID_INPUT', 'attempt', turn)
        attempts = row.setdefault('attempts', {})
        existing = attempts.get(attempt.attempt_id)
        if existing is not None:
            return existing if self._same_dispatch(existing,attempt) else _error('IDEMPOTENCY_CONFLICT','attempt',turn)
        if any(value.purpose == attempt.purpose for value in attempts.values()):
            return _error('INVALID_BOUNDS', 'attempt', turn)
        attempts[attempt.attempt_id] = attempt
        return attempt

    def save_attempt_output(self, turn, fence, attempt):
        row = self._write_row(turn, fence)
        if isinstance(row, ConversationError):
            return row
        if attempt.turn != turn or attempt.fence != fence or attempt.status != 'output_persisted':
            return _error('INVALID_INPUT', 'attempt_output', turn)
        existing = row.get('attempts', {}).get(attempt.attempt_id)
        if existing is None:
            return _error('INVALID_INPUT', 'attempt_output', turn)
        if not self._same_dispatch(existing, attempt):
            return _error('IDEMPOTENCY_CONFLICT', 'attempt_output', turn)
        if existing.status == 'output_persisted':
            return existing if existing == attempt else _error('IDEMPOTENCY_CONFLICT','attempt_output',turn)
        row['attempts'][attempt.attempt_id] = attempt
        if attempt.purpose == 'proposal' or attempt.repair_kind == 'proposal_format':
            if row['status'].phase == 'preparing':
                row['status'] = TurnStatus(turn=turn,phase='proposed')
        return attempt

    def save_reply(self, turn, fence, reply):
        row = self._write_row(turn, fence)
        if isinstance(row, ConversationError):
            return row
        recovered = RecoveredReply(turn=turn,fence=fence,reply=reply)
        row['assembled_reply'] = recovered
        return recovered

    def execute_once(
        self, turn: TurnRef, fence: int, decision: ReadyToRecheck,
    ) -> OperationReceipt | ConversationError:
        row = self._write_row(turn, fence)
        if isinstance(row, ConversationError):
            return row
        existing = self._state['receipts'].get(turn.turn_id)
        if existing is not None:
            return existing
        receipt = self._state['outcomes'].get(turn.turn_id)
        if receipt is None:
            return _error('OPERATION_UNAVAILABLE', 'operation', turn)
        try:
            receipt.verify_operation(decision.operation)
        except ValueError:
            return _error('IDEMPOTENCY_CONFLICT', 'operation', turn)
        # Stage all values before the fault point. No effect/phase is visible
        # when receipt persistence fails; real adapters must prove this in SQL.
        next_effects = self._state['effects'] + (receipt.outcome != 'rejected')
        next_status = TurnStatus(turn=turn, phase='operation_resolved')
        if self._state['fail_receipt']:
            self._state['fail_receipt'] = False
            return _error('STORAGE_UNAVAILABLE', 'operation', turn)
        self._state['effects'] = next_effects
        self._state['receipts'][turn.turn_id] = receipt
        row['status'] = next_status
        return receipt

    def scenario_claim(self, turn, worker_id):
        """Fake-only ordering/fence control; not TurnStore.claim_next."""
        row = self._write_row(turn)
        if isinstance(row, ConversationError):
            return row
        if row['lease_active']:
            return _error('LEASE_LOST', 'claim', turn)
        row['fence'] += 1
        row['lease_active'] = True
        row['worker'] = worker_id
        row['lease'] = TurnLease(turn=turn,worker_id=worker_id,fence=row['fence'],
            phase='preparing' if row['status'].phase == 'queued' else row['status'].phase,
            claimed_at=self._state['clock'], expires_at=self._state['clock'] + timedelta(seconds=20))
        if row['status'].phase == 'queued':
            row['status'] = TurnStatus(turn=turn, phase='preparing')
        return row['fence']

    def scenario_expire_lease(self, turn):
        self._state['turns'][turn.turn_id]['lease_active'] = False

    def scenario_seed_outcome(self, turn, receipt):
        if (receipt.turn_id, receipt.game_scope, receipt.npc_id) != (
                turn.turn_id, turn.key.game_scope, turn.key.npc_id):
            raise ValueError('scripted receipt must belong to the exact scoped turn')
        self._state['outcomes'][turn.turn_id] = receipt

    def scenario_fail_next_receipt(self):
        self._state['fail_receipt'] = True

    def scenario_clear(self, key):
        """Fake-only tombstone control; not LifecycleStore.clear."""
        error = self._key_error(key, 'clear')
        if error is not None:
            raise ValueError(error.code)
        self.clear(key)

    def clear(self, key):
        error = self._key_error(key, 'clear')
        if error is not None:
            return error
        self._state['epochs'][key.npc_id] += 1
        for row in self._state['turns'].values():
            turn = row['status'].turn
            if turn.key == key:
                row['status'] = TurnStatus(turn=turn, phase='invalidated')
                row.pop('submission', None)
                row.pop('worker', None)
                row.pop('lease', None)
                row['lease_active'] = False
                self._state['outcomes'].pop(turn.turn_id, None)
                self._state['publications'].pop(turn.turn_id, None)
                self._state['transcripts'].pop(turn.turn_id, None)
                row.pop('attempts', None)
                row.pop('assembled_reply', None)
        self._state['memories'] = {identity:value for identity,value in self._state['memories'].items()
                                  if (value.game_scope,value.npc_id,value.epoch) != (key.game_scope,key.npc_id,key.epoch)}
        self._state['interactions'] = {identity:value for identity,value in self._state['interactions'].items()
                                      if value.key != key}
        self._state['summaries'].pop(key, None)
        self._state['dirty'].discard(key)
        self._state['revisions'].pop(key, None)
        return ClearResult(outcome='cleared',previous_key=key,
                           current_key=ConversationKey(game_scope=key.game_scope,npc_id=key.npc_id,epoch=key.epoch+1))

    def new_game(self, expected_scope):
        if expected_scope != self._state['scope']:
            return _error('STALE_SCOPE', 'new_game')
        for npc_id, epoch in tuple(self._state['epochs'].items()):
            self.clear(ConversationKey(game_scope=expected_scope,npc_id=npc_id,epoch=epoch))
        # Scope IDs are opaque. The deterministic fake allocator never parses
        # the expected scope or equates it with legacy game/timeline identity.
        self._state['scope'] = f'fake-run:{self._state["next_scope"]}'
        self._state['next_scope'] += 1
        self._state['epochs'] = {npc_id:0 for npc_id in self._state['epochs']}
        self._state['canon'] = {}
        self._state['effects'] = 0
        return WorldResult(outcome='reset',previous_scope=expected_scope,game_scope=self._state['scope'],
                           state_projection={},state_revisions=RevisionSet(resources={}))

    def commit(self, turn, fence, reply, continuity_plan):
        row = self._state['turns'].get(turn.turn_id)
        if row is not None and row['status'].turn == turn and row['status'].phase == 'finalized':
            error = self._key_error(turn.key, 'publication', turn)
            return error if error is not None else row['status'].response
        row = self._write_row(turn, fence)
        if isinstance(row, ConversationError):
            return row
        if continuity_plan.turn != turn:
            return _error('INVALID_INPUT', 'publication', turn)
        try:
            continuity_plan.validate_reply(reply)
            continuity_plan.validate_revisions(self._state['revisions'].get(turn.key, RevisionSet(resources={})))
            continuity_plan.interaction_plan.validate_current({value.interaction_id:value
                for value in self._state['interactions'].values() if value.key == turn.key})
            continuity_plan.memory_plan.validate_current({value.memory_id:value.revision
                for value in self._state['memories'].values()
                if (value.game_scope,value.npc_id,value.epoch)==(turn.key.game_scope,turn.key.npc_id,turn.key.epoch)})
        except ValueError:
            return _error('EVIDENCE_CHANGED', 'publication', turn)
        canon = dict(self._state['canon'])
        for change in continuity_plan.canon_changes:
            identity = turn.key.game_scope, turn.key.npc_id, change.canon_id
            current = canon.get(identity)
            if ((change.kind == 'add' and (current is not None or change.expected_revision != 0)) or
                    (change.kind == 'revise' and (current is None or current.revision != change.expected_revision))):
                return _error('EVIDENCE_CHANGED', 'publication', turn)
            canon[identity] = CanonRecord(canon_id=change.canon_id,
                revision=0 if current is None else current.revision+1,game_scope=turn.key.game_scope,
                npc_id=turn.key.npc_id,subject=change.subject,predicate=change.predicate,content=change.content,
                category=change.category,origin=change.origin,authority=change.authority,status='active',
                supersedes_revision=None if current is None else current.revision,introduced_turn_id=turn.turn_id,
                accepted_claim_evidence=change.supporting_span)
        memories = dict(self._state['memories'])
        for write in continuity_plan.memory_plan.writes:
            memories[(turn.key,write.record.memory_id)] = write.record
        interactions = dict(self._state['interactions'])
        for transition in continuity_plan.interaction_plan.transitions:
            interactions[(turn.key,transition.replacement.interaction_id)] = transition.replacement
        result = self._state['publications'].get(turn.turn_id)
        if (result is None or result.turn != turn or result.final_dialogue != reply.final_text or
                result.dialogue_beats != reply.beats):
            return _error('INVALID_INPUT', 'publication', turn)
        receipt = self._state['receipts'].get(turn.turn_id)
        if result.receipt_refs != ((receipt.receipt_id,) if receipt is not None else ()):
            return _error('INVALID_INPUT', 'publication', turn)
        next_status = TurnStatus(turn=turn,phase='finalized',response=result)
        if self._state['fail_publication']:
            self._state['fail_publication'] = False
            return _error('STORAGE_UNAVAILABLE', 'publication', turn)
        self._state.update(canon=canon,memories=memories,interactions=interactions)
        self._state['transcripts'][turn.turn_id] = reply.final_text
        row['status'] = next_status
        self._state['dirty'].add(turn.key)
        return result

    def dirty_keys(self, game_scope):
        if game_scope != self._state['scope']:
            return _error('STALE_SCOPE', 'summary')
        return tuple(sorted((key for key in self._state['dirty'] if key.game_scope==game_scope),
                            key=lambda key:(key.npc_id,key.epoch)))

    def read_sources(self, key, source_range):
        error = self._key_error(key, 'summary')
        if error is not None:
            return error
        rows = (row for row in self._state['turns'].values() if row['status'].turn.key == key and
                row['status'].phase == 'finalized' and
                source_range.first_sequence <= row['status'].turn.sequence <= source_range.last_sequence)
        return tuple(VisibleTurn(turn=row['status'].turn,
            player_message=TextValue(text_id=f'message:{row["status"].turn.turn_id}',text=row['submission'].player_message),
            final_reply=TextValue(text_id=f'final:{row["status"].turn.turn_id}',text=row['status'].response.final_dialogue)) for row in
            sorted(rows,key=lambda row:row['status'].turn.sequence))

    def lookup_summary(self, key):
        error = self._key_error(key, 'summary')
        if error is not None:
            return OptionalResult.failure(error)
        return OptionalResult.success(self._state['summaries'].get(key))

    def publish(self, summary, expected_revision):
        error = self._key_error(summary.key, 'summary')
        if error is not None:
            return error
        current = self._state['summaries'].get(summary.key)
        if ((current is None) != (expected_revision is None) or
                (current is not None and (current.revision != expected_revision or current.summary_id != summary.summary_id)) or
                summary.revision != (0 if expected_revision is None else expected_revision+1)):
            return _error('EVIDENCE_CHANGED', 'summary')
        try:
            summary.validate_current(summary.key,self._state['revisions'].get(summary.key,RevisionSet(resources={})))
        except ValueError:
            return _error('EVIDENCE_CHANGED', 'summary')
        for entry in summary.entries:
            for turn in entry.source_turns:
                row = self._state['turns'].get(turn.turn_id)
                if row is None or row['status'].turn != turn or row['status'].phase != 'finalized':
                    return _error('EVIDENCE_CHANGED', 'summary')
        self._state['summaries'][summary.key] = summary
        self._state['dirty'].discard(summary.key)
        return summary

    def scenario_restart(self):
        """New adapter instance sharing already recorded fake state."""
        return FakeConversationRepository(self._state)

    def scenario_effect_count(self):
        return self._state['effects']

    def scenario_has_payload(self, turn):
        row = self._state['turns'][turn.turn_id]
        return 'submission' in row or turn.turn_id in self._state['outcomes']

    def scenario_receipt(self, turn):
        """Fake-only historical audit read; not a scoped recovery port."""
        return self._state['receipts'].get(turn.turn_id)

    def scenario_advance_seconds(self, seconds):
        self._state['clock'] += timedelta(seconds=seconds)

    def scenario_set_revisions(self, key, revisions):
        self._state['revisions'][key] = revisions
        self._state['dirty'].add(key)

    def scenario_seed_publication(self, turn, result):
        self._state['publications'][turn.turn_id] = result

    def scenario_fail_next_publication(self):
        self._state['fail_publication'] = True

    def scenario_transcript(self, turn):
        return self._state['transcripts'].get(turn.turn_id)

    def scenario_canon_count(self):
        return len(self._state['canon'])

    def scenario_memory_count(self):
        return len(self._state['memories'])

    def scenario_memory(self, memory_id):
        return next(value for value in self._state['memories'].values() if value.memory_id == memory_id)

    def scenario_seed_canon(self, turn, change):
        self._state['canon'][(turn.key.game_scope,turn.key.npc_id,change.canon_id)] = CanonRecord(
            canon_id=change.canon_id,revision=0,game_scope=turn.key.game_scope,npc_id=turn.key.npc_id,
            subject=change.subject,predicate=change.predicate,content=change.content,category=change.category,
            origin='generated',authority='narrative_only',status='active',supersedes_revision=None,
            introduced_turn_id=turn.turn_id,accepted_claim_evidence=change.supporting_span)

    def scenario_seed_interaction(self, interaction):
        self._state['interactions'][(interaction.key,interaction.interaction_id)] = interaction

    def scenario_interaction_status(self, interaction_id):
        return next(value.status for value in self._state['interactions'].values()
                    if value.interaction_id==interaction_id)
