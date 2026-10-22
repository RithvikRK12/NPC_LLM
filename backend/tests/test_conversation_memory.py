"""Pure attributed memory planning and retrieval filtering."""
import unittest

from app.services.conversation import contracts as c
from app.services.conversation import memory as module
from app.services.conversation.memory import MemoryPolicy


def source(kind='player_message', source_id='message:1', revision=1, *, scope='run:1', npc=1,
           visibility='npc_private'):
    return c.SourceRef(kind=kind, source_id=source_id, revision=revision, game_scope=scope,
                       npc_id=npc, attribution='player:1', visibility=visibility)


def turn(*, scope='run:1', npc=1, epoch=2, turn_id='turn:1'):
    return c.TurnRef(turn_id=turn_id, request_id='request:1',
                     key=c.ConversationKey(game_scope=scope, npc_id=npc, epoch=epoch), sequence=4)


def proposal(*, report_text='I already delivered the wood', report_id='report:1', source_id='message:1'):
    return c.TurnProposal(
        concerns=(), references=(),
        reports=(c.ReportedStatement(
            statement_id=report_id, attribution='player:1', content=report_text,
            source_spans=(c.TextSpan(text_id=source_id, start=0, end=10),),
        ),),
        correction_candidates=(), operation_candidates=(), interaction_links=(),
        reply=(c.ExpressiveSegment(kind='expressive', segment_id='segment:1', text='I hear you.', addressed_concern_ids=()),),
        canon_candidates=(),
    )


def assembled(*dependencies):
    return c.AssembledReply(
        text_id='final:1', final_text='I hear you.', beats=('I hear you.',), segment_spans={},
        evidence_dependencies=tuple(dependencies), candidate_continuity_changes=(),
    )


def memory(*, memory_id='memory:1', kind='player_report', uncertainty='unverified', status='active',
           scope='run:1', npc=1, epoch=2, sources=None, subject='player:1', content='I delivered wood'):
    return c.MemoryRecord(
        memory_id=memory_id, game_scope=scope, npc_id=npc, epoch=epoch, kind=kind,
        attributed_subject=subject, content=content, uncertainty=uncertainty,
        sources=tuple(sources or (source(),)), status=status, revision=1,
    )


class ConversationMemoryPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = MemoryPolicy()
        self.current_turn = turn()

    def test_player_mechanical_claim_remains_unverified_report_with_source_lineage(self):
        result = self.policy.plan(
            self.current_turn, assembled(source()), proposal(),
        )

        self.assertEqual(len(result.writes), 1)
        record = result.writes[0].record
        self.assertEqual((record.kind, record.uncertainty), ('player_report', 'unverified'))
        self.assertEqual(record.content, 'I already delivered the wood')
        self.assertEqual(record.sources[0], source())
        self.assertEqual(result.writes[0].expected_revision, None)

    def test_unseen_or_unaccepted_draft_report_is_not_persisted(self):
        result = self.policy.plan(self.current_turn, assembled(), proposal())

        self.assertEqual(result.writes, ())

    def test_retrieval_excludes_wrong_scope_epoch_npc_and_superseded_records(self):
        rows = (
            memory(),
            memory(memory_id='memory:old-scope', scope='run:old', sources=(source(scope='run:old'),)),
            memory(memory_id='memory:old-epoch', epoch=1, sources=(source(revision=1),)),
            memory(memory_id='memory:other-npc', npc=2, sources=(source(npc=2),)),
            memory(memory_id='memory:superseded', status='superseded'),
        )

        selected = self.policy.filter_retrieval(rows, self.current_turn.key)

        self.assertEqual(tuple(row.memory_id for row in selected), ('memory:1',))

    def test_retracted_ids_private_sources_and_temporary_interpretations_are_excluded(self):
        rows = (
            memory(),
            memory(memory_id='memory:retracted'),
            memory(memory_id='memory:private', sources=(source(visibility='server_private'),)),
            memory(memory_id='memory:emotion', kind='interpretation', uncertainty='tentative'),
        )

        selected = self.policy.filter_retrieval(
            rows, self.current_turn.key, retracted_ids={'memory:retracted'},
        )

        self.assertEqual(tuple(row.memory_id for row in selected), ('memory:1',))

    def test_current_inventory_source_revision_supersedes_recalled_claim(self):
        stale = memory(
            kind='recollection', uncertainty='tentative', content='The player has wood in inventory.',
            sources=(source('inventory', 'inventory:player:1', 4),),
        )
        current_fact = c.MechanicalFact(
            evidence_id='fact:inventory:wood', kind='mechanical_fact', content='Wood count is zero.',
            sources=(source('inventory', 'inventory:player:1', 5),), created_at='2026-10-15T00:00:00Z',
        )

        selected = self.policy.filter_retrieval((stale,), self.current_turn.key, current_facts=(current_fact,))

        self.assertEqual(selected, ())


