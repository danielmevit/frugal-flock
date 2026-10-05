# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
"""Durable manual draft storage; no HTTP, native tasks, approval or dispatch."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

MAX_REQUEST = 4000
MAX_RECORD = 65536
FIELDS = {'schema_version', 'id', 'created_at', 'state', 'request'}


class PlanStore:
    """Immutable drafts under one owner-selected workspace's coord/ui-plans/."""
    def __init__(self, workspace):
        workspace = Path(workspace).absolute()
        if workspace.resolve() != workspace or workspace.is_symlink():
            raise ValueError('workspace must be a real path')
        coordination = os.open(workspace / 'coord', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            try:
                os.mkdir('ui-plans', mode=0o700, dir_fd=coordination)
            except FileExistsError:
                pass
            self._fd = os.open('ui-plans', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=coordination)
        finally:
            os.close(coordination)

    def close(self):
        if self._fd is not None:
            fd, self._fd = self._fd, None
            os.close(fd)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _directory(self):
        if self._fd is None:
            raise ValueError('store is closed')
        return self._fd

    @staticmethod
    def _request(value):
        if not isinstance(value, str) or not value.strip() or len(value) > MAX_REQUEST:
            raise ValueError('request must contain 1 through 4000 characters of meaningful text')
        return value

    def create(self, request):
        request = self._request(request)
        directory = self._directory()
        identity = uuid.uuid4().hex
        record = dict(schema_version=1, id=identity, created_at=datetime.now(timezone.utc).isoformat(),
                      state='draft', request=request)
        raw = (json.dumps(record, ensure_ascii=True, sort_keys=True, separators=(',', ':')) + '\n').encode()
        temporary, name = '.' + identity + '.tmp', identity + '.json'
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=directory)
        try:
            with os.fdopen(descriptor, 'wb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            # Link publishes a complete immutable record and refuses overwrite.
            os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
            os.unlink(temporary, dir_fd=directory)
            os.fsync(directory)
        finally:
            try:
                os.unlink(temporary, dir_fd=directory)
            except FileNotFoundError:
                pass
        return {**record, 'content_sha256': hashlib.sha256(raw).hexdigest()}

    def get(self, identity):
        if not isinstance(identity, str) or re.fullmatch('[0-9a-f]{32}', identity) is None:
            raise ValueError('invalid plan ID')
        descriptor = os.open(identity + '.json', os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                             dir_fd=self._directory())
        with os.fdopen(descriptor, 'rb') as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise ValueError('plan record must be a regular file')
            raw = source.read(MAX_RECORD + 1)
        if len(raw) > MAX_RECORD:
            raise ValueError('plan record exceeds size limit')
        record = json.loads(raw)
        if (not isinstance(record, dict) or set(record) != FIELDS
                or type(record['schema_version']) is not int or record['schema_version'] != 1
                or record['id'] != identity or record['state'] != 'draft'
                or not isinstance(record['created_at'], str)):
            raise ValueError('unsupported plan record')
        self._request(record['request'])
        created = datetime.fromisoformat(record['created_at'])
        if created.tzinfo is None:
            raise ValueError('plan creation time must include timezone')
        return {**record, 'content_sha256': hashlib.sha256(raw).hexdigest()}
