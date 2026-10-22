import unittest
from measure import classify_origin, safe_url, percentiles


class MeasurementChecks(unittest.TestCase):
    def trace(self, status='succeeded', rejected=False, override=False):
        return {'generation': {'status': status, 'authoritative_override': override},
                'validation': {'rejected': rejected, 'selected_fact_ids': []}}

    def test_origins_are_separate(self):
        self.assertEqual(classify_origin(self.trace(), 'configured'), 'generated')
        self.assertEqual(classify_origin(self.trace(), 'explicit_mock'), 'explicit_mock')
        self.assertEqual(classify_origin(self.trace(rejected=True), 'explicit_mock'), 'explicit_mock_fallback')
        self.assertEqual(classify_origin(self.trace(rejected=True), 'healthy_rejected'), 'healthy_provider_fallback')
        self.assertEqual(classify_origin(self.trace('provider_or_decode_failure', True), 'outage', 'ConnectionError'), 'outage_fallback')
        self.assertEqual(classify_origin(self.trace('bypassed', override=True), 'configured'), 'scripted')

    def test_decode_is_not_outage(self):
        failed = self.trace('provider_or_decode_failure', True)
        self.assertEqual(classify_origin(failed, 'configured'), 'decode_or_unknown_error_fallback')
        self.assertEqual(classify_origin(failed, 'configured', 'HTTPStatusError'), 'provider_error_fallback')

    def test_url_redaction(self):
        self.assertEqual(safe_url('https://user:secret@example.com:123/v1?key=secret#secret'), 'https://example.com:123/v1')

    def test_percentiles_denominator(self):
        self.assertEqual(percentiles([]), {'n': 0, 'p50_seconds': None, 'p95_seconds': None})
        self.assertEqual(percentiles([1, 2, 3])['p95_seconds'], 3)

    def test_isolated_fixture_persists_scope_before_versioned_gatherer_record(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session
        from sqlalchemy.pool import StaticPool
        from app.database.base import Base
        from app.database.seed import seed_world
        from app.models import Player
        from app.services.gatherer import record
        from measure import prepare_fixture_player

        engine = create_engine('sqlite://', poolclass=StaticPool,
                               connect_args={'check_same_thread': False})
        try:
            Base.metadata.create_all(engine)
            with Session(engine) as db:
                seed_world(db)
                player = prepare_fixture_player(db)
                encounter = record(db, player)
                self.assertEqual(player.game_scope, 'baseline-measurement')
                self.assertEqual(encounter.game_scope, 'baseline-measurement')
        finally:
            engine.dispose()

if __name__ == '__main__':
    unittest.main()
