# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Focused checks for cached Codex capacity; only a local fake app-server runs."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from bridge import provider_capacity as pc  # noqa: E402
from bridge.capacity import CapacityError, CapacityStore  # noqa: E402

TOOL = ROOT / 'tools' / 'capacity-readings.py'
SECRETS = ('secret.person@example.com', 'sk-live-TOPSECRET', 'eyJhbGciOiJTOPSECRET')

# The fake reads FAKE_SCRIPT (JSON: method -> raw response line or action),
# logs every received message, argv and cwd to FAKE_LOG, and never does more.
FAKE = textwrap.dedent('''\
    #!/usr/bin/env python3
    import json, os, subprocess, sys, time
    log = open(os.environ['FAKE_LOG'], 'a')
    log.write(json.dumps({'argv': sys.argv[1:], 'cwd': os.getcwd()}) + '\\n'); log.flush()
    script = json.loads(open(os.environ['FAKE_SCRIPT']).read())
    sys.stderr.write('debug token sk-live-TOPSECRET for secret.person@example.com\\n'); sys.stderr.flush()
    if script.get('spawn'):
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])
        open(os.environ['FAKE_LOG'] + '.child', 'w').write(str(child.pid))
    for line in sys.stdin:
        message = json.loads(line)
        log.write(json.dumps(message) + '\\n'); log.flush()
        action = script.get(message['method'])
        if action is None or 'id' not in message:
            continue
        if action == 'hang':
            time.sleep(60)
        if isinstance(action, dict):
            action = json.dumps({'id': message['id'], 'result': action})
        sys.stdout.write(action.replace('ID', str(message['id'])) + '\\n'); sys.stdout.flush()
    ''')

FUTURE = int(time.time()) + 3600
WINDOW = {'usedPercent': 30, 'windowDurationMins': 300, 'resetsAt': FUTURE}
WEEK = {'usedPercent': 12.5, 'windowDurationMins': 10080, 'resetsAt': None}
ACCOUNT = {'account': {'type': 'chatgpt', 'email': SECRETS[0], 'planType': 'pro'},
           'requiresOpenaiAuth': True, 'accessToken': SECRETS[2]}
LIMITS = {'rateLimits': {'limitId': 'codex', 'primary': dict(WINDOW), 'secondary': None,
                         'credits': {'balance': SECRETS[1]}},
          'rateLimitsByLimitId': {
              'codex': {'limitId': 'codex', 'primary': dict(WINDOW), 'secondary': dict(WEEK)},
              'codex_other': {'limitId': 'codex_other', 'primary': None,
                              'secondary': {'usedPercent': 100, 'windowDurationMins': 10080,
                                            'resetsAt': FUTURE}}}}


class FakeServer(unittest.TestCase):
    def setUp(self):
        # tempfile honours the workspace-approved TMPDIR.
        self.root = os.path.realpath(tempfile.mkdtemp(prefix='provider-capacity-test-'))
        self.addCleanup(shutil.rmtree, self.root, True)
        self.project = os.path.join(self.root, 'project')
        os.mkdir(self.project)
        self.binary = os.path.join(self.root, 'fake codex')
        Path(self.binary).write_text(FAKE)
        os.chmod(self.binary, 0o755)
        self.log = os.path.join(self.root, 'fake.log')
        self.script = os.path.join(self.root, 'script.json')
        self.env = dict(os.environ, FAKE_LOG=self.log, FAKE_SCRIPT=self.script)
        self.store = pc.ProviderStore(self.project)
        self.state = Path(self.project, 'coord', 'capacity', 'providers.json')
        self.script_for()

    def script_for(self, account=ACCOUNT, limits=LIMITS, **extra):
        script = {'initialize': {'userAgent': 'fake'}, 'account/read': account,
                  'account/rateLimits/read': limits}
        script.update(extra)
        Path(self.script).write_text(json.dumps(script))

    def refresh(self, group='codex', timeout=5, **kwargs):
        return self.store.refresh(group, self.binary, timeout=timeout, env=self.env, **kwargs)

    def received(self):
        if not os.path.exists(self.log):
            return []
        return [json.loads(line) for line in Path(self.log).read_text().splitlines()]


