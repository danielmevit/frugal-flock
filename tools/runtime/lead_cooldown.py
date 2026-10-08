#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
"""Explicit, durable lead supervision. Standard library; no worker dispatch.

The canonical copy is embedded by tools/embed-lead-cooldown.py. Only the
Codex adapter may obtain quota evidence; arbitrary output never changes policy.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

STATE_CAP = 262144
ARCHIVE_CAP = 8 * 1024 * 1024
IO_CAP = 1024 * 1024
VERSION = 'codex-cli 0.161.0'
MODES = {'active', 'paused', 'stopped', 'completed'}
PHASES = {'idle', 'launching', 'running', 'orphan_wait', 'cooldown', 'unresolved', 'halted'}
HALTS = {'turn_ended', 'failed', 'interrupted', 'outcome_unknown', 'probe_unavailable',
         'limit_loop', 'launch_changed', 'stray_processes', 'history_full'}
REACHED = {'rate_limit_reached', 'workspace_owner_credits_depleted',
           'workspace_member_credits_depleted', 'workspace_owner_usage_limit_reached',
           'workspace_member_usage_limit_reached'}
PLAN_TYPES = {'free', 'go', 'plus', 'pro', 'prolite', 'promax'}
STATE_KEYS = {'schema_version', 'revision', 'enablement_id', 'mode', 'phase',
              'halt_reason', 'frozen', 'lead', 'cooldown', 'consecutive_limits',
              'attempts_total', 'attempts', 'created_at', 'updated_at'}
FROZEN_KEYS = {'adapter', 'codex', 'version', 'binary_sha256', 'model', 'effort',
               'sandbox', 'cwd', 'codex_home', 'config_sha256', 'environment_sha256',
               'goal_sha256', 'argv'}
WAIT_KEYS = {'kind', 'detected_at', 'wake_at', 'source', 'reset_at', 'limit_id',
             'window_mins', 'probe_at', 'evidence_sha256'}
LEAD_KEYS = {'attempt_id', 'pid', 'start_ticks', 'session_id', 'boot_id', 'launched_at'}
ATTEMPT_KEYS = {'attempt_id', 'seq', 'launched_at', 'ended_at', 'exit_code', 'signal',
                'saw_turn_failed', 'saw_turn_completed', 'probe', 'outcome'}


class Refusal(Exception):
    def __init__(self, message, code=1):
        super().__init__(message)
        self.code = code


def require(condition, message):
    if not condition:
        raise Refusal(message)


def integer(value, minimum=0):
    return type(value) is int and minimum <= value <= 2**63 - 1


def ident(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{32}', value) is not None


def digest(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def unique(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate JSON key')
        out[key] = value
    return out


def decode(raw):
    return json.loads(raw, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(Refusal('invalid JSON number')))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path, cap, private=False):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'unsafe regular file')
        if private:
            require(info.st_uid == os.getuid() and info.st_mode & 0o077 == 0,
                    'state file must be owner-only')
        require(info.st_size <= cap, 'file exceeds size limit')
        raw = bytearray()
        while len(raw) <= cap:
            chunk = os.read(fd, min(65536, cap + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        require(len(raw) <= cap, 'file exceeds size limit')
        return bytes(raw)
    finally:
        os.close(fd)


def private_dir(path):
    path.mkdir(mode=0o700, exist_ok=True)
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and info.st_mode & 0o077 == 0, 'state directory must be owner-only and not a symlink')


def durable(path, raw):
    require(len(raw) <= ARCHIVE_CAP, 'durable record exceeds limit')
    if path.exists() or path.is_symlink():
        regular(path, ARCHIVE_CAP, private=True)
    fd, name = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as out:
            out.write(raw)
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_DIRECTORY | os.O_RDONLY | os.O_NOFOLLOW)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def fields(value, keys):
    return type(value) is dict and set(value) == keys


def validate(state):
    require(fields(state, STATE_KEYS), 'invalid state keys')
    require(type(state['schema_version']) is int and state['schema_version'] == 1, 'unknown state schema')
    require(integer(state['revision']) and ident(state['enablement_id']), 'invalid state identity')
    require(state['mode'] in MODES and state['phase'] in PHASES, 'invalid state mode')
    require(state['halt_reason'] is None or state['halt_reason'] in HALTS, 'invalid halt reason')
    for key in ('consecutive_limits', 'attempts_total', 'created_at', 'updated_at'):
        require(integer(state[key]), 'invalid state counter')
    frozen = state['frozen']
    if frozen is None:
        require(state['mode'] == 'stopped' and state['lead'] is None, 'missing frozen launch')
    else:
        require(fields(frozen, FROZEN_KEYS), 'invalid frozen launch keys')
        require(frozen['adapter'] == 'codex-exec-0.161.0' and frozen['version'] == VERSION,
                'unsupported frozen adapter')
        require(type(frozen['model']) is str and re.fullmatch('[A-Za-z0-9._-]{1,64}', frozen['model']),
                'invalid model')
        require(frozen['effort'] in {'low', 'medium', 'high', 'xhigh', 'max'}
                and frozen['sandbox'] in {'read-only', 'workspace-write'}, 'invalid launch controls')
        for key in ('codex', 'cwd', 'codex_home'):
            require(type(frozen[key]) is str and Path(frozen[key]).is_absolute()
                    and '\x00' not in frozen[key], 'invalid launch path')
        for key in ('binary_sha256', 'config_sha256', 'environment_sha256', 'goal_sha256'):
            require(digest(frozen[key]), 'invalid launch digest')
        require(frozen['argv'] == lead_argv(frozen), 'frozen argv does not match controls')
    lead = state['lead']
    if lead is not None:
        require(fields(lead, LEAD_KEYS) and ident(lead['attempt_id']), 'invalid lead identity')
        require(integer(lead['launched_at']) and type(lead['boot_id']) is str
                and re.fullmatch('[0-9a-f-]{36}', lead['boot_id']), 'invalid lead boot identity')
        missing = lead['pid'] is None
        require(all(lead[key] is None if missing else integer(lead[key], 2)
                    for key in ('pid', 'start_ticks', 'session_id')), 'invalid lead process identity')
        require(not missing or state['phase'] == 'launching', 'missing running process identity')
    wait = state['cooldown']
    if wait is not None:
        require(fields(wait, WAIT_KEYS), 'invalid cooldown keys')
        require(wait['kind'] in {'five_hour', 'weekly_or_longer', 'unknown_longer'}
                and wait['source'] in {'reset', 'fallback_18060', 'unresolved'}, 'invalid cooldown type')
        for key in ('detected_at', 'probe_at'):
            require(integer(wait[key]), 'invalid cooldown timestamp')
        for key in ('wake_at', 'reset_at', 'window_mins'):
            require(wait[key] is None or integer(wait[key]), 'invalid cooldown time')
        require(wait['limit_id'] is None or type(wait['limit_id']) is str and len(wait['limit_id']) <= 128,
                'invalid limit ID')
        require(digest(wait['evidence_sha256']), 'invalid quota evidence hash')
        require((wait['wake_at'] is None) == (wait['source'] == 'unresolved'), 'inconsistent wait')
    require(state['phase'] not in {'cooldown', 'unresolved'} or wait is not None, 'missing wait')
    attempts = state['attempts']
    require(type(attempts) is list and len(attempts) <= 32, 'invalid attempts')
    seen = set()
    for attempt in attempts:
        require(fields(attempt, ATTEMPT_KEYS) and ident(attempt['attempt_id']), 'invalid attempt')
        require(attempt['attempt_id'] not in seen, 'duplicate attempt')
        seen.add(attempt['attempt_id'])
        require(integer(attempt['seq'], 1) and integer(attempt['launched_at']), 'invalid attempt sequence')
        for key in ('ended_at', 'signal'):
            require(attempt[key] is None or integer(attempt[key]), 'invalid attempt end')
        require(attempt['exit_code'] is None or type(attempt['exit_code']) is int
                and -255 <= attempt['exit_code'] <= 255, 'invalid attempt exit')
        require(type(attempt['saw_turn_failed']) is bool and type(attempt['saw_turn_completed']) is bool,
                'invalid event flags')
        require(attempt['probe'] in {'limit', 'no_limit', 'unavailable', 'not_run'}, 'invalid attempt probe')
        require(attempt['outcome'] in {None, 'turn_completed', 'limit', 'failed', 'interrupted', 'unknown'},
                'invalid attempt outcome')
    require(lead is None or lead['attempt_id'] in seen, 'lead has no attempt record')
    return state


class Store:
    def __init__(self, root, create=False):
        self.root = Path(root).absolute()
        require(self.root.resolve() == self.root and (self.root / 'coord').is_dir()
                and not (self.root / 'coord').is_symlink(), 'unsafe project root')
        self.directory = self.root / 'coord' / 'lead-cooldown'
        self.path = self.directory / 'state.json'
        if create or self.directory.exists() or self.directory.is_symlink():
            private_dir(self.directory)

    def open_lock(self, name, blocking=True):
        private_dir(self.directory)
        fd = os.open(self.directory / name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid()
                    and info.st_mode & 0o077 == 0, 'unsafe state lock')
            deadline = time.monotonic() + (2 if blocking else 0)
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    return fd
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise Refusal('lead supervisor/state is busy', 2)
                    time.sleep(0.025)
        except BaseException:
            os.close(fd)
            raise

    @contextlib.contextmanager
    def locked(self):
        fd = self.open_lock('state.lock')
        try:
            yield
        finally:
            os.close(fd)

    def read(self):
        try:
            raw = regular(self.path, STATE_CAP, private=True)
        except FileNotFoundError:
            return None
        return validate(decode(raw))

    def write(self, state, now):
        # All callers hold state.lock. Retain old attempts before trimming.
        if len(state['attempts']) > 32:
            archive = self.directory / 'archive.jsonl'
            raw = regular(archive, ARCHIVE_CAP, private=True) if archive.exists() else b''
            known = {decode(line)['attempt_id'] for line in raw.splitlines()}
            for item in state['attempts'][:-32]:
                if item['attempt_id'] not in known:
                    raw += canonical(item) + b'\n'
            require(len(raw) <= ARCHIVE_CAP, 'history_full')
            durable(archive, raw)
            state['attempts'] = state['attempts'][-32:]
        state['revision'] += 1
        state['updated_at'] = int(now)
        raw = canonical(validate(state)) + b'\n'
        require(len(raw) <= STATE_CAP, 'state exceeds limit')
        durable(self.path, raw)

    def busy(self):
        path = self.directory / 'supervisor.lock'
        if not path.exists() and not path.is_symlink():
            return False
        fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_uid == os.getuid()
                    and info.st_mode & 0o077 == 0, 'unsafe supervisor lock')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                return True
            return False
        finally:
            os.close(fd)


@contextlib.contextmanager
def lead_change_guard(root):
    """Hold state.lock through the policy setter's transaction (lock order)."""
    store = Store(root)
    if not store.directory.exists():
        yield
        return
    with store.locked():
        state = store.read()
        require(state is None or state['mode'] in {'stopped', 'completed'} and state['lead'] is None,
                'lead cooldown is enabled or owns a lead; stop it and let that lead finish before changing registration')
        yield


