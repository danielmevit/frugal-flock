#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Native work-policy guard regressions. Mock providers only."""
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

source = Path(__file__).resolve().parent.parent

passed = [0]

def check(label, condition=True, out=None):
    if not condition:
        print('FAIL ' + label)
        if out is not None:
            if hasattr(out, 'stdout'):
                print(out.stdout)
                print(out.stderr)
            else:
                print(out)
        sys.exit(1)
    passed[0] += 1
    print('  ok %s' % label)

with tempfile.TemporaryDirectory(prefix='work-policy-guard-') as directory:
    base = Path(directory)
    env = dict(os.environ, UNIO_BIN_DIR=str(base / 'bin'),
               UNIO_CONF_DIR=str(base / 'conf'),
               UNIO_COMPLETION_DIR=str(base / 'completion'),
               GIT_AUTHOR_NAME='mock', GIT_COMMITTER_NAME='mock',
               GIT_AUTHOR_EMAIL='mock@example.invalid',
               GIT_COMMITTER_EMAIL='mock@example.invalid',
               UNIO_AUTO_VERIFY='0', UNIO_AUTO_SYNC='0', UNIO_AUTO_OFF='0',
               UNIO_TIMEOUT='5', UNIO_REVIEW_TIMEOUT='5')
    subprocess.run(['bash', str(source / 'unio-install.sh')], env=env,
                   check=True, capture_output=True, timeout=60)
    at = str(base / 'bin' / 'unio')
    root = base / 'mock project'
    repo = root / 'repo'
    repo.mkdir(parents=True)

    owned = []
    open_streams = []

    def descendants(pid):
        found = []
        try:
            raw = Path('/proc/%s/task/%s/children' % (pid, pid)).read_text().split()
        except OSError:
            return found
        for tok in raw:
            if tok.isdigit():
                child = int(tok)
                found.append(child)
                found.extend(descendants(child))
        return found

    def stop_owned():
        targets = []
        for proc in owned:
            if proc.poll() is None:
                targets.append(proc.pid)
                targets.extend(descendants(proc.pid))
        reports = root / 'coord' / 'reports'
        if reports.is_dir():
            for pidfile in reports.glob('*.pid'):
                try:
                    pid = int(pidfile.read_text().strip())
                except (OSError, ValueError):
                    continue
                try:
                    parts = Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0')
                except OSError:
                    continue
                if (len(parts) >= 3 and parts[1].decode(errors='replace') == at
                        and parts[2] == b'run'):
                    targets.append(pid)
                    targets.extend(descendants(pid))
        seen = []
        for pid in targets:
            if pid > 0 and pid not in seen:
                seen.append(pid)
        for pid in seen:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.time() + 3
        for proc in owned:
            remain = max(0.1, deadline - time.time())
            try:
                proc.wait(timeout=remain)
            except subprocess.TimeoutExpired:
                pass
        for pid in seen:
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for proc in owned:
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    def git(*args):
        return subprocess.run(['git', *args], cwd=repo, env=env,
                              check=True, capture_output=True, timeout=30)

    def unio(*args, cwd=None, bg=False, wait=True):
        if not wait or bg:
            fout = open(repo / ('unio_run_%s.out' % args[1]), 'w')
            ferr = open(repo / ('unio_run_%s.err' % args[1]), 'w')
            open_streams.extend((fout, ferr))
            proc = subprocess.Popen([at, *args], cwd=cwd or repo, env=env,
                                    stdout=fout, stderr=ferr, text=True,
                                    start_new_session=True)
            owned.append(proc)
            return proc
        return subprocess.run([at, *args], cwd=cwd or repo, env=env,
                              capture_output=True, text=True, timeout=40)

    try:
        git('init', '--initial-branch=main')
        git('commit', '--allow-empty', '-m', 'initial')

        # We must init from root/repo so find_root uses it, but wait:
        # find_root stops where coord and wt exist. If we init from repo,
        # unio-install.sh will create coord/ and wt/ in root.
        # That is normal.
        unio('init', 'mock1')
        unio('init', 'mock2')
        unio('init', 'mock3')
        unio('init', 'mock4')
        unio('init', 'mock5')

        conf_dir = base / 'conf' / 'agents.conf'
        mock_script = repo / 'mock.sh'
        conf_dir.write_text(f"mock1=bash '{mock_script}'\nmock2=bash '{mock_script}'\nmock3=bash '{mock_script}'\nmock4=bash '{mock_script}'\nmock5=bash '{mock_script}'\n")
        mock_script.write_text("""#!/bin/bash
    if [ -n "${MOCK_MARKER:-}" ]; then
        printf 'ran\\n' >> "$MOCK_MARKER"
    fi
    barrier="${MOCK_BARRIER:-}"
    if [ -n "$barrier" ]; then
        touch "$barrier.started"
        while [ ! -f "$barrier.release" ]; do sleep 0.1; done
    fi
    if [ "${MOCK_TRAP:-0}" = "1" ]; then
        trap 'echo ignored term' TERM
        while true; do sleep 1; done
    fi
    """)
        mock_script.chmod(0o755)

        # tasks MUST be in root/coord/tasks
        (root / 'coord' / 'tasks').mkdir(parents=True, exist_ok=True)
        (root / 'coord' / 'tasks' / 'task1.md').write_text("Task 1 content")
        (root / 'coord' / 'tasks' / 'task2.md').write_text("Task 2 content")
        (root / 'coord' / 'tasks' / 'task3.md').write_text("Task 3 content")
        (root / 'coord' / 'tasks' / 'task4.md').write_text("Task 4 content")
        (root / 'coord' / 'tasks' / 'task5.md').write_text("Task 5 content")
        # And we must track them in git for quality paths if needed, wait, coord is NOT in repo!
        # Does unio run require task file to be tracked? NO. quality paths only checks wt/worker.

        # same-lock concurrent setters
        def set_mode(m):
            return unio('mode', m).stdout
        def set_tier(t):
            return unio('tier', t).stdout
        with ThreadPoolExecutor(max_workers=2) as ex:
            mode_out = ex.submit(set_mode, 'yolo')
            tier_out = ex.submit(set_tier, 'high')
            mode_out.result()
            tier_out.result()
        st = unio('policy').stdout
        check('same-lock concurrent setters', 'mode: yolo' in st and 'tier: high' in st)

        # reset state
        unio('tier', 'low')
        unio('mode', 'medium')
        unio('lead', 'none')

        # invalid timestamp
        state_file = root / 'coord' / 'work-policy.json'
        st_json = json.loads(state_file.read_text())
        st_json['updated_at'] = 'invalid'
        state_file.write_text(json.dumps(st_json))
        out = unio('mode', 'safe')
        check('invalid timestamp rejected', out.returncode != 0 and 'invalid updated_at' in out.stderr, out)
        st_json.pop('updated_at')
        state_file.write_text(json.dumps(st_json))

        # unsafe control path symlink
        lock_dir = root / 'coord' / '.locks'
        lock_dir.mkdir(parents=True, exist_ok=True)
        lock_file = lock_dir / 'work-policy.lock'
        lock_link = lock_dir / 'work-policy.link'
        if lock_file.exists():
            lock_link.write_bytes(lock_file.read_bytes())
            lock_file.unlink()
        else:
            lock_link.write_text("")
        lock_file.symlink_to(lock_link.name)
        out = unio('mode', 'yolo')
        check('unsafe policy lock symlink', out.returncode != 0 and 'unsafe control path' in out.stderr, out)
        lock_file.unlink()
        if lock_link.exists():
            lock_file.write_bytes(lock_link.read_bytes())

        # same-budget aliases denied before mock command
        unio('account', 'mock1', 'grp1')
        unio('account', 'mock2', 'grp1')
        unio('tier', 'low') # limit 1

        def wait_barrier(path):
            for _ in range(50):
                if Path(path).exists():
                    return
                time.sleep(0.1)
            print(f"timeout waiting for {path}")
            for err_file in repo.glob("unio_run_*.err"):
                print(f"--- {err_file.name} ---")
                print(err_file.read_text())
            for out_file in repo.glob("unio_run_*.out"):
                print(f"--- {out_file.name} ---")
                print(out_file.read_text())
            sys.exit(1)

        env['MOCK_BARRIER'] = str(repo / 'bar1')
        p1 = unio('run', 'mock1', 'task1', wait=False)
        wait_barrier(repo / 'bar1.started')

        out2 = unio('run', 'mock2', 'task2')
        check('same-budget alias denied', out2.returncode != 0 and 'budget refused' in out2.stderr and "budget group 'grp1' holds" in out2.stderr, out2)

        # release bar1
        (repo / 'bar1.release').touch()
        p1.wait(timeout=30)

        # different groups overlap
        unio('account', 'mock1', 'grp1')
        unio('account', 'mock2', 'grp2')
        unio('tier', 'low') # limit 1
        env['MOCK_BARRIER'] = str(repo / 'bar2')
        p1 = unio('run', 'mock1', 'task1', wait=False)
        wait_barrier(repo / 'bar2.started')

        env['MOCK_BARRIER'] = str(repo / 'bar3')
        p2 = unio('run', 'mock2', 'task2', wait=False)
        wait_barrier(repo / 'bar3.started')

        check('different groups overlap allowed', p2.poll() is None)

        (repo / 'bar2.release').touch()
        (repo / 'bar3.release').touch()
        p1.wait(timeout=30)
        p2.wait(timeout=30)
        del env['MOCK_BARRIER']

        # cap2/cap4 and lead inclusion
        unio('tier', 'high') # limit 4
        unio('account', 'mock5', 'grp1')
        unio('lead', 'mock5')

        ps = []
        # limit 4, lead is 1, so we can start 3
        for i, agent in enumerate(['mock1', 'mock2', 'mock3']):
            unio('account', agent, 'grp1')
            env['MOCK_BARRIER'] = str(repo / f'bar4_{i}')
            ps.append(unio('run', agent, f'task{i+1}', wait=False))

        for i in range(3):
            wait_barrier(repo / f'bar4_{i}.started')

        unio('account', 'mock4', 'grp1')
        env['MOCK_BARRIER'] = ''


        out_denied = unio('run', 'mock4', 'task4')
        check('cap4 with lead limits properly', out_denied.returncode != 0 and 'budget refused' in out_denied.stderr, out_denied)

        # tier reduction/regroup refusal while busy
        out_tier = unio('tier', 'medium')
        check('tier reduction while busy refused', out_tier.returncode != 0 and 'tier medium refuses' in out_tier.stderr, out_tier)

        out_regroup = unio('account', 'mock1', 'grp2')
        check('regroup occupied agent refused', out_regroup.returncode != 0 and 'holds' in out_regroup.stderr, out_regroup)

        for i in range(3): (repo / f'bar4_{i}.release').touch()
        for p in ps:
            p.wait(timeout=30)


        # held oversized/malformed metadata cannot bypass low cap or lower/regroup
        unio('tier', 'low')
        unio('lead', 'none')
    
        # 1. Create a held slot by running a background mock that waits
        env['MOCK_BARRIER'] = str(repo / 'bar_oversized')
        p_over = unio('run', 'mock1', 'task1', wait=False)
        wait_barrier(repo / 'bar_oversized.started')
    
        # 2. Find the slot file and rewrite it to be oversized
        import fcntl
        slot_dir = root / 'coord' / '.locks' / 'work-policy-slots' / 'grp1'
        slot_files = list(slot_dir.glob('wpslot-*.json'))
        check('slot file created', len(slot_files) > 0)
        slot_file = slot_files[0]
    
        # Rewrite its content to be oversized but STILL HELD by python!
        # Wait, the python process holds the fd. We can just append to the file path to make it oversized.
        try:
            with open(slot_file, 'a') as sf:
                sf.write(" " * 5000)
        except Exception as e:
            print("Failed to append", e)

        # Now verify admission is refused (it's oversized but held, so considered active)
        out_admit = unio('run', 'mock2', 'task2')
        check('held oversized slot refuses admit', out_admit.returncode != 0 and 'budget refused' in out_admit.stderr)
    
        # Verify tier reduction is refused
        out_tier = unio('tier', 'high') # wait, tier medium... wait, tier reduction.
        unio('tier', 'medium')
        out_tier = unio('tier', 'low')
        check('held oversized slot refuses tier reduction', out_tier.returncode != 0)
    
        # Verify regroup is refused
        out_regroup = unio('account', 'mock1', 'grp2')
        check('held oversized slot refuses regroup', out_regroup.returncode != 0)

        # release
        (repo / 'bar_oversized.release').touch()
        p_over.wait(timeout=30)
    
        # hardlinked policy lock rejected with state/sentinel intact
        lock_file = root / 'coord' / '.locks' / 'work-policy.lock'
        lock_link = root / 'coord' / '.locks' / 'work-policy.hardlink'
        if lock_file.exists():
            try:
                os.link(lock_file, lock_link)
                out_hardlink = unio('mode', 'yolo')
                check('hardlinked policy lock rejected', out_hardlink.returncode != 0 and 'hardlinked' in out_hardlink.stderr)
                lock_link.unlink()
            except OSError:
                pass # FS doesn't support hardlinks
            
        # unsafe admission path rejection before a counted mock command
        # Create an unsafe slot directory (symlink)
        unio('account', 'mock3', 'grp_unsafe')
        unsafe_dir = root / 'coord' / '.locks' / 'work-policy-slots' / 'grp_unsafe'
        if unsafe_dir.exists():
            unsafe_dir.rmdir()
        unsafe_target = root / 'coord' / '.locks' / 'target_unsafe'
        unsafe_target.mkdir(parents=True, exist_ok=True)
        sentinel = unsafe_target / 'sentinel.txt'
        sentinel.write_text('keep-sentinel\n')
        sentinel_bytes = sentinel.read_bytes()
        target_names = sorted(path.name for path in unsafe_target.iterdir())
        marker = repo / 'unsafe-provider-marker'
        marker.unlink(missing_ok=True)
        env['MOCK_MARKER'] = str(marker)
        env.pop('MOCK_BARRIER', None)
        unsafe_dir.symlink_to('target_unsafe')

        out_unsafe = unio('run', 'mock3', 'task3')
        check('unsafe admission path rejection',
              out_unsafe.returncode == 2 and
              'unsafe control path' in out_unsafe.stderr and
              unsafe_dir.name in out_unsafe.stderr and
              unsafe_dir.is_symlink() and
              out_unsafe.stdout == '' and
              not marker.exists() and
              sentinel.read_bytes() == sentinel_bytes and
              sorted(path.name for path in unsafe_target.iterdir()) == target_names,
              out_unsafe)

        unsafe_dir.unlink()
        env.pop('MOCK_MARKER', None)

        # check failure/timeout release
        # Add bounded --kill-after=5s to Source/review timeouts
        env['MOCK_TRAP'] = "1"
        env['UNIO_TIMEOUT'] = "2" # 2s timeout
        t0 = time.time()
        out_timeout = unio('run', 'mock1', 'task1')
        t1 = time.time()
        check('timeout enforced', out_timeout.returncode != 0 and (t1 - t0) < 15, out_timeout) # 2s + 5s kill-after

        del env['UNIO_TIMEOUT']
        del env['MOCK_TRAP']
        out_next = unio('run', 'mock1', 'task1')
        check('slot released on timeout/failure', out_next.returncode == 0, out_next)

        # original task/hash preserved and policy header/sidecar consistent
        prompt_file = root / 'coord' / 'reports' / 'task1.prompt.md'
        sidecar_file = root / 'coord' / 'reports' / 'task1.policy.json'
        check('prompt/sidecar exists', prompt_file.exists() and sidecar_file.exists())

        prompt_text = prompt_file.read_text()
        check('policy header applied', 'Unio work-policy header' in prompt_text and 'Task 1 content' in prompt_text)

        sidecar_json = json.loads(sidecar_file.read_text())
        check('sidecar JSON consistent', sidecar_json['group'] == 'grp1' and 'policy' in sidecar_json)

        # background Source and independent reviewer accounting
        unio('tier', 'low')
        unio('lead', 'none')

        # test background Source
        env['MOCK_BARRIER'] = str(repo / 'bar5')
        unio('run', '-b', 'mock1', 'task1', wait=False)
        wait_barrier(repo / 'bar5.started')

        out_fg = unio('run', 'mock2', 'task2')
        check('background Source accounted', out_fg.returncode != 0 and 'budget refused' in out_fg.stderr, out_fg)

        (repo / 'bar5.release').touch()

        # wait for background to finish properly
        released_bg = False
        for _ in range(150):
            out_pol = unio('policy', '--json')
            try:
                pol_json = json.loads(out_pol.stdout)
            except json.JSONDecodeError:
                time.sleep(0.1)
                continue
            if pol_json.get('active_native_workflows', {}).get('grp1', 0) == 0:
                out_stat = unio('status')
                mock1_line = next((line for line in out_stat.stdout.splitlines() if line.startswith('  mock1 ')), '')
                if mock1_line and '<< RUNNING' not in mock1_line:
                    released_bg = True
                    break
            time.sleep(0.1)
        check('background Source released its slot', released_bg)

        # test independent reviewer accounting
        # inject passed validation
        result_path = root / 'coord' / 'results' / 'mock2' / 'task2.json'
        injector = (
            'import json\n'
            'f = %r\n'
            'd = json.load(open(f))\n'
            'd["validation"] = {\n'
            '    "state": "passed",\n'
            '    "revision": d["current_revision"],\n'
            '    "scope": "OK",\n'
            '    "checks_run": 1,\n'
            '    "checks_failed": 0,\n'
            '    "reasons": []\n'
            '}\n'
            'json.dump(d, open(f, "w"))\n'
        ) % str(result_path)
        subprocess.run(['python3', '-c', injector], timeout=20, check=True)
        env['MOCK_BARRIER'] = str(repo / 'bar6')
        p_rev = unio('review', 'mock2', 'task2', 'mock1', wait=False)
        wait_barrier(repo / 'bar6.started')

        out_rev2 = unio('run', 'mock3', 'task3')
        check('reviewer accounted', out_rev2.returncode != 0 and 'budget refused' in out_rev2.stderr, out_rev2)

        (repo / 'bar6.release').touch()
        p_rev.wait(timeout=30)

        print('work-policy-guard: done (%d checks passed)' % passed[0])
    finally:
        stop_owned()
        for stream in open_streams:
            stream.close()
