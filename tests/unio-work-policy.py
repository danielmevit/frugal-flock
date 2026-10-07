#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Work-policy command/state slice: modes, tiers, lead/account, persistence.

Mock-only. Installs under a temporary directory, drives a mock project
whose path contains spaces, and exercises defaults, every enum switch,
persistence, lead/account grouping, invalid arguments, malformed/unsafe/
oversized state, preserved custom roles and the packaged guide. No real
provider is called: `unio run` is never invoked.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(__file__).resolve().parent.parent
passed = [0]


def check(label, condition=True):
    if not condition:
        print('FAIL ' + label)
        sys.exit(1)
    passed[0] += 1
    print('  ok %s' % label)


with tempfile.TemporaryDirectory(prefix='work-policy-') as directory:
    base = Path(directory)
    env = dict(os.environ, UNIO_BIN_DIR=str(base / 'bin'),
               UNIO_CONF_DIR=str(base / 'conf'),
               UNIO_COMPLETION_DIR=str(base / 'completion'),
               GIT_AUTHOR_NAME='mock', GIT_COMMITTER_NAME='mock',
               GIT_AUTHOR_EMAIL='mock@example.invalid',
               GIT_COMMITTER_EMAIL='mock@example.invalid',
               UNIO_AUTO_VERIFY='0', UNIO_AUTO_SYNC='0', UNIO_AUTO_OFF='0',
               UNIO_TIMEOUT='20', UNIO_VERIFY_TIMEOUT='10')
    subprocess.run(['bash', str(source / 'unio-install.sh')], env=env,
                   check=True, capture_output=True)
    at = str(base / 'bin' / 'unio')
    # Mock project path with spaces exercises quoting through every command.
    root = base / 'mock project'
    repo = root / 'repo'
    repo.mkdir(parents=True)

    def git(*args):
        return subprocess.run(['git', *args], cwd=repo, env=env,
                              check=True, capture_output=True)

    def unio(*args, cwd=None):
        return subprocess.run([at, *args], cwd=cwd or repo, env=env,
                              capture_output=True, text=True)

    git('init', '-q', '-b', 'main')
    (repo / 'seed.txt').write_text('seed\n')
    git('add', 'seed.txt')
    git('commit', '-qm', 'seed')
    # Custom owner content must survive init with one policy reference.
    (repo / 'MASTER.md').write_text('# Custom owner instructions\n')
    init = unio('init', 'mock')
    check('init exits 0', init.returncode == 0)
    check('init displays default policy',
          'mode: medium' in init.stdout and 'tier: low' in init.stdout)
    master = (repo / 'MASTER.md').read_text()
    check('custom MASTER.md preserved', '# Custom owner instructions' in master)
    check('policy reference added once', master.count('UNIO-WORK-POLICY') == 1)
    guide = root / 'coord' / 'docs' / 'WORK-MODES.md'
    check('installed guide packaged',
          guide.is_file() and 'advisory' in guide.read_text())
    rerun = unio('init', 'mock')
    check('init is idempotent',
          rerun.returncode == 0
          and (repo / 'MASTER.md').read_text().count('UNIO-WORK-POLICY') == 1)

    state_file = root / 'coord' / 'work-policy.json'
    check('missing state means defaults',
          'mode: medium' in unio('mode').stdout
          and 'tier: low' in unio('tier').stdout
          and 'lead: (none)' in unio('lead').stdout
          and 'accounts: (none)' in unio('account').stdout)

    human = unio('policy')
    check('human policy shows limits and advisory state',
          human.returncode == 0 and 'mode: medium' in human.stdout
          and 'tier: low' in human.stdout and 'capacity: unknown' in human.stdout
          and 'workflow_enforcement: advisory' in human.stdout)
    doc = json.loads(unio('policy', '--json').stdout)
    check('policy JSON matches the frozen schema',
          doc['schema_version'] == 1 and doc['mode'] == 'medium'
          and doc['tier'] == 'low' and doc['lead_agent'] is None
          and doc['accounts'] == {} and doc['workflow_limit_per_group'] == 1
          and doc['capacity'] == 'unknown'
          and doc['workflow_enforcement'] == 'advisory')

    for mode in ('yolo', 'medium', 'safe'):
        out = unio('mode', mode)
        check('mode switch ' + mode,
              out.returncode == 0 and out.stdout.strip() == 'mode: ' + mode
              and unio('mode').stdout.strip() == 'mode: ' + mode)
    for tier, limit in (('low', 1), ('medium', 2), ('high', 4)):
        out = unio('tier', tier)
        check('tier switch %s persists with limit %d' % (tier, limit),
              out.returncode == 0 and out.stdout.strip() == 'tier: ' + tier
              and json.loads(unio('policy', '--json').stdout)['workflow_limit_per_group'] == limit)
    saved = json.loads(state_file.read_text())
    check('state file is exact typed schema',
          saved['schema_version'] == 1 and type(saved['schema_version']) is int
          and saved['mode'] == 'medium' and saved['tier'] == 'high'
          and saved['lead_agent'] is None and saved['accounts'] == {}
          and type(saved['updated_at']) is str)

    check('lead registers', unio('lead', 'codex').stdout.strip() == 'lead: codex'
          and unio('lead').stdout.strip() == 'lead: codex')
    check('lead reservation recorded in JSON',
          json.loads(unio('policy', '--json').stdout)['lead_agent'] == 'codex')
    check('lead clears with none', unio('lead', 'none').stdout.strip() == 'lead: (none)')
    check('account groups aliases',
          unio('account', 'opencode', 'go-primary').returncode == 0
          and unio('account', 'glm', 'go-primary').returncode == 0
          and 'opencode=go-primary' in unio('account').stdout
          and 'glm=go-primary' in unio('account').stdout)
    check('account grouping recorded in JSON',
          json.loads(unio('policy', '--json').stdout)['accounts']
          == {'glm': 'go-primary', 'opencode': 'go-primary'})
    unio('mode', 'medium')
    unio('tier', 'low')

    good = state_file.read_bytes()

    def fails_unchanged(label, args):
        out = unio(*args)
        check(label, out.returncode != 0 and state_file.read_bytes() == good)

    fails_unchanged('invalid mode rejected', ('mode', 'turbo'))
    fails_unchanged('surplus mode args rejected', ('mode', 'yolo', 'extra'))
    fails_unchanged('invalid tier rejected', ('tier', 'ultra'))
    fails_unchanged('surplus tier args rejected', ('tier', 'low', 'extra'))
    fails_unchanged('invalid lead label rejected', ('lead', 'bad name'))
    fails_unchanged('surplus lead args rejected', ('lead', 'codex', 'extra'))
    fails_unchanged('single account arg rejected', ('account', 'opencode'))
    fails_unchanged('triple account args rejected', ('account', 'a', 'b', 'c'))
    fails_unchanged('bad account group rejected', ('account', 'opencode', '-x'))
    fails_unchanged('unknown policy flag rejected', ('policy', '--yaml'))
    fails_unchanged('surplus policy args rejected', ('policy', '--json', 'extra'))

    def fails_state_unchanged(label, payload):
        state_file.write_bytes(payload)
        out = unio('policy')
        check(label, out.returncode != 0 and state_file.read_bytes() == payload)
        state_file.write_bytes(good)

    fails_state_unchanged('garbage state fails locally', b'not json\n')
    fails_state_unchanged('duplicate keys rejected',
                          b'{"schema_version":1,"mode":"medium","mode":"yolo",'
                          b'"tier":"low","lead_agent":null,"accounts":{}}')
    fails_state_unchanged('unknown keys rejected',
                          b'{"schema_version":1,"mode":"medium","tier":"low",'
                          b'"lead_agent":null,"accounts":{},"quota":9}')
    fails_state_unchanged('unknown schema rejected',
                          b'{"schema_version":2,"mode":"medium","tier":"low",'
                          b'"lead_agent":null,"accounts":{}}')
    fails_state_unchanged('invalid enum rejected',
                          b'{"schema_version":1,"mode":"turbo","tier":"low",'
                          b'"lead_agent":null,"accounts":{}}')
    fails_state_unchanged('wrong lead type rejected',
                          b'{"schema_version":1,"mode":"medium","tier":"low",'
                          b'"lead_agent":7,"accounts":{}}')
    big = {'schema_version': 1, 'mode': 'medium', 'tier': 'low',
           'lead_agent': None, 'accounts': {}, 'updated_at': 'x' * 70000}
    fails_state_unchanged('oversized state refused', json.dumps(big).encode())
    link = state_file.with_suffix('.link')
    link.write_bytes(good)
    state_file.unlink()
    try:
        state_file.symlink_to(link)
        out = unio('policy')
        check('symlink state refused without reset',
              out.returncode != 0 and state_file.is_symlink())
    finally:
        state_file.unlink(missing_ok=True)
        state_file.write_bytes(good)
    hard = root / 'coord' / 'work-policy-hard.json'
    hard.write_bytes(good)
    state_file.unlink()
    try:
        os.link(hard, state_file)
        out = unio('policy')
        check('hardlinked state refused without reset', out.returncode != 0)
    finally:
        state_file.unlink(missing_ok=True)
        state_file.write_bytes(good)
        hard.unlink(missing_ok=True)
    fifo = root / 'coord' / 'work-policy-fifo'
    if not fifo.exists():
        os.mkfifo(fifo)
    state_file.unlink()
    try:
        os.rename(fifo, state_file)
        out = subprocess.run([at, 'policy'], cwd=repo, env=env,
                             capture_output=True, text=True, timeout=20)
        check('nonregular state refused without reset', out.returncode != 0)
    finally:
        try:
            os.unlink(state_file)
        except OSError:
            pass
        state_file.write_bytes(good)

    status = unio('status')
    check('status displays policy',
          status.returncode == 0 and 'mode: medium' in status.stdout)
    check('help documents the switches',
          'unio mode [yolo|medium|safe]' in unio('help').stdout
          and 'unio policy [--json]' in unio('help').stdout)
    completion = (base / 'completion' / 'unio').read_text()
    check('completion offers switches and values',
          'mode tier lead account policy' in completion
          and 'yolo medium safe' in completion
          and 'low medium high' in completion)
    check('fresh guide still installed', guide.is_file())

print('work-policy: %d checks passed' % passed[0])
