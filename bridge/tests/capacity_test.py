# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Focused checks for manual capacity readings; no provider, model or network call."""
import ast
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bridge import capacity  # noqa: E402
from bridge.capacity import CapacityError, CapacityStore  # noqa: E402

TOOL = ROOT / 'tools' / 'capacity-readings.py'
NOW = datetime(2026, 10, 9, 14, 0, tzinfo=timezone.utc)


def iso(moment):
    return moment.isoformat()


class Project(unittest.TestCase):
    def setUp(self):
        # tempfile honours the workspace-approved TMPDIR.
        self.root = os.path.realpath(tempfile.mkdtemp(prefix='capacity-test-'))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.project = os.path.join(self.root, 'project')
        os.mkdir(self.project)
        self.store = CapacityStore(self.project)
        self.state = Path(self.project, 'coord', 'capacity', 'readings.json')

    def record(self, group='codex', window='five-hour', minutes=300, percent=40, observed=NOW, reset=None,
               now=NOW):
        return self.store.record(group, window, minutes, percent, iso(observed),
                                 None if reset is None else iso(reset), now=now)

    def window(self, view, group='codex', window='five-hour'):
        return view['groups'][group]['windows'][window]


class RecordShow(Project):
    def test_roundtrip_keeps_last_reading_distinct_from_usable(self):
        self.record(percent=42.5, reset=NOW + timedelta(hours=2))
        reading = self.window(self.store.show('codex', now=NOW + timedelta(seconds=30)))
        self.assertEqual(reading['status'], 'fresh')
        self.assertEqual(reading['source'], 'manual')
        self.assertEqual(reading['window_minutes'], 300)
        self.assertEqual(reading['age_seconds'], 30)
        self.assertEqual(reading['reset_at'], iso(NOW + timedelta(hours=2)))
        self.assertEqual(reading['last_reading_remaining_percent'], 42.5)
        self.assertEqual(reading['usable_remaining_percent'], 42.5)
        stored = json.loads(self.state.read_text())
        self.assertEqual(set(stored), {'schema_version', 'groups'})
        self.assertEqual(stored['schema_version'], 1)

    def test_multiple_groups_and_windows_merge(self):
        self.record('codex', 'five-hour', 300, 40)
        self.record('codex', 'weekly', 10080, 85)
        self.record('claude', 'five-hour', 300, 10)
        self.record('codex', 'five-hour', 300, 35, observed=NOW + timedelta(minutes=1),
                    now=NOW + timedelta(minutes=1))
        view = self.store.show(now=NOW + timedelta(minutes=2))
        self.assertEqual(list(view['groups']), ['claude', 'codex'])
        self.assertEqual(self.window(view)['usable_remaining_percent'], 35)
        self.assertEqual(self.window(view, window='weekly')['usable_remaining_percent'], 85)
        self.assertEqual(self.window(view, 'claude')['usable_remaining_percent'], 10)

    def test_stale_expired_and_missing_are_never_usable(self):
        self.record(window='stale', minutes=300, percent=90)
        self.record(window='reset-passed', minutes=300, percent=90, reset=NOW + timedelta(minutes=5))
        self.record(window='short', minutes=10, percent=90)
        view = self.store.show('codex', max_age_seconds=900, now=NOW + timedelta(minutes=16))
        statuses = {name: (w['status'], w['usable_remaining_percent'], w['last_reading_remaining_percent'])
                    for name, w in view['groups']['codex']['windows'].items()}
        self.assertEqual(statuses, {'stale': ('stale', None, 90.0),
                                    'reset-passed': ('expired', None, 90.0),
                                    'short': ('expired', None, 90.0)})
        missing = self.store.show('gemini', now=NOW)
        self.assertEqual(missing['groups'], {'gemini': {'status': 'unknown', 'windows': {}}})

    def test_absent_state_is_unknown_and_show_creates_nothing(self):
        view = self.store.show(now=NOW)
        self.assertEqual((view['state'], view['groups']), ('missing', {}))
        self.assertEqual(os.listdir(self.project), [])

    def test_clock_rollback_reading_is_unknown(self):
        self.record()
        reading = self.window(self.store.show(now=NOW - timedelta(hours=1)))
        self.assertEqual(reading['status'], 'unknown')
        self.assertIsNone(reading['usable_remaining_percent'])

    def test_source_is_always_manual(self):
        with self.assertRaises(TypeError):
            self.store.record('codex', 'w', 5, 50, iso(NOW), source='provider', now=NOW)
        self.record()
        self.assertEqual(self.window(self.store.show(now=NOW))['source'], 'manual')


