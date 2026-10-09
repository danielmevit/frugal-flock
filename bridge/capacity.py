# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Manual capacity readings under one selected project's coord/capacity/.

Source-only foundation: no provider, model, network or auth request, no
dispatch, benching, tier/mode change or retry. A reading is what a person
saw at one time; it is never proof of current allowance once stale/expired.
"""
from datetime import datetime, timedelta, timezone
import errno
import fcntl
import json
import math
import os
import re
import stat
import uuid

SCHEMA_VERSION = 1
SOURCE = 'manual'
STATE = 'readings.json'
LOCK = '.readings.lock'
MAX_STATE_BYTES = 65536
MAX_GROUPS = 32
MAX_WINDOWS = 8
MAX_WINDOW_MINUTES = 366 * 24 * 60
MAX_TIMESTAMP_CHARS = 64
MAX_AGE_LIMIT = 366 * 24 * 3600
DEFAULT_MAX_AGE = 900
CLOCK_SKEW = timedelta(seconds=300)
LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}')
REQUIRED = {'source', 'window_minutes', 'remaining_percent', 'observed_at'}
OPTIONAL = {'reset_at'}


class CapacityError(ValueError):
    """Refused input, unsafe path or unusable existing state."""


def _now(now):
    now = datetime.now(timezone.utc) if now is None else now
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise CapacityError('now must be a timezone-aware datetime')
    return now


def validate_label(value, name='label'):
    if not isinstance(value, str) or LABEL.fullmatch(value) is None:
        raise CapacityError(f'{name} must be 1-64 ASCII letters, digits, ".", "_" or "-", '
                            'starting with a letter or digit')
    return value


def validate_window_minutes(value):
    if type(value) is not int or not 1 <= value <= MAX_WINDOW_MINUTES:
        raise CapacityError(f'window minutes must be an integer from 1 through {MAX_WINDOW_MINUTES}')
    return value


def validate_percent(value):
    if type(value) not in (int, float) or not 0 <= value <= 100 or not math.isfinite(value):
        raise CapacityError('remaining percent must be a finite number from 0 through 100')
    return float(value)


def parse_timestamp(value, name='timestamp'):
    if not isinstance(value, str) or not value or len(value) > MAX_TIMESTAMP_CHARS:
        raise CapacityError(f'{name} must be an ISO 8601 string of at most {MAX_TIMESTAMP_CHARS} characters')
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise CapacityError(f'{name} is not a valid ISO 8601 time') from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise CapacityError(f'{name} must include a timezone offset')
    try:
        return parsed.astimezone(timezone.utc)
    except (OverflowError, ValueError):
        raise CapacityError(f'{name} is outside the supported UTC range') from None


def validate_max_age(value):
    if type(value) is not int or not 1 <= value <= MAX_AGE_LIMIT:
        raise CapacityError(f'max age must be an integer number of seconds from 1 through {MAX_AGE_LIMIT}')
    return value


def _reading(window_minutes, remaining_percent, observed_at, reset_at, now):
    """Validate one reading; ``now`` is None for already-stored readings."""
    validate_window_minutes(window_minutes)
    validate_percent(remaining_percent)
    observed = parse_timestamp(observed_at, 'observed time')
    if now is not None and observed > now + CLOCK_SKEW:
        raise CapacityError('observed time is in the future')
    reset = None
    if reset_at is not None:
        reset = parse_timestamp(reset_at, 'reset time')
        if reset < observed:
            raise CapacityError('reset time is before the observed time')
        if reset - observed > timedelta(minutes=window_minutes) + CLOCK_SKEW:
            raise CapacityError('reset time is further ahead than one window length after the observation')
    return observed, reset


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CapacityError('state contains a duplicate JSON key')
        result[key] = value
    return result


def _reject_constant(name):
    raise CapacityError(f'state contains non-finite number {name}')


def _decode(raw):
    if len(raw) > MAX_STATE_BYTES:
        raise CapacityError(f'state exceeds {MAX_STATE_BYTES} bytes')
    try:
        text = raw.decode('utf-8')
        data = json.loads(text, object_pairs_hook=_strict_object, parse_constant=_reject_constant)
    except CapacityError:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError):
        raise CapacityError('state is not strict UTF-8 JSON') from None
    return validate_state(data)


def validate_state(data):
    """Validate a whole loaded document; any defect makes all of it unusable."""
    if not isinstance(data, dict) or set(data) != {'schema_version', 'groups'}:
        raise CapacityError('state must contain exactly schema_version and groups')
    if type(data['schema_version']) is not int or data['schema_version'] != SCHEMA_VERSION:
        raise CapacityError('unsupported state schema_version')
    groups = data['groups']
    if not isinstance(groups, dict) or len(groups) > MAX_GROUPS:
        raise CapacityError(f'groups must be an object with at most {MAX_GROUPS} entries')
    for group, windows in groups.items():
        validate_label(group, 'stored group')
        if not isinstance(windows, dict) or not 1 <= len(windows) <= MAX_WINDOWS:
            raise CapacityError(f'stored group {group} must hold 1 through {MAX_WINDOWS} windows')
        for window, reading in windows.items():
            validate_label(window, 'stored window')
            if (not isinstance(reading, dict) or not REQUIRED <= set(reading)
                    or not set(reading) <= REQUIRED | OPTIONAL):
                raise CapacityError(f'stored reading {group}/{window} has unexpected fields')
            if reading['source'] != SOURCE:
                raise CapacityError(f'stored reading {group}/{window} has unsupported source')
            _reading(reading['window_minutes'], reading['remaining_percent'],
                     reading['observed_at'], reading.get('reset_at'), None)
    return data


class CapacityStore:
    """Readings for one owner-selected project; every path step refuses symlinks."""
    def __init__(self, project):
        path = os.path.abspath(os.fspath(project))
        if os.path.realpath(path) != path:
            raise CapacityError('project must be a real path without symlinks')
        if not os.path.isdir(path):
            raise CapacityError('project must be an existing directory')
        self.project = path

    def _open_directory(self, create):
        """Return a descriptor for coord/capacity, or None when absent and not creating."""
        try:
            current = os.open(self.project, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as error:
            raise CapacityError(f'cannot open project: {error.strerror}') from None
        try:
            for name in ('coord', 'capacity'):
                if create:
                    try:
                        os.mkdir(name, mode=0o700, dir_fd=current)
                    except FileExistsError:
                        pass
                try:
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
                except FileNotFoundError:
                    if create:
                        raise
                    return None
                except OSError as error:
                    if error.errno in (errno.ELOOP, errno.ENOTDIR):
                        raise CapacityError(f'{name} must be a real directory, not a symlink or file') from None
                    raise
                os.close(current)
                current = child
            result, current = current, None
            return result
        finally:
            if current is not None:
                os.close(current)

    @staticmethod
    def _read(directory):
        """Return validated state, or None when no state file exists."""
        try:
            descriptor = os.open(STATE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        except FileNotFoundError:
            return None
        except OSError as error:
            if error.errno == errno.ELOOP:
                raise CapacityError('state file must not be a symlink') from None
            raise
        with os.fdopen(descriptor, 'rb') as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise CapacityError('state file must be a regular file')
            raw = source.read(MAX_STATE_BYTES + 1)
        return _decode(raw)

    @staticmethod
    def _lock(directory):
        try:
            descriptor = os.open(LOCK, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                                 0o600, dir_fd=directory)
        except OSError as error:
            if error.errno == errno.ELOOP:
                raise CapacityError('lock file must not be a symlink') from None
            raise
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise CapacityError('lock file must be a regular file')
            fcntl.flock(descriptor, fcntl.LOCK_EX)
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    @staticmethod
    def _write(directory, data):
        raw = (json.dumps(data, ensure_ascii=True, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
        if len(raw) > MAX_STATE_BYTES:
            raise CapacityError(f'state would exceed {MAX_STATE_BYTES} bytes')
        temporary = f'.readings.{uuid.uuid4().hex}.tmp'
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            # rename() replaces the directory entry itself and never follows it.
            os.replace(temporary, STATE, src_dir_fd=directory, dst_dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass

    def record(self, group, window, window_minutes, remaining_percent, observed_at, reset_at=None, now=None):
        """Merge one manual reading; refusals leave existing state bytes untouched."""
        now = _now(now)
        validate_label(group, 'group')
        validate_label(window, 'window')
        observed, reset = _reading(window_minutes, remaining_percent, observed_at, reset_at, now)
        reading = {'source': SOURCE, 'window_minutes': window_minutes,
                   'remaining_percent': float(remaining_percent), 'observed_at': observed.isoformat()}
        if reset is not None:
            reading['reset_at'] = reset.isoformat()
        directory = self._open_directory(create=True)
        try:
            lock = self._lock(directory)
            try:
                data = self._read(directory) or {'schema_version': SCHEMA_VERSION, 'groups': {}}
                groups = data['groups']
                if group not in groups and len(groups) >= MAX_GROUPS:
                    raise CapacityError(f'refusing more than {MAX_GROUPS} groups')
                windows = groups.setdefault(group, {})
                if window not in windows and len(windows) >= MAX_WINDOWS:
                    raise CapacityError(f'refusing more than {MAX_WINDOWS} windows per group')
                previous = windows.get(window)
                if previous is not None:
                    stored = parse_timestamp(previous['observed_at'])
                    if observed == stored:
                        raise CapacityError('duplicate reading: this window already has that observed time')
                    if observed < stored:
                        raise CapacityError('refusing a reading older than the stored one for this window')
                windows[window] = reading
                self._write(directory, data)
            finally:
                os.close(lock)
        finally:
            os.close(directory)
        return reading

    def show(self, group=None, max_age_seconds=DEFAULT_MAX_AGE, now=None):
        """Normalized view; only a fresh valid reading has a usable remaining value."""
        now = _now(now)
        validate_max_age(max_age_seconds)
        if group is not None:
            validate_label(group, 'group')
        view = {'schema_version': SCHEMA_VERSION, 'checked_at': now.astimezone(timezone.utc).isoformat(),
                'max_age_seconds': max_age_seconds, 'state': 'missing', 'error': None, 'groups': {}}
        data = None
        directory = self._open_directory(create=False)
        if directory is not None:
            try:
                data = self._read(directory)
            except CapacityError as error:
                view['state'], view['error'] = 'invalid', str(error)
            finally:
                os.close(directory)
        if data is not None:
            view['state'] = 'ok'
        stored = data['groups'] if data else {}
        for name in [group] if group is not None else sorted(stored):
            windows = stored.get(name)
            if not windows:
                view['groups'][name] = {'status': 'unknown', 'windows': {}}
                continue
            view['groups'][name] = {'status': 'recorded', 'windows': {
                window: _window_view(windows[window], max_age_seconds, now) for window in sorted(windows)}}
        return view


def _window_view(reading, max_age_seconds, now):
    observed = parse_timestamp(reading['observed_at'])
    reset = parse_timestamp(reading['reset_at']) if 'reset_at' in reading else None
    age = (now - observed).total_seconds()
    if observed > now + CLOCK_SKEW:
        status = 'unknown'
    elif (reset is not None and now >= reset) or age >= reading['window_minutes'] * 60:
        status = 'expired'
    elif age > max_age_seconds:
        status = 'stale'
    else:
        status = 'fresh'
    return {'source': reading['source'], 'window_minutes': reading['window_minutes'],
            'observed_at': reading['observed_at'], 'age_seconds': round(age, 3),
            'reset_at': reading.get('reset_at'), 'status': status,
            'last_reading_remaining_percent': reading['remaining_percent'],
            'usable_remaining_percent': reading['remaining_percent'] if status == 'fresh' else None}
