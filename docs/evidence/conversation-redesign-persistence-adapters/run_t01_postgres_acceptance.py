"""Run T01 schema tests in a fresh, uniquely named PostgreSQL database.

Set CONVERSATION_TEST_ADMIN_URL to an administrator connection URL. The
runner only creates and drops an `npc_test_t01_*` database; it never migrates
or deletes data in the administrator database itself.
"""
import os
import sys
import unittest
import uuid
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url


def main() -> int:
    admin_url_text = os.environ.get('CONVERSATION_TEST_ADMIN_URL')
    if not admin_url_text:
        raise SystemExit('Set CONVERSATION_TEST_ADMIN_URL to an administrator PostgreSQL URL')
    admin_url = make_url(admin_url_text)
    if admin_url.get_backend_name() != 'postgresql':
        raise SystemExit('CONVERSATION_TEST_ADMIN_URL must use PostgreSQL')

    database_name = 'npc_test_t01_' + uuid.uuid4().hex[:12]
    admin_engine = create_engine(admin_url, future=True)
    try:
        with admin_engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            version = connection.exec_driver_sql('SELECT current_setting(\'server_version\')').scalar_one()
            connection.exec_driver_sql(f'CREATE DATABASE {database_name}')
        os.environ['CONVERSATION_TEST_DATABASE_URL'] = admin_url.set(database=database_name).render_as_string(hide_password=False)
        print(f'PostgreSQL version: {version}; disposable database prefix: npc_test_t01_')

        sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
        from backend.tests.test_conversation_persistence_schema import ConversationPersistenceSchemaTests
        result = unittest.TextTestRunner(verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(ConversationPersistenceSchemaTests)
        )
        return 0 if result.wasSuccessful() else 1
    finally:
        with admin_engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.exec_driver_sql(f'DROP DATABASE IF EXISTS {database_name} WITH (FORCE)')
        admin_engine.dispose()


if __name__ == '__main__':
    sys.exit(main())