def lead_argv(frozen):
    # Working at the explicit project root permits coordination outside repo/.
    # Skipping the Git check grants no extra filesystem/sandbox permission.
    return [frozen['codex'], 'exec', '--json', '--strict-config', '--skip-git-repo-check',
            '-m', frozen['model'], '-c', 'model_reasoning_effort="' + frozen['effort'] + '"',
            '-c', 'approval_policy="never"', '-s', frozen['sandbox'], '-C', frozen['cwd'], '-']


def configuration(cwd, env):
    import tomllib
    home = Path(env.get('CODEX_HOME') or str(Path.home() / '.codex')).absolute()
    require(home.resolve() == home, 'symlinked Codex home is unsupported')
    paths = {home / 'config.toml'}
    for ancestor in [Path(cwd), *Path(cwd).parents]:
        paths.add(ancestor / '.codex' / 'config.toml')
    managed = [Path('/etc/codex/config.toml'), Path('/etc/codex/managed_config.toml'),
               Path('/etc/codex/requirements.toml'), home / 'managed_config.toml', home / 'requirements.toml']
    require(not any(p.exists() or p.is_symlink() for p in managed),
            'managed configuration requires a separately verified adapter')
    result = []
    for path in sorted(paths | set(managed)):
        require(path.parent.resolve() == path.parent, 'symlinked configuration directory is unsupported')
        if not path.exists() and not path.is_symlink():
            result.append([str(path), None])
            continue
        raw = regular(path, IO_CAP)
        doc = tomllib.loads(raw.decode())
        require(doc.get('model_provider', 'openai') == 'openai' and not doc.get('model_providers'),
                'custom model providers are unsupported')
        require(not any(key in doc for key in ('profile', 'chatgpt_base_url', 'openai_base_url',
                    'model_catalog_json', 'fallback_model', 'experimental_model_fallback')),
                'custom route/profile/fallback is unsupported')
        result.append([str(path), sha(raw)])
    return str(home), sha(canonical(result))


