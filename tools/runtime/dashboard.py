#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Managed read-only dashboard: ensure, status and stop. Standard library only.

The canonical copy is embedded by tools/embed-dashboard.py and installed as
CONF_DIR/lib/dashboard.py. It never calls a model and never changes STOP,
lead, bench, policy, grant, auth or cooldown state. It only signals a process
it positively identifies as its own launch, and only through a pidfd.
"""
import argparse
import datetime
import errno
import fcntl
import hashlib
import hmac
import http.client
import json
import os
from pathlib import Path
import re
import secrets
import select
import signal
import stat
import subprocess
import sys
import time

if sys.version_info < (3, 9):
    raise SystemExit('unio dashboard: Python 3.9 or newer is required')

SCHEMA = 1
STATE = 'state.json'
LOCK = 'lock'
LOG = 'server.log'
STATE_LIMIT = 4096
HEALTH_LIMIT = 4096
LOG_LIMIT = 65536
ENVIRON_LIMIT = 1024 * 1024
DEADLINE = 30.0       # whole command, including waiting for a concurrent ensure
READY_SECONDS = 20.0  # one new launch
OPEN_SECONDS = 8.0
STOP_SECONDS = 10.0
NONCE_ENV = 'UNIO_DASHBOARD_LAUNCH'
STATE_FIELDS = {'schema_version', 'status', 'project_hash', 'launch_nonce', 'pid', 'boot_id',
                'start_ticks', 'port', 'version', 'started_at', 'reason'}
HEALTH_FIELDS = {'schema_version', 'managed', 'project_hash', 'launch_nonce', 'version', 'mode'}
REASONS = {'exited_before_ready', 'readiness_timeout', 'health_mismatch'}
HEX64 = re.compile(r'[0-9a-f]{64}')
HEX32 = re.compile(r'[0-9a-f]{32}')
BOOT = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
VERSION = re.compile(r'[0-9A-Za-z.+_-]{1,64}')
ORIGIN_LINE = re.compile(r'^http://127\.0\.0\.1:([0-9]{1,5}) — ', re.M)
OPENER = ('import sys, webbrowser\n'
          'try:\n    opened = webbrowser.open(sys.argv[1], new=2)\n'
          'except Exception:\n    opened = False\n'
          'sys.exit(0 if opened else 1)\n')


class DashboardError(Exception):
    """A refusal with an owner-facing message; nothing was signalled."""
    def __init__(self, state, message):
        super().__init__(message)
        self.state = state


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON field')
        value[key] = item
    return value


def project_hash(project):
    return hashlib.sha256(str(project).encode('utf-8', 'surrogateescape')).hexdigest()


# ------------------------------------------------------------ private state
class StateDir:
    """coord/dashboard opened without following links; every file op is relative."""

    def __init__(self, project, create):
        self.fd = None
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        project_fd = os.open(str(project), flags)
        try:
            try:
                coord_fd = os.open('coord', flags, dir_fd=project_fd)
            except OSError as error:
                raise DashboardError('unsafe', 'coord/ is not a real directory') from error
            try:
                try:
                    self.fd = os.open('dashboard', flags, dir_fd=coord_fd)
                except FileNotFoundError:
                    if not create:
                        return
                    try:
                        os.mkdir('dashboard', 0o700, dir_fd=coord_fd)
                    except FileExistsError:
                        pass
                    self.fd = os.open('dashboard', flags, dir_fd=coord_fd)
                except OSError as error:
                    raise DashboardError('unsafe', 'coord/dashboard is not a real directory') from error
            finally:
                os.close(coord_fd)
        finally:
            os.close(project_fd)
        info = os.fstat(self.fd)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid():
            self.close()
            raise DashboardError('unsafe', 'coord/dashboard is not a private directory owned by this account')
        if stat.S_IMODE(info.st_mode) != 0o700:
            os.fchmod(self.fd, 0o700)

    @property
    def exists(self):
        return self.fd is not None

    def close(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def check_entry(self, name):
        """Return False if absent; refuse anything but a private regular single-link file."""
        try:
            info = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
        except FileNotFoundError:
            return False
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid():
            raise DashboardError('unsafe', 'coord/dashboard/' + name + ' is not a private regular file')
        return True

    def open_file(self, name, flags, mode=0o600):
        try:
            fd = os.open(name, flags | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, mode, dir_fd=self.fd)
        except OSError as error:
            if error.errno in (errno.ELOOP, errno.ENXIO, errno.EISDIR, errno.EACCES):
                raise DashboardError('unsafe', 'coord/dashboard/' + name + ' is not a private regular file') from error
            raise
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_uid != os.geteuid():
            os.close(fd)
            raise DashboardError('unsafe', 'coord/dashboard/' + name + ' is not a private regular file')
        os.set_blocking(fd, True)
        return fd

    def read_bounded(self, name, limit):
        if not self.exists or not self.check_entry(name):
            return None
        fd = self.open_file(name, os.O_RDONLY)
        try:
            chunks, size = [], 0
            while size <= limit:
                chunk = os.read(fd, limit + 1 - size)
                if not chunk:
                    break
                chunks.append(chunk)
                size += len(chunk)
            return b''.join(chunks)
        finally:
            os.close(fd)

    def write_atomic(self, name, raw):
        self.check_entry(name)
        temporary = '.' + name + '.' + secrets.token_hex(8)
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=self.fd)
        try:
            os.write(fd, raw)
            os.fsync(fd)
        except BaseException:
            os.close(fd)
            os.unlink(temporary, dir_fd=self.fd)
            raise
        os.close(fd)
        os.replace(temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd)
        os.fsync(self.fd)

    def remove(self, name):
        if self.check_entry(name):
            os.unlink(name, dir_fd=self.fd)
            os.fsync(self.fd)

    def fresh_log(self):
        self.remove(LOG)
        return os.open(LOG, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                       0o600, dir_fd=self.fd)

    def lock(self, deadline):
        fd = self.open_file(LOCK, os.O_RDWR | os.O_CREAT)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return fd
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    os.close(fd)
                    raise DashboardError('busy', 'another dashboard command still holds the lock; try again shortly') from None
                time.sleep(0.05)


def parse_state(raw, expected_hash):
    if raw is None:
        return None
    try:
        if len(raw) > STATE_LIMIT:
            raise ValueError('oversized')
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
        if not isinstance(value, dict) or set(value) != STATE_FIELDS:
            raise ValueError('fields')
        integers = ('schema_version', 'pid', 'start_ticks')
        if any(type(value[k]) is not int for k in integers) or value['schema_version'] != SCHEMA:
            raise ValueError('types')
        if value['status'] not in ('running', 'failed') or not 1 < value['pid'] < 2 ** 31 or value['start_ticks'] < 0:
            raise ValueError('values')
        if (type(value['project_hash']) is not str or not HEX64.fullmatch(value['project_hash'])
                or type(value['launch_nonce']) is not str or not HEX32.fullmatch(value['launch_nonce'])
                or type(value['boot_id']) is not str or not BOOT.fullmatch(value['boot_id'])
                or type(value['version']) is not str or not VERSION.fullmatch(value['version'])
                or type(value['started_at']) is not str or len(value['started_at']) > 40):
            raise ValueError('identity')
        port = value['port']
        if port is not None and (type(port) is not int or not 0 < port < 65536):
            raise ValueError('port')
        if value['status'] == 'running':
            if port is None or value['reason'] is not None:
                raise ValueError('running')
        elif value['reason'] not in REASONS:
            raise ValueError('reason')
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise DashboardError('unsafe', 'coord/dashboard/state.json is unreadable or not a dashboard record') from None
    if value['project_hash'] != expected_hash:
        raise DashboardError('unsafe', 'coord/dashboard/state.json belongs to another project path')
    return value


def encode_state(value):
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=True) + '\n').encode()
    if len(raw) > STATE_LIMIT:
        raise ValueError('dashboard state too large')
    return raw


# --------------------------------------------------------- process identity
def boot_id():
    try:
        with open('/proc/sys/kernel/random/boot_id', 'rb') as handle:
            value = handle.read(64).decode('ascii').strip()
    except (OSError, UnicodeDecodeError):
        return None
    return value if BOOT.fullmatch(value) else None


def start_ticks(pid):
    """Process start time in clock ticks since boot, or None when absent."""
    try:
        with open('/proc/' + str(int(pid)) + '/stat', 'rb') as handle:
            raw = handle.read(4096)
    except (FileNotFoundError, ProcessLookupError):
        return None
    fields = raw[raw.rindex(b')') + 2:].split()
    # Field 22 overall; the list starts at field 3 (state).
    if len(fields) < 20 or fields[0] == b'Z':
        return None
    return int(fields[19])


def environ_has(pid, entry):
    with open('/proc/' + str(int(pid)) + '/environ', 'rb') as handle:
        raw = handle.read(ENVIRON_LIMIT + 1)
    return entry in raw.split(b'\0')


def identify(record):
    """owned: this exact launch; gone: dead or a different process; uncertain otherwise."""
    current_boot = boot_id()
    if current_boot is None:
        return 'uncertain'
    if current_boot != record['boot_id']:
        return 'gone'
    try:
        ticks = start_ticks(record['pid'])
        if ticks is None or ticks != record['start_ticks']:
            return 'gone'
        entry = (NONCE_ENV + '=' + record['launch_nonce']).encode()
        if not environ_has(record['pid'], entry):
            return 'gone'
    except (FileNotFoundError, ProcessLookupError):
        return 'gone'
    except (OSError, ValueError, IndexError):
        return 'uncertain'
    return 'owned'


def health(port, expected_hash, nonce, timeout=2.0):
    """Ask only the metadata endpoint; it never runs the observer or a provider."""
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=timeout)
    try:
        connection.request('GET', '/api/dashboard', headers={'Host': '127.0.0.1:' + str(port)})
        response = connection.getresponse()
        raw = response.read(HEALTH_LIMIT + 1)
        if response.status != 200 or len(raw) > HEALTH_LIMIT:
            return None
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
    except (OSError, ValueError, UnicodeDecodeError, http.client.HTTPException):
        return None
    finally:
        connection.close()
    if (not isinstance(value, dict) or set(value) != HEALTH_FIELDS or value['schema_version'] != SCHEMA
            or value['managed'] is not True or value['mode'] != 'read-only'
            or value['project_hash'] != expected_hash or type(value['launch_nonce']) is not str
            or not hmac.compare_digest(value['launch_nonce'].encode(), nonce.encode())
            or type(value['version']) is not str or not VERSION.fullmatch(value['version'])):
        return None
    return value


def url_for(port):
    return 'http://127.0.0.1:' + str(port)


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


# ------------------------------------------------------------------ actions
class Dashboard:
    def __init__(self, project, engine, browser_dir, version):
        self.project, self.engine, self.browser_dir, self.version = project, engine, browser_dir, version
        self.hash = project_hash(project)
        self.start = time.monotonic()

    def remaining(self):
        return self.start + DEADLINE - time.monotonic()

    def observe(self, directory):
        """Classify recorded state without starting, writing or signalling anything."""
        record = parse_state(directory.read_bounded(STATE, STATE_LIMIT), self.hash)
        if record is None:
            return 'none', None, None
        if record['status'] == 'failed':
            return 'failed', record, None
        identity = identify(record)
        if identity == 'gone':
            return 'stale', record, None
        if identity == 'uncertain':
            return 'uncertain', record, None
        document = health(record['port'], self.hash, record['launch_nonce'])
        return ('running' if document else 'unhealthy'), record, document

    def status(self):
        directory = StateDir(self.project, create=False)
        try:
            state, record, document = self.observe(directory)
        finally:
            directory.close()
        result = dict(action='status', state=state)
        if record is not None and state in ('running', 'unhealthy'):
            result.update(pid=record['pid'])
        if state == 'running':
            result.update(url=url_for(record['port']), version=document['version'])
        if state == 'failed':
            result.update(reason=record['reason'])
        return result

    def ensure(self, open_browser):
        directory = StateDir(self.project, create=True)
        lock = None
        try:
            lock = directory.lock(self.start + DEADLINE - READY_SECONDS - 2)
            state, record, document = self.observe(directory)
            if state == 'running':
                result = dict(action='ensure', state='reused', url=url_for(record['port']),
                              pid=record['pid'], version=document['version'],
                              browser='not_new' if open_browser else 'not_requested')
                return result
            if state == 'unhealthy':
                raise DashboardError('unhealthy', 'the managed dashboard process ' + str(record['pid'])
                                     + ' is running but does not answer as this project\'s dashboard; '
                                     'run unio dashboard stop, then unio dashboard ensure')
            if state == 'uncertain':
                raise DashboardError('uncertain', 'cannot confirm whether recorded process '
                                     + str(record['pid']) + ' is this dashboard; nothing was started or signalled')
            result = self.launch(directory)
            result['previous'] = state
            if open_browser:
                result['browser'] = open_url(result['url'], self.environment(None))
            else:
                result['browser'] = 'not_requested'
            return result
        finally:
            if lock is not None:
                os.close(lock)
            directory.close()

    def environment(self, nonce):
        environment = {k: v for k, v in os.environ.items() if k != NONCE_ENV}
        if nonce is not None:
            environment[NONCE_ENV] = nonce
        return environment

    def launch(self, directory):
        current_boot = boot_id()
        if current_boot is None or not hasattr(os, 'pidfd_open'):
            raise DashboardError('uncertain', 'process identity is unavailable on this system (Linux /proc and pidfd are required)')
        nonce = secrets.token_hex(16)
        log = directory.fresh_log()
        try:
            command = [sys.executable, '-E', '-s', '-B', str(self.browser_dir / 'launcher.py'),
                       str(self.engine), str(self.project), self.version]
            # The child never inherits the caller's pipes: a captured parent returns promptly.
            child = subprocess.Popen(command, cwd=str(self.project), env=self.environment(nonce),
                                     stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                     close_fds=True, start_new_session=True)
        finally:
            os.close(log)
        ticks = start_ticks(child.pid) or 0
        record = dict(schema_version=SCHEMA, status='running', project_hash=self.hash, launch_nonce=nonce,
                      pid=child.pid, boot_id=current_boot, start_ticks=ticks, port=None,
                      version=self.version, started_at=now(), reason=None)
        reason, port, document = self.await_ready(directory, child, nonce)
        if reason is None:
            record['port'] = port
            directory.write_atomic(STATE, encode_state(record))
            return dict(action='ensure', state='started', url=url_for(port), pid=child.pid,
                        version=document['version'])
        # Unreaped, so the PID and its new session still belong to this launch.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            child.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        record.update(status='failed', port=port, reason=reason)
        directory.write_atomic(STATE, encode_state(record))
        raise DashboardError('failed', 'the new dashboard did not become ready (' + reason
                             + '); its own process was stopped. Startup output: coord/dashboard/' + LOG)

    def await_ready(self, directory, child, nonce):
        deadline = time.monotonic() + max(1.0, min(READY_SECONDS, self.remaining() - 1))
        port = None
        while time.monotonic() < deadline:
            if child.poll() is not None:
                return 'exited_before_ready', port, None
            if port is None:
                try:
                    raw = directory.read_bounded(LOG, LOG_LIMIT) or b''
                except DashboardError:
                    raise
                except OSError:
                    raw = b''  # Some mounts briefly fail reads during a write; retry until the deadline.
                match = ORIGIN_LINE.search(raw[:LOG_LIMIT].decode('utf-8', 'replace'))
                if match and 0 < int(match.group(1)) < 65536:
                    port = int(match.group(1))
            if port is not None:
                document = health(port, self.hash, nonce, timeout=1.0)
                if document is not None:
                    return None, port, document
            time.sleep(0.05)
        return ('readiness_timeout' if port is None else 'health_mismatch'), port, None

    def stop(self):
        directory = StateDir(self.project, create=False)
        if not directory.exists:
            return dict(action='stop', state='none')
        lock = None
        try:
            lock = directory.lock(self.start + DEADLINE - STOP_SECONDS - 7)
            record = parse_state(directory.read_bounded(STATE, STATE_LIMIT), self.hash)
            if record is None:
                return dict(action='stop', state='none')
            if record['status'] == 'failed':
                directory.remove(STATE)
                return dict(action='stop', state='failed', reason=record['reason'])
            if not hasattr(os, 'pidfd_open'):
                raise DashboardError('uncertain', 'this system cannot signal a process by pidfd; nothing was signalled')
            try:
                pidfd = os.pidfd_open(record['pid'])
            except ProcessLookupError:
                directory.remove(STATE)
                return dict(action='stop', state='stale')
            try:
                # Identify after pinning: a reused PID fails here, a pinned exit cannot be re-targeted.
                identity = identify(record)
                if identity == 'gone':
                    directory.remove(STATE)
                    return dict(action='stop', state='stale')
                if identity != 'owned':
                    raise DashboardError('uncertain', 'cannot confirm that process ' + str(record['pid'])
                                         + ' is this dashboard; nothing was signalled')
                healthy = health(record['port'], self.hash, record['launch_nonce']) is not None
                if not terminate(pidfd):
                    raise DashboardError('uncertain', 'managed dashboard process ' + str(record['pid'])
                                         + ' did not exit; state kept')
            finally:
                os.close(pidfd)
            directory.remove(STATE)
            return dict(action='stop', state='stopped', pid=record['pid'], was_healthy=healthy)
        finally:
            if lock is not None:
                os.close(lock)
            directory.close()


def exited(pidfd, seconds):
    readable, _, _ = select.select([pidfd], [], [], max(0.0, seconds))
    return bool(readable)


def terminate(pidfd):
    try:
        signal.pidfd_send_signal(pidfd, signal.SIGTERM)
    except ProcessLookupError:
        return True
    if exited(pidfd, STOP_SECONDS):
        return True
    try:
        signal.pidfd_send_signal(pidfd, signal.SIGKILL)
    except ProcessLookupError:
        return True
    return exited(pidfd, 5)


def open_url(url, environment):
    """Ask the desktop once from a detached helper that cannot hold the caller's pipes."""
    try:
        opener = subprocess.Popen([sys.executable, '-I', '-S', '-B', '-c', OPENER, url], env=environment,
                                  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                  stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True)
    except OSError:
        return 'not_opened'
    try:
        return 'opened' if opener.wait(timeout=OPEN_SECONDS) == 0 else 'not_opened'
    except subprocess.TimeoutExpired:
        return 'unconfirmed'


