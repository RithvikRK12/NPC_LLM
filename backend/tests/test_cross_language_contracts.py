"""Python side of the shared corpus; Godot reader is an independent C03 check."""
from pathlib import Path
import unittest

from backend.tests.contract_fixture_reader import CommandFixture, decode_fixture, read_fixture

FIXTURES = Path(__file__).resolve().parents[2].parent / "contracts" / "fixtures" / "v1"


class SharedFixtureTests(unittest.TestCase):
    def test_all_valid_shared_fixtures_decode_and_round_trip(self):
        paths = sorted(FIXTURES.glob("valid-*.json"))
        self.assertGreaterEqual(len(paths), 4)
        for path in paths:
            with self.subTest(fixture=path.name):
                value = read_fixture(path)
                self.assertEqual(value, decode_fixture(value.model_dump_json()))
                self.assertEqual(value, CommandFixture.model_validate_json(value.model_dump_json()))

    def test_all_invalid_shared_fixtures_are_rejected(self):
        paths = sorted(FIXTURES.glob("invalid-*.json"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            with self.subTest(fixture=path.name):
                with self.assertRaises(ValueError):
                    read_fixture(path)

    def test_version_failure_is_predictable(self):
        with self.assertRaisesRegex(ValueError, "schema_version"):
            read_fixture(FIXTURES / "invalid-incompatible-version.json")

    def test_json_extension_constants_and_duplicate_fields_are_rejected(self):
        for payload in ('{"envelope": NaN}', '{"envelope": Infinity}', '{"envelope":{},"envelope":{}}'):
            with self.assertRaises(ValueError):
                decode_fixture(payload)


if __name__ == "__main__":
    unittest.main()