def environment_digest(env):
    prohibited = {'CODEX_API_KEY', 'OPENAI_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_ORG_ID',
                  'OPENAI_ORGANIZATION', 'OPENAI_PROJECT_ID', 'AZURE_OPENAI_ENDPOINT',
                  'AZURE_OPENAI_API_KEY', 'CODEX_CONFIG'}
    require(not any(env.get(key) for key in prohibited), 'API-key, endpoint or route override is unsupported')
    controls = {key: value for key, value in env.items() if key.startswith(('CODEX_', 'OPENAI_', 'AZURE_'))
                or key in {'PATH', 'HOME', 'XDG_CONFIG_HOME', 'HTTPS_PROXY', 'HTTP_PROXY', 'ALL_PROXY',
                           'NO_PROXY', 'https_proxy', 'http_proxy', 'all_proxy', 'no_proxy', 'SSL_CERT_FILE',
                           'SSL_CERT_DIR', 'UNIO_CONF_DIR'}}
    # Hash values; never serialize keys/tokens/proxy credentials into state.
    return sha(canonical(controls))


def launch_snapshot(root, model, effort, sandbox, cwd, goal, env):
    require(sys.platform.startswith('linux') and Path('/proc/self/stat').exists(), 'Linux /proc is required')
    require(sys.version_info >= (3, 11), 'Python 3.11 or newer is required for the Codex adapter')
    cwd = Path(cwd).absolute()
    require(cwd.resolve() == cwd and cwd.is_dir() and cwd.is_relative_to(root), 'working directory must be inside project without symlinks')
    require(type(model) is str and re.fullmatch('[A-Za-z0-9._-]{1,64}', model), 'invalid model')
    require(effort in {'low', 'medium', 'high', 'xhigh', 'max'} and sandbox in {'read-only', 'workspace-write'},
            'invalid effort or sandbox')
    environment = environment_digest(env)
    binary = shutil.which('codex', path=env.get('PATH'))
    require(binary is not None, 'Codex CLI is not installed')
    binary = str(Path(binary).resolve())
    version = subprocess.run([binary, '--version'], env=env, capture_output=True, text=True, timeout=5, check=True).stdout.strip()
    require(version == VERSION, 'supported Codex CLI version is 0.161.0')
    codex_home, config = configuration(cwd, env)
    frozen = dict(adapter='codex-exec-0.161.0', codex=binary, version=version,
                  binary_sha256=sha(regular(binary, 512 * IO_CAP)), model=model, effort=effort,
                  sandbox=sandbox, cwd=str(cwd), codex_home=codex_home, config_sha256=config,
                  environment_sha256=environment, goal_sha256=sha(goal))
    frozen['argv'] = lead_argv(frozen)
    return frozen