# ---------------------------------------------------------------- reporting
MESSAGES = {
    'none': 'No managed dashboard is recorded for this project. A foreground "unio browser" is not tracked.',
    'stale': 'The recorded dashboard process is gone or was replaced by another process; it was not signalled.',
    'failed': 'The last managed dashboard launch failed',
    'unhealthy': 'The managed dashboard process is running but does not answer as this project\'s dashboard.',
    'uncertain': 'Cannot confirm the recorded dashboard process identity; nothing was signalled.',
}
BROWSER = {
    'opened': 'Opened in the desktop browser.',
    'not_opened': 'No desktop browser could be opened; open the link above manually.',
    'unconfirmed': 'Desktop opening was requested but not confirmed; open the link above manually.',
    'not_new': 'Already running, so no new browser tab was opened.',
}


def render(result, project):
    lines = []
    state = result['state']
    if result.get('url'):
        lines.append('Unio dashboard (read-only): ' + result['url'])
    if state == 'started':
        lines.append('Started a new managed dashboard for ' + str(project) + '.')
        if result.get('previous') in ('stale', 'failed'):
            lines.append('The earlier record was ' + result['previous'] + '; no older process was signalled.')
    elif state == 'reused':
        lines.append('Reusing the running managed dashboard for ' + str(project) + '.')
    elif state == 'running':
        lines.append('Running (process ' + str(result['pid']) + ', Unio ' + result['version'] + ') for ' + str(project) + '.')
    elif state == 'stopped':
        lines.append('Stopped managed dashboard process ' + str(result['pid']) + '. Workers and STOP were not touched.')
    elif state == 'failed':
        lines.append(MESSAGES['failed'] + ' (' + result['reason'] + ').'
                     + (' Its record was cleared.' if result['action'] == 'stop' else ''))
    elif state == 'none' and result['action'] == 'stop':
        lines.append('No managed dashboard is recorded for this project; nothing was signalled.')
    elif state == 'stale' and result['action'] == 'stop':
        lines.append(MESSAGES['stale'] + ' Its record was cleared.')
    else:
        lines.append(MESSAGES.get(state, state))
    if result.get('browser') in BROWSER:
        lines.append(BROWSER[result['browser']])
    if result.get('version') and result['version'] != result.get('installed') and state in ('reused', 'running'):
        lines.append('It runs Unio ' + result['version'] + ' while ' + result['installed']
                     + ' is installed; use stop, then ensure, to restart it.')
    return '\n'.join(lines)