class SummaryStoreFake:
    """Contract double only: explicit heads model CAS, not database durability."""
    def __init__(self):
        self.key = turn().key
        self.current_revisions = c.RevisionSet(resources={'turn:turn:1': 0, 'correction:1': 0, 'canon:1': 0})
        self.sources = (c.VisibleTurn(turn=turn(), player_message=c.TextValue(text_id='message:1', text='I delivered wood'),
                                     final_reply=c.TextValue(text_id='final:1', text='I hear you.')),)
        self.prior = None
        self.dirty = {self.key}

    def dirty_keys(self, game_scope):
        return tuple(key for key in self.dirty if key.game_scope == game_scope)

    def read_sources(self, key, source_range):
        return self.sources

    def lookup_summary(self, key):
        return c.OptionalResult.success(self.prior)

    def publish(self, summary, expected_revision):
        if summary.key != self.key:
            return summary_error('STALE_EPOCH')
        try:
            summary.validate_current(self.key, self.current_revisions)
        except ValueError:
            return summary_error('EVIDENCE_CHANGED')
        if expected_revision != (self.prior.revision if self.prior else None):
            return summary_error('EVIDENCE_CHANGED')
        self.prior = summary
        self.dirty.discard(summary.key)
        return summary


def summary_error(code='SUMMARY_FAILED'):
    return c.ConversationError(code=code, stage='summary', retryable=True, safe_detail='Refresh unavailable.')


class MemoryReadFake:
    def __init__(self, records):
        self.records = records

    def read_memories(self, game_scope, npc_id, epoch, visibility):
        return self.records


