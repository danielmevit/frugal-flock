# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Bounded observation of explicitly owned native Source receipts; no execution."""
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import secrets
import stat
import threading
import time
import unicodedata

from execution_service import _decode, _native_document

JSON_LIMIT = 131072
PAGE_BYTES = 16384
LINE_BYTES = 4096
LEDGER_BYTES = 65536
LEDGER_RECORDS = 256
MAX_BINDINGS = 32
DEADLINE = 2.0
STALE_SECONDS = 30
ERRORS = {'invalid_request': 400, 'progress_not_found': 404,
          'cursor_mismatch': 409, 'progress_unavailable': 503}
LABEL = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z')
OPAQUE = re.compile(r'[0-9a-f]{64}\Z')
SECRET = re.compile(r'(?i)(authorization|bearer\s|password|passwd|secret|api[ _-]?key|access[ _-]?token|refresh[ _-]?token|session[ _-]?token|agents\.conf|\.ssh[/\\]|\.git[/\\]|peer[ _-]?review|review[ _-]?material|BEGIN .*PRIVATE KEY|END .*PRIVATE KEY|https?://[^\s/]+:[^\s@]+@)')
TOKEN = re.compile(r'(?i)(?:sk-|gh[pousr]_|github_pat_|AKIA)[A-Za-z0-9_-]{8,}|[A-Za-z0-9+/=_-]{80,}')
ANSI = re.compile(r'\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\)|[PX^_][^\x1b]*\x1b\\|[@-_])')


class ProgressError(Exception):
    def __init__(self, code):
        self.code, self.status = code, ERRORS[code]
        super().__init__(code)


def digest(value):
    return hashlib.sha256(value).hexdigest()


def stamp(value):
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError('date')
    date = datetime.fromisoformat(value)
    if date.tzinfo is None:
        raise ValueError('timezone')
    return date.timestamp()


def literal(raw):
    text = raw.decode('utf-8', errors='strict')
    text = ANSI.sub('', text)
    text = ''.join(c for c in text if c in '\n\t' or unicodedata.category(c) not in ('Cc', 'Cf', 'Cs'))
    if SECRET.search(text) or TOKEN.search(text) or re.fullmatch(r'[A-Za-z0-9+/=]{32,}\s*', text):
        return '[sensitive output excluded]\n'
    return text


