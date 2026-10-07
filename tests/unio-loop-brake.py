#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Provider invocation markers prove the loop brake refuses before spending quota."""
import concurrent.futures
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import tempfile
import time

source = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='loop-brake-') as directory:
    base = Path(directory)
    env = dict(os.environ, UNIO_BIN_DIR=str(base/'bin'),
               UNIO_CONF_DIR=str(base/'conf'), UNIO_COMPLETION_DIR=str(base/'completion'),
               GIT_AUTHOR_NAME='mock', GIT_COMMITTER_NAME='mock',
               GIT_AUTHOR_EMAIL='mock@example.invalid', GIT_COMMITTER_EMAIL='mock@example.invalid',
               UNIO_AUTO_VERIFY='0', UNIO_AUTO_SYNC='0', UNIO_AUTO_OFF='0',
               UNIO_TIMEOUT='20', UNIO_VERIFY_TIMEOUT='10')
    subprocess.run(['bash',str(source/'unio-install.sh')],env=env,check=True,capture_output=True)
    at = str(base/'bin/unio')
    root = base/'project'; repo = root/'repo'; repo.mkdir(parents=True)
    def git(*args):
        return subprocess.run(['git',*args],cwd=repo,env=env,check=True,capture_output=True)
    git('init','-q','-b','main'); (repo/'canary.txt').write_text('pending\n')
    git('add','canary.txt'); git('commit','-qm','seed')
    subprocess.run([at,'init','mock','mock-2','mock-3'],cwd=repo,env=env,check=True,capture_output=True)
    mark = root/'calls'; info = root/'mock-process.json'
    mock = root/'mock.py'
    mock.write_text('''import os,json,subprocess,time
from pathlib import Path
p=Path(__file__).parent
with (p/'calls').open('a') as f: f.write('called\\n')
mode=os.environ.get('BRAKE_MOCK_MODE','fail')
if mode=='hold':
 (p/'mock-process.json').write_text(json.dumps({'pid':os.getpid(),'pgid':os.getpgrp()}))
 while True: time.sleep(.1)
if mode=='work':
 with Path('canary.txt').open('a') as f: f.write('ready\\n')
 subprocess.run(['git','add','canary.txt'],check=True)
 subprocess.run(['git','commit','-qm','mock'],check=True)
raise SystemExit(7 if mode=='fail' else 0)
''')
    (base/'conf/agents.conf').write_text('mock=python3 '+shlex.quote(str(mock))+'\n')
    count = 0
    def check(label, condition=True):
        global count
        assert condition,label
        count += 1
        print('  brake: '+label,flush=True)
    def calls(): return len(mark.read_text().splitlines()) if mark.exists() else 0
    def call(*args, code=0, mode='fail'):
        p = subprocess.run([at,*args],cwd=repo,env=dict(env,BRAKE_MOCK_MODE=mode),capture_output=True,text=True)
        assert p.returncode==code,(args,p.returncode,code,p.stdout,p.stderr)
        return p
    def task(name, checks='$ true'):
        (root/'coord/tasks'/f'{name}.md').write_text(f'# {name}\n## Allowed scope\n- canary.txt\n## Validate\n{checks}\n')
    def state(name): return json.loads((root/'coord/retries'/name/'state.json').read_text())
    def refuse(name, worker='mock'):
        n=calls(); p=call('run',worker,name,code=2)
        assert 'loop brake:' in p.stderr and calls()==n
        return p

    task('process')
    call('run','mock','process',code=7); check('first real process exit preserved',state('process')['failed_attempts']==1)
    call('verify','mock','process',code=1)
    check('process plus failed verification counts once',state('process')['failed_attempts']==1)
    call('run','mock-2','process',code=7)
    check('failure history spans workers',state('process')['failed_attempts']==2)
    before=(root/'coord/reports/process.log').read_bytes()
    refuse('process')
    check('third attempt spends no quota or overwrites native log',before==(root/'coord/reports/process.log').read_bytes())
    call('allow-retry','process.md'); call('allow-retry','process')
    check('owner grants do not accumulate',state('process')['retry_granted'] is True)
    call('run','mock','process',code=7); refuse('process')
    check('one grant permits one attempt and preserves failures',state('process')['failed_attempts']==3 and not state('process')['retry_granted'])
    task('unrelated'); call('run','mock','unrelated',code=7)
    check('different task has its own counter',state('unrelated')['failed_attempts']==1)
    n=calls(); call('allow-retry','unrelated',code=2)
    check('grant before a block is refused without a provider',calls()==n)

    task('validation','$ false')
    call('run','mock','validation',mode='noop'); call('verify','mock','validation',code=1)
    call('verify','mock','validation',code=1)
    check('repeated verification counts one attempt',state('validation')['failed_attempts']==1)
    call('run','mock','validation',mode='noop'); call('verify','mock','validation',code=1); refuse('validation')
    check('two validation failures after exit zero block a third call',state('validation')['failed_attempts']==2)
    task('incomplete','')
    for _ in range(2):
        call('run','mock','incomplete',mode='work'); call('verify','mock','incomplete',code=2)
    refuse('incomplete'); check('incomplete verification brakes repeated unfinished work')
    call('allow-retry','process'); call('run','mock','process',mode='work'); call('verify','mock','process')
    refuse('process')
    check('successful granted attempt does not erase failed history',state('process')['failed_attempts']==3)

    for name, damage in [('malformed','json'),('symlink','link'),('bad-lock','fifo')]:
        task(name); d=root/'coord/retries'/name; d.mkdir()
        if damage=='json': (d/'state.json').write_text('{broken')
        if damage=='link': (d/'state.json').symlink_to(base/'private')
        if damage=='fifo': os.mkfifo(d/'lock')
        n=calls(); call('run','mock',name,code=2)
        check(name+' state refused before provider invocation',calls()==n)

    task('concurrent')
    call('run','mock','concurrent',code=7); call('run','mock-2','concurrent',code=7)
    call('allow-retry','concurrent'); n=calls()
    def compete(worker):
        return subprocess.run([at,'run',worker,'concurrent'],cwd=repo,env=env,capture_output=True).returncode
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        codes=list(pool.map(compete,['mock','mock-2']))
    check('concurrent workers share a single retry grant',sorted(codes)==[2,7] and calls()==n+1)

    def interrupt(worker, name, during=None):
        if info.exists(): info.unlink()
        proc=subprocess.Popen([at,'run',worker,name],cwd=repo,
                              env=dict(env,BRAKE_MOCK_MODE='hold'),stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
        worker_group=None
        try:
            deadline=time.monotonic()+8
            while not info.exists() and time.monotonic()<deadline and proc.poll() is None: time.sleep(.05)
            assert info.exists(),'mock did not start'
            worker_group=json.loads(info.read_text())['pgid']
            assert worker_group!=os.getpgrp()
            if during: during()
            os.killpg(proc.pid,signal.SIGKILL)
            if worker_group!=proc.pid:
                try: os.killpg(worker_group,signal.SIGKILL)
                except ProcessLookupError: pass
            proc.communicate(timeout=5)
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid,signal.SIGKILL); proc.communicate(timeout=5)
            if worker_group is not None:
                try: os.killpg(worker_group,signal.SIGKILL)
                except ProcessLookupError: pass
    task('interrupted')
    for _ in range(2): interrupt('mock','interrupted')
    refuse('interrupted')
    check('two interrupted starts block another invocation',state('interrupted')['failed_attempts']==2)
    check('interruption counter never invents a worker exit',json.loads(call('result','mock','interrupted').stdout)['process']['exit_code'] is None)
    task('reassigned')
    interrupt('mock','reassigned'); interrupt('mock-2','reassigned'); refuse('reassigned','mock-3')
    check('interrupted failures remain shared after task reassignment',state('reassigned')['failed_attempts']==2)
    check('reassignment never invents either worker exit',all(json.loads(call('result',w,'reassigned').stdout)['process']['exit_code'] is None for w in ('mock','mock-2')))
    task('active')
    # The 'active' scenario overlaps two workflows. Temporarily grant medium capacity
    # (cap2) so the second run returns expected failure (7) instead of refusal (2).
    call('tier', 'medium')
    def while_active():
        call('run','mock-2','active',code=7)
        check('held active worker is not counted as interrupted',state('active')['failed_attempts']==1 and state('active')['latest']['mock']['pending'])
    interrupt('mock','active',while_active)
    call('tier', 'low')
    refuse('active','mock-3')
    check('released interrupted worker then contributes to shared brake',state('active')['failed_attempts']==2)
    print(f'loop-brake regressions: {count} passed')
