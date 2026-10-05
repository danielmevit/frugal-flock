# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
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
import threading
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
        self.assertEqual(set(job), {'id', 'draft_id', 'draft_sha256', 'worker', 'request_key', 'created_at', 'state',
                                   'approval_key', 'approved_at', 'reservation_key', 'reserved_at', 'unknown_at', 'cancelled_at'})
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
        self.assertEqual(self.store.jobs(), [first])
        self.assertEqual(self.count_jobs(), 1)

    def test_concurrent_first_open_on_new_workspace_initializes_once(self):
        workspace = Path(tempfile.mkdtemp(prefix='job-open-race-', dir=self.temp.name))
        (workspace / 'coord').mkdir()
        barrier = threading.Barrier(8)

        def open_store(_):
            barrier.wait()
            with jobs.JobStore(workspace) as store:
                return (store._db.execute('PRAGMA user_version').fetchone()[0],
                        store.jobs())

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(open_store, range(8)))
        self.assertEqual(results, [(2, [])] * 8)
        connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
        try:
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            count = connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        finally:
            connection.close()
        self.assertEqual((version, count), (2, 0))

    def test_interrupted_or_bare_database_files_initialize_to_schema_one(self):
        self.store.close()

        def zero_byte(path):
            path.write_bytes(b'')

        def bare_sqlite(path):
            connection = sqlite3.connect(path)
            try:
                connection.execute('CREATE TABLE ghost (x TEXT)')
                connection.execute('DROP TABLE ghost')
                connection.commit()
            finally:
                connection.close()

        for setup in (zero_byte, bare_sqlite):
            with self.subTest(setup=setup.__name__):
                workspace = Path(tempfile.mkdtemp(prefix='job-bare-', dir=self.temp.name))
                (workspace / 'coord').mkdir()
                setup(workspace / 'coord' / 'ui-jobs.sqlite3')
                with jobs.JobStore(workspace) as store:
                    self.assertEqual(store.jobs(), [])
                connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
                try:
                    version = connection.execute('PRAGMA user_version').fetchone()[0]
                    columns = tuple(row[1] for row
                                    in connection.execute('PRAGMA table_info(jobs)'))
                    count = connection.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
                finally:
                    connection.close()
                self.assertEqual(version, 2)
                self.assertEqual(columns, jobs.COLUMNS)
                self.assertEqual(count, 0)

    def test_concurrent_enqueue_of_same_new_key_creates_exactly_one_job(self):
        draft = self.draft()
        inputs = (draft['id'], draft['content_sha256'], 'race-worker', 'c' * 32)
        barrier = threading.Barrier(8)

        def submit(_):
            with jobs.JobStore(self.workspace) as store:
                barrier.wait()
                return store.enqueue(*inputs)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(submit, range(8)))
        self.assertEqual(results, [results[0]] * 8)
        self.assertEqual(self.store.jobs(), [results[0]])
        self.assertEqual(self.count_jobs(), 1)

    def test_failed_commit_rolls_back_and_store_stays_usable(self):
        draft = self.draft()
        real = self.store._db

        class FlakyCommitProxy:
            failed = False

            def execute(self, sql, *parameters):
                if not self.failed and sql == 'COMMIT':
                    self.failed = True
                    raise sqlite3.OperationalError('simulated COMMIT failure')
                return real.execute(sql, *parameters)

        self.store._db = FlakyCommitProxy()
        try:
            with self.assertRaises(sqlite3.OperationalError):
                self.store.enqueue(draft['id'], draft['content_sha256'],
                                   'worker', 'd' * 32)
        finally:
            self.store._db = real
        self.assertEqual(self.count_jobs(), 0)
        self.assertEqual(self.store.jobs(), [])
        job = self.store.enqueue(draft['id'], draft['content_sha256'],
                                 'worker', 'd' * 32)
        self.assertEqual(self.store.get(job['id']), job)
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
        self.assertEqual(self.store.jobs(), [ties[1], ties[0], early, late])

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
        self.assertEqual(self.store.jobs(), [original])
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
        self.assertEqual(self.store.jobs(), [job])
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
        self.assertEqual(self.store.jobs(), [])
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
            connection.execute('PRAGMA user_version = 3')

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
                store.jobs()

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
        self.store.jobs()
        raw = self.database.read_bytes()
        self.assertNotIn(b'SECRET-REQUEST-TEXT', raw)
        self.assertNotIn(request.encode(), raw)
        names = {str(p.relative_to(self.workspace)) for p in self.workspace.rglob('*')}
        self.assertEqual(names, {'coord', 'coord/ui-plans',
                                 'coord/ui-plans/' + draft['id'] + '.json',
                                 'coord/ui-jobs.sqlite3'})
        self.assertNotIn('request', job)



    def test_approve_validates_inputs_and_updates_state(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approval_key = 'b' * 32

        # Test approval updates state
        approved = self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)
        self.assertEqual(approved['state'], 'approved')
        self.assertEqual(approved['approval_key'], approval_key)
        self.assertIsNotNone(datetime.fromisoformat(approved['approved_at']).tzinfo)

        # Get should return the same
        self.assertEqual(self.store.get(job['id']), approved)

        # Pending should not return it
        self.assertEqual(self.store.pending(), [])

        # Jobs should return it
        self.assertEqual(self.store.jobs(), [approved])

    def test_approve_replay_and_conflict(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approval_key = 'b' * 32

        approved = self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)

        # Identical replay returns same
        replayed = self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)
        self.assertEqual(approved, replayed)

        # Conflicting key fails
        with self.assertRaises(ValueError):
            self.store.approve(job['id'], draft['content_sha256'], 'worker', 'c' * 32)

        # Incorrect inputs fail
        with self.assertRaises(ValueError):
            self.store.approve(job['id'], draft['content_sha256'], 'other-worker', approval_key)

    def test_reserve_validates_and_updates_state(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approval_key = 'b' * 32
        reservation_key = 'c' * 32

        # Must be approved first
        with self.assertRaises(ValueError):
            self.store.reserve(job['id'], approval_key, reservation_key)

        self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)

        res = self.store.reserve(job['id'], approval_key, reservation_key)
        self.assertTrue(res['newly_reserved'])
        reserved = res['job']
        self.assertEqual(reserved['state'], 'reserved')
        self.assertEqual(reserved['reservation_key'], reservation_key)
        self.assertIsNotNone(datetime.fromisoformat(reserved['reserved_at']).tzinfo)

    def test_reserve_replay_and_conflict(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approval_key = 'b' * 32
        reservation_key = 'c' * 32

        self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)
        self.store.reserve(job['id'], approval_key, reservation_key)

        # Identical replay returns newly_reserved=False
        res = self.store.reserve(job['id'], approval_key, reservation_key)
        self.assertFalse(res['newly_reserved'])

        # Conflicting key fails
        with self.assertRaises(ValueError):
            self.store.reserve(job['id'], approval_key, 'd' * 32)

        # Wrong approval key fails
        with self.assertRaises(ValueError):
            self.store.reserve(job['id'], 'e' * 32, reservation_key)

    def test_mark_unknown_and_replay(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approval_key = 'b' * 32
        reservation_key = 'c' * 32

        self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)

        # Cannot mark unknown if not reserved
        with self.assertRaises(ValueError):
            self.store.mark_unknown(job['id'], reservation_key)

        self.store.reserve(job['id'], approval_key, reservation_key)

        # Mark unknown
        unknown = self.store.mark_unknown(job['id'], reservation_key)
        self.assertEqual(unknown['state'], 'completion_unknown')
        self.assertIsNotNone(datetime.fromisoformat(unknown['unknown_at']).tzinfo)

        # Replay is idempotent
        replayed = self.store.mark_unknown(job['id'], reservation_key)
        self.assertEqual(unknown, replayed)

    def test_cancel_allowed_states(self):
        draft = self.draft()
        job1 = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', '1' * 32)
        job2 = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', '2' * 32)
        job3 = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', '3' * 32)

        # Cancel waiting
        c1 = self.store.cancel(job1['id'])
        self.assertEqual(c1['state'], 'cancelled')
        self.assertIsNotNone(datetime.fromisoformat(c1['cancelled_at']).tzinfo)

        # Cancel approved
        self.store.approve(job2['id'], draft['content_sha256'], 'worker', 'a' * 32)
        c2 = self.store.cancel(job2['id'])
        self.assertEqual(c2['state'], 'cancelled')
        self.assertEqual(c2['approval_key'], 'a' * 32)

        # Cannot cancel reserved
        self.store.approve(job3['id'], draft['content_sha256'], 'worker', 'b' * 32)
        self.store.reserve(job3['id'], 'b' * 32, 'c' * 32)
        with self.assertRaises(ValueError):
            self.store.cancel(job3['id'])

        # Replay of cancelled is idempotent
        c1_replay = self.store.cancel(job1['id'])
        self.assertEqual(c1, c1_replay)

    def test_stale_draft_refused_on_approve_and_reserve(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approval_key = 'b' * 32

        path = self.directory / (draft['id'] + '.json')
        edited = json.loads(path.read_text())
        edited['request'] = 'Edited after queueing'
        path.write_text(json.dumps(edited, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n')

        with self.assertRaises(ValueError):
            self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)

        # Restore draft to approve it
        edited['request'] = 'Do the bounded thing'
        path.write_text(json.dumps(edited, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n')
        self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)

        # Edit again, reserve should fail
        edited['request'] = 'Edited after approval'
        path.write_text(json.dumps(edited, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n')
        with self.assertRaises(ValueError):
            self.store.reserve(job['id'], approval_key, 'c' * 32)

    def test_schema_2_migration_preserves_records(self):
        self.store.close()
        # Setup schema 1 database
        workspace = Path(tempfile.mkdtemp(prefix='job-mig-', dir=self.temp.name))
        (workspace / 'coord').mkdir()
        connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
        connection.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY, request_key TEXT NOT NULL UNIQUE, draft_id TEXT NOT NULL, draft_sha256 TEXT NOT NULL, worker TEXT NOT NULL, created_at TEXT NOT NULL, state TEXT NOT NULL)")
        connection.execute("PRAGMA user_version = 1")
        connection.execute("INSERT INTO jobs (id, request_key, draft_id, draft_sha256, worker, created_at, state) VALUES (?, ?, ?, ?, ?, ?, ?)",
                           ('1' * 32, '2' * 32, '3' * 32, '4' * 64, 'worker-mig', '2026-10-05T00:00:00+00:00', 'awaiting_owner_approval'))
        connection.commit()
        connection.close()

        with jobs.JobStore(workspace) as store:
            job = store.get('1' * 32)
            self.assertEqual(job['id'], '1' * 32)
            self.assertEqual(job['request_key'], '2' * 32)
            self.assertEqual(job['state'], 'awaiting_owner_approval')
            self.assertEqual(job['approval_key'], None)

        # Verify schema is upgraded
        connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        self.assertEqual(version, 2)
        connection.close()

    def test_concurrent_reserve_serializes_and_returns_newly_reserved_once(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approval_key = 'b' * 32
        reservation_key = 'c' * 32

        self.store.approve(job['id'], draft['content_sha256'], 'worker', approval_key)
        barrier = threading.Barrier(8)

        def submit(_):
            with jobs.JobStore(self.workspace) as store:
                barrier.wait()
                return store.reserve(job['id'], approval_key, reservation_key)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(submit, range(8)))

        newly_reserved_counts = sum(1 for r in results if r['newly_reserved'])
        self.assertEqual(newly_reserved_counts, 1)


    def legacy_workspace(self, ddl, rows=(), extra=()):
        workspace = Path(tempfile.mkdtemp(prefix='job-legacy-', dir=self.temp.name))
        (workspace / 'coord').mkdir()
        connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
        try:
            connection.execute(ddl)
            for statement in extra:
                connection.execute(statement)
            for row in rows:
                connection.execute('INSERT INTO jobs VALUES (' + ', '.join('?' for _ in row) + ')', row)
            connection.execute('PRAGMA user_version = ' + str(2 if ddl == jobs.CREATE_JOBS else 1))
            connection.commit()
        finally:
            connection.close()
        return workspace

    def assert_refused_unchanged(self, workspace):
        path = workspace / 'coord' / 'ui-jobs.sqlite3'
        before = path.read_bytes()
        with self.assertRaises(ValueError):
            jobs.JobStore(workspace)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(sorted(p.name for p in (workspace / 'coord').iterdir()), ['ui-jobs.sqlite3'])

    def test_unknown_schema1_layouts_refused_without_migration(self):
        self.store.close()
        legacy = jobs.SCHEMA1_JOBS
        layouts = {
            'extra_column': legacy[:-1] + ', extra TEXT)',
            'missing_column': legacy.replace(', state TEXT NOT NULL', ''),
            'no_primary_key': legacy.replace('id TEXT PRIMARY KEY', 'id TEXT NOT NULL'),
            'no_unique_request_key': legacy.replace('request_key TEXT NOT NULL UNIQUE', 'request_key TEXT NOT NULL'),
            'nullable_worker': legacy.replace('worker TEXT NOT NULL', 'worker TEXT'),
            'retyped_column': legacy.replace('draft_id TEXT', 'draft_id BLOB'),
            'case_insensitive_key': legacy.replace('request_key TEXT NOT NULL UNIQUE',
                                                   'request_key TEXT COLLATE NOCASE NOT NULL UNIQUE'),
            'already_schema2_columns': jobs.CREATE_JOBS,
        }
        for label, ddl in layouts.items():
            with self.subTest(layout=label):
                workspace = self.legacy_workspace(ddl)
                if ddl == jobs.CREATE_JOBS:
                    connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
                    connection.execute('PRAGMA user_version = 1')
                    connection.close()
                self.assert_refused_unchanged(workspace)
        companions = {
            'extra_table': 'CREATE TABLE notes (x TEXT)',
            'extra_index': 'CREATE INDEX jobs_worker ON jobs (worker)',
            'trigger': 'CREATE TRIGGER jobs_touch AFTER INSERT ON jobs BEGIN SELECT 1; END',
            'view': 'CREATE VIEW waiting AS SELECT id FROM jobs',
        }
        for label, statement in companions.items():
            with self.subTest(companion=label):
                self.assert_refused_unchanged(self.legacy_workspace(legacy, extra=(statement,)))

    def test_corrupt_schema1_records_roll_back_migration_unchanged(self):
        self.store.close()
        valid = ('1' * 32, '2' * 32, '3' * 32, '4' * 64, 'worker-one',
                 '2026-10-05T12:00:00+00:00', 'awaiting_owner_approval')
        corrupt = {
            'naive_created_at': valid[:5] + ('2026-10-05T12:00:00',) + valid[6:],
            'unparseable_created_at': valid[:5] + ('yesterday',) + valid[6:],
            'non_waiting_state': valid[:6] + ('approved',),
            'unknown_state': valid[:6] + ('dispatched',),
            'bad_worker': valid[:4] + ('BAD WORKER',) + valid[5:],
            'uppercase_id': ('A' * 32,) + valid[1:],
            'short_hash': valid[:3] + ('4' * 63,) + valid[4:],
            'null_id': (None,) + valid[1:],
            'integer_draft_id': valid[:2] + (7,) + valid[3:],
        }
        for label, row in corrupt.items():
            with self.subTest(record=label):
                other = ('5' * 32, '6' * 32) + valid[2:]
                workspace = self.legacy_workspace(jobs.SCHEMA1_JOBS, rows=(other, row))
                self.assert_refused_unchanged(workspace)

    def test_valid_schema1_migration_preserves_every_field_and_constraint(self):
        self.store.close()
        rows = [
            ('1' * 32, '2' * 32, '3' * 32, '4' * 64, 'worker-one',
             '2026-10-05T12:00:00+00:00', 'awaiting_owner_approval'),
            ('5' * 32, '6' * 32, '7' * 32, '8' * 64, 'worker_two',
             '2026-10-04T08:30:00.123456+02:00', 'awaiting_owner_approval'),
        ]
        workspace = self.legacy_workspace(jobs.SCHEMA1_JOBS, rows=rows)
        empty = dict(approval_key=None, approved_at=None, reservation_key=None,
                     reserved_at=None, unknown_at=None, cancelled_at=None)
        expected = [dict(zip(jobs.COLUMNS, row), **empty) for row in sorted(rows, key=lambda r: (r[5], r[0]))]
        with jobs.JobStore(workspace) as store:
            self.assertEqual(store.jobs(), expected)
        with jobs.JobStore(workspace) as reopened:
            self.assertEqual(reopened.jobs(), expected)
            self.assertEqual(reopened.pending(), expected)
        connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
        try:
            self.assertEqual(connection.execute('PRAGMA user_version').fetchone()[0], 2)
            self.assertEqual(jobs.JobStore._layout(connection), jobs._expected_layout(jobs.CREATE_JOBS))
            for statement, values in (
                    ('UPDATE jobs SET approval_key = ? WHERE id IN (?, ?)', ('a' * 32, '1' * 32, '5' * 32)),
                    ('UPDATE jobs SET request_key = ? WHERE id = ?', ('6' * 32, '1' * 32)),
                    ('INSERT INTO jobs (id, request_key, draft_id, draft_sha256, worker, created_at, state) '
                     'VALUES (?, ?, ?, ?, ?, ?, ?)', rows[0][:1] + ('9' * 32,) + rows[0][2:])):
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(statement, values)
        finally:
            connection.close()

    def test_schema2_without_required_constraints_refused_unchanged(self):
        self.store.close()
        full = jobs.CREATE_JOBS
        layouts = {
            'names_only': 'CREATE TABLE jobs (' + ', '.join(c + ' TEXT' for c in jobs.COLUMNS) + ')',
            'no_primary_key': full.replace('id TEXT PRIMARY KEY', 'id TEXT NOT NULL'),
            'no_unique_request_key': full.replace('request_key TEXT NOT NULL UNIQUE', 'request_key TEXT NOT NULL'),
            'no_unique_approval_key': full.replace('approval_key TEXT UNIQUE', 'approval_key TEXT'),
            'no_unique_reservation_key': full.replace('reservation_key TEXT UNIQUE', 'reservation_key TEXT'),
            'nullable_state': full.replace('state TEXT NOT NULL', 'state TEXT'),
            'reordered': full.replace('approved_at TEXT, reservation_key TEXT UNIQUE',
                                      'reservation_key TEXT UNIQUE, approved_at TEXT'),
            'defaulted_state': full.replace('state TEXT NOT NULL', "state TEXT NOT NULL DEFAULT 'approved'"),
            'case_insensitive_key': full.replace('approval_key TEXT UNIQUE', 'approval_key TEXT COLLATE NOCASE UNIQUE'),
        }
        for label, ddl in layouts.items():
            with self.subTest(layout=label):
                workspace = self.legacy_workspace(ddl)
                connection = sqlite3.connect(workspace / 'coord' / 'ui-jobs.sqlite3')
                connection.execute('PRAGMA user_version = 2')
                connection.close()
                self.assert_refused_unchanged(workspace)
        for label, statement in (('extra_table', 'CREATE TABLE notes (x TEXT)'),
                                 ('partial_index', 'CREATE INDEX jobs_open ON jobs (id) WHERE state = 1'),
                                 ('trigger', 'CREATE TRIGGER jobs_touch AFTER UPDATE ON jobs BEGIN SELECT 1; END')):
            with self.subTest(companion=label):
                self.assert_refused_unchanged(self.legacy_workspace(full, extra=(statement,)))

    def edit_draft(self, draft, request):
        path = self.directory / (draft['id'] + '.json')
        saved = json.loads(path.read_text())
        saved['request'] = request
        path.write_text(json.dumps(saved, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n')

    def test_identical_replays_recheck_current_draft(self):
        draft = self.draft()
        job = self.store.enqueue(draft['id'], draft['content_sha256'], 'worker', 'a' * 32)
        approved = self.store.approve(job['id'], draft['content_sha256'], 'worker', 'b' * 32)

        self.edit_draft(draft, 'Changed after approval')
        before = self.database.read_bytes()
        with self.assertRaises(ValueError):
            self.store.approve(job['id'], draft['content_sha256'], 'worker', 'b' * 32)
        self.assertEqual(self.database.read_bytes(), before)
        self.assertEqual(self.store.get(job['id']), approved)

        self.edit_draft(draft, 'Do the bounded thing')
        self.assertEqual(self.store.approve(job['id'], draft['content_sha256'], 'worker', 'b' * 32), approved)
        first = self.store.reserve(job['id'], 'b' * 32, 'c' * 32)
        self.assertTrue(first['newly_reserved'])

        self.edit_draft(draft, 'Changed after reservation')
        before = self.database.read_bytes()
        with jobs.JobStore(self.workspace) as reopened:
            with self.assertRaises(ValueError):
                reopened.reserve(job['id'], 'b' * 32, 'c' * 32)
        with self.assertRaises(ValueError):
            self.store.reserve(job['id'], 'b' * 32, 'c' * 32)
        self.assertEqual(self.database.read_bytes(), before)
        self.assertEqual(self.store.get(job['id']), first['job'])

        self.edit_draft(draft, 'Do the bounded thing')
        with jobs.JobStore(self.workspace) as reopened:
            replay = reopened.reserve(job['id'], 'b' * 32, 'c' * 32)
        self.assertEqual(replay, dict(job=first['job'], newly_reserved=False))

if __name__ == '__main__':
    unittest.main(verbosity=2)
