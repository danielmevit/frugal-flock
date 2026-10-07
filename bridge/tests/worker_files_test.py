# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
import hashlib
import http.client
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parents[1]))
import server
from worker_files import WorkerFilesError, WorkerFilesService, LIST_CAP, PREVIEW_BYTES


SCRATCH = Path(__file__).resolve().parents[2].parent.parent / 'tmp'


def git(directory, *args):
    subprocess.run(['git', '-C', str(directory), *args], check=True, capture_output=True)


class FilesFixture:
    def __init__(self, root, worker='w1'):
        self.root, self.worker = root, worker
        self.work = root / 'wt' / worker
        for name in ('repo', 'coord', 'wt'):
            (root / name).mkdir()
        self.work.mkdir()
        git(self.work, 'init', '-q', '-b', 'main')
        git(self.work, 'config', 'user.email', 'files@invalid')
        git(self.work, 'config', 'user.name', 'Files')
        (self.work / 'src').mkdir()
        (self.work / 'src' / 'hello.txt').write_text('hello source\n', encoding='utf-8')
        (self.work / 'odd<name>.txt').write_text('plain <b>literal</b>\n', encoding='utf-8')
        (self.work / '.env').write_text('SECRET=do-not-show\n', encoding='utf-8')
        (self.work / 'auth').mkdir()
        (self.work / 'auth' / 'token.txt').write_text('SECRET-TOKEN\n', encoding='utf-8')
        (self.work / 'notes.pem').write_text('SECRET-PEM\n', encoding='utf-8')
        outside = root / 'outside-secret.txt'
        outside.write_text('SECRET-LINK\n', encoding='utf-8')
        (self.work / 'leak.txt').symlink_to(outside)
        (self.work / 'hard.txt').write_text('hard\n', encoding='utf-8')
        os.link(self.work / 'hard.txt', self.work / 'also-hard.txt')
        (self.work / 'src' / 'binary.bin').write_bytes(b'\xff\xfe binary')
        (self.work / 'src' / 'untracked.txt').write_text('UNTRACKED\n', encoding='utf-8')
        git(self.work, 'add', '--', 'src/hello.txt', 'odd<name>.txt', '.env', 'auth/token.txt',
            'notes.pem', 'leak.txt', 'hard.txt', 'also-hard.txt', 'src/binary.bin')
        git(self.work, 'commit', '-qm', 'tracked')

    @property
    def identity(self):
        return hashlib.sha256(self.worker.encode()).hexdigest()

    def file_id(self, relative):
        return hashlib.sha256((self.worker + '\0' + relative).encode()).hexdigest()


