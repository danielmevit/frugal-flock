# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Bounded read-only listing of tracked worktree text. No edits or execution."""
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import threading
import time
import unicodedata

ERRORS = {'invalid_request': 400, 'files_not_found': 404, 'files_unavailable': 503}
LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z')
OPAQUE = re.compile(r'[0-9a-f]{64}\Z')
MAX_WORKERS = 32
MAX_FILES = 256
PREVIEW_BYTES = 65536
LIST_CAP = 1024 * 1024
DEADLINE = 2.0
EXCLUDED_DIRS = {'.git', '.ssh', '.gnupg', '.aws', '.azure', '.kube', '.docker',
                 'auth', 'credential', 'credentials', 'secret', 'secrets'}
EXCLUDED_FILES = {'agents.conf', '.env', '.netrc', '.npmrc', '.pypirc', '.htpasswd',
                  '.git-credentials', '.gitconfig', '.pgpass', '.my.cnf',
                  'id_rsa', 'id_dsa', 'id_ecdsa', 'id_ed25519', 'known_hosts',
                  'credentials.json', 'credentials.yml', 'credentials.yaml',
                  'secrets.json', 'secrets.yml', 'secrets.yaml',
                  'auth.json', 'token.json', 'tokens.json', 'service-account.json'}
EXCLUDED_SUFFIXES = ('.pem', '.key', '.p12', '.pfx', '.kdbx', '.keystore')


class WorkerFilesError(Exception):
    def __init__(self, code):
        self.code, self.status = code, ERRORS[code]
        super().__init__(code)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def allowed_path(relative):
    if (not isinstance(relative, str) or not relative or len(relative) > 1024
            or len(relative.encode()) > 1024 or os.path.normpath(relative) != relative):
        return False
    if any(unicodedata.category(char) in ('Cc', 'Cf') for char in relative):
        return False
    parts = relative.split('/')
    if any(part in ('', '.', '..') for part in parts):
        return False
    if any(part in EXCLUDED_DIRS or part.startswith('.env') for part in parts):
        return False
    name = parts[-1]
    lowered = name.lower()
    if (name in EXCLUDED_FILES or name.startswith('.env') or name.endswith(EXCLUDED_SUFFIXES)
            or 'credential' in lowered):
        return False
    return True


