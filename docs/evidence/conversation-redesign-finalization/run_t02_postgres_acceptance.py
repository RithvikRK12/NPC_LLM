"""Run finalization acceptance on a fresh disposable PostgreSQL database."""
import os
from pathlib import Path
import sys
import unittest
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url


def main():
    admin = make_url(os.environ['CONVERSATION_TEST_ADMIN_URL'])
    if (admin.get_backend_name() != 'postgresql' or admin.host != '127.0.0.1'
            or admin.port != 5433 or admin.database != 'postgres'):
        raise SystemExit('Use the designated localhost:5433 postgres maintenance database')
    name = 'npc_test_finalization_t02_' + uuid4().hex[:12]
    engine = create_engine(admin, isolation_level='AUTOCOMMIT')
    created = False
    try:
        with engine.connect() as db:
            print('PostgreSQL version:', db.exec_driver_sql('SHOW server_version').scalar_one(), flush=True)
            db.exec_driver_sql(f'CREATE DATABASE {name}')
            created = True
        test_url = admin.set(database=name)
        isolated = create_engine(test_url)
        try:
            with isolated.begin() as db:
                db.exec_driver_sql('CREATE EXTENSION IF NOT EXISTS vector')
        finally:
            isolated.dispose()
        os.environ['CONVERSATION_TEST_DATABASE_URL'] = test_url.render_as_string(hide_password=False)
        print('Disposable database:', name, flush=True)
        sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'backend' / 'tests'))
        suite = unittest.defaultTestLoader.loadTestsFromName('test_conversation_finalization')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        return 0 if result.wasSuccessful() else 1
    finally:
        if created:
            with engine.connect() as db:
                db.exec_driver_sql(f'DROP DATABASE IF EXISTS {name} WITH (FORCE)')
            print('Dropped disposable database:', name, flush=True)
        engine.dispose()


if __name__ == '__main__':
    sys.exit(main())
