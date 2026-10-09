#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Installed `unio capacity` from a copied standalone installer; no live AI calls.

The storage matrix lives in bridge/tests/capacity_test.py; this file checks
the packaged command, its project selection and the installer boundaries.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parent.parent
# find_root never treats / as a workspace, so / is outside any workspace even
# when the scratch directory itself lies inside one.
OUTSIDE = '/'
EMBEDDED = {'bridge/capacity.py': (SOURCE / 'bridge' / 'capacity.py').read_bytes(),
            'tools/capacity-readings.py': (SOURCE / 'tools' / 'capacity-readings.py').read_bytes()}


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class InstalledCapacityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='unio capacity ')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.conf = self.base / 'configuration with spaces'
        self.bin = self.base / 'bin with spaces'
        self.conf.mkdir()
        self.provider_marker = self.base / 'provider unexpectedly called'
        self.config = ('mock=touch ' + shlex.quote(str(self.provider_marker)) + '\n').encode()
        (self.conf / 'agents.conf').write_bytes(self.config)
        self.installer = self.base / 'standalone installer.sh'
        shutil.copyfile(SOURCE / 'unio-install.sh', self.installer)
        self.decoy_marker = self.base / 'wrong engine or module called'
        decoys = self.base / 'decoy bin'
        (decoys / 'bridge').mkdir(parents=True)
        decoy = decoys / 'unio'
        decoy.write_text('#!/bin/sh\ntouch ' + shlex.quote(str(self.decoy_marker)) + '\nexit 93\n')
        decoy.chmod(0o755)
        # A planted package on PYTHONPATH must never replace the installed store.
        (decoys / 'bridge' / '__init__.py').write_text('')
        (decoys / 'bridge' / 'capacity.py').write_text(
            'open(' + repr(str(self.decoy_marker)) + ', "w").close()\n')
        self.env = dict(os.environ, UNIO_BIN_DIR=str(self.bin), UNIO_CONF_DIR=str(self.conf),
                        UNIO_COMPLETION_DIR=str(self.base / 'completion with spaces'),
                        UNIO_AUTO_VERIFY='0', UNIO_AUTO_OFF='0', UNIO_AUTO_SYNC='0',
                        PATH=str(decoys) + os.pathsep + os.environ['PATH'],
                        PYTHONPATH=str(decoys))
        self.install()
        self.engine = self.bin / 'unio'
        self.payload = self.conf / 'lib' / 'capacity'
        self.neutral = self.base / 'neutral cwd'
        self.neutral.mkdir()
        # A module planted in the working directory must not be imported either.
        (self.neutral / 'json.py').write_text('open(' + repr(str(self.decoy_marker)) + ', "w").close()\n')
        self.project = self.base / 'selected project'
        self.project.mkdir()
        self.state = self.project / 'coord' / 'capacity' / 'readings.json'

    def tearDown(self):
        self.assertFalse(self.provider_marker.exists(), 'provider dispatched')
        self.assertFalse(self.decoy_marker.exists(), 'decoy engine or module used')

    def install(self, code=0):
        result = subprocess.run(['bash', str(self.installer)], cwd=self.base, env=self.env,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def unio(self, *args, cwd=None, code=0):
        cwd = cwd or self.neutral
        # Pass the logical directory, as an interactive shell would.
        env = dict(self.env, PWD=str(cwd))
        result = subprocess.run([str(self.engine), *args], cwd=cwd, env=env,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        return result

    def record(self, *prefix, cwd=None, code=0, group='codex', percent='42'):
        return self.unio('capacity', *prefix, 'record', '--group', group, '--window', 'five-hour',
                         '--window-minutes', '300', '--remaining-percent', percent,
                         '--observed-at', now_iso(), cwd=cwd, code=code)

    def show(self, *prefix, cwd=None, code=0):
        return json.loads(self.unio('capacity', *prefix, 'show', '--group', 'codex', '--json',
                                    cwd=cwd, code=code).stdout)

    def assert_embedded(self):
        for name, raw in EMBEDDED.items():
            self.assertEqual((self.payload / name).read_bytes(), raw, name)
        self.assertEqual(sorted(p.name for p in self.payload.iterdir()), ['bridge', 'tools'])

    def test_native_help_version_and_exact_payload(self):
        self.assert_embedded()
        self.assertTrue(self.unio('version').stdout.startswith('Unio 0.5.7 '))
        self.assertIn('unio capacity [--project DIR] record|show', self.unio('help').stdout)
        for args in (('capacity',), ('capacity', '--help'), ('capacity', 'record', '--help')):
            with self.subTest(args=args):
                shown = self.unio(*args, cwd=OUTSIDE)
                self.assertIn('usage: unio capacity', shown.stdout)
        self.assertIn('--remaining-percent', shown.stdout)
        subprocess.run(['bash', '-n', str(self.engine)], check=True)
        if shutil.which('shellcheck'):
            subprocess.run(['shellcheck', '-S', 'warning', str(self.engine)], check=True)

    def test_explicit_project_roundtrip_from_neutral_cwd(self):
        done = self.record('--project', str(self.project))
        self.assertIn('Recorded manual reading codex/five-hour', done.stdout)
        reading = self.show('--project', str(self.project))['groups']['codex']['windows']['five-hour']
        self.assertEqual((reading['source'], reading['status'], reading['last_reading_remaining_percent'],
                          reading['usable_remaining_percent']), ('manual', 'fresh', 42.0, 42.0))
        self.assertIn('Usable now: 42%', self.unio('capacity', '--project=' + str(self.project), 'show').stdout)
        self.assertEqual(self.show('--project', str(self.base / 'neutral cwd'))['state'], 'missing')

    def test_initialized_workspace_supplies_project_root(self):
        workspace = self.base / 'workspace root'
        nested = workspace / 'repo' / 'nested dir'
        for part in (nested, workspace / 'wt' / 'codex', workspace / 'coord'):
            part.mkdir(parents=True)
        self.record(cwd=nested)
        self.assertTrue((workspace / 'coord' / 'capacity' / 'readings.json').is_file())
        self.assertFalse((nested / 'coord').exists())
        # A symlinked cwd selects the same physical root the store accepts.
        alias = self.base / 'workspace alias'
        alias.symlink_to(workspace, target_is_directory=True)
        self.assertNotEqual((alias / 'repo').resolve(), alias / 'repo')
        view = self.show(cwd=alias / 'repo')
        self.assertEqual(view['groups']['codex']['windows']['five-hour']['status'], 'fresh')
        # An explicit project still wins inside a workspace.
        self.record('--project', str(self.project), cwd=nested, group='claude')
        self.assertEqual(list(json.loads(self.state.read_text())['groups']), ['claude'])

    def test_missing_project_and_bad_arguments_fail_before_writes(self):
        missing = self.unio('capacity', 'show', cwd=OUTSIDE, code=1)
        self.assertIn('--project PATH', missing.stderr)
        self.record(cwd=OUTSIDE, code=1)
        for args in (('--proj', str(self.project), 'show'),
                     ('--project', str(self.project), 'show', '--bogus'),
                     ('--project', str(self.project), 'record', '--group', 'codex', '--source', 'provider'),
                     ('--project', str(self.project), 'remove')):
            with self.subTest(args=args):
                self.unio('capacity', *args, code=2)
        # Input is data: a shell-looking label is refused, never evaluated.
        hostile = '$(touch ' + shlex.quote(str(self.provider_marker)) + ')'
        refused = self.record('--project', str(self.project), group=hostile, code=1)
        self.assertIn('unio capacity: refused', refused.stderr)
        self.record('--project', str(self.project), percent='nan', code=1)
        self.assertFalse((self.project / 'coord').exists())
        self.assertEqual(list(self.neutral.iterdir()), [self.neutral / 'json.py'])

    def test_corrupt_forged_and_symlinked_state_is_refused(self):
        self.state.parent.mkdir(parents=True)
        forged = {'schema_version': 1, 'groups': {'codex': {'five-hour': {
            'source': 'provider', 'window_minutes': 300, 'remaining_percent': 9999,
            'observed_at': now_iso()}}}}
        for raw in (b'{not json', json.dumps(forged).encode()):
            with self.subTest(raw=raw[:12]):
                self.state.write_bytes(raw)
                view = self.show('--project', str(self.project), code=1)
                self.assertEqual((view['state'], view['groups']['codex']['status']), ('invalid', 'unknown'))
                self.record('--project', str(self.project), code=1)
                self.assertEqual(self.state.read_bytes(), raw)
        outside = self.base / 'outside coord'
        outside.mkdir()
        linked = self.base / 'linked project'
        linked.mkdir()
        (linked / 'coord').symlink_to(outside, target_is_directory=True)
        self.record('--project', str(linked), code=1)
        alias = self.base / 'project alias'
        alias.symlink_to(self.project, target_is_directory=True)
        self.assertIn('symlinks', self.record('--project', str(alias), code=1).stderr)
        self.assertEqual(list(outside.iterdir()), [])

    def test_reinstall_preserves_readings_config_and_bytes(self):
        self.record('--project', str(self.project))
        state = self.state.read_bytes()
        (self.payload / 'tools' / 'capacity-readings.py').write_text('tampered\n')
        self.install()
        self.assert_embedded()
        self.assertEqual(self.state.read_bytes(), state)
        self.assertEqual((self.conf / 'agents.conf').read_bytes(), self.config)
        self.assertFalse((self.conf / 'coord').exists())
        self.assertEqual(self.show('--project', str(self.project))['state'], 'ok')

    def test_unsafe_destinations_are_refused_before_replacement(self):
        outside = self.base / 'outside payload'
        outside.mkdir()
        victim = outside / 'capacity.py'
        victim.write_text('outside\n')
        store = self.payload / 'bridge' / 'capacity.py'
        cases = {
            'directory symlink': lambda: (shutil.rmtree(self.payload / 'bridge'),
                                          (self.payload / 'bridge').symlink_to(outside)),
            'file symlink': lambda: (store.unlink(), store.symlink_to(victim)),
            'hardlink': lambda: (store.unlink(), os.link(victim, store)),
            'non-regular file': lambda: (store.unlink(), store.mkdir()),
            'non-directory': lambda: (shutil.rmtree(self.payload / 'tools'),
                                      (self.payload / 'tools').write_text('file\n')),
        }
        for name, arrange in cases.items():
            with self.subTest(name=name):
                cli = self.payload / 'tools' / 'capacity-readings.py'
                if cli.is_file():
                    cli.write_text('old cli\n')
                arrange()
                refused = self.install(code=1)
                self.assertIn('refusing unsafe capacity', refused.stderr)
                self.assertEqual(victim.read_text(), 'outside\n')
                if name != 'non-directory':
                    self.assertEqual(cli.read_text(), 'old cli\n')
                for path in (self.payload / 'bridge', self.payload / 'tools'):
                    if path.is_symlink() or not path.is_dir():
                        path.unlink()
                    else:
                        shutil.rmtree(path)
                self.install()
                self.assert_embedded()


if __name__ == '__main__':
    unittest.main()