def select_project(value):
    project = Path(value).absolute()
    try:
        real = project.is_symlink() is False and project.resolve(strict=True) == project
    except OSError:
        real = False
    if not real or any(not (project / part).is_dir() or (project / part).is_symlink()
                       for part in ('repo', 'coord', 'wt')):
        raise DashboardError('invalid', 'project must be a real enclosing Unio workspace (repo/, coord/, wt/)')
    return project


EXIT = {'started': 0, 'reused': 0, 'running': 0, 'stopped': 0, 'none': 3, 'stale': 3, 'failed': 3}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) < 4:
        raise SystemExit('unio dashboard: run through the installed unio command')
    engine, browser_dir, version, default_project = argv[:4]
    parser = argparse.ArgumentParser(
        prog='unio dashboard',
        description='Start or reuse a detached, local, read-only browser dashboard for one project.')
    parser.add_argument('action', nargs='?', choices=('ensure', 'status', 'stop'), default='ensure',
                        help='ensure (default) starts or reuses it; status only reports; stop ends it')
    parser.add_argument('--project', help='enclosing workspace with repo/, coord/, wt/ (inferred inside a workspace)')
    parser.add_argument('--open-browser', action='store_true', help='ensure only: ask the desktop to open a newly started dashboard')
    parser.add_argument('--json', action='store_true', help='print one JSON document')
    options = parser.parse_args(argv[4:])
    if options.open_browser and options.action != 'ensure':
        parser.error('--open-browser applies to ensure only')
    if not VERSION.fullmatch(version):
        raise SystemExit('unio dashboard: invalid installed version')
    selected = options.project if options.project is not None else default_project
    try:
        if not selected:
            raise DashboardError('invalid', 'no Unio workspace (coord/ and wt/) found here; pass --project PATH')
        project = select_project(selected)
        dashboard = Dashboard(project, Path(engine).absolute(), Path(browser_dir).absolute(), version)
        result = getattr(dashboard, options.action)(**({'open_browser': options.open_browser}
                                                        if options.action == 'ensure' else {}))
        result['installed'] = version
        code = 0 if options.action == 'stop' and result['state'] in ('none', 'stale', 'failed') else EXIT.get(result['state'], 1)
    except DashboardError as error:
        result = dict(action=options.action, state=error.state, error=str(error))
        code = 2 if error.state == 'invalid' else 1
        project = None
    except OSError as error:
        result = dict(action=options.action, state='unsafe',
                      error='dashboard state is unavailable (' + (os.strerror(error.errno) if error.errno else 'I/O error') + ')')
        code, project = 1, None
    if options.json:
        result['schema_version'] = SCHEMA
        print(json.dumps(result, sort_keys=True, ensure_ascii=True))
    elif 'error' in result:
        print('unio dashboard: ' + result['error'], file=sys.stderr)
    else:
        print(render(result, project), flush=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