class TransportTests(FakeServer):
    def test_exact_allowlisted_sequence_from_neutral_cwd(self):
        entry = self.refresh()
        self.assertEqual(entry['state'], 'ok', entry)
        start, *messages = self.received()
        self.assertEqual(start['argv'], ['app-server', '--listen', 'stdio://'])
        neutral = os.path.join(self.project, 'coord', 'capacity', 'codex-cwd')
        self.assertEqual(start['cwd'], neutral)
        self.assertEqual(os.listdir(neutral), [])
        self.assertEqual([(m['method'], m.get('id')) for m in messages],
                         [('initialize', 0), ('initialized', None), ('account/read', 1),
                          ('account/rateLimits/read', 2)])
        self.assertEqual(messages[2]['params'], {'refreshToken': False})
        self.assertEqual(messages[3]['params'], {'excludeResetCreditDetails': True})
        self.assertEqual(pc.ALLOWED_METHODS, tuple(m['method'] for m in messages))

    def test_send_refuses_any_method_outside_the_allowlist(self):
        server = pc.AppServer(self.binary, self.root, 5, self.env)
        try:
            for method in ('thread/start', 'turn/start', 'account/login/start', 'account/logout',
                           'model/list', 'config/read'):
                with self.assertRaises(pc.ProbeFailure):
                    server.send(method, {}, 9)
        finally:
            server.close()
        self.assertEqual([m.get('method') for m in self.received()[1:]], [])

    def test_signed_out_and_api_key_accounts_stop_before_rate_limits(self):
        for account, reason in (({'account': None, 'requiresOpenaiAuth': True}, 'not_signed_in'),
                                ({'account': {'type': 'apiKey'}, 'requiresOpenaiAuth': True},
                                 'unsupported_account'),
                                ({'account': 'chatgpt'}, 'invalid_account')):
            with self.subTest(reason=reason):
                os.unlink(self.log) if os.path.exists(self.log) else None
                self.script_for(account=account)
                entry = self.refresh()
                self.assertEqual((entry['state'], entry['reason'], entry['buckets']), ('unknown', reason, None))
                self.assertNotIn('account/rateLimits/read', [m.get('method') for m in self.received()])

    def test_protocol_defects_become_bounded_unknown(self):
        cases = {
            'request_failed': {'account/read': '{"id": ID, "error": {"message": "token sk-live-TOPSECRET"}}'},
            'invalid_message': {'account/read': '{"id": ID, "id": ID, "result": {}}'},
            'unexpected_request': {'account/read': '{"id": ID, "method": "item/approval", "params": {}}'},
            'output_limit': {'account/read': 'x' * (pc.MAX_MESSAGE_BYTES + 10)},
        }
        for reason, extra in cases.items():
            with self.subTest(reason=reason):
                self.script_for(**extra)
                entry = self.refresh()
                self.assertEqual((entry['state'], entry['reason']), ('unknown', reason))
        for raw in ('{"id": ID, "result": {"x": NaN}}', '{"id": ID, "result": ' + '[' * 100000 + ']' * 100000 + '}',
                    '{"id": ID, "result": {"n": ' + '9' * 5000 + '}}'):
            with self.subTest(raw=raw[:30]):
                self.script_for(**{'account/rateLimits/read': raw})
                entry = self.refresh()
                self.assertEqual(entry['state'], 'unknown')
                self.assertIn(entry['reason'], ('invalid_message', 'output_limit'))

    def test_missing_binary_and_start_failure(self):
        self.assertEqual(self.store.refresh('codex', None)['reason'], 'binary_missing')
        missing = os.path.join(self.root, 'no such codex')
        self.assertEqual(self.store.refresh('codex', missing)['reason'], 'start_failed')

    def test_timeout_kills_the_owned_process_group(self):
        self.script_for(spawn=True, **{'account/rateLimits/read': 'hang'})
        started = time.monotonic()
        entry = self.refresh(timeout=1.5)
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual((entry['state'], entry['reason']), ('unknown', 'timeout'))
        child = int(Path(self.log + '.child').read_text())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and _alive(child):
            time.sleep(0.05)
        self.assertFalse(_alive(child), 'grandchild survived cleanup')

    def test_secrets_never_reach_state_or_output(self):
        self.refresh()
        self.script_for(**{'account/rateLimits/read': '{"id": ID, "error": {"message": "sk-live-TOPSECRET"}}'})
        self.refresh()
        result = subprocess.run([sys.executable, '-B', str(TOOL), '--project', self.project, 'refresh', 'codex',
                                 '--group', 'codex', '--json'], capture_output=True, text=True, timeout=30,
                                env=dict(self.env, **{pc.TEST_BINARY_ENV: self.binary}))
        shown = subprocess.run([sys.executable, '-B', str(TOOL), '--project', self.project, 'show',
                                '--provider', 'codex', '--json'], capture_output=True, text=True, timeout=30)
        stored = self.state.read_text()
        for secret in SECRETS + ('planType', 'pro"', 'email', 'credits'):
            for text in (stored, result.stdout, result.stderr, shown.stdout, shown.stderr):
                self.assertNotIn(secret, text)


