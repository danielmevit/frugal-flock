#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only
"""Offline clock, durable controls and actual local process/protocol acceptance.

No real Codex, user config, authentication, network, model call or global install.
"""
import contextlib
import copy
import fcntl
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('cooldown', ROOT / 'tools/runtime/lead_cooldown.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
passed = 0
if sys.argv[1:] not in ([], ['--daemon-only']):
    raise SystemExit('usage: unio-lead-cooldown.py [--daemon-only]')


def check(name, condition):
    global passed
    assert condition, name
    passed += 1
    print('  ok ' + name, flush=True)


def refuses(fn):
    try:
        fn()
    except (m.Refusal, OSError, ValueError, TypeError):
        return True
    return False


ACCOUNT = {'account': {'type': 'chatgpt', 'planType': 'plus', 'email': 'private@example.invalid'}}
D = 2000000


def quota(allowed=False, duration=300, reset=None, secondary=None):
    return dict(ordinaryUsageAllowed=allowed, rateLimits=dict(limitId='codex',
                rateLimitReachedType=None if allowed else 'rate_limit_reached',
                primary=dict(usedPercent=10 if allowed else 100, windowDurationMins=duration, resetsAt=reset),
                secondary=secondary))


def proof(response, now=D):
    return m.classify(ACCOUNT, response, now)


def daemon_admission_checks():
    # Exercise the actual process-admission path against an isolated proc tree,
    # not the machine's running Codex or any real model executable.
    with tempfile.TemporaryDirectory(prefix='cooldown-proc-') as directory:
        root = Path(directory); entry = root/'1234';entry.mkdir()
        binary = root/'codex';binary.write_text('not an executable')
        (entry/'exe').symlink_to(binary)
        (entry/'environ').write_bytes(b'')
        old_iterdir = Path.iterdir
        words, parents = {}, {}
        def entries(path):return iter([entry]) if str(path)=='/proc' else old_iterdir(path)
        with patch.object(m.Path,'iterdir',entries),patch.object(m,'process_identity',return_value={'pid':1234}),\
             patch.object(m,'process_words',side_effect=lambda pid:words.get(pid,[])),\
             patch.object(m,'parent_pid',side_effect=lambda pid:parents.get(pid,0)):
            f={'codex':str(binary)}
            for args, label in [([b'codex'],'interactive lead'),([b'codex',b'exec'],'exec lead'),
                                ([b'codex',b'resume'],'resumed lead'),([b'codex',b'app-server',b'--listen'],'standalone app-server')]:
                words[1234]=args;parents.clear()
                check(label+' blocks a competing workflow',m.external_codex(f))
            words[1234]=[b'codex',b'app-server',b'daemon',b'run']
            check('persistent daemon manager is infrastructure',not m.external_codex(f))
            words[1234]=[b'codex',b'app-server',b'--listen'];parents[1234]=1200
            words[1200]=[b'codex',b'app-server',b'daemon',b'run']
            check('backend with exact daemon ancestry is infrastructure',not m.external_codex(f))
            words[1200]=[b'bash',b'-c',b'codex app-server daemon run']
            check('daemon words in another command do not bypass admission',m.external_codex(f))
            words[1234]=[]
            check('unknown process role blocks conservatively',m.external_codex(f))
            words[1234]=[b'codex',b'exec'];(entry/'environ').write_bytes(b'UNIO_LEAD_ATTEMPT=token\0')
            check('only the already owned attempt is exempt',not m.external_codex(f,'token') and m.external_codex(f,'other'))


daemon_admission_checks()
if sys.argv[1:] == ['--daemon-only']:
    print('lead cooldown daemon admission: %d assertions passed; model calls=0' % passed)
    raise SystemExit(0)


q = proof(quota())
check('known five-hour fallback is exactly 18060 seconds', q['wait']['wake_at'] == D + 18060)
check('real reset uses reset plus 60 seconds', proof(quota(reset=D+7200))['wait']['wake_at'] == D+7260)
check('a fourteen-day reset is retained', proof(quota(duration=20160, reset=D+14*86400))['wait']['wake_at'] == D+14*86400+60)
check('unknown weekly reset stays unresolved', proof(quota(duration=10080))['wait']['wake_at'] is None)
check('unknown duration cannot become five-hour', proof(quota(duration=None))['wait']['source'] == 'unresolved')
check('stale five-hour reset creates a fresh fallback', proof(quota(reset=D-10))['wait']['wake_at'] == D+18060)
check('a near reset cannot rapid-loop', proof(quota(reset=D+1))['wait']['wake_at'] == D+300)
unknown_weekly = dict(usedPercent=100, windowDurationMins=10080, resetsAt=None)
check('shorter known reset cannot hide unknown weekly reset',
      proof(quota(reset=D+200, secondary=unknown_weekly))['wait']['wake_at'] is None)
unknown_duration = dict(usedPercent=100, windowDurationMins=None, resetsAt=None)
check('unknown exhausted window cannot be guessed shorter',
      proof(quota(secondary=unknown_duration))['wait']['kind'] == 'unknown_longer')
allowed = quota(allowed=True)
check('explicit ordinary permission permits a launch', proof(allowed)['state'] == 'no_limit')
unknown = quota(allowed=True); unknown['ordinaryUsageAllowed'] = None
check('low usage percentages cannot establish recovery', refuses(lambda: proof(unknown)))
check('API account is unsupported', refuses(lambda: m.classify({'account': {'type': 'apiKey'}}, allowed, D)))
check('managed account requires a verified adapter', refuses(lambda: m.classify({'account': {'type': 'chatgpt', 'planType': 'enterprise'}}, allowed, D)))
bad = quota(); bad['rateLimits']['primary']['usedPercent'] = True
check('boolean percentage is invalid metadata', refuses(lambda: proof(bad)))
check('API key override refuses before dispatch', refuses(lambda: m.environment_digest({'OPENAI_API_KEY': 'fixture'})))
check('endpoint override refuses before dispatch', refuses(lambda: m.environment_digest({'OPENAI_BASE_URL': 'https://example.invalid'})))
workspace_block = quota(); workspace_block['rateLimits']['rateLimitReachedType'] = 'workspace_owner_credits_depleted'
check('workspace credit block cannot borrow five-hour fallback', proof(workspace_block)['wait']['wake_at'] is None)

with tempfile.TemporaryDirectory(prefix='lead-cooldown-') as tmp:
    base = Path(tmp)
    executable = base / 'codex-stub'
    executable.write_text(r'''#!/usr/bin/env python3
import json, os, subprocess, sys, time
from pathlib import Path
base=Path(os.environ['COOLDOWN_FIXTURE'])
def record(value):
 with (base/'calls').open('a') as out: out.write(json.dumps(value)+'\n')
if sys.argv[1:]==['--version']:
 print('codex-cli 0.161.0');sys.exit(0)
if 'app-server' in sys.argv:
 record({'probe_pid':os.getpid()})
 for line in sys.stdin:
  request=json.loads(line);record(request)
  method=request['method']
  assert method in ['initialize','initialized','account/read','account/rateLimits/read']
  if method=='initialized':continue
  if method=='initialize':result={'userAgent':'mock'}
  elif method=='account/read':result={'account':{'type':'chatgpt','planType':'plus','email':'private@example.invalid'}}
  else:result=json.loads((base/'quota').read_text())
  if (base/'protocol-case').exists():
   case=(base/'protocol-case').read_text()
   if case=='timeout':
    while True:time.sleep(1)
   if case=='oversized':print('x'*1100000,flush=True);continue
   if case=='malformed':print('not json',flush=True);continue
  print(json.dumps({'id':request['id'],'result':result}),flush=True)
 sys.exit(0)
record({'exec_pid':os.getpid(),'argv':sys.argv[1:]})
fds=[]
for item in Path('/proc/self/fd').iterdir():
 try:fds.append(os.readlink(item))
 except OSError:pass
(base/'fds').write_text(json.dumps(fds))
(base/'prompt').write_text(sys.stdin.read())
case=(base/'case').read_text()
print(json.dumps({'type':'turn.started'}),flush=True)
if case=='hang':
 while True:time.sleep(0.05)
if case=='child':
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True,
  close_fds=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 (base/'worker-pid').write_text(str(child.pid))
if case in ['success','child','mixed']:print(json.dumps({'type':'turn.completed'}),flush=True)
if case in ['failed','mixed']:
 print(json.dumps({'type':'turn.failed','error':{'message':'ignored text'}}),flush=True);sys.exit(1)
if case=='crash':sys.exit(7)
if case=='oversized':print('x'*1100000,flush=True)
if case=='phrase':print(json.dumps({'type':'item.completed','item':{'text':'usage limit exceeded resets in 5 hours'}}),flush=True)
sys.exit(0)
''')
    executable.chmod(0o700)
    runner = base / 'unio-stub'
    runner.write_text('#!/usr/bin/env python3\nimport json\nprint(json.dumps(dict(lead_agent="codex",tier="low")))\n')
    runner.chmod(0o700)
    fixture_env = dict(os.environ, COOLDOWN_FIXTURE=str(base))

    def calls():
        return [json.loads(line) for line in (base/'calls').read_text().splitlines()] if (base/'calls').exists() else []

    def exec_count():
        return sum('exec_pid' in item for item in calls())

    def frozen(root):
        f = dict(adapter='codex-exec-0.161.0', codex=str(executable), version=m.VERSION,
                 binary_sha256=m.sha(executable.read_bytes()), model='fixture-model', effort='high',
                 sandbox='workspace-write', cwd=str(root), codex_home=str(base/'native-config'),
                 config_sha256='0'*64, environment_sha256='1'*64, goal_sha256=m.sha(b'Finish the fixture goal.'))
        f['argv'] = m.lead_argv(f)
        return f

    class Adapter:
        def __init__(self, f, clock):
            self.frozen = f
            self.clock = clock
            self.env = fixture_env
            self.response = allowed
            self.probes = 0
            self.change = False

        def check(self, goal):
            m.require(not self.change and m.sha(goal) == self.frozen['goal_sha256'], 'launch_changed')

        def probe(self):
            self.probes += 1
            return proof(self.response, self.clock())

    def scenario(name, case='success'):
        root = base / ('project with spaces ' + name)
        (root/'coord').mkdir(parents=True)
        (root/'wt').mkdir()
        store = m.Store(root, create=True)
        goal = b'Finish the fixture goal.'
        m.durable(store.directory/'goal.md', goal)
        f = frozen(root)
        clock = [D]
        state = m.fresh_state(f, clock[0])
        with store.locked():store.write(state, clock[0])
        adapter = Adapter(f, lambda: clock[0])
        supervisor = m.Supervisor(store, str(runner), adapter, clock=adapter.clock)
        (base/'case').write_text(case)
        return store, adapter, supervisor, clock

    def finish(supervisor, deadline=8):
        end = time.monotonic()+deadline
        while supervisor.process is not None and time.monotonic()<end:
            supervisor.step();time.sleep(0.01)
        assert supervisor.process is None, 'local fixture process did not finish'

    # Avoid observing the real host's active Codex; all actual spawned model
    # processes in these fixtures are the local executable above.
    with patch.object(m, 'external_codex', return_value=False):
        store, adapter, supervisor, clock = scenario('wait', 'failed')
        before = exec_count()
        supervisor.step();finish(supervisor)
        # First failure with explicitly allowed quota halts, no guessed retry.
        check('nonquota failure halts with actual exit1', store.read()['phase']=='halted' and store.read()['attempts'][-1]['exit_code']==1)
        clock[0] += 999999
        check('ordinary failure does not relaunch itself', supervisor.step() is False and exec_count()==before+1)

        store, adapter, supervisor, clock = scenario('quota', 'failed')
        before=exec_count()
        supervisor.step()
        adapter.response=quota()
        finish(supervisor)
        check('actual failure plus structured quota enters persisted cooldown', store.read()['phase']=='cooldown' and store.read()['attempts'][-1]['outcome']=='limit')
        wake=store.read()['cooldown']['wake_at'];probes=adapter.probes
        clock[0]=wake-1;supervisor.step()
        check('no model or metadata request during known wait', exec_count()==before+1 and adapter.probes==probes)
        clock[0]=wake
        adapter.response=allowed;(base/'case').write_text('success')
        supervisor.step();finish(supervisor)
        check('at wake starts exactly one new local session', exec_count()==before+2 and store.read()['attempts_total']==2)
        check('successful turn stops normal relaunch and clears consecutive limits', supervisor.step() is False and store.read()['halt_reason']=='turn_ended' and store.read()['consecutive_limits']==0)
        check('goal and reconciliation reach the actual lead stdin', all(s in (base/'prompt').read_text() for s in ['Finish the fixture goal.','Do not redispatch completed or unknown tasks','unio policy','no-replay claims']))
        check('lead has no inherited state/account/control descriptors', not any('state.lock' in s or 'supervisor.lock' in s or 'work-policy' in s for s in json.loads((base/'fds').read_text())))
        check('lead argv preserves explicit model effort sandbox without bypass', '--dangerously-bypass-approvals-and-sandbox' not in store.read()['frozen']['argv'] and store.read()['frozen']['argv']==m.lead_argv(store.read()['frozen']))

        store, adapter, supervisor, clock = scenario('weekly')
        adapter.response=quota(duration=10080)
        before=exec_count();supervisor.step()
        check('unknown weekly wait persists without a five-hour timer', store.read()['phase']=='unresolved' and store.read()['cooldown']['wake_at'] is None)
        probes=adapter.probes;clock[0]+=3599;supervisor.step()
        check('unknown longer poll is no more often than hourly', adapter.probes==probes and exec_count()==before)
        clock[0]+=1;adapter.response=allowed;supervisor.step();finish(supervisor)
        check('authoritative recovery exits unknown longer wait', exec_count()==before+1)

        store, adapter, supervisor, clock = scenario('loop')
        adapter.response=quota()
        before=exec_count()
        for i in range(7):
            supervisor.step()
            if store.read()['cooldown']:clock[0]=store.read()['cooldown']['wake_at']
        check('seventh repeated limit halts without a launch loop', store.read()['halt_reason']=='limit_loop' and exec_count()==before)
        check('limit-loop halt needs explicit resume', supervisor.step() is False)

        for command, mode in [('pause','paused'),('stop','stopped'),('complete','completed')]:
            store, adapter, supervisor, clock = scenario(command)
            adapter.response=quota();supervisor.step()
            wake=store.read()['cooldown']['wake_at']
            m.controls(store, command, clock[0]);clock[0]=wake+100000
            restored=m.Supervisor(store,str(runner),adapter,adapter.clock)
            before=exec_count();probes=adapter.probes
            check(command+' persists across supervisor restart', restored.step() is False and store.read()['mode']==mode and exec_count()==before and adapter.probes==probes)
            if command=='pause':
                m.controls(store,'resume',clock[0]);adapter.response=allowed
                restored.step();finish(restored)
                check('explicit resume permits overdue paused wait', store.read()['attempts_total']==1)
            else:
                check(command+' cannot be resurrected by resume', refuses(lambda: m.controls(store,'resume',clock[0])))
                check(command+' is idempotent', m.controls(store,command,clock[0])['mode']==mode)

        store, adapter, supervisor, clock = scenario('stop-marker')
        adapter.response=quota();supervisor.step();clock[0]+=6*3600
        (store.root/'coord/STOP').touch();adapter.response=allowed
        before=exec_count();probes=adapter.probes;supervisor.step()
        check('host sleep past wake respects STOP without probes', exec_count()==before and adapter.probes==probes)
        (store.root/'coord/STOP').unlink();supervisor.step();finish(supervisor)
        check('clearing STOP resumes persisted overdue wait', exec_count()==before+1)

        store, adapter, supervisor, clock = scenario('pause-race')
        expected=store.read();permission=adapter.probe();m.controls(store,'pause',clock[0])
        before=exec_count();supervisor.launch(expected,permission)
        check('pause wins race with a previously prepared launch', exec_count()==before and store.read()['attempts_total']==0)

        store, adapter, supervisor, clock = scenario('signal','hang')
        supervisor.step();pid=supervisor.process.pid
        for _ in range(10):supervisor.step();time.sleep(0.01)
        supervisor.interrupted=True;supervisor.step();finish(supervisor)
        check('supervisor interruption reaps owned lead and stores real signal', m.process_identity(pid) is None and store.read()['attempts'][-1]['exit_code']==-signal.SIGTERM and store.read()['halt_reason']=='interrupted')

        store, adapter, supervisor, clock = scenario('worker-session','child')
        supervisor.step();finish(supervisor)
        worker_pid=int((base/'worker-pid').read_text())
        check('lead cleanup preserves separately sessioned native worker', m.process_identity(worker_pid) is not None)
        os.kill(worker_pid,signal.SIGTERM)

        store, adapter, supervisor, clock = scenario('orphan','hang')
        supervisor.step()
        for _ in range(10):supervisor.step();time.sleep(0.01)
        orphan=m.Supervisor(store,str(runner),adapter,adapter.clock)
        before=exec_count();orphan.step()
        check('supervisor crash with live token becomes orphan wait, no duplicate', store.read()['phase']=='orphan_wait' and exec_count()==before)
        supervisor.process.terminate();supervisor.process.wait()
        for stream in (supervisor.process.stdin,supervisor.process.stdout,supervisor.process.stderr):stream.close()
        supervisor.selector.close();supervisor.process=None
        orphan.step()
        check('lost nonchild exit becomes unknown, never fabricated success', store.read()['halt_reason']=='outcome_unknown' and store.read()['attempts'][-1]['outcome']=='unknown' and store.read()['attempts'][-1]['exit_code'] is None)
        check('unknown outcome with available quota is not replayed', orphan.step() is False and exec_count()==before)

        store, adapter, supervisor, clock = scenario('launching-crash')
        state=store.read();token='a'*32
        state['attempts_total']=1
        state['attempts']=[dict(attempt_id=token,seq=1,launched_at=D,ended_at=None,exit_code=None,signal=None,saw_turn_failed=False,saw_turn_completed=False,probe='no_limit',outcome=None)]
        state.update(phase='launching',lead=dict(attempt_id=token,pid=None,start_ticks=None,session_id=None,boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(),launched_at=D))
        with store.locked():store.write(state,clock[0])
        before=exec_count();supervisor.step()
        check('crash between durable claim and spawn does not re-dispatch', store.read()['halt_reason']=='outcome_unknown' and exec_count()==before)

        for case in ['crash','phrase','mixed','oversized']:
            store, adapter, supervisor, clock = scenario(case,case)
            supervisor.step();finish(supervisor)
            before=exec_count()
            check(case+' output never authorizes automatic relaunch', supervisor.step() is False and exec_count()==before and store.read()['phase']=='halted')
            if case=='crash':check('plain crash never probes after exit', adapter.probes==1 and store.read()['attempts'][-1]['exit_code']==7)
            if case=='mixed':check('completed event cannot mask later failure', store.read()['attempts'][-1]['outcome']=='failed')

        store, adapter, supervisor, clock = scenario('changed')
        adapter.change=True;before=exec_count();supervisor.step()
        check('changed launch halts before probe/provider', store.read()['halt_reason']=='launch_changed' and adapter.probes==0 and exec_count()==before)

        store, adapter, supervisor, clock = scenario('null')
        adapter.response=unknown;before=exec_count();supervisor.step()
        check('unavailable quota permission halts before launch', store.read()['halt_reason']=='probe_unavailable' and exec_count()==before)

    # Strict state and lock evidence use actual files and flock.
    store, adapter, supervisor, clock = scenario('strict-state')
    valid=store.path.read_bytes()
    for name, raw in [('unknown-key',json.dumps(dict(store.read(), unexpected=1)).encode()),
                      ('duplicate-key',valid.replace(b'"schema_version":1',b'"schema_version":1,"schema_version":1')),
                      ('unknown-schema',valid.replace(b'"schema_version":1',b'"schema_version":99')),
                      ('malformed',b'not json'),('oversized',b'x'*(m.STATE_CAP+1))]:
        m.durable(store.path,raw)
        check(name+' state refuses without resetting it', refuses(store.read) and store.path.read_bytes()==raw)
    m.durable(store.path,valid)
    saved=store.path.with_name('saved');store.path.rename(saved);store.path.symlink_to(saved)
    check('symlinked state refuses', refuses(store.read))
    store.path.unlink();saved.rename(store.path)
    os.chmod(store.path,0o644)
    check('nonprivate state refuses', refuses(store.read))
    os.chmod(store.path,0o600)
    fd=store.open_lock('supervisor.lock',blocking=False)
    check('second supervisor cannot acquire lifetime ownership', refuses(lambda:store.open_lock('supervisor.lock',blocking=False)) and store.busy())
    os.close(fd)
    check('kernel releases lifetime ownership after close', not store.busy())
    check('enabled supervisor prevents lead reservation change', refuses(lambda:m.lead_change_guard(store.root).__enter__()))
    m.controls(store,'stop',D)
    with m.lead_change_guard(store.root):check('terminal idle supervisor permits reservation change',True)

    # Probe's real stdin protocol: exact four messages, no model/credit/auth mutation.
    store, adapter, supervisor, clock = scenario('rpc')
    (base/'quota').write_text(json.dumps(quota(reset=D+7200)))
    before=len(calls())
    codex=m.CodexAdapter(store.root,store.read()['frozen'],env=fixture_env,clock=lambda:D)
    observed=codex.probe();items=calls()[before:]
    methods=[item['method'] for item in items if 'method' in item]
    check('probe sends exactly documented read-only handshake/messages', methods==['initialize','initialized','account/read','account/rateLimits/read'])
    check('probe never sends automatic fallback or auth refresh', items[-2]['params']=={'refreshToken':False} and items[-1]['params']=={'excludeResetCreditDetails':True})
    probe_pid=next(item['probe_pid'] for item in items if 'probe_pid' in item)
    check('real protocol parser reads structured wait then reaps probe', observed['wait']['wake_at']==D+7260 and m.process_identity(probe_pid) is None)
    check('quota receipt contains no email or raw credential', 'private@example.invalid' not in json.dumps(observed))
    codex.probe_timeout=0.3
    for case in ['malformed','oversized','timeout']:
        (base/'protocol-case').write_text(case)
        check('probe '+case+' output refuses and is reaped', refuses(codex.probe))
        pid=next(item['probe_pid'] for item in reversed(calls()) if 'probe_pid' in item)
        check('probe '+case+' leaves no process',m.process_identity(pid) is None)
    (base/'protocol-case').unlink()

    # Configuration snapshots read only the isolated pretend home and fixture
    # project. No actual user configuration, auth store or live app-server.
    fake_home=base/'pretend-home';(fake_home/'.codex').mkdir(parents=True)
    with patch.object(m.Path,'home',return_value=fake_home):
        _,initial=m.configuration(store.root,{})
        project_config=store.root/'.codex';project_config.mkdir()
        (project_config/'config.toml').write_text('model_provider="openai"\n')
        _,changed=m.configuration(store.root,{})
        check('new project configuration changes frozen digest',initial!=changed)
        (project_config/'config.toml').write_text('model_provider="custom"\n')
        check('custom project provider is refused',refuses(lambda:m.configuration(store.root,{})))
        (project_config/'config.toml').unlink();(fake_home/'.codex/config.toml').write_text('profile="paid"\n')
        check('default profile that could change route is refused',refuses(lambda:m.configuration(store.root,{})))

    # Public CLI state surfaces in an isolated staged installation, no adapter.
    install=base/'install';env=dict(os.environ,UNIO_BIN_DIR=str(install/'bin'),UNIO_CONF_DIR=str(install/'conf'),
                                  UNIO_COMPLETION_DIR=str(install/'completion'))
    subprocess.run(['bash',str(ROOT/'unio-install.sh')],env=env,check=True,capture_output=True)
    at=str(install/'bin/unio')
    (store.root/'repo').mkdir()
    def cli(*args):return subprocess.run([at,'lead-cooldown',*args],cwd=store.root/'repo',env=env,capture_output=True,text=True,timeout=20)
    result=cli('status','--json')
    check('packaged CLI loads helper and returns real state JSON',result.returncode==0 and json.loads(result.stdout)['state']['enablement_id']==store.read()['enablement_id'])
    result=cli('pause')
    check('packaged pause persists',result.returncode==0 and store.read()['mode']=='paused')
    registration=subprocess.run([at,'lead','none'],cwd=store.root/'repo',env=env,capture_output=True,text=True,timeout=20)
    check('native policy setter refuses while paused supervisor owns registration',registration.returncode!=0 and not (store.root/'coord/work-policy.json').exists())
    result=cli('stop')
    check('packaged stop persists',result.returncode==0 and store.read()['mode']=='stopped')
    result=cli('resume')
    check('packaged resume cannot resurrect stopped goal',result.returncode!=0)
    result=cli('status','--unexpected')
    check('surplus public arguments refuse',result.returncode!=0)
    m.durable(store.path,b'{broken')
    result=cli('status','--json')
    check('packaged corrupt status is explicit and nonzero',result.returncode!=0 and json.loads(result.stdout)['state']=='corrupt')
    result=cli('stop','--force-corrupt')
    check('explicit force-stop preserves corrupt evidence',result.returncode==0 and store.read()['mode']=='stopped' and any(p.read_bytes()==b'{broken' for p in store.directory.glob('state.corrupt-*')))
    check('standalone installed helper matches canonical source', (install/'conf/lib/lead_cooldown.py').read_bytes()==(ROOT/'tools/runtime/lead_cooldown.py').read_bytes())

    # Actual detached command -> inherited lifetime lock -> private supervise
    # entry. The adapter alone is substituted; no production test override.
    store, adapter, supervisor, clock = scenario('detached-controls')
    store.path.unlink()  # A genuinely disabled fixture project, not a replay.
    goal_path=store.root/'coord/owner-goal.md';goal_path.write_bytes(b'Finish the fixture goal.')
    frozen_launch=frozen(store.root)
    harness=base/'detached-harness.py'
    harness.write_text('''import importlib.util,json,os,sys,time\nfrom pathlib import Path\np=Path(%r)\nspec=importlib.util.spec_from_file_location('cooldown',p)\nm=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)\nclass LocalAdapter:\n def __init__(self,root,frozen,**kwargs):\n  self.root=Path(root);self.frozen=frozen;self.env=dict(os.environ)\n  (self.root/'coord'/('detached-ready-'+str(os.getpid()))).write_text('owned')\n def check(self,goal):m.require(m.sha(goal)==self.frozen['goal_sha256'],'launch_changed')\n def probe(self):return m.classify(%r,%r,time.time())\nm.CodexAdapter=LocalAdapter\nm.external_codex=lambda *args:False\nsys.exit(m.main(sys.argv[1:]))\n''' % (str(ROOT/'tools/runtime/lead_cooldown.py'), ACCOUNT, quota()))
    class LocalAdapter:
        def __init__(self,*args,**kwargs):pass
        def probe(self):return proof(quota(),time.time())
    children=[]
    original_spawn=m.spawn_supervisor
    def spawn(*args):
        pid=original_spawn(*args);children.append(pid);return pid
    def invoke(*args):
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            return m.main([str(store.root),'--runner',str(runner),*args])
    def ready(pid):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            if (store.root/'coord'/('detached-ready-'+str(pid))).exists():return
            time.sleep(0.02)
        raise AssertionError('detached supervisor did not validate inherited ownership')
    def ended(pid):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline and store.busy():time.sleep(0.02)
        assert not store.busy(),'detached supervisor did not stop'
        os.waitpid(pid,0)
    with patch.dict(os.environ),patch.object(m,'launch_snapshot',return_value=frozen_launch),\
         patch.object(m,'CodexAdapter',LocalAdapter),patch.object(m,'external_codex',return_value=False),\
         patch.object(m,'__file__',str(harness)),patch.object(m,'spawn_supervisor',side_effect=spawn):
        os.environ.pop('CODEX_THREAD_ID',None);os.environ.pop('UNIO_LEAD_SUPERVISED',None)
        result=invoke('start','--model','fixture-model','--cd',str(store.root),'--goal-file',str(goal_path))
        check('explicit start creates a real detached supervisor',result==0 and len(children)==1)
        ready(children[-1])
        check('child retains lifetime ownership after launcher closes descriptor',store.busy() and store.read()['phase']=='cooldown')
        result=invoke('start','--model','fixture-model','--cd',str(store.root),'--goal-file',str(goal_path))
        check('competing public start is refused without another child',result==2 and len(children)==1)
        result=invoke('resume')
        check('resume against a live supervisor does not spawn another',result==0 and len(children)==1)
        result=invoke('pause');ended(children[-1])
        check('pause ends idle detached supervisor and preserves wait',result==0 and store.read()['mode']=='paused' and store.read()['cooldown']['wake_at'] is not None)
        result=invoke('resume');ready(children[-1])
        check('resume respawns exactly one missing supervisor',result==0 and len(children)==2 and store.busy())
        result=invoke('stop');ended(children[-1])
        check('stop persists after detached supervisor exits',result==0 and store.read()['mode']=='stopped' and not store.busy())
        check('terminal public resume creates no new process',invoke('resume')!=0 and len(children)==2)

print('lead cooldown: %d assertions passed; model calls=0' % passed)