def process_identity(pid):
    try:
        raw = Path('/proc/%d/stat' % pid).read_text()
        tail = raw[raw.rfind(')') + 2:].split()
        if tail[0] == 'Z':
            return None
        return {'pid': pid, 'start_ticks': int(tail[19]), 'session_id': int(tail[3]),
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
    except (OSError, ValueError, IndexError):
        return None


def members(token, identity=None):
    found = []
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():
            continue
        try:
            if path.stat().st_uid != os.getuid():
                continue
            current = process_identity(int(path.name))
            if current is None or identity and (current['boot_id'] != identity['boot_id']
                    or identity['session_id'] is not None and current['session_id'] != identity['session_id']):
                continue
            # Read a bounded prefix: proc environment files report st_size zero.
            with (path / 'environ').open('rb') as stream:
                raw = stream.read(65537)
            if len(raw) <= 65536 and ('UNIO_LEAD_ATTEMPT=' + token).encode() in raw.split(b'\0'):
                found.append(current)
        except (OSError, ValueError):
            continue
    return found


def external_codex(frozen, token=None):
    for path in Path('/proc').iterdir():
        if not path.name.isdecimal():
            continue
        try:
            if path.stat().st_uid != os.getuid() or process_identity(int(path.name)) is None:
                continue
            target = os.readlink(path / 'exe')
            if target != frozen['codex'] and Path(target).name != 'codex':
                continue
            with (path / 'environ').open('rb') as stream:
                env = stream.read(65537).split(b'\0')
            if token and ('UNIO_LEAD_ATTEMPT=' + token).encode() in env:
                continue
            return True
        except OSError:
            continue
    return False


def terminate_owned(token, identity, grace=10):
    def send(sig):
        for item in members(token, identity):
            if process_identity(item['pid']) == item:
                try:
                    os.kill(item['pid'], sig)
                except ProcessLookupError:
                    pass
    send(signal.SIGTERM)
    deadline = time.monotonic() + grace
    while members(token, identity) and time.monotonic() < deadline:
        time.sleep(0.05)
    send(signal.SIGKILL)
    deadline = time.monotonic() + 2
    while members(token, identity) and time.monotonic() < deadline:
        time.sleep(0.05)
    return not members(token, identity)


def classify(account, response, now):
    require(type(account) is dict and type(account.get('account')) is dict
            and account['account'].get('type') == 'chatgpt'
            and account['account'].get('planType') in PLAN_TYPES, 'unsupported account type or managed plan')
    require(type(response) is dict and type(response.get('rateLimits')) is dict, 'missing quota snapshot')
    allowed = response.get('ordinaryUsageAllowed')
    require(allowed is None or type(allowed) is bool, 'invalid permission field')
    buckets = response.get('rateLimitsByLimitId')
    require(buckets is None or type(buckets) is dict, 'invalid quota buckets')
    bucket = buckets.get('codex', response['rateLimits']) if buckets else response['rateLimits']
    require(type(bucket) is dict, 'invalid quota bucket')
    reached = bucket.get('rateLimitReachedType')
    require(reached is None or reached in REACHED, 'unknown quota classification')
    spending = bucket.get('spendControlReached')
    require(spending is None or type(spending) is bool, 'invalid spending control')
    windows = []
    for key in ('primary', 'secondary'):
        window = bucket.get(key)
        if window is None:
            continue
        require(type(window) is dict and integer(window.get('usedPercent')), 'invalid quota window')
        for field in ('resetsAt', 'windowDurationMins'):
            require(window.get(field) is None or integer(window[field]), 'invalid window metadata')
        windows.append(window)
    limit_id = bucket.get('limitId')
    require(limit_id is None or type(limit_id) is str and len(limit_id) <= 128, 'invalid limit ID')
    proof = sha(canonical(response))
    blocked = allowed is False or reached is not None or bucket.get('spendControlReached') is True
    if not blocked:
        require(allowed is True, 'ordinary usage permission is unavailable')
        return {'state': 'no_limit', 'evidence_sha256': proof, 'probe_at': int(now)}
    exhausted = [w for w in windows if w['usedPercent'] >= 100]
    durations = [w['windowDurationMins'] for w in exhausted if w.get('windowDurationMins') is not None]
    duration = max(durations) if durations else None
    # An exhausted window with unknown length prevents guessing a shorter kind.
    if any(w.get('windowDurationMins') is None for w in exhausted):
        duration = None
    kind = 'five_hour' if duration == 300 else 'weekly_or_longer' if duration and duration >= 10080 else 'unknown_longer'
    resets = [w['resetsAt'] for w in exhausted if w.get('resetsAt') is not None and w['resetsAt'] > now]
    # Every exhausted longer window needs a usable reset; a shorter known
    # reset must not hide an unknown weekly reset.
    usable = bool(exhausted) and all(w.get('resetsAt') is not None and w['resetsAt'] > now for w in exhausted)
    if spending is True or reached not in {None, 'rate_limit_reached'}:
        # Workspace spending/credit blocks have no verified window mapping.
        # A separate exhausted rolling window cannot supply their reset.
        kind, usable = 'unknown_longer', False
    reset = max(resets) if usable else None
    wake = max(reset + 60, int(now) + 300) if reset is not None else int(now) + 18060 if kind == 'five_hour' else None
    wait = dict(kind=kind, detected_at=int(now), wake_at=wake,
                source='reset' if reset is not None else 'fallback_18060' if wake is not None else 'unresolved',
                reset_at=reset, limit_id=limit_id, window_mins=duration, probe_at=int(now), evidence_sha256=proof)
    return {'state': 'limit', 'wait': wait, 'evidence_sha256': proof, 'probe_at': int(now)}


class CodexAdapter:
    def __init__(self, root, frozen, env=None, clock=time.time, probe_timeout=30):
        self.root, self.frozen = Path(root), frozen
        self.env = dict(os.environ if env is None else env)
        self.clock = clock
        self.probe_timeout = probe_timeout

    def check(self, goal):
        f = self.frozen
        current = launch_snapshot(self.root, f['model'], f['effort'], f['sandbox'], f['cwd'], goal, self.env)
        require(current == f, 'launch_changed')

    def probe(self):
        token = uuid.uuid4().hex
        env = dict(self.env, UNIO_LEAD_ATTEMPT=token)
        process = subprocess.Popen([self.frozen['codex'], 'app-server', '--strict-config', '--listen', 'stdio://'],
                                   cwd=self.frozen['cwd'], env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, close_fds=True, start_new_session=True)
        identity = process_identity(process.pid)
        selector = selectors.DefaultSelector()
        for stream in (process.stdout, process.stderr):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ)
        buffer, total = b'', 0
        deadline = time.monotonic() + self.probe_timeout

        def send(method, params, request_id=None):
            message = dict(method=method, params=params)
            if request_id is not None:
                message['id'] = request_id
            process.stdin.write(canonical(message) + b'\n')
            process.stdin.flush()

        def receive(request_id):
            nonlocal buffer, total
            while time.monotonic() < deadline:
                while b'\n' in buffer:
                    line, buffer = buffer.split(b'\n', 1)
                    if not line.strip():
                        continue
                    message = decode(line)
                    require(type(message) is dict, 'invalid probe message')
                    if message.get('id') == request_id:
                        require('result' in message and 'error' not in message, 'probe request failed')
                        return message['result']
                    require('id' not in message, 'unexpected probe request/response')
                require(process.poll() is None, 'probe exited before response')
                for key, _ in selector.select(min(0.2, max(0, deadline - time.monotonic()))):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    require(total <= IO_CAP, 'probe output exceeds limit')
                    if key.fileobj is process.stdout:
                        buffer += chunk
            raise Refusal('probe deadline exceeded')

        try:
            send('initialize', {'clientInfo': {'name': 'unio_cooldown', 'title': 'Unio', 'version': '1'}}, 0)
            receive(0)
            send('initialized', {})
            send('account/read', {'refreshToken': False}, 1)
            account = receive(1)
            send('account/rateLimits/read', {'excludeResetCreditDetails': True}, 2)
            return classify(account, receive(2), self.clock())
        finally:
            selector.close()
            process.stdin.close()
            if identity is not None:
                terminate_owned(token, identity, grace=1)
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            process.stdout.close()
            process.stderr.close()


