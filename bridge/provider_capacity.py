# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Read-only Codex allowance snapshots under coord/capacity/providers.json.

Only an explicit refresh starts the installed `codex app-server` over stdio
and sends exactly initialize, initialized, account/read (refreshToken false)
and account/rateLimits/read (excludeResetCreditDetails true): metadata reads,
never a thread, turn, model call, login, token refresh or credit consume.
Show is strictly local. A snapshot is an observation, never permission to
run, bench or retry. Manual readings.json is a separate file and untouched.
"""
from datetime import datetime, timezone
import errno
import fcntl
import json
import math
import os
import re
import selectors
import shutil
import signal
import stat
import subprocess
import time
import uuid

from bridge.capacity import (CLOCK_SKEW, DEFAULT_MAX_AGE, MAX_WINDOW_MINUTES, CapacityError, CapacityStore,
                             parse_timestamp, validate_label, validate_max_age)

SCHEMA_VERSION = 1
PROVIDER = 'codex'
STATE = 'providers.json'
LOCK = '.providers.lock'
NEUTRAL_CWD = 'codex-cwd'
TEST_BINARY_ENV = 'UNIO_CAPACITY_TEST_CODEX'
MAX_STATE_BYTES = 262144
MAX_GROUPS = 32
MAX_BUCKETS = 16
MAX_MESSAGE_BYTES = 262144
MAX_OUTPUT_BYTES = 1048576
MAX_INT_DIGITS = 20
DEFAULT_TIMEOUT = 30.0
# Plausible Unix seconds: 2001-09-09 through 2100-01-01.
MIN_UNIX, MAX_UNIX = 1000000000, 4102444800
WINDOWS = ('primary', 'secondary')
ALLOWED_METHODS = ('initialize', 'initialized', 'account/read', 'account/rateLimits/read')
ACCOUNT_KINDS = {'chatgpt': 'chatgpt', 'apiKey': 'api_key'}
REASONS = frozenset((
    'binary_missing', 'start_failed', 'timeout', 'exited', 'output_limit', 'invalid_message',
    'unexpected_request', 'request_failed', 'not_signed_in', 'unsupported_account',
    'invalid_account', 'invalid_rate_limits', 'no_valid_window', 'internal_error',
    'invalid_bucket', 'invalid_window', 'implausible_reset'))
BUCKET_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,63}')


class ProbeFailure(Exception):
    """A bounded reason code; never carries provider text."""
    def __init__(self, reason):
        assert reason in REASONS
        super().__init__(reason)
        self.reason = reason


def _now(now):
    now = datetime.now(timezone.utc) if now is None else now
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise CapacityError('now must be a timezone-aware datetime')
    return now.astimezone(timezone.utc)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate key')
        result[key] = value
    return result


def _bounded_int(text):
    if len(text.lstrip('-')) > MAX_INT_DIGITS:
        raise ValueError('integer too long')
    return int(text)


def _reject_constant(_):
    raise ValueError('non-finite number')


def strict_json(raw):
    """Strict bounded JSON: duplicate keys, NaN/Infinity and huge integers refuse."""
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_unique, parse_int=_bounded_int,
                      parse_constant=_reject_constant)


# ------------------------------------------------------------ normalization
def _integer(value):
    return type(value) is int


def normalize_window(window, observed_unix):
    """One provider window to a stored entry; None stays a legitimate absence."""
    if window is None:
        return None
    if not isinstance(window, dict):
        return {'status': 'unknown', 'reason': 'invalid_window'}
    used = window.get('usedPercent')
    minutes = window.get('windowDurationMins')
    resets = window.get('resetsAt')
    if (type(used) not in (int, float) or not math.isfinite(used) or not 0 <= used <= 100
            or not _integer(minutes) or not 1 <= minutes <= MAX_WINDOW_MINUTES
            or not (resets is None or _integer(resets) and MIN_UNIX <= resets <= MAX_UNIX)):
        return {'status': 'unknown', 'reason': 'invalid_window'}
    if resets is not None and resets - observed_unix > minutes * 60 + CLOCK_SKEW.total_seconds():
        return {'status': 'unknown', 'reason': 'implausible_reset'}
    used = float(used)
    return {'status': 'valid', 'window_minutes': minutes, 'used_percent': used,
            'remaining_percent': round(100.0 - used, 6),
            'reset_at': None if resets is None else _iso_unix(resets)}


def _iso_unix(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).isoformat()


def _bucket(snapshot, observed_unix):
    if not isinstance(snapshot, dict):
        return {'status': 'unknown', 'reason': 'invalid_bucket', 'windows': {}}
    windows = {name: normalize_window(snapshot.get(name), observed_unix) for name in WINDOWS}
    return {'status': 'ok', 'reason': None, 'windows': windows}


def normalize_rate_limits(result, observed_unix):
    """Return buckets keyed by limit ID; raises ProbeFailure when nothing is usable."""
    if not isinstance(result, dict):
        raise ProbeFailure('invalid_rate_limits')
    buckets = {}
    # The keyed map wins whenever present; a malformed map never falls back.
    # Compatibility: an explicit null rateLimitsByLimitId is treated exactly
    # like an absent key (older app-servers), so only then is the legacy
    # single rateLimits object read. Any non-null map is used or refused.
    if result.get('rateLimitsByLimitId') is not None:
        mapped = result['rateLimitsByLimitId']
        if not isinstance(mapped, dict) or not 1 <= len(mapped) <= MAX_BUCKETS:
            raise ProbeFailure('invalid_rate_limits')
        for key in sorted(mapped):
            if not isinstance(key, str) or BUCKET_ID.fullmatch(key) is None:
                raise ProbeFailure('invalid_rate_limits')
            buckets[key] = _bucket(mapped[key], observed_unix)
    elif 'rateLimits' in result and isinstance(result['rateLimits'], dict):
        legacy = result['rateLimits']
        name = legacy.get('limitId')
        name = name if isinstance(name, str) and BUCKET_ID.fullmatch(name) else 'default'
        buckets[name] = _bucket(legacy, observed_unix)
    else:
        raise ProbeFailure('invalid_rate_limits')
    if not any(w and w['status'] == 'valid' for b in buckets.values() for w in b['windows'].values()):
        raise ProbeFailure('no_valid_window')
    return buckets


def classify_account(result):
    """Bounded account kind only; email, plan and tokens are never kept."""
    if not isinstance(result, dict):
        raise ProbeFailure('invalid_account')
    account = result.get('account')
    if account is None:
        raise ProbeFailure('not_signed_in')
    if not isinstance(account, dict) or not isinstance(account.get('type'), str):
        raise ProbeFailure('invalid_account')
    kind = ACCOUNT_KINDS.get(account['type'])
    if kind != 'chatgpt':
        raise ProbeFailure('unsupported_account')
    return kind


# ------------------------------------------------------------ transport
class AppServer:
    """One owned `codex app-server` process group on stdio, method-allowlisted."""

    def __init__(self, binary, cwd, timeout, env=None):
        self.deadline = time.monotonic() + timeout
        self.buffer = b''
        self.total = 0
        self.process = None
        try:
            self.process = subprocess.Popen(
                [binary, 'app-server', '--listen', 'stdio://'], cwd=cwd,
                env=dict(os.environ if env is None else env), stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, start_new_session=True)
        except OSError:
            raise ProbeFailure('start_failed') from None
        self.selector = selectors.DefaultSelector()
        for stream in (self.process.stdout, self.process.stderr):
            os.set_blocking(stream.fileno(), False)
            self.selector.register(stream, selectors.EVENT_READ)

    def send(self, method, params, request_id=None):
        if method not in ALLOWED_METHODS:
            raise ProbeFailure('internal_error')
        message = {'method': method, 'params': params}
        if request_id is not None:
            message['id'] = request_id
        try:
            self.process.stdin.write(json.dumps(message, separators=(',', ':')).encode() + b'\n')
            self.process.stdin.flush()
        except (BrokenPipeError, OSError):
            raise ProbeFailure('exited') from None

    def receive(self, request_id):
        while True:
            while b'\n' in self.buffer:
                line, self.buffer = self.buffer.split(b'\n', 1)
                if line.strip():
                    result = self._message(line, request_id)
                    if result is not None:
                        return result[0]
            if len(self.buffer) > MAX_MESSAGE_BYTES:
                raise ProbeFailure('output_limit')
            remaining = self.deadline - time.monotonic()
            if remaining <= 0:
                raise ProbeFailure('timeout')
            if not self.selector.get_map():
                raise ProbeFailure('exited')
            for key, _ in self.selector.select(min(0.2, remaining)):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    self.selector.unregister(key.fileobj)
                    continue
                self.total += len(chunk)
                if self.total > MAX_OUTPUT_BYTES:
                    raise ProbeFailure('output_limit')
                # stderr is drained and discarded; it may carry secrets.
                if key.fileobj is self.process.stdout:
                    self.buffer += chunk

    @staticmethod
    def _message(line, request_id):
        if len(line) > MAX_MESSAGE_BYTES:
            raise ProbeFailure('output_limit')
        try:
            message = strict_json(line)
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise ProbeFailure('invalid_message') from None
        if not isinstance(message, dict):
            raise ProbeFailure('invalid_message')
        if 'id' not in message:
            return None  # notification: ignored, never answered
        if 'method' in message:
            # A server-initiated request (approval, login, ...) is never answered.
            raise ProbeFailure('unexpected_request')
        if message['id'] != request_id or type(message['id']) is not int:
            raise ProbeFailure('invalid_message')
        if 'error' in message or 'result' not in message:
            raise ProbeFailure('request_failed')
        return (message['result'],)

    def _signal_group(self, sig):
        try:
            os.killpg(self.process.pid, sig)
        except (ProcessLookupError, PermissionError):
            pass

    def _exited(self):
        """True once the leader has exited; leaves it unreaped (WNOWAIT)."""
        try:
            return os.waitid(os.P_PID, self.process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
        except ChildProcessError:
            return True

    def close(self):
        process = self.process
        if process is None:
            return
        self.selector.close()
        try:
            process.stdin.close()
        except OSError:
            pass
        # Until wait() reaps the leader its PID, and so its process group ID,
        # cannot be reused: signal only that owned group, never a name pattern.
        self._signal_group(signal.SIGTERM)
        grace = time.monotonic() + 1.0
        while time.monotonic() < grace and not self._exited():
            time.sleep(0.02)
        self._signal_group(signal.SIGKILL)
        process.wait(timeout=5)
        process.stdout.close()
        process.stderr.close()


def probe_codex(binary, cwd, timeout=DEFAULT_TIMEOUT, clock=time.time, env=None):
    """Return (account_kind, buckets, observed_unix) or raise ProbeFailure."""
    server = AppServer(binary, cwd, timeout, env)
    try:
        return _exchange(server, clock)
    except (OSError, ValueError, subprocess.SubprocessError):
        raise ProbeFailure('internal_error') from None
    finally:
        server.close()


def _exchange(server, clock):
    """The whole allowlisted sequence; no other request is ever sent."""
    server.send('initialize', {'clientInfo': {'name': 'unio_capacity', 'title': 'Unio', 'version': '1'}}, 0)
    server.receive(0)
    server.send('initialized', {})
    server.send('account/read', {'refreshToken': False}, 1)
    kind = classify_account(server.receive(1))
    server.send('account/rateLimits/read', {'excludeResetCreditDetails': True}, 2)
    result = server.receive(2)
    observed = int(clock())
    return kind, normalize_rate_limits(result, observed), observed


def resolve_binary(env=None):
    """The explicit test injection wins; otherwise the installed `codex` on PATH."""
    env = os.environ if env is None else env
    injected = env.get(TEST_BINARY_ENV)
    if injected:
        if not os.path.isabs(injected) or not os.path.isfile(injected) or not os.access(injected, os.X_OK):
            raise CapacityError(f'{TEST_BINARY_ENV} must be an absolute path to an executable file')
        return injected
    return shutil.which('codex', path=env.get('PATH'))


# ------------------------------------------------------------ stored state
def _expect(condition, message='provider state is malformed'):
    if not condition:
        raise CapacityError(message)


def _stored_time(value, name):
    """A stored timestamp inside the plausible range, so later arithmetic never overflows."""
    parsed = parse_timestamp(value, name)
    _expect(MIN_UNIX <= parsed.timestamp() <= MAX_UNIX, f'{name} is outside the plausible range')
    return parsed


def _stored_window(window, observed):
    if window is None:
        return
    _expect(isinstance(window, dict) and window.get('status') in ('valid', 'unknown'))
    if window['status'] == 'unknown':
        _expect(set(window) == {'status', 'reason'} and window['reason'] in REASONS)
        return
    _expect(set(window) == {'status', 'window_minutes', 'used_percent', 'remaining_percent', 'reset_at'})
    used, remaining = window['used_percent'], window['remaining_percent']
    # Each value is range-checked on its own; the tolerance only ties them together.
    _expect(type(used) is float and math.isfinite(used) and 0 <= used <= 100)
    _expect(type(remaining) is float and math.isfinite(remaining) and 0 <= remaining <= 100)
    _expect(abs(remaining - (100 - used)) < 1e-5)
    minutes = window['window_minutes']
    _expect(_integer(minutes) and 1 <= minutes <= MAX_WINDOW_MINUTES)
    if window['reset_at'] is not None:
        # The same plausibility rule as a fresh provider value: a forged far-future
        # reset never becomes usable capacity.
        reset = _stored_time(window['reset_at'], 'stored reset time')
        _expect((reset - observed).total_seconds() <= minutes * 60 + CLOCK_SKEW.total_seconds(),
                'stored reset time is implausibly far from its observation')


def _stored_buckets(buckets, observed):
    _expect(isinstance(buckets, dict) and 1 <= len(buckets) <= MAX_BUCKETS)
    for key, bucket in buckets.items():
        _expect(BUCKET_ID.fullmatch(key) is not None)
        _expect(isinstance(bucket, dict) and set(bucket) == {'status', 'reason', 'windows'})
        _expect(isinstance(bucket['windows'], dict))
        if bucket['status'] == 'unknown':
            _expect(bucket['reason'] in REASONS and bucket['windows'] == {})
        else:
            _expect(bucket['status'] == 'ok' and bucket['reason'] is None and set(bucket['windows']) == set(WINDOWS))
            for window in bucket['windows'].values():
                _stored_window(window, observed)


def _stored_entry(entry):
    keys = {'source', 'attempted_at', 'state', 'reason', 'account_kind', 'observed_at', 'buckets', 'last_good'}
    _expect(isinstance(entry, dict) and set(entry) == keys and entry['source'] == PROVIDER)
    attempted = _stored_time(entry['attempted_at'], 'stored attempt time')
    if entry['state'] == 'ok':
        _expect(entry['reason'] is None and entry['account_kind'] == 'chatgpt')
        observed = _stored_time(entry['observed_at'], 'stored observed time')
        _expect((observed - attempted).total_seconds() <= CLOCK_SKEW.total_seconds())
        _stored_buckets(entry['buckets'], observed)
    else:
        _expect(entry['state'] == 'unknown' and entry['reason'] in REASONS)
        _expect(entry['account_kind'] in (None, *ACCOUNT_KINDS.values()))
        _expect(entry['observed_at'] is None and entry['buckets'] is None)
    last = entry['last_good']
    if last is not None:
        _expect(isinstance(last, dict) and set(last) == {'observed_at', 'buckets'})
        _stored_buckets(last['buckets'], _stored_time(last['observed_at'], 'stored last-good time'))


def validate_state(data):
    """Any defect makes the whole provider document unusable."""
    _expect(isinstance(data, dict) and set(data) == {'schema_version', 'providers'},
            'provider state must contain exactly schema_version and providers')
    _expect(type(data['schema_version']) is int and data['schema_version'] == SCHEMA_VERSION,
            'unsupported provider state schema_version')
    providers = data['providers']
    _expect(isinstance(providers, dict) and set(providers) <= {PROVIDER}, 'unsupported provider in state')
    groups = providers.get(PROVIDER, {})
    _expect(isinstance(groups, dict) and len(groups) <= MAX_GROUPS, 'too many provider groups')
    for group, entry in groups.items():
        validate_label(group, 'stored group')
        _stored_entry(entry)
    return data


def _decode(raw):
    if len(raw) > MAX_STATE_BYTES:
        raise CapacityError(f'provider state exceeds {MAX_STATE_BYTES} bytes')
    try:
        data = strict_json(raw)
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise CapacityError('provider state is not strict UTF-8 JSON') from None
    try:
        return validate_state(data)
    except (TypeError, OverflowError):
        raise CapacityError('provider state has invalid field types') from None


class ProviderStore:
    """providers.json beside, never inside, the manual readings.json."""

    def __init__(self, project):
        self.paths = CapacityStore(project)  # same real-path, no-symlink project rule
        self.project = self.paths.project

    @staticmethod
    def _open(name, flags, directory):
        try:
            return os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=directory)
        except OSError as error:
            if error.errno == errno.ELOOP:
                raise CapacityError(f'{name} must not be a symlink') from None
            raise

    def _read(self, directory):
        try:
            descriptor = self._open(STATE, os.O_RDONLY, directory)
        except FileNotFoundError:
            return None
        with os.fdopen(descriptor, 'rb') as source:
            info = os.fstat(source.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise CapacityError('provider state must be a single-link regular file')
            raw = source.read(MAX_STATE_BYTES + 1)
        return _decode(raw)

    def _lock(self, directory):
        descriptor = self._open(LOCK, os.O_RDWR | os.O_CREAT, directory)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise CapacityError('provider lock must be a regular file')
            fcntl.flock(descriptor, fcntl.LOCK_EX)
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    @staticmethod
    def _write(directory, data):
        validate_state(data)
        raw = (json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
        if len(raw) > MAX_STATE_BYTES:
            raise CapacityError(f'provider state would exceed {MAX_STATE_BYTES} bytes')
        temporary = f'.providers.{uuid.uuid4().hex}.tmp'
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, STATE, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass

    def _neutral_cwd(self, directory):
        """An empty project-owned directory: no repository config or plugins."""
        try:
            os.mkdir(NEUTRAL_CWD, mode=0o700, dir_fd=directory)
        except FileExistsError:
            pass
        descriptor = self._open(NEUTRAL_CWD, os.O_RDONLY | os.O_DIRECTORY, directory)
        os.close(descriptor)
        return os.path.join(self.project, 'coord', 'capacity', NEUTRAL_CWD)

    def refresh(self, group, binary=None, timeout=DEFAULT_TIMEOUT, now=None, clock=time.time, env=None):
        """One explicit metadata read; failure replaces current usability with Unknown."""
        validate_label(group, 'group')
        if not (isinstance(timeout, (int, float)) and 0 < timeout <= DEFAULT_TIMEOUT):
            raise CapacityError(f'timeout must be greater than 0 and at most {DEFAULT_TIMEOUT:g} seconds')
        directory = self.paths._open_directory(create=True)
        try:
            # Refuse unusable state before any provider process starts.
            self._read(directory)
            cwd = self._neutral_cwd(directory)
            try:
                if binary is None:
                    raise ProbeFailure('binary_missing')
                kind, buckets, observed = probe_codex(binary, cwd, timeout, clock, env)
                outcome = {'state': 'ok', 'reason': None, 'account_kind': kind,
                           'observed_at': _iso_unix(observed), 'buckets': buckets}
            except ProbeFailure as failure:
                outcome = {'state': 'unknown', 'reason': failure.reason, 'account_kind': None,
                           'observed_at': None, 'buckets': None}
            attempted = _now(now).isoformat()
            lock = self._lock(directory)
            try:
                data = self._read(directory) or {'schema_version': SCHEMA_VERSION, 'providers': {}}
                groups = data['providers'].setdefault(PROVIDER, {})
                if group not in groups and len(groups) >= MAX_GROUPS:
                    raise CapacityError(f'refusing more than {MAX_GROUPS} provider groups')
                previous = groups.get(group)
                last = previous['last_good'] if previous else None
                if previous and previous['state'] == 'ok':
                    last = {'observed_at': previous['observed_at'], 'buckets': previous['buckets']}
                entry = dict(outcome, source=PROVIDER, attempted_at=attempted, last_good=last)
                groups[group] = entry
                self._write(directory, data)
            finally:
                os.close(lock)
        finally:
            os.close(directory)
        return entry

    def show(self, group=None, max_age_seconds=DEFAULT_MAX_AGE, now=None):
        """Strictly local: reads providers.json only, never starts a process."""
        now = _now(now)
        validate_max_age(max_age_seconds)
        if group is not None:
            validate_label(group, 'group')
        view = {'schema_version': SCHEMA_VERSION, 'provider': PROVIDER, 'checked_at': now.isoformat(),
                'max_age_seconds': max_age_seconds, 'state': 'missing', 'error': None, 'groups': {}}
        data = None
        directory = self.paths._open_directory(create=False)
        if directory is not None:
            try:
                data = self._read(directory)
            except CapacityError as error:
                view['state'], view['error'] = 'invalid', str(error)
            finally:
                os.close(directory)
        if data is not None:
            view['state'] = 'ok'
        stored = data['providers'].get(PROVIDER, {}) if data else {}
        for name in [group] if group is not None else sorted(stored):
            view['groups'][name] = _entry_view(stored.get(name), max_age_seconds, now)
        return view


def _entry_view(entry, max_age_seconds, now):
    if entry is None:
        return {'source': PROVIDER, 'state': 'unknown', 'reason': 'not_refreshed', 'attempted_at': None,
                'account_kind': None, 'observed_at': None, 'age_seconds': None, 'freshness': 'unknown',
                'buckets': {}, 'last_good': None}
    view = {'source': PROVIDER, 'state': entry['state'], 'reason': entry['reason'],
            'attempted_at': entry['attempted_at'], 'account_kind': entry['account_kind'],
            'observed_at': entry['observed_at'], 'age_seconds': None, 'freshness': 'unknown',
            'buckets': {}, 'last_good': None}
    if entry['state'] == 'ok':
        observed = parse_timestamp(entry['observed_at'])
        view['age_seconds'] = round((now - observed).total_seconds(), 3)
        view['freshness'] = _freshness(observed, None, None, max_age_seconds, now)
        view['buckets'] = _buckets_view(entry['buckets'], observed, max_age_seconds, now, current=True)
    last = entry['last_good']
    if last is not None:
        observed = parse_timestamp(last['observed_at'])
        # Historical only: never usable, whatever its age.
        view['last_good'] = {'historical': True, 'observed_at': last['observed_at'],
                             'age_seconds': round((now - observed).total_seconds(), 3),
                             'buckets': _buckets_view(last['buckets'], observed, max_age_seconds, now,
                                                      current=False)}
    return view


def _freshness(observed, reset, minutes, max_age_seconds, now):
    age = (now - observed).total_seconds()
    if observed > now + CLOCK_SKEW:
        return 'unknown'
    # A passed reset is not recovered quota: the remaining value is simply unknown.
    if (reset is not None and now >= reset) or (minutes is not None and age >= minutes * 60):
        return 'expired'
    return 'stale' if age > max_age_seconds else 'fresh'


def _buckets_view(buckets, observed, max_age_seconds, now, current):
    view = {}
    for key in sorted(buckets):
        bucket = buckets[key]
        windows = {}
        for name, window in sorted(bucket['windows'].items()):
            if window is None:
                windows[name] = None
            elif window['status'] != 'valid':
                windows[name] = {'status': 'unknown', 'reason': window['reason'], 'usable_remaining_percent': None}
            else:
                reset = parse_timestamp(window['reset_at']) if window['reset_at'] else None
                freshness = _freshness(observed, reset, window['window_minutes'], max_age_seconds, now)
                usable = current and freshness == 'fresh'
                windows[name] = {'status': freshness if current else 'historical',
                                 'window_minutes': window['window_minutes'],
                                 'reset_at': window['reset_at'],
                                 'last_reading_remaining_percent': window['remaining_percent'],
                                 'usable_remaining_percent': window['remaining_percent'] if usable else None}
        view[key] = {'status': bucket['status'], 'reason': bucket['reason'], 'windows': windows}
    return view


__all__ = ['ProviderStore', 'ProbeFailure', 'probe_codex', 'resolve_binary', 'normalize_rate_limits',
           'normalize_window', 'classify_account', 'validate_state', 'ALLOWED_METHODS', 'TEST_BINARY_ENV',
           'DEFAULT_TIMEOUT']
