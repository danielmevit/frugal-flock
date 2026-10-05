# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Durable queue jobs with explicit approval and reservation; no executor or dispatch."""
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
COLUMNS = ('id', 'request_key', 'draft_id', 'draft_sha256', 'worker', 'created_at', 'state', 'approval_key', 'approved_at', 'reservation_key', 'reserved_at', 'unknown_at', 'cancelled_at')
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
               'state TEXT NOT NULL, '
               'approval_key TEXT UNIQUE, '
               'approved_at TEXT, '
               'reservation_key TEXT UNIQUE, '
               'reserved_at TEXT, '
               'unknown_at TEXT, '
               'cancelled_at TEXT)')
# The only schema-1 layout ever created; anything else at version 1 is refused.
SCHEMA1_JOBS = ('CREATE TABLE jobs ('
                'id TEXT PRIMARY KEY, '
                'request_key TEXT NOT NULL UNIQUE, '
                'draft_id TEXT NOT NULL, '
                'draft_sha256 TEXT NOT NULL, '
                'worker TEXT NOT NULL, '
                'created_at TEXT NOT NULL, '
                'state TEXT NOT NULL)')
SCHEMA1_SELECT = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state '
                  'FROM jobs ORDER BY created_at, id')
MIGRATE_JOBS = ('INSERT INTO jobs_new '
                '(id, request_key, draft_id, draft_sha256, worker, created_at, state) '
                'SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state FROM jobs')
SELECT_JOB = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state, '
               'approval_key, approved_at, reservation_key, reserved_at, unknown_at, cancelled_at '
               'FROM jobs WHERE id = ?')
SELECT_BY_KEY = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state, '
                 'approval_key, approved_at, reservation_key, reserved_at, unknown_at, cancelled_at '
                 'FROM jobs WHERE request_key = ?')
SELECT_PENDING = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state, '
                   'approval_key, approved_at, reservation_key, reserved_at, unknown_at, cancelled_at '
                   'FROM jobs WHERE state = ? ORDER BY created_at, id')
SELECT_JOBS = ('SELECT id, request_key, draft_id, draft_sha256, worker, created_at, state, '
               'approval_key, approved_at, reservation_key, reserved_at, unknown_at, cancelled_at '
               'FROM jobs ORDER BY created_at, id')
INSERT_JOB = ('INSERT INTO jobs '
              '(id, request_key, draft_id, draft_sha256, worker, created_at, state) '
              'VALUES (?, ?, ?, ?, ?, ?, ?)')


def _quote(name):
    return '"' + name.replace('"', '""') + '"'


def _schema_tokens(sql):
    """Keep DDL syntax that PRAGMAs omit, ignoring whitespace and name quoting.

    ALTER TABLE quotes the migrated table name. Other syntax, including
    CHECK constraints and table options, must still match the known DDL.
    """
    tokens = re.findall(r'"(?:[^"]|"")*"|[A-Za-z_][A-Za-z0-9_]*|[^\s]', sql)
    return tuple((token[1:-1].replace('""', '"') if token.startswith('"') else token).lower()
                 for token in tokens)


def _expected_layout(create):
    reference = sqlite3.connect(':memory:')
    try:
        reference.execute(create)
        return JobStore._layout(reference)
    finally:
        reference.close()


