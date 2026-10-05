# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Durable jobs awaiting owner approval; no dispatch, executor or approval."""
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import sqlite3
import stat
import uuid

try:
    from plan_store import PlanStore
except ImportError:
    import importlib.util

    _spec = importlib.util.spec_from_file_location(
        'plan_store', Path(__file__).with_name('plan_store.py'))
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    PlanStore = _module.PlanStore

STATE = 'awaiting_owner_approval'
DATABASE = 'ui-jobs.sqlite3'
COLUMNS = ('id', 'request_key', 'draft_id', 'draft_sha256', 'worker', 'created_at', 'state')
HEX32 = re.compile('[0-9a-f]{32}')
HEX64 = re.compile('[0-9a-f]{64}')
WORKER = re.compile('[a-z][a-z0-9_-]{0,63}')
BUSY_TIMEOUT = 10.0

CREATE_JOBS = ('CREATE TABLE jobs ('
               'id TEXT PRIMARY KEY, '
               'request_key TEXT NOT NULL UNIQUE, '
               'draft_id TEXT NOT NULL, '
               'draft_sha256 TEXT NOT NULL, '
               'worker TEXT NOT NULL, '
               'created_at TEXT NOT NULL, '
               'state TEXT NOT NULL)')
SELECT_JOB = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state '
               'FROM jobs WHERE id = ?')
SELECT_BY_KEY = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state '
                 'FROM jobs WHERE request_key = ?')
SELECT_PENDING = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state '
                   'FROM jobs ORDER BY created_at, id')
INSERT_JOB = ('INSERT INTO jobs '
              '(id, request_key, draft_id, draft_sha256, worker, created_at, state) '
              'VALUES (?, ?, ?, ?, ?, ?, ?)')