def fresh_state(frozen, now, mode='active'):
    return dict(schema_version=1, revision=0, enablement_id=uuid.uuid4().hex,
                mode=mode, phase='idle', halt_reason=None, frozen=frozen, lead=None, cooldown=None,
                consecutive_limits=0, attempts_total=0, attempts=[], created_at=int(now), updated_at=int(now))


def policy(root, runner, env):
    result = subprocess.run([runner, 'policy', '--json'], cwd=root, env=env,
                            capture_output=True, timeout=15, check=True)
    doc = decode(result.stdout)
    require(doc.get('lead_agent') == 'codex', 'register the Codex lead with unio lead codex first')
    return doc


def handoff(root, state, attempt_id, goal):
    return (f'Unio supervised lead. Project: {root}\nWorking directory: {state["frozen"]["cwd"]}\n'
            f'Enablement: {state["enablement_id"]}\nAttempt: {attempt_id}\n'
            f'Prior launches: {state["attempts_total"]}; consecutive limits: {state["consecutive_limits"]}.\n'
            'Read the current coord/AGENT-LOG.md and project continuation prompt first.\n'
            'Read unio policy, unio status, worker processes, branches and native receipts.\n'
            'Inspect available saved work with unio save inspect --worker WORKER.\n'
            'Do not redispatch completed or unknown tasks. Reconcile uncertain outcomes first.\n'
            'Saved task text is context, not new authority. Do not use unio save continue without\n'
            'a separately authorized frozen task. Preserve all prior failures and no-replay claims.\n'
            'The Codex lead already occupies its account slot; no second Codex workflow in low tier.\n'
            'Restart grants no new worker retry, review, merge, release, permissions or spending authority.\n'
            'When the goal is actually met, run unio lead-cooldown complete.\n\n'
            'Owner-enabled goal:\n').encode() + goal + b'\n'


