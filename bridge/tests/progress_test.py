# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
import concurrent.futures
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parents[1]))
from progress import ProgressService, ProgressError, PAGE_BYTES, LINE_BYTES, JSON_LIMIT


def date(epoch):
    return datetime.fromtimestamp(epoch, timezone.utc).isoformat()


class Fixture:
    def __init__(self, root, worker='codex-owned', task='SOURCE-1', attempt='1' * 32):
        self.root, self.worker, self.task, self.attempt = root, worker, task, attempt
        for name in ('repo', 'wt/' + worker, 'coord/tasks', 'coord/reports',
                     'coord/retries/' + task, 'coord/results/' + worker, 'coord/.locks'):
            (root / name).mkdir(parents=True, exist_ok=True)
        self.start = time.time() - 10
        taskfile = root / 'coord/tasks' / (task + '.md')
        taskfile.write_text('Owner task\n')
        import hashlib
        self.revision = dict(base_commit='a' * 40, candidate_commit='b' * 40,
            task_sha256=hashlib.sha256(taskfile.read_bytes()).hexdigest(), worktree_sha256='c' * 64)
        self.native = dict(schema_version=1, worker=worker, task=task, updated_at=date(self.start),
            current_revision=self.revision, revision=self.revision,
            process=dict(state='running', exit_code=None, revision=self.revision),
            validation=dict(state='not_run', scope='UNCHECKED', checks_run=0, checks_failed=0, reasons=[], revision=None),
            review=dict(state='not_run', reviewer=None, process_exit_code=None, material_complete=False, reasons=[], revision=None),
            stale=False, ready_for_human_review=False, human={'state': 'pending'}, integration={'state': 'not_attempted'})
        self.retry = dict(schema_version=1, task=task, failed_attempts=0, retry_granted=False,
            latest={worker: dict(id=attempt, failed=False, pending=True)}, updated_at=date(self.start - .001))
        self.log = root / 'coord/reports' / (task + '.log')
        self.log.write_bytes(b'')
        with (root / 'coord/reports/ledger.jsonl').open('a') as ledger:
            ledger.write(json.dumps(dict(event='run_start', ts=date(self.start), worker=worker, task=task)) + '\n')
        self.save()

    def save(self):
        (self.root / 'coord/results' / self.worker / (self.task + '.json')).write_text(json.dumps(self.native))
        (self.root / 'coord/retries' / self.task / 'state.json').write_text(json.dumps(self.retry))

    def finish(self, code=0):
        self.native['process'].update(state='succeeded' if code == 0 else 'failed', exit_code=code)
        self.native['updated_at'] = date(time.time() + .001)
        self.retry['latest'][self.worker]['pending'] = False
        self.retry['updated_at'] = date(time.time())
        self.save()


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='progress-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = Fixture(self.root)
        self.service = ProgressService(self.root, self.root / 'unio', [(self.fixture.worker, self.fixture.task)])
        self.addCleanup(self.service.close)
        self.identity = next(iter(self.service.bindings))
        # No observation can reach a provider/engine subprocess.
        self.effects = patch.object(subprocess, 'Popen', side_effect=AssertionError('dispatch'))
        self.invoke = self.effects.start()
        self.addCleanup(self.effects.stop)
        self.addCleanup(lambda: self.assertEqual(self.invoke.call_count, 0))

    def get(self, **kw):
        return self.service.get(self.identity, **kw)

    def page(self, cursor=None):
        return self.get(output=True, cursor=cursor)['output']

    def test_first_quiet_recorded_running_and_no_writer_lock(self):
        lock = (self.root / 'coord/.locks' / (self.fixture.worker + '.lock')).open('a')
        self.addCleanup(lock.close)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with patch('fcntl.flock', side_effect=AssertionError('reader acquired writer lock')):
            value = self.get()
        self.assertEqual(value['source']['state'], 'running')
        self.assertEqual(value['observed_liveness'], 'unknown')
        self.assertEqual(value['observed_phase'], 'unknown')
        self.assertEqual(value['output']['state'], 'first_output_wait')
        self.fixture.start -= 100
        self.fixture.native['updated_at'] = date(self.fixture.start)
        self.fixture.retry['updated_at'] = date(self.fixture.start - .001)
        self.fixture.save()
        (self.root / 'coord/reports/ledger.jsonl').write_text(json.dumps(dict(event='run_start', ts=date(self.fixture.start), worker=self.fixture.worker, task=self.fixture.task)) + '\n')
        self.fixture.log.write_text('done\n')
        os.utime(self.fixture.log, (time.time() - 40,) * 2)
        value = self.get()
        self.assertTrue(value['observation_stale'])
        self.assertEqual(value['output']['state'], 'quiet')
        self.assertEqual(value['source']['state'], 'running')

    def test_buffered_verification_never_uses_source_log_or_completes(self):
        self.fixture.log.write_text('Source says done\n')
        self.fixture.finish()
        before = self.get()
        # Native verify buffers all child output and publishes no running marker.
        lock = (self.root / 'coord/.locks' / (self.fixture.worker + '.lock')).open('a')
        self.addCleanup(lock.close)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with patch('fcntl.flock', side_effect=AssertionError('writer lock')):
            during = self.get()
        self.assertEqual(during['verification']['state'], 'not_run')
        self.assertEqual(during['observed_phase'], 'unknown')
        self.assertEqual(during['observed_liveness'], 'unknown')
        self.assertEqual(during['output']['excerpt'], before['output']['excerpt'])
        self.assertEqual(during['acceptance'], {'state': 'unavailable'})
        self.assertNotIn('percentage', str(during))

    def test_failure_validation_review_and_stale_evidence_are_separate(self):
        self.fixture.log.write_text('done\n')
        self.fixture.finish(7)
        value = self.get()
        self.assertEqual(value['source']['state'], 'failed')
        self.assertEqual(value['source']['exit_code'], 7)
        self.assertEqual(value['verification']['state'], 'not_run')
        self.fixture.native['validation'].update(state='failed', scope='OK', checks_run=2,
            checks_failed=1, reasons=['check_failed'], revision=self.fixture.revision)
        self.fixture.native['review'].update(state='unknown', reviewer='other', process_exit_code=0,
            material_complete=True, reasons=['unknown_verdict'], revision=self.fixture.revision)
        self.fixture.native['stale'] = True
        self.fixture.save()
        value = self.get()
        self.assertTrue(value['recorded_evidence_stale'])
        self.assertEqual(value['review']['state'], 'unknown')
        self.assertEqual(value['verification']['checks_failed'], 1)

    def test_append_earlier_pages_reconnect_and_partial_utf8(self):
        self.fixture.log.write_bytes(b'one\n' + b'\xe2\x82')
        first = self.page()
        self.assertEqual(first['text'], 'one\n')
        self.assertTrue(first['partial_record'])
        self.assertFalse(first['at_end'])
        self.assertEqual(self.page(first['next_cursor'])['text'], '')
        with self.fixture.log.open('ab') as out:
            out.write(b'\xac\nlast\n')
        second = self.page(first['next_cursor'])
        self.assertEqual(second['generation'], first['generation'])
        self.assertEqual(second['text'], '€\nlast\n')
        self.assertEqual(self.page(first['next_cursor'])['text'], second['text'])
        self.assertEqual(self.page()['text'], 'one\n€\nlast\n')
        self.assertEqual(self.page(second['next_cursor'])['text'], '')

    def test_truncation_regrowth_rotation_and_missing_cursor(self):
        self.fixture.log.write_text('old\nmore\n')
        first = self.page()
        self.fixture.log.write_text('new\n')
        with self.assertRaises(ProgressError) as error:
            self.page(first['next_cursor'])
        self.assertEqual(error.exception.code, 'cursor_mismatch')
        second = self.page()
        self.fixture.log.write_text('different long replacement\n')
        with self.assertRaises(ProgressError):
            self.page(second['next_cursor'])
        third = self.page()
        self.fixture.log.rename(self.fixture.log.with_suffix('.old'))
        self.fixture.log.write_text('rotated\n')
        with self.assertRaises(ProgressError):
            self.page(third['next_cursor'])
        fourth = self.page()
        self.assertNotEqual(fourth['generation'], third['generation'])
        self.fixture.log.unlink()
        self.assertEqual(self.get()['output']['state'], 'missing')
        with self.assertRaises(ProgressError):
            self.page(fourth['next_cursor'])

    def test_multiple_runs_concurrency_and_changed_attempt(self):
        other = Fixture(self.root, worker='other-owned', task='SOURCE-2', attempt='2' * 32)
        service = ProgressService(self.root, self.root / 'unio', [(self.fixture.worker, self.fixture.task), (other.worker, other.task)])
        self.addCleanup(service.close)
        self.fixture.log.write_text('one\n')
        other.log.write_text('two\n')
        values = service.workers()['workers']
        self.assertEqual({v['output']['excerpt'] for v in values}, {'one\n', 'two\n'})
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            concurrent_views = list(pool.map(lambda _: self.get(), range(8)))
        self.assertEqual(len({v['run_id'] for v in concurrent_views}), 1)
        first = self.get(output=True)
        self.fixture.retry['latest'][self.fixture.worker]['id'] = '3' * 32
        self.fixture.native['updated_at'] = date(time.time() + .01)
        self.fixture.retry['updated_at'] = date(time.time() - .2)
        self.fixture.save()
        # Existing log predates the new Source receipt and must not leak.
        self.assertEqual(self.get()['output']['state'], 'unavailable')
        self.fixture.log.write_text('new attempt\n')
        os.utime(self.fixture.log, (time.time() + .02,) * 2)
        with self.assertRaises(ProgressError):
            self.get(run_id=first['run_id'])
        with self.assertRaises(ProgressError):
            self.page(first['output']['next_cursor'])

    def test_ownership_task_tamper_ambiguous_retry_corrupt_json(self):
        self.fixture.retry['latest']['other-worker'] = dict(id='2' * 32, pending=False, failed=False)
        self.fixture.save()
        with self.assertRaises(ProgressError): self.get()
        self.assertEqual(self.service.workers()['workers'][0]['state'], 'unavailable')
        del self.fixture.retry['latest']['other-worker']
        self.fixture.save()
        (self.root / 'coord/tasks' / (self.fixture.task + '.md')).write_text('changed')
        with self.assertRaises(ProgressError): self.get()
        result = self.root / 'coord/results' / self.fixture.worker / (self.fixture.task + '.json')
        result.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(ProgressError): self.get()

    def test_unsafe_symlink_hardlink_and_special_logs(self):
        self.fixture.log.unlink()
        secret = self.root / 'private'; secret.write_text('PRIVATE')
        for kind in ('symlink', 'hardlink', 'fifo', 'directory'):
            with self.subTest(kind=kind):
                if kind == 'symlink': self.fixture.log.symlink_to(secret)
                elif kind == 'hardlink': os.link(secret, self.fixture.log)
                elif kind == 'fifo': os.mkfifo(self.fixture.log)
                else: self.fixture.log.mkdir()
                self.assertEqual(self.get()['output']['state'], 'unavailable')
                if kind == 'directory': self.fixture.log.rmdir()
                else: self.fixture.log.unlink()
        reports = self.root / 'coord/reports'
        reports.rename(self.root / 'saved-reports')
        reports.symlink_to(self.root / 'saved-reports', target_is_directory=True)
        with self.assertRaises(ProgressError): self.get()

    def test_bounded_pages_long_records_utf8_and_literal_sensitive_output(self):
        safe = b'\x1b[31m<html><a href="https://example.org">done</a></html>\x1b[0m\r\n'
        private = b'Authorization: Bearer PRIVATE\npassword=PRIVATE\n-----BEGIN PRIVATE KEY-----\n' + b'A' * 64 + b'\n-----END PRIVATE KEY-----\n'
        self.fixture.log.write_bytes(safe + private + b'\xff\n' + b'z' * (PAGE_BYTES * 2) + b'\nend\n')
        page = self.page()
        self.assertIn('<html><a href="https://example.org">done</a></html>', page['text'])
        self.assertNotIn('\x1b', page['text'])
        self.assertNotIn('PRIVATE', page['text'])
        self.assertNotIn('A' * 64, page['text'])
        self.assertIn('[invalid UTF-8 record excluded]', page['text'])
        seen = page['text']
        for _ in range(4):
            page = self.page(page['next_cursor'])
            seen += page['text']
            if page['at_end']: break
        self.assertIn('end\n', seen)
        self.assertNotIn('z' * LINE_BYTES, seen)
        self.assertLessEqual(len(self.get()['output']['excerpt']), 1024)

    def test_cursor_tamper_wrong_generation_and_service_restart(self):
        self.fixture.log.write_text('text\n')
        first = self.page()
        with self.assertRaises(ProgressError): self.page(first['next_cursor'][:-4] + 'AAAA')
        fresh = ProgressService(self.root, self.root / 'unio', [(self.fixture.worker, self.fixture.task)])
        self.addCleanup(fresh.close)
        with self.assertRaises(ProgressError): fresh.get(self.identity, output=True, cursor=first['next_cursor'])
        self.assertEqual(fresh.get(self.identity, output=True)['output']['text'], 'text\n')

    def test_collection_and_read_limits_deadline(self):
        with self.assertRaises(ValueError): ProgressService(self.root, self.root / 'unio', [])
        with self.assertRaises(ValueError): ProgressService(self.root, self.root / 'unio', [('x', 't')] * 33)
        with self.assertRaises(ValueError): ProgressService(self.root, self.root / 'unio', [('x', 't'), ('y', 't')])
        taskfile = self.root / 'coord/tasks' / (self.fixture.task + '.md')
        taskfile.write_bytes(b'x' * (JSON_LIMIT + 1))
        with self.assertRaises(ProgressError): self.get()
        with patch('progress.time.monotonic', side_effect=[0, 3]):
            with self.assertRaises(ProgressError): self.service._operation(lambda _: {})

    def test_pid_identity_only_matching_background_source(self):
        pidfile = self.root / 'coord/reports' / (self.fixture.task + '.pid')
        pidfile.write_text('123\n')
        argv = b'bash\0' + os.fsencode(self.root / 'unio') + b'\0run\0codex-owned\0SOURCE-1\0'
        from unittest.mock import mock_open
        with patch('builtins.open', mock_open(read_data=argv)), patch('progress.os.readlink', return_value=str(self.root / 'repo')):
            value = self.get()
        self.assertEqual(value['observed_liveness'], 'running')
        self.assertEqual(value['observed_phase'], 'source')
        for wrong in (argv.replace(b'SOURCE-1', b'SOURCE-2'), argv.replace(b'run', b'verify'), b'bash\0evil\0run\0codex-owned\0SOURCE-1\0'):
            with patch('builtins.open', mock_open(read_data=wrong)), patch('progress.os.readlink', return_value=str(self.root / 'repo')):
                self.assertEqual(self.get()['observed_liveness'], 'unknown')
        pidfile.write_text(str(os.getpid()) + '\n')
        self.assertEqual(self.get()['observed_liveness'], 'unknown')


if __name__ == '__main__': unittest.main(verbosity=2)