class InputRefusals(Project):
    def assert_refused(self, **changes):
        before = self.state.read_bytes()
        with self.assertRaises(CapacityError, msg=repr(changes)):
            self.record(**changes)
        self.assertEqual(self.state.read_bytes(), before, repr(changes))

    def test_invalid_inputs_preserve_state(self):
        self.record(window='keep', percent=12)
        for bad in (-0.1, 100.01, 10 ** 500, -(10 ** 500), float('nan'), float('inf'),
                    float('-inf'), True, False, '50', None):
            self.assert_refused(percent=bad)
        for bad in (0, -5, 5.0, 5.5, True, '5', capacity.MAX_WINDOW_MINUTES + 1):
            self.assert_refused(minutes=bad)
        for bad in ('', 'has space', 'a/b', '../x', '.hidden', 'émoji', 'user@example.com', 'x' * 65, 7):
            self.assert_refused(group=bad)
            self.assert_refused(window=bad)

    def test_invalid_timestamps_preserve_state(self):
        self.record(window='keep')
        before = self.state.read_bytes()
        cases = [('2026-10-09T14:00:00', None), ('not-a-time', None), ('2026-10-09', None),
                 ('0001-01-01T00:00:00+01:00', None),
                 ('9999-12-31T23:59:59-01:00', None),
                 ('2026-10-09T14:00:00+00:00' + ' ' * 60, None),
                 (iso(NOW + timedelta(minutes=6)), None),
                 (iso(NOW + timedelta(days=365)), None),
                 (iso(NOW), '2026-10-09T15:00:00'),
                 (iso(NOW), iso(NOW - timedelta(seconds=1))),
                 (iso(NOW), iso(NOW + timedelta(minutes=300, seconds=301)))]
        for observed, reset in cases:
            with self.assertRaises(CapacityError, msg=(observed, reset)):
                self.store.record('codex', 'other', 300, 50, observed, reset, now=NOW)
        self.assertEqual(self.state.read_bytes(), before)

    def test_duplicate_and_older_readings_refused(self):
        self.record(percent=50)
        before = self.state.read_bytes()
        same_instant = NOW.astimezone(timezone(timedelta(hours=2)))
        for observed in (NOW, same_instant, NOW - timedelta(seconds=1)):
            with self.assertRaises(CapacityError):
                self.record(percent=60, observed=observed)
        self.assertEqual(self.state.read_bytes(), before)

    def test_group_and_window_counts_are_bounded(self):
        for index in range(capacity.MAX_WINDOWS):
            self.record(window=f'w{index}')
        before = self.state.read_bytes()
        with self.assertRaises(CapacityError):
            self.record(window='one-too-many')
        for index in range(1, capacity.MAX_GROUPS):
            self.record(group=f'g{index}')
        with self.assertRaises(CapacityError):
            self.record(group='one-too-many')
        self.assertNotIn(b'one-too-many', self.state.read_bytes())
        self.assertNotEqual(before, b'')


def forged(**fields):
    reading = {'source': 'manual', 'window_minutes': 300, 'remaining_percent': 50,
               'observed_at': iso(NOW)}
    reading.update(fields)
    return json.dumps({'schema_version': 1, 'groups': {'codex': {'five-hour': reading}}}).encode()