class SummaryRefreshTests(unittest.TestCase):
    def setUp(self):
        self.store = SummaryStoreFake()
        self.reader = MemoryReadFake((memory().model_copy(update={'revision': 0}),))
        self.source_range = c.SourceRange(first_sequence=4, last_sequence=4)
        self.revisions = self.store.current_revisions
        self.lineage = {'memory:1': None}
        self.deadline = c.Deadline.after(20, clock=lambda: 0.0)

    def service(self, **kwargs):
        self.assertTrue(hasattr(module, 'SummaryService'), 'SummaryService must implement recoverable refresh')
        kwargs.setdefault('lineage', lambda key, records, revisions: module.SummaryLineageSnapshot(
            key=key, records=records, revisions=revisions, correction_links=self.lineage))
        return module.SummaryService(self.store, self.reader, **kwargs)

    def refresh(self, service):
        return service.refresh(self.store.key, self.source_range, self.revisions, self.deadline)

    def test_finalized_sources_publish_detached_attributed_summary(self):
        result = self.refresh(self.service())
        self.assertIsInstance(result, c.SummaryRecord)
        self.assertEqual(result.entries[0].memory.content, 'I delivered wood')
        self.assertEqual(result.entries[0].memory.uncertainty, 'unverified')
        self.assertEqual(result.entries[0].memory.attributed_subject, 'player:1')
        self.assertEqual(result.entries[0].source_turns, (turn(),))
        self.assertIsNot(result.entries[0].memory, self.reader.records[0])
        self.assertEqual(result.source_revisions, self.revisions)
        self.assertEqual(self.store.dirty, set())

    def test_scan_recovers_missed_notification_until_successful_publication(self):
        service = self.service()
        self.assertEqual(service.dirty_keys('run:1'), (self.store.key,))
        self.assertEqual(service.dirty_keys('run:other'), ())
        self.refresh(service)
        self.assertEqual(service.dirty_keys('run:1'), ())

    def test_retracted_superseded_private_and_cross_epoch_memories_not_revived(self):
        self.reader.records = (
            memory().model_copy(update={'revision': 0}),
            memory(memory_id='retired', status='superseded'),
            memory(memory_id='private', sources=(source(visibility='server_private'),)),
            memory(memory_id='old', epoch=1),
        )
        result = self.refresh(self.service())
        self.assertEqual(tuple(entry.memory.memory_id for entry in result.entries), ('memory:1',))
        self.reader.records = (memory(status='superseded'),)
        result = self.refresh(self.service())
        self.assertIsInstance(result, c.ConversationError)
        self.assertEqual(result.code, 'SUMMARY_FAILED')

    def test_stale_canon_and_correction_heads_reject_late_publication(self):
        for changed_head in ('canon:1', 'correction:1'):
            with self.subTest(head=changed_head):
                self.store = SummaryStoreFake()
                def delayed(entries, deadline):
                    self.store.current_revisions = c.RevisionSet(resources={**dict(self.revisions.resources), changed_head: 1})
                    return entries
                result = self.refresh(self.service(summarize=delayed))
                self.assertIsInstance(result, c.ConversationError)
                self.assertEqual(result.code, 'EVIDENCE_CHANGED')
                self.assertIsNone(self.store.prior)
                self.assertIn(self.store.key, self.store.dirty)

    def test_late_summary_after_clear_does_not_publish_old_epoch(self):
        old_key = self.store.key
        def clear_during_summary(entries, deadline):
            self.store.key = old_key.model_copy(update={'epoch': 3})
            return entries
        result = self.service(summarize=clear_during_summary).refresh(
            old_key, self.source_range, self.revisions, self.deadline)
        self.assertEqual(result.code, 'STALE_EPOCH')
        self.assertIsNone(self.store.prior)

    def test_provider_failure_retains_only_valid_prior_and_leaves_work_dirty(self):
        prior = self.refresh(self.service())
        self.store.dirty.add(self.store.key)
        def unavailable(entries, deadline):
            raise RuntimeError('provider is offline')
        result = self.refresh(self.service(summarize=unavailable))
        self.assertEqual(result, prior)
        self.assertIn(self.store.key, self.store.dirty)
        self.reader.records = ()
        result = self.refresh(self.service(summarize=unavailable))
        self.assertIsInstance(result, c.ConversationError)
        self.assertEqual(result.code, 'SUMMARY_FAILED')

    def test_failed_index_is_disposable_after_summary_commit(self):
        def unavailable(summary):
            raise RuntimeError('embedding/index offline')
        result = self.refresh(self.service(index=unavailable))
        self.assertIsInstance(result, c.SummaryRecord)
        self.assertEqual(self.store.prior, result)

    def test_provider_cannot_upgrade_or_replace_current_memory_metadata(self):
        def rewrite(entries, deadline):
            record = entries[0].memory.model_copy(update={'kind': 'recollection', 'uncertainty': 'verified'})
            return (entries[0].model_copy(update={'memory': record}),)
        result = self.refresh(self.service(summarize=rewrite))
        self.assertEqual(result.code, 'SUMMARY_FAILED')
        self.assertIsNone(self.store.prior)

    def test_wrong_source_turn_or_unknown_message_cannot_be_summarized(self):
        self.store.sources = (self.store.sources[0].model_copy(update={'turn': turn(epoch=1)}),)
        result = self.refresh(self.service())
        self.assertEqual(result.code, 'SUMMARY_FAILED')
        self.store.sources = ()
        result = self.refresh(self.service())
        self.assertEqual(result.code, 'SUMMARY_FAILED')

    def test_deadline_expiring_during_provider_does_not_publish(self):
        now = [0.0]
        self.deadline = c.Deadline.after(1, clock=lambda: now[0])
        def late(entries, deadline):
            now[0] = 2.0
            return entries
        result = self.refresh(self.service(summarize=late))
        self.assertEqual(result.code, 'DEADLINE_EXCEEDED')
        self.assertIsNone(self.store.prior)

    def test_revision_zero_linked_replacement_retains_authoritative_correction_lineage(self):
        write = c.MemoryWrite(expected_revision=None, record=self.reader.records[0],
                              correction_link='correction:replacement:1')
        self.reader.records = (write.record,)
        self.lineage = {write.record.memory_id: write.correction_link}
        result = self.refresh(self.service())
        self.assertIsInstance(result, c.SummaryRecord)
        self.assertEqual(result.entries[0].memory.revision, 0)
        self.assertEqual(result.entries[0].correction_link, 'correction:replacement:1')

    def test_current_correction_lookup_preserves_link_for_changed_revision(self):
        self.refresh(self.service())
        self.reader.records = (self.reader.records[0].model_copy(update={'revision': 1, 'content': 'I did not deliver wood'}),)
        self.lineage = {'memory:1': 'correction:accepted:1'}
        result = self.refresh(self.service())
        self.assertEqual(result.entries[0].memory.content, 'I did not deliver wood')
        self.assertEqual(result.entries[0].memory.uncertainty, 'unverified')
        self.assertEqual(result.entries[0].correction_link, 'correction:accepted:1')

    def test_missing_lineage_lookup_cannot_publish_revision_zero_memory(self):
        result = self.refresh(self.service(lineage=None))
        self.assertEqual(result.code, 'SUMMARY_FAILED')
        self.assertIsNone(self.store.prior)
        self.assertIn(self.store.key, self.store.dirty)

    def test_incomplete_or_failed_lineage_lookup_fails_closed_without_prior(self):
        def unavailable(key, records, revisions):
            raise RuntimeError('lineage store unavailable')
        for lookup in (unavailable, lambda *args: summary_error(), lambda *args: {}):
            with self.subTest(lookup=lookup):
                result = self.refresh(self.service(lineage=lookup))
                self.assertEqual(result.code, 'SUMMARY_FAILED')
                self.assertIsNone(self.store.prior)

    def test_lineage_outage_can_retain_only_revision_valid_prior(self):
        prior = self.refresh(self.service())
        self.store.dirty.add(self.store.key)
        result = self.refresh(self.service(lineage=None))
        self.assertEqual(result, prior)
        self.assertIn(self.store.key, self.store.dirty)
        self.revisions = c.RevisionSet(resources={**dict(self.revisions.resources), 'correction:1': 1})
        result = self.refresh(self.service(lineage=None))
        self.assertEqual(result.code, 'SUMMARY_FAILED')

    def test_lineage_metadata_from_different_snapshot_cannot_publish(self):
        for field, value in (
                ('key', turn(epoch=1).key),
                ('records', (self.reader.records[0].model_copy(update={'content': 'different snapshot'}),)),
                ('revisions', c.RevisionSet(resources={'correction:1': 7})),
                ('correction_links', {}),
                ('correction_links', {'memory:1': None, 'unrequested:1': 'correction:other'})):
            with self.subTest(field=field):
                def stale(key, records, revisions):
                    values = dict(key=key, records=records, revisions=revisions, correction_links=self.lineage)
                    values[field] = value
                    return module.SummaryLineageSnapshot(**values)
                result = self.refresh(self.service(lineage=stale))
                self.assertIsInstance(result, c.ConversationError)
                self.assertIsNone(self.store.prior)

    def test_provider_cannot_erase_current_revision_zero_correction_link(self):
        self.lineage = {'memory:1': 'correction:replacement:1'}
        def erase(entries, deadline):
            return (entries[0].model_copy(update={'correction_link': None}),)
        result = self.refresh(self.service(summarize=erase))
        self.assertEqual(result.code, 'SUMMARY_FAILED')
        self.assertIsNone(self.store.prior)


if __name__ == '__main__':
    unittest.main()