class ProgressService:
    """Startup bindings are authority. Only latest native attempts are supported."""
    def __init__(self, workspace, engine, bindings):
        self.workspace = Path(workspace).absolute()
        self.engine = Path(engine).absolute()
        if self.workspace.resolve() != self.workspace or not self.workspace.is_dir():
            raise ValueError('invalid workspace')
        if not 1 <= len(bindings) <= MAX_BINDINGS:
            raise ValueError('invalid bindings')
        self.bindings = {}
        tasks = set()
        for worker, task in bindings:
            if not LABEL.fullmatch(worker) or not LABEL.fullmatch(task) or task in tasks:
                raise ValueError('invalid or ambiguous binding')
            tasks.add(task)
            identity = digest((worker + '\0' + task).encode())
            self.bindings[identity] = (worker, task)
        self.key = secrets.token_bytes(32)
        self.generations = {}
        self.lock = threading.Lock()
        self.root = os.open(self.workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    def close(self):
        with self.lock:
            if self.root is not None:
                os.close(self.root)
                self.root = None

    def _open(self, *parts, directory=False):
        """Walk only fixed owned components, with dirfds to close rename races."""
        fd = os.dup(self.root)
        try:
            for index, part in enumerate(parts):
                if part in ('', '.', '..') or '/' in part:
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

    def _read(self, *parts, limit=JSON_LIMIT):
        fd = self._open(*parts)
        try:
            if os.fstat(fd).st_size > limit:
                raise ValueError('size')
            raw = os.read(fd, limit + 1)
            if len(raw) > limit:
                raise ValueError('size')
            return raw
        finally:
            os.close(fd)

    def _start(self, worker, task):
        fd = self._open('coord', 'reports', 'ledger.jsonl')
        try:
            size = os.fstat(fd).st_size
            start = max(0, size - LEDGER_BYTES)
            raw = os.pread(fd, LEDGER_BYTES, start)
        finally:
            os.close(fd)
        if start:
            raw = raw.partition(b'\n')[2]
        records = raw.split(b'\n')
        # Partial final records never establish ownership.
        for line in reversed(records[:-1][-LEDGER_RECORDS:]):
            event = _decode(line)
            if not isinstance(event, dict):
                raise ValueError('ledger')
            if event.get('event') == 'run_start' and event.get('task') == task:
                if event.get('worker') != worker:
                    raise ValueError('foreign source')
                return stamp(event['ts'])
        raise ValueError('missing source start')

    def _evidence(self, identity):
        if identity not in self.bindings:
            raise ProgressError('progress_not_found')
        worker, task = self.bindings[identity]
        fd = self._open('wt', worker, directory=True)
        os.close(fd)
        task_hash = digest(self._read('coord', 'tasks', task + '.md'))
        raw = self._read('coord', 'results', worker, task + '.json')
        native = _native_document(_decode(raw), worker, task)
        retry = _decode(self._read('coord', 'retries', task, 'state.json'))
        if (not isinstance(retry, dict) or type(retry.get('schema_version')) is not int
                or retry['schema_version'] != 1 or retry.get('task') != task
                or type(retry.get('failed_attempts')) is not int or retry['failed_attempts'] < 0
                or type(retry.get('retry_granted')) is not bool
                or not isinstance(retry.get('latest'), dict) or set(retry['latest']) != {worker}):
            raise ValueError('ambiguous attempt')
        attempt = retry['latest'][worker]
        if (not isinstance(attempt, dict) or set(attempt) != {'id', 'pending', 'failed'}
                or not isinstance(attempt['id'], str) or not re.fullmatch('[0-9a-f]{32}', attempt['id'])
                or type(attempt['pending']) is not bool or type(attempt['failed']) is not bool):
            raise ValueError('attempt')
        revision = native['process']['revision']
        if revision is None or revision['task_sha256'] != task_hash:
            raise ValueError('task changed')
        start = self._start(worker, task)
        updated = stamp(native['updated_at'])
        retry_time = stamp(retry['updated_at'])
        if start > updated + 1 or retry_time > updated:
            raise ValueError('inconsistent receipts')
        state = native['process']['state']
        if (state == 'running') != attempt['pending']:
            raise ValueError('inconsistent attempt')
        run = digest((identity + attempt['id'] + task_hash).encode())
        return worker, task, native, run, start, updated

    def _liveness(self, worker, task):
        try:
            raw = self._read('coord', 'reports', task + '.pid', limit=32)
        except FileNotFoundError:
            return 'unknown'
        if not re.fullmatch(b'[1-9][0-9]{0,9}\n', raw):
            return 'unknown'
        pid = int(raw)
        # Proc observation never signals, attaches to, or scans other processes.
        try:
            with open('/proc/' + str(pid) + '/cmdline', 'rb') as source:
                argv = source.read(4097).split(b'\0')
            cwd = os.readlink('/proc/' + str(pid) + '/cwd')
            if (len(argv) != 6 or argv[-1] != b'' or Path(os.fsdecode(argv[0])).name != 'bash'
                    or argv[1] != os.fsencode(self.engine) or argv[2:5] != [b'run', worker.encode(), task.encode()]
                    or cwd != str(self.workspace / 'repo')):
                return 'unknown'
            return 'running'
        except (OSError, ValueError):
            return 'unknown'

    def _cursor(self, run, generation, offset, skip=False):
        data = json.dumps([run, generation, offset, skip], separators=(',', ':')).encode()
        return base64.urlsafe_b64encode(data + hmac.digest(self.key, data, 'sha256')).decode().rstrip('=')

    def _uncursor(self, cursor, run, generation):
        if not isinstance(cursor, str) or not re.fullmatch('[A-Za-z0-9_-]{1,512}', cursor):
            raise ProgressError('invalid_request')
        try:
            raw = base64.b64decode(cursor + '=' * (-len(cursor) % 4), altchars=b'-_', validate=True)
            data, signature = raw[:-32], raw[-32:]
            value = _decode(data)
            if (not hmac.compare_digest(signature, hmac.digest(self.key, data, 'sha256'))
                    or not isinstance(value, list) or len(value) != 4 or value[:2] != [run, generation]
                    or type(value[2]) is not int or not 0 <= value[2] <= 2**63 - 1
                    or type(value[3]) is not bool):
                raise ValueError('cursor')
            return value[2], value[3]
        except (ValueError, TypeError):
            raise ProgressError('cursor_mismatch') from None

    def _log(self, identity, run, task, start, updated, native):
        fd = self._open('coord', 'reports', task + '.log')
        try:
            info = os.fstat(fd)
            # Running receipt precedes the shell's truncate/open. Old output is unavailable.
            earliest = updated if native['process']['state'] == 'running' else start
            if info.st_mtime < earliest or (native['process']['state'] != 'running' and info.st_mtime > updated):
                raise ValueError('unbound log')
            prior = self.generations.get(identity)
            changed = prior is None or prior['run'] != run or prior['file'] != (info.st_dev, info.st_ino)
            if not changed:
                changed = (info.st_size < prior['size']
                    or (info.st_size == prior['size'] and (info.st_mtime_ns, info.st_ctime_ns) != prior['times'])
                    or os.pread(fd, len(prior['prefix']), 0) != prior['prefix']
                    or os.pread(fd, len(prior['anchor']), prior['at']) != prior['anchor'])
            generation = secrets.token_hex(32) if changed else prior['generation']
            at = max(0, info.st_size - 256)
            self.generations[identity] = dict(run=run, file=(info.st_dev, info.st_ino), size=info.st_size,
                at=at, anchor=os.pread(fd, 256, at), prefix=os.pread(fd, min(info.st_size, 256), 0),
                times=(info.st_mtime_ns, info.st_ctime_ns), generation=generation)
            return fd, info, generation
        except BaseException:
            os.close(fd)
            raise

    def _page(self, fd, size, run, generation, cursor=None, excerpt=False):
        offset, skip = self._uncursor(cursor, run, generation) if cursor else (0, False)
        if excerpt:
            offset, skip = max(0, size - PAGE_BYTES), size > PAGE_BYTES
        if offset > size:
            raise ProgressError('cursor_mismatch')
        raw = os.pread(fd, PAGE_BYTES, offset)
        end = raw.rfind(b'\n') + 1
        partial = len(raw) > end
        output = []
        consumed = end
        if skip:
            first = raw.find(b'\n')
            if first < 0:
                return '', offset + len(raw), True, partial
            raw_records = raw[first + 1:end]
            skip = False
        else:
            raw_records = raw[:end]
        for line in raw_records.splitlines(keepends=True):
            if len(line) > LINE_BYTES:
                output.append('[long output record excluded]\n')
            else:
                try:
                    output.append(literal(line))
                except UnicodeError:
                    output.append('[invalid UTF-8 record excluded]\n')
        if len(raw) - end > LINE_BYTES:
            consumed, skip = len(raw), True
            output.append('[long output record excluded]\n')
        text = ''.join(output)
        if excerpt:
            text = text[-1024:]
        return text, offset + consumed, skip, partial

    def _view(self, identity, run_id=None, cursor=None, output=False):
        worker, task, native, run, start, updated = self._evidence(identity)
        if run_id is not None and run_id != run:
            raise ProgressError('progress_not_found')
        now = time.time()
        observed = datetime.now(timezone.utc).isoformat()
        life = self._liveness(worker, task)
        view = dict(schema_version=1, worker_id=identity, worker=worker, task=task, run_id=run,
            observed_at=observed, recorded_at=native['updated_at'], observation_stale=now - updated > STALE_SECONDS,
            source=native['process'], verification=native['validation'], review=native['review'],
            acceptance={'state': 'unavailable'}, recorded_evidence_stale=native['stale'],
            observed_liveness=life, observed_phase='source' if life == 'running' else 'unknown',
            output=dict(state='unavailable', generation=None, observed_at=observed, modified_at=None,
                        excerpt='', text='', next_cursor=None, at_end=None, partial_record=False))
        try:
            fd, info, generation = self._log(identity, run, task, start, updated, native)
        except FileNotFoundError:
            self.generations.pop(identity, None)
            view['output']['state'] = 'missing'
            if cursor:
                raise ProgressError('cursor_mismatch') from None
            return view
        except (ValueError, OSError):
            self.generations.pop(identity, None)
            if cursor:
                raise ProgressError('cursor_mismatch') from None
            return view
        try:
            text, offset, skip, partial = self._page(fd, info.st_size, run, generation, cursor, excerpt=not output)
            # Verify the same owned path, identity and already-read content after the read.
            other = self._open('coord', 'reports', task + '.log')
            try:
                after = os.fstat(other)
                if (after.st_dev, after.st_ino) != (info.st_dev, info.st_ino) or after.st_size < info.st_size:
                    raise ProgressError('cursor_mismatch')
            finally:
                os.close(other)
            if self._evidence(identity)[3] != run:
                raise ProgressError('cursor_mismatch')
            state = 'first_output_wait' if info.st_size == 0 else ('quiet' if now - info.st_mtime > STALE_SECONDS else 'available')
            view['output'] = dict(state=state, generation=generation, observed_at=observed,
                modified_at=datetime.fromtimestamp(info.st_mtime, timezone.utc).isoformat(),
                excerpt='' if output else text, text=text if output else '',
                next_cursor=self._cursor(run, generation, offset, skip), at_end=offset == info.st_size,
                partial_record=partial)
            return view
        finally:
            os.close(fd)

    def _operation(self, call):
        begin = time.monotonic()
        if not self.lock.acquire(timeout=DEADLINE):
            raise ProgressError('progress_unavailable')
        try:
            value = call(begin)
            if time.monotonic() - begin > DEADLINE:
                raise ProgressError('progress_unavailable')
            return value
        except ProgressError:
            raise
        except Exception:
            raise ProgressError('progress_unavailable') from None
        finally:
            self.lock.release()

    def workers(self):
        def collect(begin):
            views = []
            for identity in self.bindings:
                if time.monotonic() - begin > DEADLINE:
                    raise ProgressError('progress_unavailable')
                try:
                    views.append(self._view(identity))
                except (ValueError, OSError):
                    views.append(dict(schema_version=1, worker_id=identity, worker=self.bindings[identity][0],
                                      task=self.bindings[identity][1], state='unavailable'))
            return dict(schema_version=1, workers=views)
        return self._operation(collect)

    def runs(self, worker_id):
        return dict(schema_version=1, runs=[self.get(worker_id)])

    def get(self, worker_id, run_id=None, cursor=None, output=False):
        if not isinstance(worker_id, str) or not OPAQUE.fullmatch(worker_id) or (run_id is not None and not OPAQUE.fullmatch(run_id)):
            raise ProgressError('invalid_request')
        return self._operation(lambda _: self._view(worker_id, run_id, cursor, output))
