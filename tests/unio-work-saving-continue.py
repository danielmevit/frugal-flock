#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Offline continuation through real native admission, supervision and checks.

No AI, network, global install or timer-suite replay. Every launch uses a local
stub and real worktrees; compare actual HEAD/index/bytes/modes and durable claims.
"""
import fcntl
import hashlib
import json
import os
import shlex
import signal
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent
passed = 0
if sys.argv[1:] not in ([], ['--prompt-only'], ['--remaining-only']):
    raise SystemExit('usage: unio-work-saving-continue.py [--prompt-only|--remaining-only]')
remaining_only = sys.argv[1:] == ['--remaining-only']


def check(label, condition):
    global passed
    assert condition, label
    passed += 1
    print('  ok ' + label, flush=True)


def until(predicate, seconds=40):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.1)
    raise AssertionError('fixture evidence did not arrive')


with tempfile.TemporaryDirectory(prefix='saving-continue-') as directory:
    base = Path(directory)
    env = dict(os.environ, UNIO_BIN_DIR=str(base / 'bin'), UNIO_CONF_DIR=str(base / 'conf'),
               UNIO_COMPLETION_DIR=str(base / 'completion'), UNIO_TIMEOUT='120',
               UNIO_AUTO_VERIFY='0', UNIO_AUTO_SYNC='0', UNIO_AUTO_OFF='0', GIT_OPTIONAL_LOCKS='0',
               GIT_AUTHOR_NAME='mock', GIT_COMMITTER_NAME='mock',
               GIT_AUTHOR_EMAIL='mock@example.invalid', GIT_COMMITTER_EMAIL='mock@example.invalid')
    for key in ('UNIO_SAVE_TEST_FAULT', 'BASH_ENV', 'RUN_CONTINUATION_CLAIM'):
        env.pop(key, None)
    subprocess.run(['bash', str(SOURCE / 'unio-install.sh')], env=env, check=True, capture_output=True)
    at = str(base / 'bin' / 'unio')
    root = base / 'project with spaces'
    repo = root / 'repo'
    repo.mkdir(parents=True)

    def git(cwd, *args):
        return subprocess.check_output(['git', *args], cwd=cwd, env=env, stderr=subprocess.DEVNULL)

    def unio(*args, extra=None, timeout=300):
        # The native provider may run for120s, plus bounded30s snapshots,
        # admission and final bookkeeping. The outer fixture must outlive it.
        started = time.monotonic()
        try:
            result = subprocess.run([at, *args], cwd=repo, env=dict(env, **(extra or {})),
                                    capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            # Preserve evidence if a later failure is a real lifecycle stall.
            print('fixture timeout: %r after %ss; stdout=%r; stderr=%r'
                  % (args, timeout, error.stdout, error.stderr), file=sys.stderr, flush=True)
            raise
        elapsed = time.monotonic() - started
        if elapsed >= 60:
            print('fixture duration: %r %.3fs, actual exit=%s'
                  % (args[:2], elapsed, result.returncode), flush=True)
        return result

    def good(run):
        assert run.returncode == 0, run.stdout + run.stderr
        return run

    git(repo, 'init', '-q', '-b', 'main')
    (repo / 'tracked').write_text('base\n')
    (repo / 'deleted').write_text('delete me\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'base')
    workers = ['mock-' + name for name in
               ('source', 'dest', 'other', 'unknown', 'budget', 'changed', 'fault',
                'signal', 'success', 'prompt', 'clean', 'clean-dest')]
    good(unio('init', *workers))
    coord, wt = root / 'coord', root / 'wt'
    tasks = coord / 'tasks'
    calls = base / 'calls'
    provider = base / 'provider.py'
    provider.write_text(r'''
import json, os, subprocess, time
from pathlib import Path
base = Path(os.environ['CONTINUE_FIXTURE'])
case = os.environ['CONTINUE_CASE']
with (base / 'calls').open('a') as out: out.write(case + '\n')
paths = subprocess.check_output(['git', 'ls-files', '-c', '-o', '--exclude-standard', '-z']).split(b'\0')
files = {}
for raw in set(paths) - {b''}:
    p = Path(os.fsdecode(raw))
    if p.is_file(): files[os.fsdecode(raw)] = [p.stat().st_mode & 0o777, p.read_bytes().hex()]
fds = []
for p in Path('/proc/self/fd').iterdir():
    try: fds.append(os.readlink(p))
    except OSError: pass
lineage, pid = [], os.getpid()
for _ in range(5):
    lineage.append(pid)
    pid = int(Path('/proc/%d/status' % pid).read_text().split('PPid:\t')[1].splitlines()[0])
(base / (case + '.json')).write_text(json.dumps(dict(
    head=subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode(),
    index=subprocess.check_output(['git', 'ls-files', '-s', '-z']).hex(), files=files,
    orders=Path(os.environ['TASKFILE']).read_text(),
    original=Path(os.environ['UNIO_ORIGINAL_TASKFILE']).read_text(), fds=fds, pids=lineage)))
(base / (case + '-started')).touch()
if case == 'signal':
    while True: time.sleep(1)
raise SystemExit(0 if case in ('success', 'clean') else 23)
''')
    (base / 'conf' / 'agents.conf').write_text('mock=python3 ' + shlex.quote(str(provider)) + '\n')
    env.update(CONTINUE_FIXTURE=str(base), CONTINUE_CASE='source')
    old = tasks / 'OLD.md'
    old.write_text('# OLD\nOriginal failed task; this is literal context only.\n'
                   '## Allowed scope\n- *\n## Validate\n$ false\n')
    orders = ('# NEW\nSeparately authorized recovery task.\n## Allowed scope\n- *\n'
              '## Validate\n$ test "$(git show :tracked)" = staged\n'
              '$ test "$(cat tracked)" = unstaged\n')
    (tasks / 'NEW.md').write_text(orders)
    (tasks / 'OTHER.md').write_text(orders.replace('# NEW', '# OTHER'))
    for name in ('UNKNOWN', 'BUDGET', 'CHANGED', 'FAULT', 'SIGNAL', 'SUCCESS', 'PROMPT'):
        (tasks / (name + '.md')).write_text(orders.replace('# NEW', '# ' + name))
    source = wt / 'mock-source'
    (source / 'committed').write_text('carried commit\n')
    git(source, 'add', 'committed')
    git(source, 'commit', '-qm', 'unfinished feature checkpoint')
    (source / 'tracked').write_text('staged\n')
    git(source, 'add', 'tracked')
    (source / 'tracked').write_text('unstaged\n')
    (source / 'deleted').unlink()
    (source / 'binary').write_bytes(b'\0\xff\x01')
    (source / 'empty').touch()
    (source / 'executable').write_text('#!/bin/sh\nexit 0\n')
    (source / 'executable').chmod(0o755)

    def view(path):
        names = set(git(path, 'ls-files', '-c', '-o', '--exclude-standard', '-z').split(b'\0'))
        files = {}
        for name in names - {b''}:
            p = path / os.fsdecode(name)
            if p.exists():
                files[os.fsdecode(name)] = [stat.S_IMODE(p.stat().st_mode), p.read_bytes().hex()]
        return dict(head=git(path, 'rev-parse', 'HEAD').decode(),
                    index=git(path, 'ls-files', '-s', '-z').hex(), files=files)

    def count():
        return len(calls.read_text().splitlines()) if calls.exists() else 0

    def claim(sid):
        docs = [json.loads(p.read_text()) for p in (coord / 'saves' / 'claims').glob('*.json')]
        return [d for d in docs if d['save_id'] == sid and d['new_task'] is not None]

    def save():
        good(unio('save', 'create', 'mock-source', 'OLD'))
        data = json.loads(good(unio('save', 'inspect', '--worker', 'mock-source', '--json')).stdout)
        return data['last_good']['save_id']

    def restore(sid, worker):
        good(unio('save', 'restore', sid, worker))
        check(worker + ' explicitly restores exact HEAD, full index and bytes/modes', view(wt / worker) == original)

    def continuing(sid, worker, task='NEW', **extra):
        return unio('save', 'continue', sid, worker, task, extra=extra)

    def refused(label, sid, worker='mock-dest', task='NEW', **extra):
        before = count()
        run = continuing(sid, worker, task, **extra)
        check(label + ': refused without another provider call', run.returncode != 0 and count() == before)
        return run

    def released(worker, case):
        with (coord / '.locks' / (worker + '.lock')).open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check(case + ' releases worker and account ownership',
              not json.loads(good(unio('policy', '--json')).stdout)['active_native_workflows'])
        info = json.loads((base / (case + '.json')).read_text())
        check(case + ' inherits no worker or account-control descriptors',
              not any('/coord/.locks/' in p for p in info['fds']))
        def live(pid):
            try:
                return Path('/proc/%d/stat' % pid).read_text().rsplit(')', 1)[1].split()[0] != 'Z'
            except FileNotFoundError:
                return False
        check(case + ' provider, timeout, supervisor, native run and frontend are reaped',
              all(not live(pid) for pid in info['pids']))

    def exercise_prompt(prompt):
        restore(prompt, 'mock-prompt')
        wrapper_dir = base / 'python-wrapper'
        wrapper_dir.mkdir()
        wrapper = wrapper_dir / 'python3'
        real_python = subprocess.check_output(['which', 'python3'], env=env, text=True).strip()
        wrapper.write_text('#!/bin/bash\n'
                           'if [ "${3:-}" = _supervise ] && [ -n "${8:-}" ]; then\n'
                           '  printf "\\nunapproved prompt text\\n" >> "$MODIFY_PROMPT"\nfi\n'
                           'exec ' + shlex.quote(real_python) + ' "$@"\n')
        wrapper.chmod(0o755)
        run = refused('effective native prompt changed after task authorization', prompt, worker='mock-prompt',
                task='PROMPT', PATH=str(wrapper_dir) + os.pathsep + env['PATH'],
                MODIFY_PROMPT=str(coord / 'reports' / 'PROMPT.prompt.md'))
        check('fault changes effective prompt only and native authority check refuses it',
              'unapproved prompt text' in (coord / 'reports' / 'PROMPT.prompt.md').read_text()
              and 'effective continuation orders changed' in run.stderr
              and (tasks / 'PROMPT.md').read_text() == orders.replace('# NEW', '# PROMPT'))
        check('prompt refusal settles a failed claim without changed recovery bytes',
              claim(prompt)[0]['state'] == 'failed' and view(wt / 'mock-prompt') == original)


    def exercise_clean():
        # A clean recovered commit would ordinarily auto-merge the newer base.
        clean = wt / 'mock-clean'
        (clean / 'feature').write_text('recovered committed work\n')
        git(clean, 'add', 'feature')
        git(clean, 'commit', '-qm', 'clean recovered checkpoint')
        good(unio('save', 'create', 'mock-clean', 'OLD'))
        clean_sid = json.loads(good(unio('save', 'inspect', '--worker', 'mock-clean', '--json')).stdout)['last_good']['save_id']
        clean_before = view(clean)
        good(unio('save', 'restore', clean_sid, 'mock-clean-dest'))
        (repo / 'new-base').write_text('main advanced while source was offline\n')
        git(repo, 'add', 'new-base')
        git(repo, 'commit', '-qm', 'advance main')
        (tasks / 'CLEAN.md').write_text('# CLEAN\n## Allowed scope\n- *\n## Validate\n$ test -f feature\n')
        before = count()
        run = continuing(clean_sid, 'mock-clean-dest', task='CLEAN', CONTINUE_CASE='clean', UNIO_AUTO_SYNC='1')
        check('auto-sync enabled preserves clean restored commits with a newer main',
              run.returncode == 0 and count() == before + 1 and view(wt / 'mock-clean-dest') == clean_before
              and 'continuation skips auto-sync' in run.stdout and not (wt / 'mock-clean-dest' / 'new-base').exists())
        return clean_sid

    def finish(save_ids):
        check('original mixed source and raw index remain byte-for-byte unchanged',
              view(source) == original and source_index.read_bytes() == raw_index)
        # Main advancement makes freshness stale; the stored original evidence must stay identical.
        original_json = json.loads(original_result)
        current_json = json.loads(good(unio('result', 'mock-source', 'OLD')).stdout)
        check('original failed source process, checks and review evidence remain intact',
              all(current_json[k] == original_json[k] for k in ('process', 'validation', 'review')))
        check('claimed saves stay pinned and valid',
              all(good(unio('save', 'inspect', s, '--json')).returncode == 0
                  for s in save_ids))
        check('all native account slots are released',
              not json.loads(good(unio('policy', '--json')).stdout)['active_native_workflows'])

    good(unio('resume'))
    try:
        failed = unio('run', 'mock-source', 'OLD', extra=dict(UNIO_SAVE_TEST_FAULT='capture-launch'))
        check('preserve an actual failed source result', failed.returncode == 23)
        original_result = good(unio('result', 'mock-source', 'OLD')).stdout
        original = view(source)
        source_index = Path(git(source, 'rev-parse', '--path-format=absolute', '--git-path', 'index').decode().strip())
        raw_index = source_index.read_bytes()
        sid = save()
        if sys.argv[1:] == ['--prompt-only']:
            exercise_prompt(sid)
            clean_sid = exercise_clean()
            finish((sid, clean_sid))
            print('unio-work-saving-continue prompt/recovery: %d assertions passed' % passed)
            raise SystemExit(0)
        # Partial diagnostic only: the default release invocation runs all cases.
        prefix_saves = []
        if not remaining_only:
            good(unio('stop'))
            refused('STOP', sid)
            good(unio('resume'))
            refused('destination not restored', sid)
            restore(sid, 'mock-dest')
            refused('same original task is context, not new authority', sid, task='OLD')
            refused('source worker cannot be destination', sid, worker='mock-source')
            refused('missing task', sid, task='MISSING')
            for body in ('# no scope\n## Validate\n$ true\n',
                         '# no checks\n## Allowed scope\n- *\n',
                         '# whitespace\n## Allowed scope\n-   \n## Validate\n$   \n'):
                (tasks / 'BAD.md').write_text(body)
                refused('incomplete new orders', sid, task='BAD')
            (wt / 'mock-dest' / 'binary').write_bytes(b'changed')
            refused('changed recovered bytes', sid)
            (wt / 'mock-dest' / 'binary').write_bytes(b'\0\xff\x01')
            with (coord / '.locks' / 'mock-dest.lock').open('a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                refused('busy destination', sid)
                before = count()
                forged = unio('run', 'mock-dest', 'NEW', extra=dict(RUN_CONTINUATION_CLAIM='a' * 32))
                check('environment cannot bypass ordinary run lock', forged.returncode != 0 and count() == before)
            check('private bridge without inherited ownership refuses',
                  unio('_continue-run', 'mock-dest', 'NEW', 'a' * 32).returncode != 0)
            check('preflight refusals reserve no continuation', not claim(sid))

            before = count()
            run = continuing(sid, 'mock-dest', CONTINUE_CASE='failed', UNIO_AUTO_SYNC='1')
            check('one continuation preserves actual provider failure exit', run.returncode == 23 and count() == before + 1)
            info = json.loads((base / 'failed.json').read_text())
            check('provider receives exact recovered commit, staged/unstaged and working state',
                  {k: info[k] for k in original} == original)
            check('provider receives only current separately authorized orders',
                  info['original'] == orders and 'Separately authorized' in info['orders']
                  and 'Original failed task' not in info['orders'] and '$ false' not in info['orders'])
            doc = claim(sid)[0]
            check('called claim binds full task hash, worker, save and real exit',
                  len(claim(sid)) == 1 and doc['state'] == 'called' and doc['destination'] == 'mock-dest'
                  and doc['new_task'] == 'NEW' and doc['task_sha256'] == hashlib.sha256(orders.encode()).hexdigest()
                  and doc['outcome'] == dict(exit_code=23, reason='called'))
            result = json.loads(good(unio('result', 'mock-dest', 'NEW')).stdout)
            check('new failure has fresh process evidence and no inherited acceptance',
                  result['process']['exit_code'] == 23 and not result['ready_for_human_review'])
            released('mock-dest', 'failed')
            refused('same-task replay', sid)
            refused('different-task replay', sid, task='OTHER')
            restore(sid, 'mock-other')
            refused('different-destination replay', sid, worker='mock-other', task='OTHER')

            unknown = save()
            restore(unknown, 'mock-unknown')
            refused('lost launch after durable calling', unknown, worker='mock-unknown',
                    task='UNKNOWN', UNIO_SAVE_TEST_FAULT='continue-after-calling')
            check('uncertain launch is Unknown, never unclaimed', claim(unknown)[0]['state'] == 'unknown')
            refused('Unknown blocks replay under another task', unknown, worker='mock-unknown', task='OTHER')

            budget = save()
            restore(budget, 'mock-budget')
            good(unio('tier', 'low'))
            good(unio('lead', 'mock'))
            refused('current shared account occupied by lead', budget, worker='mock-budget', task='BUDGET')
            good(unio('lead', 'none'))
            check('admission refusal settles a durable failed claim without changing restored bytes',
                  claim(budget)[0]['state'] == 'failed' and view(wt / 'mock-budget') == original)
            refused('freeing account does not grant a replay', budget, worker='mock-budget')

            prefix_saves = [unknown, budget]

        changed = save()
        restore(changed, 'mock-changed')
        bash_env = base / 'change-task.sh'
        bash_env.write_text('if [ "${1:-}" = _continue-run ]; then\n'
                            '  printf "\\nchanged after authorization\\n" >> "$CHANGED_TASK"\nfi\n')
        refused('task changed between authorization and native entry', changed, worker='mock-changed',
                task='CHANGED', BASH_ENV=str(bash_env), CHANGED_TASK=str(tasks / 'CHANGED.md'))
        (tasks / 'CHANGED.md').write_text(orders.replace('# NEW', '# CHANGED'))
        check('changed-task refusal retains claim evidence', claim(changed)[0]['state'] == 'failed')
        refused('restoring task text does not reset claim', changed, worker='mock-changed')

        fault = save()
        restore(fault, 'mock-fault')
        refused('frontend launch failure', fault, worker='mock-fault', task='FAULT',
                UNIO_SAVE_TEST_FAULT='continue-before-native')
        check('frontend failure is durable failed evidence', claim(fault)[0]['state'] == 'failed')
        refused('frontend failure grants no retry', fault, worker='mock-fault')

        interrupted = save()
        restore(interrupted, 'mock-signal')
        proc = subprocess.Popen([at, 'save', 'continue', interrupted, 'mock-signal', 'SIGNAL'],
                                cwd=repo, env=dict(env, CONTINUE_CASE='signal'),
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            until(lambda: (base / 'signal-started').exists())
        finally:
            if proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
            stdout, stderr = proc.communicate(timeout=70)
        check('TERM forwards through frontend and preserves native exit', proc.returncode == 143)
        check('TERM settles known completion and final save',
              claim(interrupted)[0]['outcome'] == dict(exit_code=143, reason='called')
              and any(json.loads(p.read_text()).get('provider_exit') == 143
                      for p in (coord / 'saves').glob('*/manifest.json')))
        released('mock-signal', 'signal')
        refused('terminated task cannot replay', interrupted, worker='mock-signal')

        success = save()
        restore(success, 'mock-success')
        before = count()
        good(continuing(success, 'mock-success', task='SUCCESS', CONTINUE_CASE='success', UNIO_AUTO_VERIFY='1'))
        result = json.loads(good(unio('result', 'mock-success', 'SUCCESS')).stdout)
        check('automatic verification reuses inherited worker ownership without another launch', count() == before + 1)
        check('fresh new-task checks pass despite original task false check',
              result['process']['exit_code'] == 0 and result['validation']['state'] == 'passed'
              and not result['ready_for_human_review'])
        released('mock-success', 'success')

        prompt = save()
        exercise_prompt(prompt)

        clean_sid = exercise_clean()
        finish((sid, *prefix_saves, changed, fault, interrupted, success, prompt, clean_sid))
    finally:
        unio('stop')

print(('unio-work-saving-continue remaining-only (partial): ' if remaining_only
       else 'unio-work-saving-continue: ') + '%d assertions passed' % passed)
