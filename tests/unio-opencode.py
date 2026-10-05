#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Fresh default dispatches to an offline OpenCode stub; reinstall preserves config."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
source=Path(__file__).resolve().parent.parent
with tempfile.TemporaryDirectory(prefix='opencode-default-') as directory:
    base=Path(directory);root=base/'project';repo=root/'repo';repo.mkdir(parents=True)
    env=dict(os.environ, UNIO_BIN_DIR=str(base/'bin'),UNIO_CONF_DIR=str(base/'conf'),
             UNIO_COMPLETION_DIR=str(base/'completion'),UNIO_AUTO_VERIFY='0',
             UNIO_AUTO_OFF='0',UNIO_AUTO_SYNC='0',GIT_AUTHOR_NAME='mock',
             GIT_COMMITTER_NAME='mock',GIT_AUTHOR_EMAIL='mock@example.invalid',GIT_COMMITTER_EMAIL='mock@example.invalid')
    subprocess.run(['bash',str(source/'unio-install.sh')],env=env,check=True,capture_output=True)
    at=str(base/'bin/unio');stub=base/'stub';stub.mkdir()
    executable=stub/'opencode'
    executable.write_text('''#!/usr/bin/env python3
import json,sys,subprocess,os
from pathlib import Path
assert sys.argv[1]=='run' and sys.argv[2]=='--auto', sys.argv
assert len(sys.argv)==4 and 'permission canary' in sys.argv[3], sys.argv
Path(os.environ['OPENCODE_ARGS_RECEIPT']).write_text(json.dumps(sys.argv[1:]))
Path('canary.txt').write_text('ready\\n')
subprocess.run(['git','add','canary.txt'],check=True)
subprocess.run(['git','commit','-qm','offline OpenCode'],check=True)
''');executable.chmod(0o755)
    env.update(PATH=str(stub)+os.pathsep+env['PATH'],OPENCODE_ARGS_RECEIPT=str(base/'args.json'))
    def git(*args):return subprocess.run(['git',*args],cwd=repo,env=env,check=True,capture_output=True)
    def call(*args):return subprocess.run([at,*args],cwd=repo,env=env,check=True,capture_output=True)
    git('init','-q','-b','main');(repo/'canary.txt').write_text('pending\n');git('add','canary.txt');git('commit','-qm','seed')
    call('init','opencode')
    (root/'coord/tasks/flags.md').write_text('# OpenCode permission canary\n## Allowed scope\n- canary.txt\n## Validate\n$ test "$(cat canary.txt)" = ready\n')
    call('run','opencode','flags');call('verify','opencode','flags')
    result=json.loads(call('result','opencode','flags').stdout)
    assert result['process']['state']=='succeeded' and result['validation']['state']=='passed'
    assert json.loads((base/'args.json').read_text())[1]=='--auto'
    print('opencode: fresh source default dispatches --auto and task text, native verification passed',flush=True)
    config=base/'conf/agents.conf';config.write_text('# user settings\nopencode=opencode run --dangerously-skip-permissions -m owner-choice\n')
    before=(base/'args.json').read_bytes()
    doctor=call('doctor').stdout.decode()
    assert 'legacy OpenCode permission flag' in doctor and '--auto' in doctor
    assert (base/'args.json').read_bytes()==before
    print('opencode: doctor warns on legacy direct entry without executing or changing it',flush=True)
    original=config.read_bytes()
    subprocess.run(['bash',str(source/'unio-install.sh')],env=env,check=True,capture_output=True)
    assert config.read_bytes()==original
    print('opencode: reinstall preserves existing model and command configuration',flush=True)