INVALID_STATES = {
    'not json': b'invalid json',
    'not utf-8': b'\xff\xfe{}',
    'empty file': b'',
    'top-level list': b'[]',
    'schema 2': b'{"schema_version": 2, "groups": {}}',
    'schema true': b'{"schema_version": true, "groups": {}}',
    'schema 1.0': b'{"schema_version": 1.0, "groups": {}}',
    'extra top-level key': b'{"schema_version": 1, "groups": {}, "account": "x"}',
    'duplicate key': b'{"schema_version": 1, "schema_version": 1, "groups": {}}',
    'NaN constant': forged().replace(b'50', b'NaN'),
    'oversized': b'{"schema_version": 1, "groups": {}}' + b' ' * capacity.MAX_STATE_BYTES,
    'empty group': b'{"schema_version": 1, "groups": {"codex": {}}}',
    'bad group label': forged().replace(b'"codex"', b'"bad label"'),
    'reviewer forgery': forged(source='provider', window_minutes=True, remaining_percent=9999),
    'provider source': forged(source='provider'),
    'bool minutes': forged(window_minutes=True),
    'percent 9999': forged(remaining_percent=9999),
    'huge integer percent': forged(remaining_percent=10 ** 500),
    'integer exceeds decoder limit': forged().replace(b'50', b'9' * 5000),
    'UTC timestamp underflow': forged(observed_at='0001-01-01T00:00:00+01:00'),
    'UTC timestamp overflow': forged(observed_at='9999-12-31T23:59:59-01:00'),
    'percent bool': forged(remaining_percent=False),
    'naive time': forged(observed_at='2026-10-09T14:00:00'),
    'reset before observation': forged(reset_at=iso(NOW - timedelta(minutes=1))),
    'unknown field': forged(account_id='acct-1'),
    'missing field': json.dumps({'schema_version': 1, 'groups': {'codex': {'five-hour': {
        'source': 'manual', 'window_minutes': 300, 'observed_at': iso(NOW)}}}}).encode(),
}


class LoadedStateValidation(Project):
    def test_invalid_state_is_unknown_and_never_overwritten(self):
        self.record()
        for name, raw in INVALID_STATES.items():
            with self.subTest(name):
                self.state.write_bytes(raw)
                view = self.store.show('codex', now=NOW)
                self.assertEqual(view['state'], 'invalid')
                self.assertTrue(view['error'])
                self.assertEqual(view['groups'], {'codex': {'status': 'unknown', 'windows': {}}})
                self.assertNotIn('9999', json.dumps(view))
                with self.assertRaises(CapacityError):
                    self.record(window='new', observed=NOW + timedelta(seconds=1))
                self.assertEqual(self.state.read_bytes(), raw)
        leftovers = [n for n in os.listdir(self.state.parent) if n.endswith('.tmp')]
        self.assertEqual(leftovers, [])

    def test_non_regular_state_is_refused_without_blocking(self):
        self.record()
        self.state.unlink()
        os.mkfifo(self.state)
        self.assertEqual(self.store.show(now=NOW)['state'], 'invalid')
        with self.assertRaises(CapacityError):
            self.record(observed=NOW + timedelta(seconds=1))


class SymlinkBoundary(Project):
    def setUp(self):
        super().setUp()
        self.outside = os.path.join(self.root, 'outside')
        os.mkdir(self.outside)

    def assert_outside_untouched(self):
        self.assertEqual(os.listdir(self.outside), [])

    def test_coord_symlink_is_refused(self):
        os.symlink(self.outside, os.path.join(self.project, 'coord'))
        with self.assertRaises(CapacityError):
            self.record()
        with self.assertRaises(CapacityError):
            self.store.show(now=NOW)
        self.assert_outside_untouched()

    def test_capacity_directory_symlink_is_refused(self):
        os.mkdir(os.path.join(self.project, 'coord'))
        os.symlink(self.outside, os.path.join(self.project, 'coord', 'capacity'))
        with self.assertRaises(CapacityError):
            self.record()
        self.assert_outside_untouched()

    def test_state_and_lock_symlinks_are_refused(self):
        self.record()
        target = Path(self.outside, 'target.json')
        for name in ('readings.json', capacity.LOCK):
            with self.subTest(name):
                target.write_bytes(b'outside')
                link = self.state.parent / name
                saved = link.read_bytes()
                link.unlink()
                link.symlink_to(target)
                with self.assertRaises(CapacityError):
                    self.record(observed=NOW + timedelta(seconds=1))
                self.assertEqual(target.read_bytes(), b'outside')
                self.assertTrue(link.is_symlink())
                link.unlink()
                link.write_bytes(saved)

    def test_symlinked_or_missing_project_is_refused(self):
        alias = os.path.join(self.root, 'alias')
        os.symlink(self.project, alias)
        for path in (alias, os.path.join(self.root, 'absent')):
            with self.assertRaises(CapacityError):
                CapacityStore(path)


def cli(*args, cwd):
    env = {key: value for key, value in os.environ.items() if key != 'PYTHONPATH'}
    return subprocess.run([sys.executable, '-B', str(TOOL), *args], cwd=cwd, env=env,
                          capture_output=True, text=True, timeout=60)