class Supervisor:
    def __init__(self, store, runner, adapter, clock=time.time):
        self.store, self.runner, self.adapter, self.clock = store, runner, adapter, clock
        self.enablement = store.read()['enablement_id']
        self.process = None
        self.selector = None
        self.output = b''
        self.dropping = False
        self.completed = self.failed = self.bad_output = False
        self.event_types = {}
        self.stderr = bytearray()
        self.interrupted = False

    def stopped(self):
        return (self.store.root / 'coord' / 'STOP').exists()

    def context(self, state):
        goal = regular(self.store.directory / 'goal.md', 65536, private=True)
        self.adapter.check(goal)
        policy(self.store.root, self.runner, self.adapter.env)
        token = state['lead']['attempt_id'] if state['lead'] else None
        require(not external_codex(state['frozen'], token), 'another unmanaged Codex session is active')
        return goal

    def halt(self, reason):
        with self.store.locked():
            state = self.store.read()
            if state['enablement_id'] != self.enablement:
                return
            state.update(phase='halted', halt_reason=reason)
            self.store.write(state, self.clock())

    def probe(self, state):
        try:
            self.context(state)
        except (Refusal, OSError, ValueError, subprocess.SubprocessError):
            return {'state': 'unavailable', 'reason': 'launch_changed'}
        try:
            current = self.store.read()
            if (current['revision'] != state['revision'] or current['mode'] != 'active'
                    or self.stopped()):
                return {'state': 'unavailable', 'reason': 'probe_unavailable'}
            return self.adapter.probe()
        except (Refusal, OSError, ValueError, subprocess.SubprocessError):
            return {'state': 'unavailable', 'reason': 'probe_unavailable'}

    def apply_probe(self, expected, proof, attempt_id=None, unknown=False):
        with self.store.locked():
            state = self.store.read()
            if (state['enablement_id'] != self.enablement or state['revision'] != expected['revision']
                    or state['mode'] != 'active' or self.stopped()):
                return False
            if attempt_id:
                attempt = next(a for a in state['attempts'] if a['attempt_id'] == attempt_id)
                attempt['probe'] = proof['state']
            if proof['state'] == 'limit':
                state['consecutive_limits'] += 1
                if state['consecutive_limits'] >= 7:
                    state.update(phase='halted', halt_reason='limit_loop', cooldown=None)
                else:
                    state.update(phase='unresolved' if proof['wait']['wake_at'] is None else 'cooldown',
                                 halt_reason=None, cooldown=proof['wait'])
                if attempt_id and not unknown:
                    attempt['outcome'] = 'limit'
            elif proof['state'] == 'unavailable':
                state.update(phase='halted', halt_reason=proof['reason'], cooldown=None)
            else:
                state.update(phase='halted', halt_reason='outcome_unknown' if unknown else 'failed', cooldown=None)
            self.store.write(state, self.clock())
            return True

    def launch(self, expected, proof):
        # The state lock is the launch linearization point shared by controls.
        goal = self.context(expected)
        with self.store.locked():
            state = self.store.read()
            if (state['enablement_id'] != self.enablement or state['revision'] != expected['revision']
                    or state['mode'] != 'active' or state['lead'] is not None or self.stopped()):
                return
            require(proof['state'] == 'no_limit' and self.clock() - proof['probe_at'] <= 30,
                    'fresh ordinary usage permission is required')
            token, now = uuid.uuid4().hex, int(self.clock())
            directory = self.store.directory / 'attempts'
            private_dir(directory)
            directory = directory / token
            private_dir(directory)
            prompt = handoff(self.store.root, state, token, goal)
            durable(directory / 'prompt.md', prompt)
            attempt = dict(attempt_id=token, seq=state['attempts_total'] + 1, launched_at=now,
                           ended_at=None, exit_code=None, signal=None, saw_turn_failed=False,
                           saw_turn_completed=False, probe='no_limit', outcome=None)
            state['attempts'].append(attempt)
            state['attempts_total'] += 1
            state.update(phase='launching', halt_reason=None, cooldown=None,
                         lead=dict(attempt_id=token, pid=None, start_ticks=None, session_id=None,
                                   boot_id=Path('/proc/sys/kernel/random/boot_id').read_text().strip(), launched_at=now))
            self.store.write(state, self.clock())
            # No inherited lock/control descriptors. Uncertain spawn/write is
            # reconciled by the durable launching claim, never auto-replayed.
            self.process = subprocess.Popen(state['frozen']['argv'], cwd=state['frozen']['cwd'],
                env=dict(self.adapter.env, UNIO_LEAD_SUPERVISED='1', UNIO_LEAD_ATTEMPT=token),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                close_fds=True, start_new_session=True)
            identity = process_identity(self.process.pid)
            if identity is not None:
                state['lead'].update(identity)
                state['phase'] = 'running'
                self.store.write(state, self.clock())
        self.selector = selectors.DefaultSelector()
        for stream in (self.process.stdout, self.process.stderr):
            os.set_blocking(stream.fileno(), False)
            self.selector.register(stream, selectors.EVENT_READ)
        self.output = b''
        self.dropping = self.completed = self.failed = self.bad_output = False
        self.event_types = {}
        self.stderr = bytearray()
        # Feed a bounded prompt without blocking supervision on a stalled CLI.
        self.input = memoryview(prompt)
        os.set_blocking(self.process.stdin.fileno(), False)
        self.selector.register(self.process.stdin, selectors.EVENT_WRITE)

    def event(self, line):
        try:
            item = decode(line)
            kind = item.get('type') if type(item) is dict else None
            require(type(kind) is str and len(kind) <= 128, 'invalid exec event')
        except (Refusal, ValueError, UnicodeError):
            self.bad_output = True
            return
        if kind in {'thread.started', 'turn.started', 'turn.completed', 'turn.failed', 'error',
                    'item.started', 'item.updated', 'item.completed'}:
            self.event_types[kind] = self.event_types.get(kind, 0) + 1
        self.completed |= kind == 'turn.completed'
        self.failed |= kind in {'turn.failed', 'error'}

    def drain(self):
        activity = 0
        for key, _ in self.selector.select(0):
            stream = key.fileobj
            if stream is self.process.stdin:
                try:
                    count = os.write(stream.fileno(), self.input[:65536])
                    self.input = self.input[count:]
                    activity += count
                except BrokenPipeError:
                    self.input = memoryview(b'')
                if not self.input:
                    self.selector.unregister(stream)
                    stream.close()
                continue
            chunk = os.read(stream.fileno(), 65536)
            activity += len(chunk)
            if not chunk:
                self.selector.unregister(stream)
                continue
            if stream is self.process.stderr:
                self.stderr.extend(chunk[:max(0, 65536 - len(self.stderr))])
                continue
            if self.dropping:
                if b'\n' not in chunk:
                    continue
                chunk = chunk.split(b'\n', 1)[1]
                self.dropping = False
            self.output += chunk
            while b'\n' in self.output:
                line, self.output = self.output.split(b'\n', 1)
                if len(line) <= IO_CAP:
                    if line.strip():
                        self.event(line)
                else:
                    self.bad_output = True
            if len(self.output) > IO_CAP:
                self.output = b''
                self.dropping = self.bad_output = True
        return activity

    def finish(self):
        process = self.process
        # Drain finite pipe data after reap; lingering descendants are cleaned
        # by token+session, excluding separately sessioned native workers.
        for _ in range(64):
            if self.drain() == 0:
                break
        if self.output.strip() and not self.dropping:
            self.event(self.output)
        state = self.store.read()
        lead = state['lead']
        clean = terminate_owned(lead['attempt_id'], dict(lead, session_id=process.pid), grace=10) if lead else True
        actual_exit = process.wait()
        self.selector.close()
        for stream in (process.stdin, process.stdout, process.stderr):
            if not stream.closed:
                stream.close()
        self.process = self.selector = None
        success = actual_exit == 0 and self.completed and not self.failed and not self.bad_output
        with self.store.locked():
            state = self.store.read()
            require(state['enablement_id'] == self.enablement and state['lead'] is not None,
                    'lead ownership changed during execution')
            token = state['lead']['attempt_id']
            attempt = next(a for a in state['attempts'] if a['attempt_id'] == token)
            attempt.update(ended_at=int(self.clock()), exit_code=actual_exit,
                           signal=-actual_exit if actual_exit < 0 else None,
                           saw_turn_completed=self.completed, saw_turn_failed=self.failed,
                           outcome='interrupted' if self.interrupted else 'turn_completed' if success else 'failed')
            reason = 'interrupted' if self.interrupted else 'stray_processes' if not clean else 'turn_ended' if success else 'failed'
            state.update(lead=None, phase='halted', halt_reason=reason, cooldown=None)
            if success:
                state['consecutive_limits'] = 0
            directory = self.store.directory / 'attempts' / token
            durable(directory / 'exec-events.json', canonical(dict(types=self.event_types,
                    malformed_or_oversized=self.bad_output, exit_code=actual_exit)) + b'\n')
            durable(directory / 'stderr.log', bytes(self.stderr))
            self.store.write(state, self.clock())
        # A plain crash/auth/network exit cannot trigger a guessed retry. Only
        # actual exec failure events plus independent quota evidence may wait.
        if state['mode'] == 'active' and self.failed and not self.interrupted and clean and not self.stopped():
            self.apply_probe(state, self.probe(state), token)

    def reconcile(self, state):
        lead = state['lead']
        if members(lead['attempt_id'], lead):
            if state['phase'] != 'orphan_wait':
                with self.store.locked():
                    current = self.store.read()
                    if current['revision'] == state['revision']:
                        current['phase'] = 'orphan_wait'
                        self.store.write(current, self.clock())
            return
        with self.store.locked():
            current = self.store.read()
            if current['revision'] != state['revision']:
                return
            token = current['lead']['attempt_id']
            attempt = next(a for a in current['attempts'] if a['attempt_id'] == token)
            attempt.update(ended_at=int(self.clock()), outcome='unknown')
            current.update(lead=None, phase='halted', halt_reason='outcome_unknown')
            self.store.write(current, self.clock())
        if current['mode'] == 'active' and not self.stopped():
            self.apply_probe(current, self.probe(current), token, unknown=True)

    def step(self):
        state = self.store.read()
        require(state is not None and state['enablement_id'] == self.enablement, 'supervisor enablement changed')
        if self.process is not None:
            self.drain()
            if self.interrupted and self.process.poll() is None:
                lead = state['lead']
                terminate_owned(lead['attempt_id'], lead, grace=30)
            if self.process.poll() is not None:
                self.finish()
            return True
        if state['lead'] is not None:
            self.reconcile(state)
            return not self.interrupted
        if self.interrupted:
            self.halt('interrupted')
            return False
        if state['mode'] != 'active' or state['phase'] == 'halted':
            return False
        if self.stopped():
            return True
        wait = state['cooldown']
        if wait and self.clock() < (wait['wake_at'] if wait['wake_at'] is not None else wait['probe_at'] + 3600):
            return True
        proof = self.probe(state)
        if proof['state'] == 'no_limit':
            try:
                self.launch(state, proof)
            except (Refusal, OSError, ValueError, subprocess.SubprocessError) as exc:
                # Preserve a potentially started attempt for reconciliation.
                if self.process is not None:
                    self.interrupted = True
                elif self.store.read()['lead'] is None:
                    self.halt('history_full' if str(exc) == 'history_full' else 'launch_changed')
        else:
            self.apply_probe(state, proof)
        return True

    def run(self):
        for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
            signal.signal(sig, lambda *_: setattr(self, 'interrupted', True))
        try:
            while self.step():
                time.sleep(0.1 if self.process is not None else 5)
        finally:
            if self.process is not None:
                state = self.store.read()
                if state and state['lead']:
                    terminate_owned(state['lead']['attempt_id'], dict(state['lead'], session_id=self.process.pid), grace=30)
                if self.process.poll() is None:
                    self.process.kill()
                self.process.wait()