class WorkerFilesTests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='worker-files-', dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = FilesFixture(self.root)
        self.service = WorkerFilesService(self.root, [self.fixture.worker])
        self.addCleanup(self.service.close)
        self.calls = []
        self.pins = []
        real = subprocess.Popen
        def spy(*args, **kwargs):
            argv = args[0] if args else kwargs.get('args')
            idents = []
            for fd in kwargs.get('pass_fds') or ():
                info = os.fstat(fd)
                idents.append((info.st_dev, info.st_ino))
            self.calls.append((list(argv), kwargs.get('env')))
            self.pins.append(tuple(idents))
            return real(*args, **kwargs)
        self.effects = patch('worker_files.subprocess.Popen', side_effect=spy)
        self.effects.start()
        self.addCleanup(self.effects.stop)

    def test_tracked_text_excludes_secrets_links_and_untracked_files(self):
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'PRIVATE-ENV'
        self.addCleanup(os.environ.pop, 'AWS_SECRET_ACCESS_KEY', None)
        body = self.service.files(self.fixture.identity)
        paths = [item['relative_path'] for item in body['files']]
        self.assertEqual(paths, ['odd<name>.txt', 'src/binary.bin', 'src/hello.txt'])
        self.assertFalse(body['truncated'])
        self.assertNotIn('SECRET', json.dumps(body))
        self.assertTrue(self.calls)
        argv, env = self.calls[-1]
        self.assertEqual(argv[:2], ['git', '-C'])
        self.assertRegex(argv[2], r'\A/proc/self/fd/[0-9]+\Z')
        self.assertEqual(argv[3:6], ['-c', 'core.fsmonitor=false', '-c'])
        self.assertEqual(argv[6:], ['core.untrackedCache=false', 'ls-files', '-z', '--', '.'])
        self.assertNotIn(str(self.fixture.work), argv)
        self.assertNotIn('shell', argv)
        self.assertNotIn(self.fixture.identity, argv)
        info = os.stat(self.fixture.work)
        self.assertIn((info.st_dev, info.st_ino), self.pins[-1])
        self.assertEqual(env.get('GIT_CONFIG_NOSYSTEM'), '1')
        self.assertEqual(env.get('GIT_CONFIG_GLOBAL'), os.devnull)
        self.assertEqual(env.get('GIT_CONFIG_SYSTEM'), os.devnull)
        self.assertEqual(env.get('GIT_TERMINAL_PROMPT'), '0')
        self.assertNotIn('AWS_SECRET_ACCESS_KEY', env)
        self.assertNotIn('PRIVATE-ENV', json.dumps(env))
        preview = self.service.preview(self.fixture.identity, self.fixture.file_id('src/hello.txt'))
        self.assertEqual(preview['text'], 'hello source\n')
        self.assertFalse(preview['truncated'])
        self.assertEqual(preview['relative_path'], 'src/hello.txt')
        odd = self.service.preview(self.fixture.identity, self.fixture.file_id('odd<name>.txt'))
        self.assertIn('<b>literal</b>', odd['text'])
        with self.assertRaises(WorkerFilesError) as missing:
            self.service.preview(self.fixture.identity, self.fixture.file_id('.env'))
        self.assertEqual(missing.exception.code, 'files_not_found')
        for hidden in ('auth/token.txt', 'leak.txt', 'hard.txt', 'src/untracked.txt', '../outside-secret.txt'):
            with self.assertRaises(WorkerFilesError):
                self.service.preview(self.fixture.identity, self.fixture.file_id(hidden))
        with self.assertRaises(WorkerFilesError) as binary:
            self.service.preview(self.fixture.identity, self.fixture.file_id('src/binary.bin'))
        self.assertEqual(binary.exception.code, 'files_unavailable')

    def test_preview_truncates_at_the_byte_bound_and_invalid_utf8_is_unavailable(self):
        path = self.fixture.work / 'src' / 'hello.txt'
        path.write_bytes(b'a' * (PREVIEW_BYTES + 20) + b'END')
        preview = self.service.preview(self.fixture.identity, self.fixture.file_id('src/hello.txt'))
        self.assertTrue(preview['truncated'])
        self.assertLessEqual(len(preview['text'].encode()), PREVIEW_BYTES)
        self.assertNotIn('END', preview['text'])
        path.write_bytes('hello '.encode() + b'\xff\xfe')
        with self.assertRaises(WorkerFilesError) as error:
            self.service.preview(self.fixture.identity, self.fixture.file_id('src/hello.txt'))
        self.assertEqual(error.exception.code, 'files_unavailable')
        self.assertNotIn('hello', str(error.exception))

    def test_listing_truncates_after_256_tracked_files(self):
        for index in range(257):
            (self.fixture.work / f'f{index:03d}.txt').write_text('x\n', encoding='utf-8')
        git(self.fixture.work, 'add', '--', '.')
        git(self.fixture.work, 'commit', '-qm', 'many')
        body = self.service.files(self.fixture.identity)
        self.assertTrue(body['truncated'])
        self.assertEqual(len(body['files']), 256)
        paths = [item['relative_path'] for item in body['files']]
        self.assertNotIn('.env', paths)
        self.assertNotIn('auth/token.txt', paths)

    def test_startup_rejects_partial_duplicate_and_missing_worktrees(self):
        with self.assertRaises(ValueError):
            WorkerFilesService(self.root, [])
        with self.assertRaises(ValueError):
            WorkerFilesService(self.root, ['w1', 'w1'])
        with self.assertRaises(ValueError):
            WorkerFilesService(self.root, ['missing-worker'])
        with self.assertRaises(ValueError):
            WorkerFilesService(self.root, ['bad/worker'])
        with self.assertRaises(ValueError):
            WorkerFilesService(self.root, ['w' + str(index) for index in range(33)])

    def install_git(self, script):
        directory = self.root / 'fake-bin'
        directory.mkdir(exist_ok=True)
        path = directory / 'git'
        path.write_text(script, encoding='utf-8')
        path.chmod(0o755)
        return directory

    def assert_reaped(self, pid):
        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            if not os.path.exists('/proc/%d' % pid):
                return
            time.sleep(0.02)
        self.fail('process %s was not reaped' % pid)

    def read_pid(self, path):
        self.assertTrue(path.is_file(), path)
        return int(path.read_text(encoding='utf-8').strip())

    def test_silent_git_hits_deadline_reaps_group_and_next_request_works(self):
        leader = self.root / 'leader.pid'
        child = self.root / 'child.pid'
        self.install_git(
            '#!/bin/sh\n'
            'echo $$ > %s\n'
            'sleep 30 &\n'
            'echo $! > %s\n'
            'wait\n' % (shlex.quote(str(leader)), shlex.quote(str(child))))
        old = os.environ.get('PATH', '')
        os.environ['PATH'] = str(self.root / 'fake-bin') + os.pathsep + old
        try:
            started = time.monotonic()
            with self.assertRaises(WorkerFilesError) as error:
                self.service.files(self.fixture.identity)
            elapsed = time.monotonic() - started
        finally:
            os.environ['PATH'] = old
        self.assertEqual(error.exception.code, 'files_unavailable')
        self.assertGreater(elapsed, 1.5)
        self.assertLess(elapsed, 3.0)
        self.assert_reaped(self.read_pid(leader))
        self.assert_reaped(self.read_pid(child))
        restored = time.monotonic()
        body = self.service.files(self.fixture.identity)
        self.assertLess(time.monotonic() - restored, 3.0)
        self.assertIn('src/hello.txt', [item['relative_path'] for item in body['files']])
        self.assertNotIn('shell', self.calls[-1][0])

    def test_parent_exits_while_child_holds_pipe_reaps_group_and_next_request_works(self):
        leader = self.root / 'exited-leader.pid'
        child = self.root / 'pipe-holder.pid'
        group = self.root / 'pipe-holder.pgid'
        script = (
            '#!/usr/bin/env python3\n'
            'import os, time\n'
            'open(%r, "w").write(str(os.getpid()))\n'
            'pid = os.fork()\n'
            'if pid == 0:\n'
            '    open(%r, "w").write(str(os.getpid()))\n'
            '    open(%r, "w").write(str(os.getpgid(0)))\n'
            '    time.sleep(30)\n'
            '    os._exit(0)\n'
            'os._exit(0)\n' % (str(leader), str(child), str(group)))
        self.install_git(script)
        unrelated = subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(30)'],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True)

        def stop_unrelated():
            if unrelated.poll() is None:
                unrelated.kill()
                try:
                    unrelated.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass

        self.addCleanup(stop_unrelated)
        old = os.environ.get('PATH', '')
        os.environ['PATH'] = str(self.root / 'fake-bin') + os.pathsep + old
        try:
            started = time.monotonic()
            with self.assertRaises(WorkerFilesError) as error:
                self.service.files(self.fixture.identity)
            elapsed = time.monotonic() - started
        finally:
            os.environ['PATH'] = old
        self.assertEqual(error.exception.code, 'files_unavailable')
        self.assertGreater(elapsed, 1.5)
        self.assertLess(elapsed, 3.0)
        leader_pid = self.read_pid(leader)
        child_pid = self.read_pid(child)
        self.assertEqual(self.read_pid(group), leader_pid)
        self.assertNotEqual(child_pid, leader_pid)
        self.assertIsNone(unrelated.poll())
        self.assertNotEqual(os.getpgid(unrelated.pid), leader_pid)
        self.assert_reaped(leader_pid)
        self.assert_reaped(child_pid)
        self.assertIsNone(unrelated.poll())
        restored = time.monotonic()
        body = self.service.files(self.fixture.identity)
        self.assertLess(time.monotonic() - restored, 3.0)
        self.assertIn('src/hello.txt', [item['relative_path'] for item in body['files']])
        self.assertNotIn('shell', self.calls[-1][0])

    def test_partial_git_output_stall_is_unavailable_and_reaped(self):
        leader = self.root / 'partial.pid'
        self.install_git(
            '#!/bin/sh\n'
            'echo $$ > %s\n'
            "printf 'src/hello.txt\\0'\n"
            'sleep 30\n' % shlex.quote(str(leader)))
        old = os.environ.get('PATH', '')
        os.environ['PATH'] = str(self.root / 'fake-bin') + os.pathsep + old
        try:
            started = time.monotonic()
            with self.assertRaises(WorkerFilesError) as error:
                self.service.files(self.fixture.identity)
            elapsed = time.monotonic() - started
        finally:
            os.environ['PATH'] = old
        self.assertEqual(error.exception.code, 'files_unavailable')
        self.assertGreater(elapsed, 1.5)
        self.assertLess(elapsed, 3.0)
        self.assert_reaped(self.read_pid(leader))
        body = self.service.files(self.fixture.identity)
        self.assertEqual(
            [item['relative_path'] for item in body['files']],
            ['odd<name>.txt', 'src/binary.bin', 'src/hello.txt'])

    def test_chunked_git_output_is_assembled_before_the_deadline(self):
        self.install_git(
            '#!/bin/sh\n'
            "printf 'src/hello.txt\\0'\n"
            'sleep 0.3\n'
            "printf 'odd<name>.txt\\0src/binary.bin\\0'\n")
        old = os.environ.get('PATH', '')
        os.environ['PATH'] = str(self.root / 'fake-bin') + os.pathsep + old
        try:
            started = time.monotonic()
            body = self.service.files(self.fixture.identity)
            elapsed = time.monotonic() - started
        finally:
            os.environ['PATH'] = old
        self.assertLess(elapsed, 2.0)
        self.assertGreater(elapsed, 0.2)
        self.assertFalse(body['truncated'])
        self.assertEqual(
            [item['relative_path'] for item in body['files']],
            ['odd<name>.txt', 'src/binary.bin', 'src/hello.txt'])

    def test_git_stdout_overflow_stops_at_the_cap_and_reaps(self):
        leader = self.root / 'overflow.pid'
        script = (
            '#!/usr/bin/env python3\n'
            'import os, sys, time\n'
            'open(%r, "w").write(str(os.getpid()))\n'
            'sys.stdout.buffer.write(b"a" * %d + b"\\0zz-marker.txt\\0")\n'
            'sys.stdout.buffer.flush()\n'
            'time.sleep(30)\n' % (str(leader), LIST_CAP))
        self.install_git(script)
        old = os.environ.get('PATH', '')
        os.environ['PATH'] = str(self.root / 'fake-bin') + os.pathsep + old
        try:
            started = time.monotonic()
            body = self.service.files(self.fixture.identity)
            elapsed = time.monotonic() - started
        finally:
            os.environ['PATH'] = old
        self.assertLess(elapsed, 1.5)
        self.assertTrue(body['truncated'])
        self.assertEqual(body['files'], [])
        self.assert_reaped(self.read_pid(leader))
        restored = self.service.files(self.fixture.identity)
        self.assertIn('src/hello.txt', [item['relative_path'] for item in restored['files']])

    def replace_worktree(self, work):
        os.rename(work, work.with_name('w1-granted'))
        work.mkdir()
        git(work, 'init', '-q', '-b', 'main')
        git(work, 'config', 'user.email', 'files@invalid')
        git(work, 'config', 'user.name', 'Files')
        (work / 'sentinel-unrelated.txt').write_text('unrelated\n', encoding='utf-8')
        git(work, 'add', '--', 'sentinel-unrelated.txt')
        git(work, 'commit', '-qm', 'replacement')

    def test_replaced_worktree_is_unavailable(self):
        self.replace_worktree(self.fixture.work)
        listed = subprocess.run(['git', '-C', str(self.fixture.work), 'ls-files'],
                                check=True, capture_output=True, text=True)
        self.assertIn('sentinel-unrelated.txt', listed.stdout)
        before = len(self.calls)
        with self.assertRaises(WorkerFilesError) as error:
            self.service.files(self.fixture.identity)
        self.assertEqual(error.exception.code, 'files_unavailable')
        self.assertEqual(len(self.calls), before)

    def test_path_replacement_during_discovery_does_not_return_unrelated_index(self):
        real = self.service._git_paths
        seen = {}

        def swap(root_fd):
            info = os.fstat(root_fd)
            seen['inode'] = (info.st_dev, info.st_ino)
            self.replace_worktree(self.fixture.work)
            return real(root_fd)

        self.service._git_paths = swap
        with self.assertRaises(WorkerFilesError) as error:
            body = self.service.files(self.fixture.identity)
            self.fail('replacement returned %s' % json.dumps(body))
        self.assertEqual(error.exception.code, 'files_unavailable')
        granted = os.stat(self.fixture.work.with_name('w1-granted'))
        self.assertEqual(seen['inode'], (granted.st_dev, granted.st_ino))
        self.assertTrue(self.calls)
        self.assertRegex(self.calls[-1][0][2], r'\A/proc/self/fd/[0-9]+\Z')
        self.assertNotIn(str(self.fixture.work), self.calls[-1][0])

    def test_linked_worktree_common_dir_uses_confirmed_descriptor(self):
        root = self.root / 'linked'
        repo = root / 'repo'
        work = root / 'wt' / 'w1'
        repo.mkdir(parents=True)
        work.parent.mkdir()
        git(repo, 'init', '-q', '-b', 'main')
        git(repo, 'config', 'user.email', 'files@invalid')
        git(repo, 'config', 'user.name', 'Files')
        (repo / 'base.txt').write_text('base\n', encoding='utf-8')
        git(repo, 'add', '--', 'base.txt')
        git(repo, 'commit', '-qm', 'base')
        git(repo, 'worktree', 'add', '-q', '-b', 'agent/w1', str(work))
        (work / 'src').mkdir()
        (work / 'src' / 'hello.txt').write_text('from-worktree\n', encoding='utf-8')
        git(work, 'add', '--', 'src/hello.txt')
        git(work, 'commit', '-qm', 'hello')
        service = WorkerFilesService(root, ['w1'])
        self.addCleanup(service.close)
        identity = hashlib.sha256(b'w1').hexdigest()
        body = service.files(identity)
        paths = [item['relative_path'] for item in body['files']]
        self.assertIn('src/hello.txt', paths)
        self.assertIn('base.txt', paths)
        self.assertNotIn('sentinel-unrelated.txt', paths)
        argv = self.calls[-1][0]
        self.assertRegex(argv[2], r'\A/proc/self/fd/[0-9]+\Z')
        info = os.stat(work)
        self.assertIn((info.st_dev, info.st_ino), self.pins[-1])


