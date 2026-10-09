#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Installed `unio capacity refresh codex` from a copied standalone installer.

A fake metadata executable is selected only through the explicit
UNIO_CAPACITY_TEST_CODEX injection; no live provider is ever called. The
normalization matrix lives in bridge/tests/provider_capacity_test.py.
"""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import time
import unittest

SOURCE = Path(__file__).resolve().parent.parent
EMBEDDED = {name: (SOURCE / name).read_bytes() for name in
            ('bridge/capacity.py', 'bridge/provider_capacity.py', 'tools/capacity-readings.py')}
RESET = int(time.time()) + 3600
FAKE = '''#!/usr/bin/env python3
import json, os, sys
log = open(os.environ["FAKE_LOG"], "a")
log.write(json.dumps({"argv": sys.argv[1:], "cwd": os.getcwd()}) + "\\n")
sys.stderr.write("secret.person@example.com sk-live-TOPSECRET\\n")
results = {
    "initialize": {"userAgent": "fake"},
    "account/read": {"account": {"type": "chatgpt", "email": "secret.person@example.com",
                                 "planType": "pro"}, "requiresOpenaiAuth": True},
    "account/rateLimits/read": {"rateLimitsByLimitId": {"codex": {
        "primary": {"usedPercent": 25, "windowDurationMins": 300, "resetsAt": RESET},
        "secondary": None}}},
}
if os.environ.get("FAKE_SIGNED_OUT"):
    results["account/read"] = {"account": None, "requiresOpenaiAuth": True}
for line in sys.stdin:
    message = json.loads(line)
    log.write(json.dumps({"method": message["method"]}) + "\\n"); log.flush()
    if "id" in message:
        print(json.dumps({"id": message["id"], "result": results[message["method"]]}), flush=True)
'''.replace('RESET', str(RESET))


class InstalledProviderCapacityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='unio provider capacity ')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.conf = self.base / 'configuration with spaces'
        self.bin = self.base / 'bin with spaces'
        self.conf.mkdir()
        self.provider_marker = self.base / 'provider unexpectedly called'
        (self.conf / 'agents.conf').write_text('mock=touch ' + shlex.quote(str(self.provider_marker)) + '\n')
        self.installer = self.base / 'standalone installer.sh'
        shutil.copyfile(SOURCE / 'unio-install.sh', self.installer)
        # A `codex` on PATH that must never run unless refresh selects it.
        decoys = self.base / 'decoy bin'
        decoys.mkdir()
        self.path_marker = self.base / 'PATH codex called'
        decoy = decoys / 'codex'
        decoy.write_text('#!/bin/sh\ntouch ' + shlex.quote(str(self.path_marker)) + '\nexit 93\n')
        decoy.chmod(0o755)
        self.fake = self.base / 'fake metadata codex'
        self.fake.write_text(FAKE)
        self.fake.chmod(0o755)
        self.log = self.base / 'fake.log'
        self.env = dict(os.environ, UNIO_BIN_DIR=str(self.bin), UNIO_CONF_DIR=str(self.conf),
                        UNIO_COMPLETION_DIR=str(self.base / 'completion with spaces'),
                        UNIO_AUTO_VERIFY='0', UNIO_AUTO_OFF='0', UNIO_AUTO_SYNC='0',
                        PATH=str(decoys) + os.pathsep + os.environ['PATH'], PYTHONPATH=str(decoys),
                        FAKE_LOG=str(self.log))
        self.env.pop('UNIO_CAPACITY_TEST_CODEX', None)
        result = subprocess.run(['bash', str(self.installer)], cwd=self.base, env=self.env,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.engine = self.bin / 'unio'
        self.payload = self.conf / 'lib' / 'capacity'
        self.neutral = self.base / 'neutral cwd'
        self.neutral.mkdir()
        self.project = self.base / 'selected project'
        self.project.mkdir()

    def tearDown(self):
        self.assertFalse(self.provider_marker.exists(), 'configured agent dispatched')

    def unio(self, *args, code=0, inject=True, **extra):
        env = dict(self.env, PWD=str(self.neutral), **extra)
        if inject:
            env['UNIO_CAPACITY_TEST_CODEX'] = str(self.fake)
        result = subprocess.run([str(self.engine), 'capacity', '--project', str(self.project), *args],
                                cwd=self.neutral, env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def calls(self):
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def test_payload_help_and_completion(self):
        for name, raw in EMBEDDED.items():
            self.assertEqual((self.payload / name).read_bytes(), raw, name)
        help_text = subprocess.run([str(self.engine), 'help'], env=self.env, capture_output=True, text=True,
                                   timeout=60).stdout
        self.assertIn('unio capacity [--project DIR] record|show|refresh', help_text)
        refresh_help = self.unio('refresh', '--help').stdout
        self.assertIn('never a model turn', refresh_help)
        completion = next((self.base / 'completion with spaces').iterdir()).read_text()
        self.assertIn('refresh) COMPREPLY=( $(compgen -W "codex --group --json --help"', completion)
        self.assertEqual(self.calls(), [])

    def test_installed_refresh_then_cached_show(self):
        stored = json.loads(self.unio('refresh', 'codex', '--group', 'codex', '--json').stdout)
        self.assertEqual((stored['source'], stored['state'], stored['account_kind']), ('codex', 'ok', 'chatgpt'))
        methods = [c['method'] for c in self.calls() if 'method' in c]
        self.assertEqual(methods, ['initialize', 'initialized', 'account/read', 'account/rateLimits/read'])
        start = self.calls()[0]
        self.assertEqual(start['cwd'], str(self.project / 'coord' / 'capacity' / 'codex-cwd'))
        before = self.log.read_bytes()
        # Show is cache-only: neither the injected fake nor PATH codex runs.
        view = json.loads(self.unio('show', '--provider', 'codex', '--group', 'codex', '--json',
                                    inject=False).stdout)
        window = view['groups']['codex']['buckets']['codex']['windows']['primary']
        self.assertEqual((window['status'], window['usable_remaining_percent']), ('fresh', 75.0))
        self.assertIsNone(view['groups']['codex']['buckets']['codex']['windows']['secondary'])
        self.assertEqual(self.log.read_bytes(), before)
        self.assertFalse(self.path_marker.exists())
        text = (self.project / 'coord' / 'capacity' / 'providers.json').read_text()
        for secret in ('secret.person', 'sk-live', 'planType', 'pro"'):
            self.assertNotIn(secret, text)
        # Manual readings stay a separate, unchanged document.
        manual = json.loads(self.unio('show', '--json').stdout)
        self.assertEqual((manual['state'], manual['groups']), ('missing', {}))
        self.assertFalse((self.project / 'coord' / 'capacity' / 'readings.json').exists())

    def test_failed_refresh_shows_unknown_and_historical_only(self):
        self.unio('refresh', 'codex', '--group', 'codex')
        failed = self.unio('refresh', 'codex', '--group', 'codex', code=1, FAKE_SIGNED_OUT='1')
        self.assertIn('Unknown (not_signed_in)', failed.stdout)
        view = json.loads(self.unio('show', '--provider', 'codex', '--json', inject=False).stdout)
        entry = view['groups']['codex']
        self.assertEqual((entry['state'], entry['buckets']), ('unknown', {}))
        last = entry['last_good']['buckets']['codex']['windows']['primary']
        self.assertEqual((last['status'], last['usable_remaining_percent']), ('historical', None))

    def test_path_codex_is_used_without_injection_and_failure_is_unknown(self):
        refused = self.unio('refresh', 'codex', '--group', 'codex', inject=False, code=1)
        self.assertTrue(self.path_marker.exists())
        self.assertIn('Unknown (', refused.stdout)
        self.assertNotIn('Traceback', refused.stderr)
        self.unio('refresh', 'gemini', '--group', 'gemini', code=1)
        self.assertEqual(self.calls(), [])


if __name__ == '__main__':
    unittest.main()