def spawn_supervisor(store, runner, lock_fd):
    process = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()), str(store.root),
            '--runner', runner, 'supervise', '--lock-fd', str(lock_fd)], cwd=store.root,
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            pass_fds=(lock_fd,), close_fds=True, start_new_session=True)
    return process.pid


def controls(store, command, now):
    with store.locked():
        state = store.read()
        require(state is not None, 'lead cooldown has not been enabled')
        if state['mode'] == {'stop': 'stopped', 'complete': 'completed'}.get(command):
            return state
        require(state['mode'] not in {'stopped', 'completed'}, 'enablement is terminal; start a new goal explicitly')
        state['mode'] = {'pause': 'paused', 'resume': 'active', 'stop': 'stopped', 'complete': 'completed'}[command]
        if command in {'stop', 'complete'}:
            state['cooldown'] = None
            if state['lead'] is None:
                state.update(phase='idle', halt_reason=None)
        if command == 'resume' and state['phase'] == 'halted' and state['lead'] is None:
            state.update(phase='idle', halt_reason=None)
        store.write(state, now)
        return state


def main(argv=None):
    parser = argparse.ArgumentParser(description='Explicit Unio lead cooldown controls')
    parser.add_argument('root')
    parser.add_argument('--runner', required=True)
    subs = parser.add_subparsers(dest='command', required=True)
    start = subs.add_parser('start')
    start.add_argument('--model', required=True)
    start.add_argument('--effort', choices=['low', 'medium', 'high', 'xhigh', 'max'], default='high')
    start.add_argument('--sandbox', choices=['read-only', 'workspace-write'], default='workspace-write')
    start.add_argument('--cd', required=True)
    start.add_argument('--goal-file', required=True)
    subs.add_parser('resume')
    subs.add_parser('pause')
    stop = subs.add_parser('stop')
    stop.add_argument('--force-corrupt', action='store_true')
    subs.add_parser('complete')
    status = subs.add_parser('status')
    status.add_argument('--json', action='store_true')
    worker = subs.add_parser('supervise')
    worker.add_argument('--lock-fd', type=int, required=True)
    args = parser.parse_args(argv)
    store = None
    try:
        store = Store(args.root, create=args.command != 'status')
        if args.command == 'status':
            state = store.read()
            result = {'state': 'disabled'} if state is None else {'state': state, 'supervisor_alive': store.busy(),
                'evidence_age_seconds': max(0, int(time.time()) - state['cooldown']['probe_at']) if state['cooldown'] else None}
            print(json.dumps(result) if args.json else 'lead cooldown: ' + json.dumps(result, indent=2))
            return 0
        if args.command in {'start', 'resume'}:
            require(not os.environ.get('UNIO_LEAD_SUPERVISED') and not os.environ.get('CODEX_THREAD_ID'),
                    'start/resume from an owner terminal after the existing Codex lead exits')
        if args.command == 'supervise':
            fd = args.lock_fd
            require(fd >= 3 and os.fstat(fd).st_ino == (store.directory / 'supervisor.lock').stat().st_ino
                    and os.fstat(fd).st_dev == (store.directory / 'supervisor.lock').stat().st_dev,
                    'invalid inherited supervisor ownership')
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            require(store.busy(), 'inherited descriptor does not own supervisor lock')
            state = store.read()
            require(state is not None and state['frozen'] is not None, 'missing supervisor launch')
            adapter = CodexAdapter(store.root, state['frozen'])
            try:
                Supervisor(store, args.runner, adapter).run()
            finally:
                os.close(fd)
            return 0
        if args.command in {'pause', 'stop', 'complete'}:
            if args.command == 'stop' and args.force_corrupt:
                with store.locked():
                    try:
                        state = store.read()
                    except (Refusal, OSError, ValueError, TypeError):
                        # Rename preserves even a malformed/symlinked original;
                        # never follow it or manufacture a successful old run.
                        backup = store.directory / ('state.corrupt-' + str(time.time_ns()))
                        os.replace(store.path, backup)
                        state = fresh_state(None, time.time(), mode='stopped')
                        store.write(state, time.time())
                        print('lead cooldown: stopped; corrupt state preserved; inspect any old lead process')
                        return 0
            state = controls(store, args.command, time.time())
            print('lead cooldown: ' + state['mode'] + ('; existing lead finishes' if state['lead'] else ''))
            return 0
        if args.command == 'resume':
            state = store.read()
            require(state is not None and state['frozen'] is not None, 'no restartable enablement')
            require(not external_codex(state['frozen'], state['lead']['attempt_id'] if state['lead'] else None),
                    'another unmanaged Codex session is active')
            try:
                fd = store.open_lock('supervisor.lock', blocking=False)
            except Refusal as exc:
                if exc.code != 2:
                    raise
                controls(store, 'resume', time.time())
                print('lead cooldown: resumed existing supervisor')
                return 0
            try:
                controls(store, 'resume', time.time())
                spawn_supervisor(store, args.runner, fd)
            finally:
                os.close(fd)  # Do not LOCK_UN: child owns this open description.
            print('lead cooldown: resumed')
            return 0
        # Start owns the lifetime lock before probing, serializing enablements.
        fd = store.open_lock('supervisor.lock', blocking=False)
        try:
            with store.locked():
                before = store.read()
                require(before is None or before['mode'] in {'stopped', 'completed'} and before['lead'] is None,
                        'an enablement already exists; use its controls')
                require(not (store.root / 'coord' / 'STOP').exists(), 'STOP is set; no probe or launch')
            goal_path = Path(args.goal_file).absolute()
            require(goal_path.resolve() == goal_path and goal_path.is_relative_to(store.root), 'goal file must be inside project without symlinks')
            goal = regular(goal_path, 65536)
            require(b'\x00' not in goal, 'goal must be UTF-8 text without NUL bytes')
            goal.decode('utf-8')
            frozen = launch_snapshot(store.root, args.model, args.effort, args.sandbox, args.cd, goal, os.environ)
            require(not external_codex(frozen), 'another unmanaged Codex session is active')
            policy(store.root, args.runner, os.environ)
            proof = CodexAdapter(store.root, frozen).probe()
            with store.locked():
                current = store.read()
                require(current == before and not (store.root / 'coord' / 'STOP').exists(), 'start changed while probing')
                if before is not None:
                    history = store.directory / 'history'
                    private_dir(history)
                    durable(history / (before['enablement_id'] + '.json'), canonical(before) + b'\n')
                    if (store.directory / 'goal.md').exists():
                        durable(history / (before['enablement_id'] + '.md'), regular(store.directory / 'goal.md', 65536, private=True))
                state = fresh_state(frozen, time.time())
                if proof['state'] == 'limit':
                    state.update(cooldown=proof['wait'], consecutive_limits=1,
                                 phase='unresolved' if proof['wait']['wake_at'] is None else 'cooldown')
                durable(store.directory / 'goal.md', goal)
                store.write(state, time.time())
            spawn_supervisor(store, args.runner, fd)
        finally:
            os.close(fd)
        print('lead cooldown: enabled; ' + state['phase'])
        return 0
    except (Refusal, OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        if args.command == 'status':
            print(json.dumps({'state': 'corrupt', 'reason': 'unsafe, unreadable or invalid cooldown state'}))
            return 1
        print('unio lead cooldown: ' + str(exc), file=sys.stderr)
        return exc.code if isinstance(exc, Refusal) else 1


if __name__ == '__main__':
    sys.exit(main())
