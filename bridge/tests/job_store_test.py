# Frugal Flock — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/frugal-flock
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
import concurrent.futures
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


plans = load('plan_store', 'plan_store.py')
sys.modules['plan_store'] = plans
jobs = load('job_store', 'job_store.py')


class JobStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='job-store-')
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        (self.workspace / 'coord').mkdir()
        self.store = jobs.JobStore(self.workspace)
        self.addCleanup(self.store.close)
        self.plans = plans.PlanStore(self.workspace)
        self.addCleanup(self.plans.close)
        self.database = self.workspace / 'coord' / 'ui-jobs.sqlite3'
        self.directory = self.workspace / 'coord/ui-plans'

    def draft(self, request='Do the bounded thing'):
        return self.plans.create(request)

    def count_jobs(self):
        connection = sqlite3.connect(self.database)
        try:
            return connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        finally:
            connection.close()

    def test_queued_job_survives_restart_and_waits_for_owner(self):
        draft = self.draft('Café sweep\n$ literal text, not a command\n- ../../private')
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker-one', 'f' * 32)
        self.assertEqual(set(job), {'id', 'draft_id', 'draft_sha256', 'worker',
                                   'request_key', 'created_at', 'state'})
        self.assertEqual(job['state'], 'awaiting_owner_approval')
        self.assertEqual(job['draft_id'], draft['id'])
        self.assertEqual(job['draft_sha256'], draft['content_sha256'])
        self.assertEqual(job['worker'], 'worker-one')
        self.assertEqual(job['request_key'], 'f' * 32)
        self.assertEqual(len(job['id']), 32)
        self.assertNotEqual(job['id'], draft['id'])
        self.assertIsNotNone(datetime.fromisoformat(job['created_at']).tzinfo)
        json.dumps(job)
        self.store.close()
        with jobs.JobStore(self.workspace) as reopened:
            self.assertEqual(reopened.get(job['id']), job)
            self.assertEqual(reopened.pending(), [job])
            self.assertIsNone(reopened.get('e' * 32))
        self.assertEqual({p.name for p in (self.workspace / 'coord').iterdir()},
                         {'ui-plans', 'ui-jobs.sqlite3'})

    def test_repeated_and_concurrent_same_key_create_one_job(self):
        draft = self.draft()
        inputs = (draft['id'], draft['content_sha256'], 'queue-worker', '0' * 31 + '7')
        first = self.store.enqueue(*inputs)
        self.assertEqual(self.store.enqueue(*inputs), first)
        with jobs.JobStore(self.workspace) as restarted:
            self.assertEqual(restarted.enqueue(*inputs), first)

        def submit(_):
            with jobs.JobStore(self.workspace) as store:
                return store.enqueue(*inputs)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(submit, range(8)))
        self.assertEqual(results, [first] * 8)
        self.assertEqual(self.store.pending(), [first])
        self.assertEqual(self.count_jobs(), 1)

    def test_pending_orders_by_creation_time_then_id(self):
        early_draft = self.draft('First request')
        late_draft = self.draft('Second request')
        tie_b_draft = self.draft('Third request')
        tie_a_draft = self.draft('Fourth request')
        early = self.store.enqueue(early_draft['id'], early_draft['content_sha256'],
                                   'worker', '1' * 32)
        late = self.store.enqueue(late_draft['id'], late_draft['content_sha256'],
                                  'worker', '2' * 32)
        frozen = datetime(2000, 1, 1, tzinfo=timezone.utc)

        class FrozenClock(datetime):
            @classmethod
            def now(cls, tz=None):
                return frozen

        tie_ids = ('b' * 32, 'a' * 32)
        ties = []
        for identity, request_key in zip(tie_ids, ('3' * 32, '4' * 32)):
            fixed = type('FixedUUID', (), {'hex': identity})()
            with patch.object(jobs.uuid, 'uuid4', return_value=fixed), \
                    patch.object(jobs, 'datetime', FrozenClock):
                ties.append(self.store.enqueue(tie_b_draft['id'] if identity == 'b' * 32
                                               else tie_a_draft['id'],
                                               tie_b_draft['content_sha256'] if identity == 'b' * 32
                                               else tie_a_draft['content_sha256'],
                                               'worker', request_key))
        self.assertEqual(ties[0]['created_at'], ties[1]['created_at'])
        self.assertEqual(self.store.pending(), [ties[1], ties[0], early, late])

    def test_conflicting_request_key_reuse_preserves_original(self):
        draft = self.draft('Original request')
        other = self.draft('Competing request')
        original = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker-a', '5' * 32)
        for changed in ((other['id'], other['content_sha256'], 'worker-a'),
                        (draft['id'], other['content_sha256'], 'worker-a'),
                        (draft['id'], draft['content_sha256'], 'worker-b')):
            with self.subTest(changed=changed):
                with self.assertRaises(ValueError):
                    self.store.enqueue(*changed, '5' * 32)
        self.assertEqual(self.store.get(original['id']), original)
        self.assertEqual(self.store.pending(), [original])
        self.assertEqual(self.count_jobs(), 1)

    def test_edited_draft_fails_even_on_identical_replay(self):
        draft = self.draft('Editable request')
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', '6' * 32)
        path = self.directory / (draft['id'] + '.json')
        edited = json.loads(path.read_text())
        edited['request'] = 'Edited after queueing'
        path.write_text(json.dumps(edited, ensure_ascii=True, sort_keys=True,
                                   separators=(',', ':')) + '\n')
        with jobs.JobStore(self.workspace) as store:
            with self.assertRaises(ValueError):
                store.enqueue(draft['id'], draft['content_sha256'], 'worker', '6' * 32)
            with self.assertRaises(ValueError):
                store.enqueue(draft['id'], '0' * 64, 'worker', '7' * 32)
        self.assertEqual(self.store.get(job['id']), job)
        self.assertEqual(self.store.pending(), [job])
        self.assertEqual(self.count_jobs(), 1)

    def test_invalid_inputs_never_select_paths_or_become_sql(self):
        draft = self.draft()
        self.assertIsNone(self.store.get('0' * 32))
        bad_ids = ('../secret', '/tmp/secret', 'a' * 31, 'a' * 33, 'A' * 32, 'g' * 32,
                   'a' * 32 + '.json', '', None, 1, {}, ('a' * 32,))
        bad_hashes = ('../x', '0' * 63, '0' * 65, 'G' * 64, 'zz', '', None, 1, {})
        bad_workers = ('../x', '1worker', 'Worker', 'worker space', 'worker/x',
                       'worker;DROP TABLE jobs', 'w' * 65, '', None, 1, {})
        for value in bad_ids:
            with self.subTest(draft_id=str(value)):
                with self.assertRaises(ValueError):
                    self.store.enqueue(value, draft['content_sha256'], 'worker', '8' * 32)
                with self.assertRaises(ValueError):
                    self.store.get(value)
        for value in bad_hashes:
            with self.subTest(hash=str(value)):
                with self.assertRaises(ValueError):
                    self.store.enqueue(draft['id'], value, 'worker', '8' * 32)
        for value in bad_workers:
            with self.subTest(worker=str(value)):
                with self.assertRaises(ValueError):
                    self.store.enqueue(draft['id'], draft['content_sha256'], value, '8' * 32)
        for value in bad_ids:
            with self.subTest(request_key=str(value)):
                with self.assertRaises(ValueError):
                    self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', value)
        self.assertEqual(self.store.pending(), [])
        self.assertEqual(self.count_jobs(), 0)
        self.assertEqual({p.name for p in self.directory.iterdir()}, {draft['id'] + '.json'})
        self.assertEqual(self.store.enqueue(draft['id'], draft['content_sha256'],
                                           'w' * 64, '9' * 32)['worker'], 'w' * 64)

    def test_unknown_schema_or_corrupt_database_fail_closed(self):
        self.store.close()

        def prepared_workspace(setup):
            workspace = Path(tempfile.mkdtemp(prefix='job-bad-', dir=self.temp.name))
            (workspace / 'coord').mkdir()
            connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
            try:
                setup(connection)
            finally:
                connection.close()
            return workspace

        def foreign(connection):
            connection.execute('CREATE TABLE other (x TEXT)')

        def correct(connection):
            connection.execute(jobs.CREATE_JOBS)
            connection.execute('PRAGMA user_version = 2')

        def unmarked(connection):
            connection.execute(jobs.CREATE_JOBS)

        def reshaped(connection):
            connection.execute(jobs.CREATE_JOBS)
            connection.execute('PRAGMA user_version = 1')
            connection.execute('DROP TABLE jobs')
            connection.execute('CREATE TABLE jobs (id TEXT)')

        for setup in (foreign, correct, unmarked, reshaped):
            with self.subTest(setup=setup.__name__):
                workspace = prepared_workspace(setup)
                path = workspace / 'coord' / 'ui-jobs.sqlite3'
                before = path.read_bytes()
                with self.assertRaises(ValueError):
                    jobs.JobStore(workspace)
                self.assertEqual(path.read_bytes(), before)

    def test_corrupt_records_fail_closed_on_read(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        connection = sqlite3.connect(self.database)
        try:
            connection.execute(jobs.INSERT_JOB,
                               ('c' * 32, 'd' * 32, 'e' * 32, 'f' * 64, 'BAD WORKER',
                                '2026-10-05T00:00:00+00:00', 'dispatched'))
            connection.commit()
        finally:
            connection.close()
        with jobs.JobStore(self.workspace) as store:
            self.assertEqual(store.get(job['id']), job)
            with self.assertRaises(ValueError):
                store.get('c' * 32)
            with self.assertRaises(ValueError):
                store.pending()

    def test_garbage_database_refused_without_reinitializing(self):
        self.store.close()
        self.database.write_bytes(b'this is definitely not a sqlite database')
        before = self.database.read_bytes()
        with self.assertRaises(ValueError):
            jobs.JobStore(self.workspace)
        self.assertEqual(self.database.read_bytes(), before)

    def test_symlink_fifo_or_nonregular_database_and_coordination_refused(self):
        self.store.close()
        database = self.workspace / 'coord' / 'ui-jobs.sqlite3'
        database.unlink()
        os.mkfifo(database)
        with self.assertRaises(ValueError):
            jobs.JobStore(self.workspace)
        database.unlink()
        database.mkdir()
        with self.assertRaises(ValueError):
            jobs.JobStore(self.workspace)
        database.rmdir()
        target = self.workspace / 'outside.sqlite3'
        target.write_text('PRIVATE DATA')
        database.symlink_to(target)
        with self.assertRaises(ValueError):
            jobs.JobStore(self.workspace)
        database.unlink()
        self.assertEqual(target.read_text(), 'PRIVATE DATA')

        outside = self.workspace / 'outside'
        outside.mkdir()
        linked = Path(tempfile.mkdtemp(prefix='job-coord-', dir=self.temp.name))
        (linked / 'coord').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(OSError):
            jobs.JobStore(linked)
        (linked / 'coord').unlink()
        (linked / 'coord').write_text('not a directory')
        with self.assertRaises(OSError):
            jobs.JobStore(linked)
        real = Path(tempfile.mkdtemp(prefix='job-real-', dir=self.temp.name))
        (real / 'coord').mkdir()
        alias = self.workspace / 'linked-workspace'
        alias.symlink_to(real, target_is_directory=True)
        with self.assertRaises(ValueError):
            jobs.JobStore(alias)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertEqual({p.name for p in real.rglob('*')}, {'coord'})
        self.assertEqual(list((real / 'coord').iterdir()), [])

    def test_queue_operations_create_no_native_or_provider_side_effects(self):
        request = 'SECRET-REQUEST-TEXT keep it out of the queue database'
        draft = self.draft(request)
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'b' * 32)
        self.store.get(job['id'])
        self.store.pending()
        raw = self.database.read_bytes()
        self.assertNotIn(b'SECRET-REQUEST-TEXT', raw)
        self.assertNotIn(request.encode(), raw)
        names = {str(p.relative_to(self.workspace)) for p in self.workspace.rglob('*')}
        self.assertEqual(names, {'coord', 'coord/ui-plans',
                                 'coord/ui-plans/' + draft['id'] + '.json',
                                 'coord/ui-jobs.sqlite3'})
        self.assertNotIn('request', job)


if __name__ == '__main__':
    unittest.main(verbosity=2)