class JobStore:
    """Waiting jobs in coord/ui-jobs.sqlite3 under one owner-selected workspace.

    Reading a stored job never claims its referenced draft is still current,
    approved by the owner, or ready for dispatch; records only ever wait.
    """

    def __init__(self, workspace):
        workspace = Path(workspace).absolute()
        if workspace.resolve() != workspace or workspace.is_symlink():
            raise ValueError('workspace must be a real path')
        coordination = os.open(workspace / 'coord', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            try:
                info = os.stat(DATABASE, dir_fd=coordination, follow_symlinks=False)
            except FileNotFoundError:
                try:
                    descriptor = os.open(DATABASE,
                                         os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                         0o600, dir_fd=coordination)
                except FileExistsError:
                    pass
                else:
                    os.close(descriptor)
            else:
                if not stat.S_ISREG(info.st_mode):
                    raise ValueError('job database must be a regular file')
        finally:
            os.close(coordination)
        try:
            connection = sqlite3.connect(str(workspace / 'coord' / DATABASE),
                                         timeout=BUSY_TIMEOUT, isolation_level=None)
        except sqlite3.Error as error:
            raise ValueError('cannot open job database') from error
        try:
            connection.execute('BEGIN IMMEDIATE')
            version = connection.execute('PRAGMA user_version').fetchone()[0]
            objects = connection.execute(
                'SELECT COUNT(*) FROM sqlite_master').fetchone()[0]
            if version == 0 and objects == 0:
                try:
                    connection.execute(CREATE_JOBS)
                    connection.execute('PRAGMA user_version = 1')
                    connection.execute('COMMIT')
                except BaseException:
                    self._rollback(connection)
                    raise
            else:
                connection.execute('ROLLBACK')
                self._verify(connection)
        except sqlite3.Error as error:
            connection.close()
            raise ValueError('corrupt or unsupported job database') from error
        except BaseException:
            connection.close()
            raise
        self._db = connection
        self._workspace = workspace

    def close(self):
        if self._db is not None:
            db, self._db = self._db, None
            db.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _connection(self):
        if self._db is None:
            raise ValueError('store is closed')
        return self._db

    @staticmethod
    def _rollback(connection):
        try:
            connection.execute('ROLLBACK')
        except sqlite3.Error:
            pass

    @staticmethod
    def _verify(connection):
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version != 1:
            raise ValueError('unsupported job database schema version')
        columns = tuple(row[1] for row in connection.execute('PRAGMA table_info(jobs)'))
        if columns != COLUMNS:
            raise ValueError('unsupported job database schema')

    @staticmethod
    def _hex32(value, label):
        if not isinstance(value, str) or HEX32.fullmatch(value) is None:
            raise ValueError('invalid ' + label)
        return value

    @staticmethod
    def _hex64(value, label):
        if not isinstance(value, str) or HEX64.fullmatch(value) is None:
            raise ValueError('invalid ' + label)
        return value

    @staticmethod
    def _worker(value):
        if not isinstance(value, str) or WORKER.fullmatch(value) is None:
            raise ValueError('invalid worker ID')
        return value

    @staticmethod
    def _record(row):
        identity, request_key, draft_id, draft_sha256, worker, created_at, state = row
        values = (identity, request_key, draft_id, draft_sha256, worker, created_at, state)
        if any(not isinstance(value, str) for value in values):
            raise ValueError('corrupt job record')
        if (HEX32.fullmatch(identity) is None or HEX32.fullmatch(request_key) is None
                or HEX32.fullmatch(draft_id) is None or HEX64.fullmatch(draft_sha256) is None
                or WORKER.fullmatch(worker) is None or state != STATE):
            raise ValueError('corrupt job record')
        if datetime.fromisoformat(created_at).tzinfo is None:
            raise ValueError('job creation time must include timezone')
        return dict(id=identity, draft_id=draft_id, draft_sha256=draft_sha256, worker=worker,
                    request_key=request_key, created_at=created_at, state=state)

    def enqueue(self, draft_id, expected_hash, worker, request_key):
        """Idempotently record one job awaiting owner approval.

        The draft's current PlanStore content hash is checked before every
        create and every replay, so an edited draft never queues or requeues.
        """
        self._hex32(draft_id, 'draft ID')
        self._hex64(expected_hash, 'draft hash')
        self._worker(worker)
        self._hex32(request_key, 'request key')
        connection = self._connection()
        with PlanStore(self._workspace) as plans:
            draft = plans.get(draft_id)
            if draft['content_sha256'] != expected_hash:
                raise ValueError('draft content changed since the expected hash')
        connection.execute('BEGIN IMMEDIATE')
        try:
            existing = connection.execute(SELECT_BY_KEY, (request_key,)).fetchone()
            if existing is not None:
                record = self._record(existing)
                if (record['draft_id'] != draft_id
                        or record['draft_sha256'] != expected_hash
                        or record['worker'] != worker):
                    raise ValueError('request key already used with different job inputs')
                connection.execute('ROLLBACK')
                return record
            identity = uuid.uuid4().hex
            created_at = datetime.now(timezone.utc).isoformat()
            connection.execute(INSERT_JOB, (identity, request_key, draft_id, expected_hash,
                                            worker, created_at, STATE))
        except sqlite3.IntegrityError:
            self._rollback(connection)
            row = connection.execute(SELECT_BY_KEY, (request_key,)).fetchone()
            if row is None:
                raise
            record = self._record(row)
            if (record['draft_id'] != draft_id or record['draft_sha256'] != expected_hash
                    or record['worker'] != worker):
                raise ValueError('request key already used with different job inputs') from None
            return record
        except BaseException:
            self._rollback(connection)
            raise
        try:
            connection.execute('COMMIT')
        except sqlite3.Error:
            self._rollback(connection)
            raise
        return self.get(identity)

    def get(self, job_id):
        self._hex32(job_id, 'job ID')
        row = self._connection().execute(SELECT_JOB, (job_id,)).fetchone()
        return None if row is None else self._record(row)

    def pending(self):
        rows = self._connection().execute(SELECT_PENDING).fetchall()
        return [self._record(row) for row in rows]