class WorkerFilesService:
    """Startup worker grants are the only roots. Requests cannot choose a path."""

    def __init__(self, workspace, workers):
        self.workspace = Path(workspace).absolute()
        if self.workspace.resolve() != self.workspace or not self.workspace.is_dir():
            raise ValueError('invalid workspace')
        if not isinstance(workers, (list, tuple)) or not 1 <= len(workers) <= MAX_WORKERS:
            raise ValueError('invalid files workers')
        self.root = os.open(self.workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        self.lock = threading.Lock()
        self.grants = {}
        seen = []
        try:
            for worker in workers:
                if not isinstance(worker, str) or LABEL.fullmatch(worker) is None or worker in seen:
                    raise ValueError('invalid files worker')
                seen.append(worker)
                try:
                    fd = self._open('wt', worker, directory=True)
                except OSError:
                    raise ValueError('invalid files worker') from None
                try:
                    info = os.fstat(fd)
                finally:
                    os.close(fd)
                self.grants[digest(worker.encode())] = dict(worker=worker, dev=info.st_dev, ino=info.st_ino)
        except BaseException:
            os.close(self.root)
            self.root = None
            raise

    def close(self):
        with self.lock:
            if self.root is not None:
                os.close(self.root)
                self.root = None

    def _open(self, *parts, directory=False):
        if self.root is None:
            raise WorkerFilesError('files_unavailable')
        fd = os.dup(self.root)
        try:
            for index, part in enumerate(parts):
                if part in ('', '.', '..') or '/' in part or '\\' in part:
                    raise ValueError('path')
                isdir = index < len(parts) - 1 or directory
                nxt = os.open(part, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                              (os.O_DIRECTORY if isdir else 0), dir_fd=fd)
                os.close(fd)
                fd = nxt
                info = os.fstat(fd)
                if not (stat.S_ISDIR(info.st_mode) if isdir else stat.S_ISREG(info.st_mode)):
                    raise ValueError('special file')
                if not isdir and info.st_nlink != 1:
                    raise ValueError('hard link')
            return fd
        except BaseException:
            os.close(fd)
            raise

    def _entry(self, worker_id):
        if not isinstance(worker_id, str) or OPAQUE.fullmatch(worker_id) is None:
            raise WorkerFilesError('invalid_request')
        entry = self.grants.get(worker_id)
        if entry is None:
            raise WorkerFilesError('files_not_found')
        return entry

    def _confirm(self, entry):
        fd = self._open('wt', entry['worker'], directory=True)
        try:
            info = os.fstat(fd)
            if (info.st_dev, info.st_ino) != (entry['dev'], entry['ino']) or not stat.S_ISDIR(info.st_mode):
                raise WorkerFilesError('files_unavailable')
        except BaseException:
            os.close(fd)
            raise
        return fd

    def _open_relative(self, root_fd, relative):
        if not allowed_path(relative):
            raise ValueError('path')
        fd = os.dup(root_fd)
        try:
            parts = relative.split('/')
            for index, part in enumerate(parts):
                isdir = index < len(parts) - 1
                nxt = os.open(part, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK |
                              (os.O_DIRECTORY if isdir else 0), dir_fd=fd)
                os.close(fd)
                fd = nxt
                info = os.fstat(fd)
                if isdir:
                    if not stat.S_ISDIR(info.st_mode):
                        raise ValueError('special file')
                elif not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise ValueError('special file')
            return fd
        except BaseException:
            os.close(fd)
            raise

    def _git_paths(self, entry):
        # The worktree path is the startup grant, never request text.
        directory = str(self.workspace / 'wt' / entry['worker'])
        argv = ['git', '-C', directory, '-c', 'core.fsmonitor=false', '-c', 'core.untrackedCache=false',
                'ls-files', '-z', '--', '.']
        env = {'PATH': os.environ.get('PATH', ''), 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
               'GIT_CONFIG_GLOBAL': os.devnull, 'GIT_CONFIG_SYSTEM': os.devnull, 'GIT_TERMINAL_PROMPT': '0'}
        proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                env=env, start_new_session=True, close_fds=True)
        try:
            raw = proc.stdout.read(LIST_CAP + 1)
            overflow = len(raw) > LIST_CAP
            if overflow and proc.poll() is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                code = proc.wait(timeout=DEADLINE)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait(timeout=1)
                raise WorkerFilesError('files_unavailable') from None
        finally:
            if proc.stdout is not None:
                proc.stdout.close()
        if code != 0 and not overflow:
            raise WorkerFilesError('files_unavailable')
        if overflow:
            raw = raw[:LIST_CAP].rsplit(b'\0', 1)[0]
        elif raw.endswith(b'\0'):
            raw = raw[:-1]
        paths = []
        if raw:
            for piece in raw.split(b'\0'):
                try:
                    relative = piece.decode('utf-8')
                except UnicodeError:
                    continue
                if allowed_path(relative):
                    paths.append(relative)
        paths.sort()
        return paths, overflow

    def _safe_files(self, entry, begin):
        root = self._confirm(entry)
        try:
            paths, overflow = self._git_paths(entry)
            kept = []
            for relative in paths:
                if time.monotonic() - begin > DEADLINE:
                    raise WorkerFilesError('files_unavailable')
                try:
                    fd = self._open_relative(root, relative)
                except (OSError, ValueError):
                    continue
                os.close(fd)
                kept.append(relative)
                if len(kept) > MAX_FILES:
                    break
            truncated = overflow or len(kept) > MAX_FILES
            files = []
            for relative in kept[:MAX_FILES]:
                files.append(dict(file_id=digest((entry['worker'] + '\0' + relative).encode()),
                                   relative_path=relative))
            return files, truncated
        finally:
            os.close(root)

    def _read_text(self, entry, relative):
        root = self._confirm(entry)
        try:
            fd = self._open_relative(root, relative)
        except (OSError, ValueError):
            os.close(root)
            raise WorkerFilesError('files_unavailable') from None
        try:
            info = os.fstat(fd)
            raw = os.read(fd, PREVIEW_BYTES + 1)
            if b'\0' in raw[:PREVIEW_BYTES]:
                raise WorkerFilesError('files_unavailable')
            oversized = info.st_size > PREVIEW_BYTES or len(raw) > PREVIEW_BYTES
            chunk = raw[:PREVIEW_BYTES]
            try:
                if oversized:
                    try:
                        text = chunk.decode('utf-8')
                    except UnicodeDecodeError as error:
                        if error.start <= 0 or error.end != len(chunk):
                            raise WorkerFilesError('files_unavailable') from None
                        text = chunk[:error.start].decode('utf-8')
                else:
                    text = raw.decode('utf-8')
            except UnicodeError:
                raise WorkerFilesError('files_unavailable') from None
            other = self._open_relative(root, relative)
            try:
                after = os.fstat(other)
                if ((after.st_dev, after.st_ino) != (info.st_dev, info.st_ino)
                        or after.st_nlink != 1 or os.read(other, len(raw)) != raw):
                    raise WorkerFilesError('files_unavailable')
            finally:
                os.close(other)
            again = self._confirm(entry)
            os.close(again)
            return text, oversized
        finally:
            os.close(fd)
            os.close(root)

    def _operation(self, call):
        begin = time.monotonic()
        if self.root is None or not self.lock.acquire(timeout=DEADLINE):
            raise WorkerFilesError('files_unavailable')
        try:
            value = call(begin)
            if time.monotonic() - begin > DEADLINE:
                raise WorkerFilesError('files_unavailable')
            return value
        except WorkerFilesError:
            raise
        except Exception:
            raise WorkerFilesError('files_unavailable') from None
        finally:
            self.lock.release()

    def workers(self):
        def collect(_begin):
            rows = []
            for identity, entry in self.grants.items():
                fd = self._confirm(entry)
                os.close(fd)
                rows.append(dict(worker_id=identity, worker=entry['worker'],
                                 worktree_label='wt/' + entry['worker']))
            return dict(schema_version=1, workers=rows)
        return self._operation(collect)

    def files(self, worker_id):
        def collect(begin):
            entry = self._entry(worker_id)
            rows, truncated = self._safe_files(entry, begin)
            return dict(schema_version=1, worker_id=worker_id, worker=entry['worker'],
                        files=rows, truncated=truncated)
        return self._operation(collect)

    def preview(self, worker_id, file_id):
        def collect(begin):
            if not isinstance(file_id, str) or OPAQUE.fullmatch(file_id) is None:
                raise WorkerFilesError('invalid_request')
            entry = self._entry(worker_id)
            rows, _truncated = self._safe_files(entry, begin)
            match = next((row for row in rows if row['file_id'] == file_id), None)
            if match is None:
                raise WorkerFilesError('files_not_found')
            text, truncated = self._read_text(entry, match['relative_path'])
            return dict(schema_version=1, worker_id=worker_id, file_id=file_id,
                        relative_path=match['relative_path'],
                        observed_at=datetime.now(timezone.utc).isoformat(),
                        text=text, truncated=truncated)
        return self._operation(collect)
