#!/usr/bin/env python3
"""Additional contract regressions inside the shell suite's disposable checkout."""
import copy
import json
import os
from pathlib import Path
import subprocess
import time

root = Path.cwd().parent
wt = root / 'wt/mock'
at = str(Path(os.environ['AGENTTEAM_BIN_DIR']) / 'frugal-flock')
conf = Path(os.environ['AGENTTEAM_CONF_DIR']) / 'agents.conf'
result = root / 'coord/results/mock/evidence.json'
tf = root / 'coord/tasks/evidence.md'
count = 0


def call(*args, code=0, env=None):
    p = subprocess.run([at, *args], capture_output=True, text=True,
                       env=dict(os.environ, **(env or {})))
    assert p.returncode == code, (args, p.returncode, code, p.stdout, p.stderr)
    return p


def git(*args, cwd=wt):
    return subprocess.run(['git', '-C', str(cwd), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def check(label, condition=True):
    global count
    assert condition, label
    count += 1
    print('  quality: ' + label)


def configuration(review='printf "VERDICT: APPROVE\\n"', extra=''):
    conf.write_text("mock=bash -c 'echo evidence >> hello.txt; git add hello.txt; git commit -qm evidence'\n"
                    "noop=bash -c 'exit 0'\nrev=bash -c " + __import__('shlex').quote(review) + '\n' + extra)


def data(task='evidence'):
    return json.loads(call('result', 'mock', task).stdout)


def verify():
    call('verify', 'mock', 'evidence')


def ready():
    call('run', 'mock', 'evidence')
    verify()
    call('review', 'mock', 'evidence', 'rev')
    check('current success persists and reloads', data()['ready_for_human_review'])


tf.write_text('# Evidence\n## Allowed scope\n- *\n## Validate\n$ test -s hello.txt\n')
configuration()
call('result', 'mock', 'evidence', code=2)
check('missing result fails closed')
call('review', 'mock', 'evidence', 'rev', code=2)
check('review requires structured validation')
ready()
d = data()
check('separate human and integration states', d['human']=={'state':'pending'} and d['integration']=={'state':'not_attempted'})
call('run', 'mock', 'evidence')
d = data()
check('new run clears old validation/review', d['validation']['state']=='not_run' and d['review']['state']=='not_run' and not d['ready_for_human_review'])
verify()
for label, command, code, state in [
    ('approve', 'printf "VERDICT: APPROVE\\n"', 0, 'approved'),
    ('request changes', 'printf "VERDICT: REQUEST-CHANGES\\n"', 1, 'changes_requested'),
    ('stderr approval', 'printf "VERDICT: APPROVE\\n" >&2', 2, 'unknown'),
    ('no verdict', 'printf done', 2, 'unknown'),
    ('malformed verdict', 'printf "VERDICT: APPROVED\\n"', 2, 'unknown'),
    ('indented verdict', 'printf " VERDICT: APPROVE\\n"', 2, 'unknown'),
    ('duplicate verdict', 'printf "VERDICT: APPROVE\\nVERDICT: APPROVE\\n"', 2, 'unknown'),
    ('contradictory verdict', 'printf "VERDICT: APPROVE\\nVERDICT: REQUEST-CHANGES\\n"', 2, 'unknown'),
    ('process failed with approval', 'printf "VERDICT: APPROVE\\n"; exit 7', 1, 'failed'),
]:
    configuration(command)
    call('review','mock','evidence','rev',code=code)
    d=data()
    check('review '+label, d['review']['state']==state and d['review']['process_exit_code']==(7 if state=='failed' else 0))
configuration('sleep 3; printf "VERDICT: APPROVE\\n"')
call('review','mock','evidence','rev',code=1,env={'AGENTTEAM_REVIEW_TIMEOUT':'1'})
check('timeout process exit preserved',data()['review']['process_exit_code']==124)
configuration()
ready()

# Every dimension independently invalidates already-ready evidence.
original_task = tf.read_text()
tf.write_text(original_task+'changed task\n')
check('task hash stale', data()['stale'] and not data()['ready_for_human_review'])
call('review','mock','evidence','rev',code=2)
tf.write_text(original_task)
hello=wt/'hello.txt'; original=hello.read_text()
hello.write_text(original+'dirty\n')
check('tracked content stale',data()['stale'])
git('add','hello.txt')
check('index stale',data()['stale'])
git('restore','--staged','hello.txt')
hello.write_text(original)
git('update-index','--assume-unchanged','hello.txt')
hello.write_text(original+'hidden edit\n')
check('assume-unchanged content is hashed',data()['stale'])
hello.write_text(original)
git('update-index','--no-assume-unchanged','hello.txt')
special=wt/'space " quote\\ tab\tline\nž.txt'
special.write_text('one')
check('JSON-special untracked filename',data()['stale'])
verify()
first=data()['revision']['worktree_sha256']
special.write_text('two')
check('untracked content changes hash',data()['current_revision']['worktree_sha256']!=first)
verify()
call('review','mock','evidence','rev',code=2)
check('dirty review refused without invocation',data()['review']['state']=='unknown' and not data()['review']['material_complete'])
special.unlink()
git('commit','--allow-empty','-qm','candidate advanced')
check('candidate commit stale',data()['stale'])
ready()
git('commit','--allow-empty','-qm','base advanced',cwd=root/'repo')
check('base commit stale',data()['stale'])
ready()

fifo=wt/'pipe'
os.mkfifo(fifo)
call('result','mock','evidence',code=2)
check('FIFO refused without blocking')
fifo.unlink()
nested=wt/'nested'
git('init','-q',str(nested))
(nested/'file').write_text('nested')
call('result','mock','evidence',code=2)
check('nested repository refuses incomplete hash')
__import__('shutil').rmtree(nested)
link=wt/'link'
link.symlink_to('/a/nonexistent/outside-target')
verify()
linkhash=data()['revision']['worktree_sha256']
link.unlink(); link.symlink_to('/different-target')
check('symlink target hashed without dereference',data()['current_revision']['worktree_sha256']!=linkhash)
link.unlink()
ready()

# A check or reviewer modifying the candidate cannot issue fresh evidence.
tf.write_text('# Evidence\n## Allowed scope\n- *\n## Validate\n$ echo mutation >> hello.txt\n')
call('run','mock','evidence')
call('verify','mock','evidence',code=2)
check('candidate changes during validation',data()['validation']['state']=='incomplete' and data()['stale'])
tf.write_text(original_task)
configuration()
ready()
configuration('printf mutation >> "$QUALITY_WT/hello.txt"; printf "VERDICT: APPROVE\\n"')
call('review','mock','evidence','rev',code=2,env={'QUALITY_WT':str(wt)})
check('candidate changes during review',data()['review']['state']=='unknown' and data()['stale'])
configuration()
ready()

# Contradictory JSON must not manufacture readiness after a refresh.
good=result.read_text()
for label, mutate in [
    ('process exit',lambda d:d['process'].update(exit_code=7)),
    ('zero checks',lambda d:d['validation'].update(checks_run=0)),
    ('failed checks',lambda d:d['validation'].update(checks_failed=1)),
    ('unknown scope',lambda d:d['validation'].update(scope='UNCHECKED')),
    ('review exit',lambda d:d['review'].update(process_exit_code=7)),
    ('partial material',lambda d:d['review'].update(material_complete=False)),
    ('missing evidence revision',lambda d:d['review'].update(revision=None)),
    ('human forged',lambda d:d.update(human={'state':'accepted'})),
]:
    altered=json.loads(good); mutate(altered); result.write_text(json.dumps(altered))
    call('result','mock','evidence',code=2)
    check('malformed state rejects '+label)
result.write_text('{broken')
call('result','mock','evidence',code=2)
call('handoff','mock','evidence',code=2)
check('malformed JSON fails closed for result and handoff')
result.write_text(good)

# One real flock blocks run, review, and packet creation.
lock=root/'coord/.locks/mock.lock'
with lock.open('a') as f:
    __import__('fcntl').flock(f,__import__('fcntl').LOCK_EX)
    for operation in ('run','review','handoff','verify'):
        call(operation,'mock','evidence',code=1)
        check(operation+' refuses worker lock')

# Review itself owns the lock throughout its provider call.
marker=root/'review-started'
configuration('touch "$QUALITY_MARKER"; sleep 2; printf "VERDICT: APPROVE\\n"')
review=subprocess.Popen([at,'review','mock','evidence','rev'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                        env=dict(os.environ,QUALITY_MARKER=str(marker)))
for _ in range(100):
    if marker.exists(): break
    time.sleep(.05)
assert marker.exists()
call('run','mock','evidence',code=1)
call('handoff','mock','evidence',code=1)
out,err=review.communicate(timeout=10)
check('review holds worker lock',review.returncode==0)
configuration()

# Handoff is unique context only, with uncommitted data still in the checkout.
(wt/'local.txt').write_text('not a backup')
packet1=Path(call('handoff','mock','evidence').stdout.strip())
packet2=Path(call('handoff','mock','evidence').stdout.strip())
check('unique atomic handoff',packet1!=packet2 and packet1.is_dir() and packet2.is_dir() and not list(packet1.parent.glob('.pending-*')))
check('handoff contains only context',set(p.name for p in packet1.iterdir())=={'task.md','result.json','revision.json','changed-files.json','HANDOFF.md'})
check('handoff states source-only untracked work','local.txt' in (packet1/'changed-files.json').read_text() and 'NOT a backup' in (packet1/'HANDOFF.md').read_text() and not (packet1/'local.txt').exists())
check('handoff result is current and stale',json.loads((packet1/'result.json').read_text())['stale'])
(wt/'local.txt').unlink()
absent=root/'coord/tasks/absent.md'; absent.write_text(original_task)
newpacket=Path(call('handoff','mock','absent').stdout.strip())
check('handoff without result has explicit unknown states',json.loads((newpacket/'result.json').read_text())['process']['state']=='not_run')
for operation in ('result','handoff'):
    call(operation,'../escape','evidence',code=1)
    check(operation+' invalid IDs refused')
outside=root/'outside'; outside.mkdir()
escape=root/'coord/handoffs/mock/escape'; escape.symlink_to(outside,target_is_directory=True)
(root/'coord/tasks/escape.md').write_text(original_task)
call('handoff','mock','escape',code=2)
check('handoff symlink escape refused',not list(outside.iterdir()))
result.unlink(); result.symlink_to(outside/'result.json')
call('verify','mock','evidence',code=2)
check('result symlink refused',not (outside/'result.json').exists())
result.unlink(); result.write_text(good)

# Availability never executes even hostile configured commands.
marker=root/'availability-executed'
configuration(extra='literal=LANG="en US" env X=1 /usr/bin/true\nmissing=env X=1 /no/such/binary\n'
                    'wrapper=bash -c "touch '+str(marker)+'"\nquoted=env X="a b" "/usr/bin/true"\n')
agents=json.loads(call('agents','--json').stdout)['agents']
mapping={a['name']:a for a in agents}
check('assignments/env and quoted executable resolve',mapping['literal']['binary']['present'] is True and mapping['quoted']['binary']['present'] is True)
check('missing and ambiguous binaries truthful',mapping['missing']['binary']['present'] is False and mapping['wrapper']['binary']['present'] is None)
check('no availability command executed',not marker.exists())
check('availability authentication/capacity unknown',all(a['authentication']=='unknown' and a['capacity']=='unknown' and a['execution_boundary']=='trusted_host' for a in agents))
call('off','literal','5m')
a={a['name']:a for a in json.loads(call('agents','--json').stdout)['agents']}['literal']
check('operator retry recorded honestly',a['bench']['off'] and a['bench']['operator_retry_at']>time.time() and 'not a provider reset' in call('agents').stdout)
print(f'quality contract regressions: {count} passed')