class NoEffects:
    def read(self):
        raise AssertionError('observation dispatched engine')


class WorkerFilesAPITests(unittest.TestCase):
    def setUp(self):
        SCRATCH.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix='worker-files-api-', dir=SCRATCH)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = FilesFixture(self.root)
        self.files = WorkerFilesService(self.root, [self.fixture.worker])
        self.server = server.ActivityServer(0, NoEffects(), files=self.files)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.thread.join(3)
        self.server.server_close()

    def request(self, path, method='GET', headers=None, body=None):
        session = {'X-Unio-Session': self.server.session_token}
        if headers is not None:
            session.update(headers)
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.request(method, path, headers=session, body=body)
            reply = connection.getresponse()
            raw = reply.read()
            return reply.status, dict(reply.getheaders()), json.loads(raw) if raw else None
        finally:
            connection.close()

    def test_session_list_and_literal_preview(self):
        code, headers, session = self.request('/api/session')
        self.assertEqual(code, 200)
        self.assertTrue(session['worker_files'])
        self.assertFalse(session['progress_output'])
        self.assertFalse(session['execution'])
        self.assertFalse(session['manual_drafts'])
        self.assertEqual(session['token'], self.server.session_token)
        code, headers, listed = self.request('/api/worker-files/workers')
        self.assertEqual(code, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(listed['workers'], [dict(worker_id=self.fixture.identity, worker='w1', worktree_label='wt/w1')])
        code, _, body = self.request('/api/worker-files/workers/' + self.fixture.identity + '/files')
        self.assertEqual(code, 200)
        self.assertEqual(set(body), {'schema_version', 'worker_id', 'worker', 'files', 'truncated'})
        preview_path = '/api/worker-files/workers/' + self.fixture.identity + '/files/' + self.fixture.file_id('odd<name>.txt')
        code, _, preview = self.request(preview_path)
        self.assertEqual(code, 200)
        self.assertEqual(set(preview), {'schema_version', 'worker_id', 'file_id', 'relative_path', 'observed_at', 'text', 'truncated'})
        self.assertEqual(preview['text'], 'plain <b>literal</b>\n')
        self.assertNotIn('SECRET', json.dumps(body))

    def test_off_unknown_malformed_and_mutation_errors_are_fixed(self):
        disabled = server.ActivityServer(0, NoEffects())
        thread = threading.Thread(target=disabled.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (disabled.shutdown(), thread.join(3), disabled.server_close()))
        conn = http.client.HTTPConnection('127.0.0.1', disabled.server_port, timeout=3)
        conn.request('GET', '/api/worker-files/workers')
        reply = conn.getresponse()
        self.assertEqual(reply.status, 404)
        self.assertEqual(json.loads(reply.read())['error'], 'not_found')
        conn.close()
        bare = server.ActivityServer(0, NoEffects())
        bare_thread = threading.Thread(target=bare.serve_forever, daemon=True)
        bare_thread.start()
        self.addCleanup(lambda: (bare.shutdown(), bare_thread.join(3), bare.server_close()))
        conn = http.client.HTTPConnection('127.0.0.1', bare.server_port, timeout=3)
        conn.request('GET', '/api/session')
        session = json.loads(conn.getresponse().read())
        conn.close()
        self.assertFalse(session['worker_files'])
        self.assertIsNone(session['token'])
        path = '/api/worker-files/workers/' + self.fixture.identity + '/files/' + self.fixture.file_id('src/hello.txt')
        self.assertEqual(self.request('/api/worker-files/workers/' + '0' * 64 + '/files')[0], 404)
        self.assertEqual(self.request('/api/worker-files/workers/' + '0' * 64 + '/files')[2]['error'], 'files_not_found')
        self.assertEqual(self.request('/api/worker-files/workers/' + self.fixture.identity + '/files/' + '0' * 64)[2]['error'], 'files_not_found')
        for bad in ('/api/worker-files', '/api/worker-files/workers/', '/api/worker-files/workers/' + self.fixture.identity,
                    path + '?path=../secret', '/api/worker-files/workers?root=secret', path + '?cursor=1'):
            self.assertEqual(self.request(bad)[0], 400, bad)
        self.assertEqual(self.request(path, headers={'Content-Length': '0'})[0], 400)
        self.assertEqual(self.request(path, headers={'Transfer-Encoding': 'chunked'})[0], 400)
        for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            self.assertEqual(self.request(path, method=method)[0], 405)
        self.assertEqual(self.request('/api/worker-files/workers', headers={'X-Unio-Session': 'wrong'})[0], 403)
        self.assertEqual(self.request(path, headers={'Host': 'evil.example'})[0], 403)
        self.assertEqual(self.request(path, headers={'Origin': 'https://evil.example'})[0], 403)
        with patch.object(self.files, 'preview', side_effect=RuntimeError('PRIVATE /native/auth SECRET')):
            code, _, error = self.request(path)
        self.assertEqual((code, error), (503, {'schema_version': 1, 'error': 'files_unavailable'}))
        self.assertNotIn('PRIVATE', json.dumps(error))

    def test_duplicate_framing_headers_are_refused(self):
        path = '/api/worker-files/workers'
        request = ('GET ' + path + ' HTTP/1.1\r\nHost: 127.0.0.1:' + str(self.server.server_port)
                   + '\r\nX-Unio-Session: ' + self.server.session_token
                   + '\r\nContent-Length: 0\r\nContent-Length: 0\r\nConnection: close\r\n\r\n')
        with socket.create_connection(self.server.server_address, timeout=3) as client:
            client.sendall(request.encode())
            first = client.recv(4096)
        self.assertIn(b' 400 ', first)

    def test_capability_off_post_is_not_found_and_enabled_post_is_read_only(self):
        self.assertEqual(self.request('/api/worker-files/workers', method='POST', body='{"path":"secret"}')[0], 405)
        disabled = server.ActivityServer(0, NoEffects())
        thread = threading.Thread(target=disabled.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(lambda: (disabled.shutdown(), thread.join(3), disabled.server_close()))
        conn = http.client.HTTPConnection('127.0.0.1', disabled.server_port, timeout=3)
        conn.request('POST', '/api/worker-files/workers', body=b'{}')
        reply = conn.getresponse()
        raw = reply.read()
        conn.close()
        self.assertEqual(reply.status, 404)
        self.assertEqual(json.loads(raw)['error'], 'not_found')
        self.assertNotIn(b'secret', raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