class CommandLine(Project):
    def test_help_and_roundtrip_without_pythonpath_from_any_cwd(self):
        observed = datetime.now(timezone.utc).replace(microsecond=0)
        for index, cwd in enumerate((self.root, str(ROOT))):
            with self.subTest(cwd=cwd):
                help_run = cli('--help', cwd=cwd)
                self.assertEqual(help_run.returncode, 0, help_run.stderr)
                self.assertIn('record', help_run.stdout)
                done = cli('--project', self.project, 'record', '--group', 'codex', '--window', f'w{index}',
                           '--window-minutes', '300', '--remaining-percent', '37.5',
                           '--observed-at', iso(observed), cwd=cwd)
                self.assertEqual(done.returncode, 0, done.stderr)
                shown = cli('--project', self.project, 'show', '--group', 'codex', '--json', cwd=cwd)
                self.assertEqual(shown.returncode, 0, shown.stderr)
                reading = json.loads(shown.stdout)['groups']['codex']['windows'][f'w{index}']
                self.assertEqual((reading['status'], reading['usable_remaining_percent']), ('fresh', 37.5))
                text = cli('--project', self.project, 'show', cwd=cwd)
                self.assertIn('Usable now: 37.5%', text.stdout)

    def test_cli_refusals_and_invalid_state_exit_nonzero(self):
        base = ['--project', self.project, 'record', '--group', 'codex', '--window', 'w',
                '--window-minutes', '300', '--observed-at', iso(datetime.now(timezone.utc))]
        for percent in ('nan', 'inf', '101', 'true'):
            run = cli(*base, '--remaining-percent', percent, cwd=self.root)
            self.assertNotEqual(run.returncode, 0, percent)
        run = cli(*base[:-4], '--window-minutes', 'true', *base[-2:], '--remaining-percent', '5', cwd=self.root)
        self.assertEqual(run.returncode, 2)
        self.assertFalse(self.state.exists())
        self.state.parent.mkdir(parents=True)
        self.state.write_bytes(INVALID_STATES['reviewer forgery'])
        shown = cli('--project', self.project, 'show', '--json', cwd=self.root)
        self.assertEqual(shown.returncode, 1)
        self.assertEqual(json.loads(shown.stdout)['state'], 'invalid')
        refused = cli(*base, '--remaining-percent', '5', cwd=self.root)
        self.assertEqual(refused.returncode, 1)
        self.assertIn('refused', refused.stderr)
        self.assertEqual(self.state.read_bytes(), INVALID_STATES['reviewer forgery'])

    def test_concurrent_cli_writers_keep_every_group_and_window(self):
        observed = iso(datetime.now(timezone.utc).replace(microsecond=0))
        runs = []
        for group in ('codex', 'claude', 'gemini', 'grok'):
            for window in ('five-hour', 'weekly', 'daily'):
                command = [sys.executable, '-B', str(TOOL), '--project', self.project, 'record',
                           '--group', group, '--window', window, '--window-minutes', '10080',
                           '--remaining-percent', '50', '--observed-at', observed]
                runs.append(subprocess.Popen(command, cwd=self.root, stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE, text=True))
        for run in runs:
            _, error = run.communicate(timeout=120)
            self.assertEqual(run.returncode, 0, error)
        view = self.store.show()
        self.assertEqual(view['state'], 'ok')
        self.assertEqual({g: sorted(e['windows']) for g, e in view['groups'].items()},
                         {g: ['daily', 'five-hour', 'weekly'] for g in ('claude', 'codex', 'gemini', 'grok')})


class NoProviderCall(Project):
    def test_only_local_standard_modules_are_imported(self):
        allowed = {'datetime', 'errno', 'fcntl', 'json', 'math', 'os', 're', 'stat', 'uuid',
                   'argparse', 'pathlib', 'sys', 'bridge.capacity'}
        for path in (ROOT / 'bridge' / 'capacity.py', TOOL):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Import):
                    names = {alias.name for alias in node.names}
                elif isinstance(node, ast.ImportFrom):
                    names = {node.module}
                else:
                    continue
                self.assertLessEqual(names, allowed, path.name)

    def test_record_and_show_open_no_socket(self):
        with mock.patch.object(socket, 'socket', side_effect=AssertionError('network use')):
            self.record()
            self.assertEqual(self.store.show(now=NOW)['state'], 'ok')


if __name__ == '__main__':
    unittest.main()