def _alive(pid):
    try:
        state = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
    except (FileNotFoundError, ProcessLookupError):
        return False
    return state != 'Z'


class NormalizationTests(unittest.TestCase):
    NOW = 1791554400

    def norm(self, result):
        return pc.normalize_rate_limits(result, self.NOW)

    def test_keyed_map_wins_and_preserves_every_bucket_and_window(self):
        buckets = self.norm(LIMITS)
        self.assertEqual(sorted(buckets), ['codex', 'codex_other'])
        self.assertEqual(buckets['codex']['windows']['secondary']['remaining_percent'], 87.5)
        self.assertEqual(buckets['codex']['windows']['primary']['remaining_percent'], 70.0)
        self.assertIsNone(buckets['codex_other']['windows']['primary'])
        self.assertEqual(buckets['codex_other']['windows']['secondary']['remaining_percent'], 0.0)

    def test_legacy_only_when_map_absent_never_when_malformed(self):
        legacy = {'rateLimits': {'limitId': 'codex', 'primary': dict(WINDOW, resetsAt=None), 'secondary': None}}
        self.assertEqual(list(self.norm(legacy)), ['codex'])
        self.assertEqual(list(self.norm(dict(legacy, rateLimitsByLimitId=None))), ['codex'])
        for broken in ([], {}, 'x', {'bad id!': {}}, {str(i): {} for i in range(pc.MAX_BUCKETS + 1)}):
            with self.subTest(broken=str(broken)[:20]):
                with self.assertRaises(pc.ProbeFailure) as raised:
                    self.norm(dict(legacy, rateLimitsByLimitId=broken))
                self.assertEqual(raised.exception.reason, 'invalid_rate_limits')

    def test_window_validation(self):
        now = self.NOW
        bad = [{'usedPercent': True, 'windowDurationMins': 300}, {'usedPercent': -1, 'windowDurationMins': 300},
               {'usedPercent': 100.01, 'windowDurationMins': 300}, {'usedPercent': float('nan'), 'windowDurationMins': 300},
               {'usedPercent': float('inf'), 'windowDurationMins': 300}, {'usedPercent': '5', 'windowDurationMins': 300},
               {'usedPercent': 5}, {'usedPercent': 5, 'windowDurationMins': None},
               {'usedPercent': 5, 'windowDurationMins': 0}, {'usedPercent': 5, 'windowDurationMins': 300.0},
               {'usedPercent': 5, 'windowDurationMins': True}, {'usedPercent': 5, 'windowDurationMins': 10 ** 9},
               {'usedPercent': 5, 'windowDurationMins': 300, 'resetsAt': 5},
               {'usedPercent': 5, 'windowDurationMins': 300, 'resetsAt': 10 ** 15},
               {'usedPercent': 5, 'windowDurationMins': 300, 'resetsAt': now + 0.5}, []]
        for window in bad:
            with self.subTest(window=window):
                self.assertEqual(pc.normalize_window(window, now), {'status': 'unknown', 'reason': 'invalid_window'})
        absurd = pc.normalize_window({'usedPercent': 5, 'windowDurationMins': 300, 'resetsAt': now + 86400}, now)
        self.assertEqual(absurd['reason'], 'implausible_reset')
        self.assertIsNone(pc.normalize_window(None, now))
        past = pc.normalize_window({'usedPercent': 0, 'windowDurationMins': 300, 'resetsAt': now - 60}, now)
        self.assertEqual(past['status'], 'valid')

    def test_no_valid_window_is_unknown(self):
        for result in ({'rateLimitsByLimitId': {'codex': {'primary': None, 'secondary': None}}},
                       {'rateLimitsByLimitId': {'codex': {'primary': {'usedPercent': 200}}}},
                       {'rateLimitsByLimitId': {'codex': 'x'}}):
            with self.assertRaises(pc.ProbeFailure) as raised:
                self.norm(result)
            self.assertEqual(raised.exception.reason, 'no_valid_window')
        for result in (None, {}, {'rateLimits': None}, {'rateLimits': []}):
            with self.assertRaises(pc.ProbeFailure):
                self.norm(result)

    def test_invalid_bucket_keeps_identity_without_values(self):
        buckets = self.norm({'rateLimitsByLimitId': {'codex': {'primary': dict(WINDOW, resetsAt=None)}, 'other': 7}})
        self.assertEqual(buckets['other'], {'status': 'unknown', 'reason': 'invalid_bucket', 'windows': {}})

    def test_strict_json(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":-Infinity}', b'{"a":' + b'1' * 25 + b'}', b'\xff'):
            with self.subTest(raw=raw[:16]):
                with self.assertRaises((ValueError, UnicodeDecodeError)):
                    pc.strict_json(raw)


class CacheTests(FakeServer):
    def test_show_is_local_and_reports_freshness(self):
        self.refresh()
        os.unlink(self.binary)  # show can not start anything
        observed = datetime.fromisoformat(self.store.show()['groups']['codex']['observed_at'])
        fresh = self.store.show('codex', now=observed + timedelta(seconds=10))['groups']['codex']
        self.assertEqual((fresh['source'], fresh['state'], fresh['freshness']), ('codex', 'ok', 'fresh'))
        window = fresh['buckets']['codex']['windows']['primary']
        self.assertEqual((window['status'], window['usable_remaining_percent']), ('fresh', 70.0))
        stale = self.store.show('codex', now=observed + timedelta(seconds=1000))['groups']['codex']
        window = stale['buckets']['codex']['windows']['primary']
        self.assertEqual((window['status'], window['usable_remaining_percent'],
                          window['last_reading_remaining_percent']), ('stale', None, 70.0))
        # A passed reset never turns into recovered quota.
        reset = datetime.fromtimestamp(FUTURE, timezone.utc) + timedelta(seconds=1)
        expired = self.store.show('codex', 100000, now=reset)['groups']['codex']['buckets']['codex']['windows']
        self.assertEqual((expired['primary']['status'], expired['primary']['usable_remaining_percent']),
                         ('expired', None))
        self.assertEqual(expired['secondary']['status'], 'fresh')
        self.assertEqual(self.store.show('claude')['groups']['claude']['state'], 'unknown')
        self.assertEqual(len([m for m in self.received() if 'argv' in m]), 1)

    def test_failed_refresh_invalidates_and_keeps_last_good_historical(self):
        first = self.refresh()
        self.script_for(account={'account': None, 'requiresOpenaiAuth': True})
        failed = self.refresh()
        self.assertEqual((failed['state'], failed['buckets'], failed['last_good']['observed_at']),
                         ('unknown', None, first['observed_at']))
        view = self.store.show('codex')['groups']['codex']
        self.assertEqual((view['state'], view['reason'], view['buckets']), ('unknown', 'not_signed_in', {}))
        historical = view['last_good']
        self.assertTrue(historical['historical'])
        for window in historical['buckets']['codex']['windows'].values():
            self.assertEqual((window['status'], window['usable_remaining_percent']), ('historical', None))
        # Another failure keeps the same last good; a success replaces it.
        self.assertEqual(self.refresh()['last_good']['observed_at'], first['observed_at'])
        self.script_for()
        self.assertEqual(self.refresh()['state'], 'ok')

    def test_manual_readings_are_separate_and_untouched(self):
        manual = CapacityStore(self.project)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        manual.record('codex', 'five-hour', 300, 42, now.isoformat())
        before = Path(self.project, 'coord', 'capacity', 'readings.json').read_bytes()
        self.refresh()
        self.assertEqual(Path(self.project, 'coord', 'capacity', 'readings.json').read_bytes(), before)
        self.assertEqual(manual.show('codex')['groups']['codex']['windows']['five-hour']['source'], 'manual')
        # Manual validation stays strict: a provider source is still forged there.
        forged = json.loads(before)
        forged['groups']['codex']['five-hour']['source'] = 'codex'
        Path(self.project, 'coord', 'capacity', 'readings.json').write_text(json.dumps(forged))
        self.assertEqual(manual.show()['state'], 'invalid')


class StateRefusalTests(FakeServer):
    def test_corrupt_state_refuses_before_provider_and_is_not_overwritten(self):
        self.refresh()
        good = json.loads(self.state.read_text())
        os.unlink(self.log)
        bad_entry = json.loads(json.dumps(good))
        bad_entry['providers']['codex']['codex']['buckets']['codex']['windows']['primary']['used_percent'] = 'x'
        forged = json.loads(json.dumps(good))
        forged['providers']['codex']['codex']['source'] = 'manual'
        for raw in (b'{not json', b'{"schema_version": 1, "schema_version": 1, "providers": {}}',
                    b'{"schema_version": 1, "providers": {"claude": {}}}', json.dumps(bad_entry).encode(),
                    json.dumps(forged).encode(), b' ' * (pc.MAX_STATE_BYTES + 1)):
            with self.subTest(raw=raw[:24]):
                self.state.write_bytes(raw)
                with self.assertRaises(CapacityError):
                    self.refresh()
                self.assertEqual(self.state.read_bytes(), raw)
                self.assertEqual(self.store.show()['state'], 'invalid')
        self.assertEqual(self.received(), [])

    def test_extreme_stored_values_are_invalid_without_traceback(self):
        # Reproduced at 3db60aa: 100.000001 remaining was usable and a year-9999
        # attempt time overflowed attempted+CLOCK_SKEW instead of refusing.
        self.refresh()
        good = json.loads(self.state.read_text())
        os.unlink(self.log)

        def forged(change):
            data = json.loads(json.dumps(good))
            change(data['providers']['codex']['codex'])
            return json.dumps(data).encode()

        def primary(entry):
            return entry['buckets']['codex']['windows']['primary']

        cases = {
            'remaining_above_100': lambda e: primary(e).update(used_percent=0.0, remaining_percent=100.000001),
            'remaining_below_0': lambda e: primary(e).update(used_percent=100.0, remaining_percent=-0.000001),
            'attempt_year_9999': lambda e: e.update(attempted_at='9999-12-31T23:59:59+00:00'),
            'observed_year_9999': lambda e: e.update(observed_at='9999-12-31T23:59:59+00:00'),
            'observed_year_0001': lambda e: e.update(observed_at='0001-01-01T00:00:00+00:00'),
            'reset_far_future': lambda e: primary(e).update(reset_at='2099-12-31T00:00:00+00:00'),
            'reset_year_9999': lambda e: primary(e).update(reset_at='9999-12-31T23:59:59+00:00'),
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                raw = forged(change)
                self.state.write_bytes(raw)
                view = self.store.show('codex', now=datetime.now(timezone.utc))
                self.assertEqual(view['state'], 'invalid')
                self.assertEqual(view['groups']['codex']['buckets'], {})
                with self.assertRaises(CapacityError):
                    self.refresh()
                self.assertEqual(self.state.read_bytes(), raw)
                tool = subprocess.run([sys.executable, '-B', str(TOOL), '--project', self.project, 'show',
                                       '--provider', 'codex', '--json'],
                                      capture_output=True, text=True, timeout=20)
                self.assertNotIn('Traceback', tool.stderr)
                self.assertEqual(json.loads(tool.stdout)['state'], 'invalid')
        # A forged last-good far-future reset is refused the same way.
        self.state.write_bytes(json.dumps(good).encode())
        self.script_for(account={'account': None, 'requiresOpenaiAuth': True})
        self.refresh()
        failed = json.loads(self.state.read_text())
        last = failed['providers']['codex']['codex']['last_good']
        last['buckets']['codex']['windows']['primary']['reset_at'] = '2099-12-31T00:00:00+00:00'
        self.state.write_text(json.dumps(failed))
        self.assertEqual(self.store.show()['state'], 'invalid')

    def test_symlinked_paths_are_refused(self):
        outside = os.path.join(self.root, 'outside')
        os.mkdir(outside)
        Path(outside, 'providers.json').write_text('{}')
        os.makedirs(self.state.parent)
        self.state.symlink_to(os.path.join(outside, 'providers.json'))
        with self.assertRaises(CapacityError):
            self.refresh()
        self.assertEqual(self.store.show()['state'], 'invalid')
        self.state.unlink()
        hardlink = os.path.join(outside, 'hard.json')
        Path(hardlink).write_text('{}')
        os.link(hardlink, self.state)
        with self.assertRaises(CapacityError):
            self.refresh()
        self.state.unlink()
        linked = os.path.join(self.root, 'linked')
        os.makedirs(os.path.join(linked))
        os.symlink(outside, os.path.join(linked, 'coord'))
        with self.assertRaises(CapacityError):
            pc.ProviderStore(linked).refresh('codex', self.binary, env=self.env)
        self.assertEqual(sorted(os.listdir(outside)), ['hard.json', 'providers.json'])
        with self.assertRaises(CapacityError):
            pc.ProviderStore(os.path.join(self.root, 'missing'))
        self.assertEqual(self.received(), [])

    def test_bad_labels_and_timeouts_refused_without_writes(self):
        for kwargs in ({'group': '$(id)'}, {'timeout': 0}, {'timeout': 31}, {'timeout': True and 'x'}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(CapacityError):
                    self.refresh(**kwargs)
        self.assertFalse(Path(self.project, 'coord').exists())


class CliTests(FakeServer):
    def test_manual_paths_never_load_the_provider_module(self):
        probe = ('import importlib.util, sys\n'
                 'spec = importlib.util.spec_from_file_location("cli", sys.argv[1])\n'
                 'cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)\n'
                 'code = cli.main(sys.argv[2:])\n'
                 'print("LOADED" if "bridge.provider_capacity" in sys.modules else "MANUAL-ONLY")\n')
        observed = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        for args in (('record', '--group', 'codex', '--window', 'five-hour', '--window-minutes', '300',
                      '--remaining-percent', '42', '--observed-at', observed), ('show',), ('show', '--json')):
            result = subprocess.run([sys.executable, '-B', '-c', probe, str(TOOL), '--project', self.project, *args],
                                    capture_output=True, text=True, timeout=30)
            self.assertTrue(result.stdout.endswith('MANUAL-ONLY\n'), result.stdout + result.stderr)
        result = subprocess.run([sys.executable, '-B', '-c', probe, str(TOOL), '--project', self.project, 'show',
                                 '--provider', 'codex'], capture_output=True, text=True, timeout=30)
        self.assertTrue(result.stdout.endswith('LOADED\n'), result.stdout + result.stderr)

    def run_tool(self, *args, code=0, env=None):
        result = subprocess.run([sys.executable, '-B', str(TOOL), '--project', self.project, *args],
                                capture_output=True, text=True, timeout=30, env=env or self.env)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def test_refresh_and_show_roundtrip_and_unsupported_providers(self):
        env = dict(self.env, **{pc.TEST_BINARY_ENV: self.binary})
        self.assertIn('Refreshed codex/codex', self.run_tool('refresh', 'codex', '--group', 'codex', env=env).stdout)
        view = json.loads(self.run_tool('show', '--provider', 'codex', '--group', 'codex', '--json').stdout)
        self.assertEqual(view['groups']['codex']['buckets']['codex']['windows']['primary']['usable_remaining_percent'],
                         70.0)
        self.assertIn('usable now 70%', self.run_tool('show', '--provider', 'codex').stdout)
        other = json.loads(self.run_tool('show', '--provider', 'claude', '--json').stdout)
        self.assertEqual(other['state'], 'unsupported')
        self.assertIn('only codex', self.run_tool('refresh', 'claude', '--group', 'c', env=env, code=1).stderr)
        relative = dict(self.env, **{pc.TEST_BINARY_ENV: 'fake'})
        self.assertIn(pc.TEST_BINARY_ENV, self.run_tool('refresh', 'codex', '--group', 'c', env=relative,
                                                         code=1).stderr)
        self.script_for(account={'account': None})
        failed = self.run_tool('refresh', 'codex', '--group', 'codex', env=env, code=1)
        self.assertIn('Unknown (not_signed_in)', failed.stdout)
        self.assertIn('historical', self.run_tool('show', '--provider', 'codex').stdout)

    def test_manual_show_output_is_unchanged_by_provider_state(self):
        env = dict(self.env, **{pc.TEST_BINARY_ENV: self.binary})
        before = self.run_tool('show', '--json').stdout
        self.run_tool('refresh', 'codex', '--group', 'codex', env=env)
        after = self.run_tool('show', '--json').stdout
        strip = lambda text: {k: v for k, v in json.loads(text).items() if k != 'checked_at'}  # noqa: E731
        self.assertEqual(strip(before), strip(after))
        self.assertEqual(strip(after), {'schema_version': 1, 'max_age_seconds': 900, 'state': 'missing',
                                        'error': None, 'groups': {}})


if __name__ == '__main__':
    unittest.main()
