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

def check(label, condition=True):
    if not condition:
        print('FAIL ' + label)
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

    def unio(*args, cwd=None, bg=False):
        if bg:
            return subprocess.Popen([at, *args], cwd=cwd or repo, env=env,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return subprocess.run([at, *args], cwd=cwd or repo, env=env,
                              capture_output=True, text=True)

    git('init', '--initial-branch=main')
    git('commit', '--allow-empty', '-m', 'initial')
    unio('init', 'mock1')
    unio('init', 'mock2')
    unio('init', 'mock3')
    unio('init', 'mock4')
    unio('init', 'mock5')

    conf_dir = base / 'conf' / 'agents.conf'
    conf_dir.write_text("mock1=bash mock.sh\nmock2=bash mock.sh\nmock3=bash mock.sh\nmock4=bash mock.sh\nmock5=bash mock.sh\n")

    mock_script = repo / 'mock.sh'
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

    print('work-policy-guard: done')
