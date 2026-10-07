#!/usr/bin/env python3
import json
import os
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
                   check=True, capture_output=True)
    at = str(base / 'bin' / 'unio')
    root = base / 'mock project'
    repo = root / 'repo'
    repo.mkdir(parents=True)

    def git(*args):
        return subprocess.run(['git', *args], cwd=repo, env=env,
                              check=True, capture_output=True)

    def unio(*args, cwd=None, bg=False, wait=True):
        if not wait or bg:
            fout = open(repo / f'unio_run_{args[1]}.out', 'w')
            ferr = open(repo / f'unio_run_{args[1]}.err', 'w')
            return subprocess.Popen([at, *args], cwd=cwd or repo, env=env,
                                    stdout=fout, stderr=ferr, text=True)
        return subprocess.run([at, *args], cwd=cwd or repo, env=env,
                              capture_output=True, text=True)

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
        p=unio('mode', m); print('MODE ERR:', repr(p.stderr)); return p.stdout
    def set_tier(t):
        return unio('tier', t).stdout
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(set_mode, 'yolo')
        f2 = ex.submit(set_tier, 'high')
        print('f1:', repr(f1.result()))
        print('f2:', repr(f2.result()))
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
    p1.wait()

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
    p1.wait()
    p2.wait()
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
        p.wait()


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
    p_over.wait()
    
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
    unsafe_dir.symlink_to('target_unsafe')
    
    out_unsafe = unio('run', 'mock3', 'task3')
    print('RC:', out_unsafe.returncode, 'STDERR:', out_unsafe.stderr, 'STDOUT:', out_unsafe.stdout); check('unsafe admission path rejection', out_unsafe.returncode != 0 and 'symlink' in out_unsafe.stderr)
    
    unsafe_dir.unlink()

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
    for _ in range(50):
        out_pol = unio('policy', '--json')
        try:
            pol_json = json.loads(out_pol.stdout)
            if 'active_native_workflows' in pol_json and pol_json['active_native_workflows'].get('grp1', 0) == 0:
                out_stat = unio('status')
                mock1_line = next((line for line in out_stat.stdout.splitlines() if line.startswith('  mock1 ')), '')
                if mock1_line and '<< RUNNING' not in mock1_line:
                    break
        except json.JSONDecodeError as e:
            print("JSON ERROR in unio policy --json!")
            print(f"STDOUT: {repr(out_pol.stdout)}")
            print(f"STDERR: {repr(out_pol.stderr)}")
            raise e
        time.sleep(0.1)

    # test independent reviewer accounting
    # inject passed validation
    subprocess.run(['python3', '-c', f'''
import json, sys, os
from pathlib import Path
f = "{root}/coord/results/mock2/task2.json"
d = json.load(open(f))
d["validation"] = {{
    "state": "passed",
    "revision": d["current_revision"],
    "scope": "OK",
    "checks_run": 1,
    "checks_failed": 0,
    "reasons": []
}}
json.dump(d, open(f, "w"))
'''])
    env['MOCK_BARRIER'] = str(repo / 'bar6')
    p_rev = unio('review', 'mock2', 'task2', 'mock1', wait=False)
    wait_barrier(repo / 'bar6.started')

    out_rev2 = unio('run', 'mock3', 'task3')
    check('reviewer accounted', out_rev2.returncode != 0 and 'budget refused' in out_rev2.stderr, out_rev2)

    (repo / 'bar6.release').touch()
    p_rev.wait()

    print('work-policy-guard: done')
