#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Provider limit phrases wall only failed runs; worker prose and success never bench an agent."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import time

source = Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='limit-wall-') as directory:
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
    subprocess.run([at,'init','mock'],cwd=repo,env=env,check=True,capture_output=True)
    mock = root/'mock.py'
    mock.write_text('''import os,subprocess
from pathlib import Path
print(os.environ.get('WALL_MOCK_TEXT',''))
if os.environ.get('WALL_MOCK_MODE','fail')=='work':
    with Path('canary.txt').open('a') as f: f.write('done\\n')
    subprocess.run(['git','add','canary.txt'],check=True)
    subprocess.run(['git','commit','-qm','mock'],check=True)
    raise SystemExit(0)
raise SystemExit(7)
''')
    (base/'conf/agents.conf').write_text('mock=python3 '+shlex.quote(str(mock))+'\n')
    count = 0
    def check(label, condition=True):
        global count
        assert condition,label
        count += 1
        print('  wall: '+label,flush=True)
    def bench(): return (base/'conf/off/mock').exists()
    def call(*args, code=0, mode='fail', text='', auto_off='0'):
        p = subprocess.run([at,*args],cwd=repo,env=dict(env,WALL_MOCK_MODE=mode,WALL_MOCK_TEXT=text,
                            UNIO_AUTO_OFF=auto_off),capture_output=True,text=True)
        assert p.returncode==code,(args,p.returncode,code,p.stdout,p.stderr)
        return p
    def task(name, checks='$ true'):
        (root/'coord/tasks'/f'{name}.md').write_text(f'# {name}\n## Allowed scope\n- canary.txt\n## Validate\n{checks}\n')
    def wall(name):
        events=[json.loads(line) for line in (root/'coord/reports/ledger.jsonl').read_text().splitlines()]
        return [e for e in events if e.get('event')=='run' and e.get('task')==name][-1]['wall']
    WARNING='!! output mentions usage limits'

    task('superseded')
    p=call('run','mock','superseded',code=7,auto_off='1',text='The preceding quota question is superseded.')
    check('worker prose about quotas never walls or benches',WARNING not in p.stderr and wall('superseded')==0 and not bench())

    task('capped')
    p=call('run','mock','capped',code=7,auto_off='1',text="Error: You've hit your usage limit. Resets at 3pm.")
    exp=int((base/'conf/off/mock').read_text())
    check('provider cap language walls and benches a failed run',
          WARNING in p.stderr and wall('capped')==1 and bench() and 4*3600 < exp-time.time() < 6*3600)
    call('on','mock')

    task('requests')
    p=call('run','mock','requests',code=7,text='HTTP 429 Too Many Requests')
    check('too many requests walls a failed run',WARNING in p.stderr and wall('requests')==1)

    task('succeeds')
    p=call('run','mock','succeeds',code=0,mode='work',auto_off='1',text='rate limit exceeded')
    check('successful run never walls or benches',WARNING not in p.stderr and wall('succeeds')==0 and not bench())
    print(f'limit-wall regressions: {count} passed')