class JobStore:
    """Waiting jobs in coord/ui-jobs.sqlite3 under one owner-selected workspace.

    Reading a stored job never claims its referenced draft is still current
    or ready for dispatch; approve and reserve recheck the draft each time.
    Nothing here executes a job, starts a process or calls a provider.
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
                    connection.execute('PRAGMA user_version = 2')
                    connection.execute('COMMIT')
                except BaseException:
                    self._rollback(connection)
                    raise
            elif version == 1:
                try:
                    self._migrate(connection)
                    connection.execute('COMMIT')
                except BaseException:
                    self._rollback(connection)
                    raise
            else:
                try:
                    self._verify(connection)
                finally:
                    self._rollback(connection)
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
    def _layout(connection):
        """Describe the jobs table's columns, constraints and companion objects.

        Autoindex names are left out because a renamed table keeps its
        original numbering; everything that affects stored data is kept.
        """
        # table_info hides generated columns; table_xinfo includes them and
        # their hidden/generated flags so they cannot be lost in migration.
        columns = tuple(row[1:] for row in connection.execute('PRAGMA table_xinfo(jobs)'))
        indexes = []
        for _, name, unique, origin, partial in connection.execute('PRAGMA index_list(jobs)').fetchall():
            keys = tuple((row[2], row[3], row[4]) for row
                         in connection.execute('PRAGMA index_xinfo(' + _quote(name) + ')') if row[5])
            indexes.append((origin, unique, partial, keys))
        others = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE NOT (type = 'table' AND name = 'jobs') "
            "AND NOT (type = 'index' AND tbl_name = 'jobs' AND sql IS NULL)").fetchone()[0]
        schema = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'jobs'").fetchone()
        definition = _schema_tokens(schema[0]) if schema is not None else ()
        return columns, tuple(sorted(indexes)), others, definition

    @classmethod
    def _verify(cls, connection):
        version = connection.execute('PRAGMA user_version').fetchone()[0]
        if version != 2:
            raise ValueError('unsupported job database schema version')
        if cls._layout(connection) != _expected_layout(CREATE_JOBS):
            raise ValueError('unsupported job database schema')

    @classmethod
    def _migrate(cls, connection):
        """Upgrade the recognized schema-1 layout inside the caller's transaction.

        Every legacy record is validated before anything is written, and the
        result is verified before the caller commits, so a refusal leaves the
        database exactly as it was.
        """
        if cls._layout(connection) != _expected_layout(SCHEMA1_JOBS):
            raise ValueError('unsupported schema-1 job database layout')
        legacy = connection.execute(SCHEMA1_SELECT).fetchall()
        for row in legacy:
            if cls._record(tuple(row) + (None,) * 6)['state'] != STATE:
                raise ValueError('corrupt schema-1 job record')
        connection.execute(CREATE_JOBS.replace('CREATE TABLE jobs', 'CREATE TABLE jobs_new'))
        connection.execute(MIGRATE_JOBS)
        connection.execute('DROP TABLE jobs')
        connection.execute('ALTER TABLE jobs_new RENAME TO jobs')
        connection.execute('PRAGMA user_version = 2')
        cls._verify(connection)
        migrated = connection.execute(SELECT_JOBS).fetchall()
        if [tuple(row[:7]) for row in migrated] != [tuple(row) for row in legacy]:
            raise ValueError('schema-1 migration did not preserve job records')
        for row in migrated:
            cls._record(row)

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
        (identity, request_key, draft_id, draft_sha256, worker, created_at, state,
         approval_key, approved_at, reservation_key, reserved_at, unknown_at, cancelled_at) = row
        values = (identity, request_key, draft_id, draft_sha256, worker, created_at, state)
        if any(not isinstance(value, str) for value in values):
            raise ValueError('corrupt job record')
        if (HEX32.fullmatch(identity) is None or HEX32.fullmatch(request_key) is None
                or HEX32.fullmatch(draft_id) is None or HEX64.fullmatch(draft_sha256) is None
                or WORKER.fullmatch(worker) is None):
            raise ValueError('corrupt job record')
        if datetime.fromisoformat(created_at).tzinfo is None:
            raise ValueError('job creation time must include timezone')

        def check_hex32(val):
            return val is None or (isinstance(val, str) and HEX32.fullmatch(val) is not None)

        def check_ts(val):
            return val is None or (isinstance(val, str) and datetime.fromisoformat(val).tzinfo is not None)

        if not (check_hex32(approval_key) and check_hex32(reservation_key)):
            raise ValueError('corrupt job record')
        if not (check_ts(approved_at) and check_ts(reserved_at) and check_ts(unknown_at) and check_ts(cancelled_at)):
            raise ValueError('corrupt job record')

        if ((approval_key is None) != (approved_at is None)
                or (reservation_key is None) != (reserved_at is None)):
            raise ValueError('corrupt job record')

        if state == 'awaiting_owner_approval':
            if any(value is not None for value in row[7:]):
                raise ValueError('corrupt job record')
        elif state == 'approved':
            if (approval_key is None
                    or any(value is not None for value in (reservation_key, reserved_at, unknown_at, cancelled_at))):
                raise ValueError('corrupt job record')
        elif state == 'reserved':
            if (approval_key is None or reservation_key is None
                    or unknown_at is not None or cancelled_at is not None):
                raise ValueError('corrupt job record')
        elif state == 'completion_unknown':
            if (approval_key is None or reservation_key is None
                    or unknown_at is None or cancelled_at is not None):
                raise ValueError('corrupt job record')
        elif state == 'cancelled':
            if (cancelled_at is None
                    or any(value is not None for value in (reservation_key, reserved_at, unknown_at))):
                raise ValueError('corrupt job record')
        else:
            raise ValueError('corrupt job record')

        return dict(id=identity, draft_id=draft_id, draft_sha256=draft_sha256, worker=worker,
                    request_key=request_key, created_at=created_at, state=state,
                    approval_key=approval_key, approved_at=approved_at,
                    reservation_key=reservation_key, reserved_at=reserved_at,
                    unknown_at=unknown_at, cancelled_at=cancelled_at)

    def _require_current(self, draft_id, expected_hash):
        with PlanStore(self._workspace) as plans:
            draft = plans.get(draft_id)
        if draft['content_sha256'] != expected_hash:
            raise ValueError('draft content changed since the expected hash')

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
        rows = self._connection().execute(SELECT_PENDING, ('awaiting_owner_approval',)).fetchall()
        return [self._record(row) for row in rows]

    def jobs(self):
        rows = self._connection().execute(SELECT_JOBS).fetchall()
        return [self._record(row) for row in rows]

    def approve(self, job_id, expected_hash, worker, approval_key):
        self._hex32(job_id, 'job ID')
        self._hex64(expected_hash, 'draft hash')
        self._worker(worker)
        self._hex32(approval_key, 'approval key')
        connection = self._connection()
        connection.execute('BEGIN IMMEDIATE')
        try:
            row = connection.execute(SELECT_JOB, (job_id,)).fetchone()
            if row is None:
                raise ValueError('job not found')
            record = self._record(row)

            if record['draft_sha256'] != expected_hash or record['worker'] != worker:
                raise ValueError('approval inputs do not match job')

            if record['state'] in ('reserved', 'completion_unknown', 'cancelled'):
                raise ValueError('job cannot be approved in current state')

            # Recheck the draft even on replay: an old approval is never
            # returned as success once its draft has changed.
            self._require_current(record['draft_id'], expected_hash)

            if record['state'] == 'approved':
                if record['approval_key'] == approval_key:
                    connection.execute('ROLLBACK')
                    return record
                raise ValueError('job already approved with a different key')

            approved_at = datetime.now(timezone.utc).isoformat()
            try:
                connection.execute('UPDATE jobs SET state = ?, approval_key = ?, approved_at = ? WHERE id = ?',
                                   ('approved', approval_key, approved_at, job_id))
            except sqlite3.IntegrityError:
                raise ValueError('approval key already used')
            connection.execute('COMMIT')
        except BaseException:
            self._rollback(connection)
            raise
        return self.get(job_id)

    def reserve(self, job_id, approval_key, reservation_key):
        self._hex32(job_id, 'job ID')
        self._hex32(approval_key, 'approval key')
        self._hex32(reservation_key, 'reservation key')
        connection = self._connection()
        connection.execute('BEGIN IMMEDIATE')
        try:
            row = connection.execute(SELECT_JOB, (job_id,)).fetchone()
            if row is None:
                raise ValueError('job not found')
            record = self._record(row)

            if record['state'] not in ('approved', 'reserved'):
                raise ValueError('job cannot be reserved in current state')

            if record['approval_key'] != approval_key:
                raise ValueError('approval key mismatch')

            # Recheck the draft even on replay. A successful replay still
            # reports newly_reserved=False, so it never authorizes a dispatch.
            self._require_current(record['draft_id'], record['draft_sha256'])

            if record['state'] == 'reserved':
                if record['reservation_key'] == reservation_key:
                    connection.execute('ROLLBACK')
                    return dict(job=record, newly_reserved=False)
                raise ValueError('job already reserved with a different key')

            reserved_at = datetime.now(timezone.utc).isoformat()
            try:
                connection.execute('UPDATE jobs SET state = ?, reservation_key = ?, reserved_at = ? WHERE id = ?',
                                   ('reserved', reservation_key, reserved_at, job_id))
            except sqlite3.IntegrityError:
                raise ValueError('reservation key already used')
            connection.execute('COMMIT')
        except BaseException:
            self._rollback(connection)
            raise
        return dict(job=self.get(job_id), newly_reserved=True)

    def mark_unknown(self, job_id, reservation_key):
        self._hex32(job_id, 'job ID')
        self._hex32(reservation_key, 'reservation key')
        connection = self._connection()
        connection.execute('BEGIN IMMEDIATE')
        try:
            row = connection.execute(SELECT_JOB, (job_id,)).fetchone()
            if row is None:
                raise ValueError('job not found')
            record = self._record(row)

            if record['state'] == 'completion_unknown':
                if record['reservation_key'] == reservation_key:
                    connection.execute('ROLLBACK')
                    return record
                raise ValueError('job already marked unknown for a different reservation')

            if record['state'] != 'reserved':
                raise ValueError('only reserved jobs can be marked unknown')

            if record['reservation_key'] != reservation_key:
                raise ValueError('reservation key mismatch')

            unknown_at = datetime.now(timezone.utc).isoformat()
            connection.execute('UPDATE jobs SET state = ?, unknown_at = ? WHERE id = ?',
                               ('completion_unknown', unknown_at, job_id))
            connection.execute('COMMIT')
        except BaseException:
            self._rollback(connection)
            raise
        return self.get(job_id)

    def cancel(self, job_id):
        self._hex32(job_id, 'job ID')
        connection = self._connection()
        connection.execute('BEGIN IMMEDIATE')
        try:
            row = connection.execute(SELECT_JOB, (job_id,)).fetchone()
            if row is None:
                raise ValueError('job not found')
            record = self._record(row)

            if record['state'] == 'cancelled':
                connection.execute('ROLLBACK')
                return record

            if record['state'] not in ('awaiting_owner_approval', 'approved'):
                raise ValueError('job cannot be cancelled in current state')

            cancelled_at = datetime.now(timezone.utc).isoformat()
            connection.execute('UPDATE jobs SET state = ?, cancelled_at = ? WHERE id = ?',
                               ('cancelled', cancelled_at, job_id))
            connection.execute('COMMIT')
        except BaseException:
            self._rollback(connection)
            raise
        return self.get(job_id)
