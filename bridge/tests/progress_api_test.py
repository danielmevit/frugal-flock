# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
import http.client
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).parents[1]))
from progress import ProgressService
from progress_test import Fixture
import server


class NoEffects:
    def read(self): raise AssertionError('observation dispatched engine')
    def __getattr__(self, name): raise AssertionError('execution effect: ' + name)


class ProgressAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='progress-api-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = Fixture(self.root)
        self.fixture.log.write_text('done <a href="https://example.org">link</a>\n')
        self.progress = ProgressService(self.root, self.root / 'unio', [(self.fixture.worker, self.fixture.task)])
        self.server = server.ActivityServer(0, NoEffects(), progress=self.progress)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.identity = next(iter(self.progress.bindings))
        self.path = '/api/progress/workers/' + self.identity
        self.effects = patch.object(subprocess, 'Popen', side_effect=AssertionError('provider/dispatch'))
        self.invoke = self.effects.start()
        self.addCleanup(self.effects.stop)
        self.addCleanup(lambda: self.assertEqual(self.invoke.call_count, 0))

    def close(self):
        self.server.shutdown()
        self.thread.join(3)
        self.server.server_close()

    def request(self, path, method='GET', headers=None, body=None):
        session = {'X-Unio-Session': self.server.session_token}
        if headers is not None: session.update(headers)
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.request(method, path, headers=session, body=body)
            reply = connection.getresponse()
            raw = reply.read()
            return reply.status, dict(reply.getheaders()), json.loads(raw) if raw else None
        finally: connection.close()

    def test_discovery_worker_run_output_literal_no_effects(self):
        code, headers, session = self.request('/api/session')
        self.assertEqual(code, 200)
        self.assertTrue(session['progress_output'])
        self.assertFalse(session['execution'])
        self.assertFalse(session['manual_drafts'])
        self.assertEqual(session['token'], self.server.session_token)
        code, headers, collection = self.request('/api/progress/workers')
        self.assertEqual(code, 200)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(len(collection['workers']), 1)
        code, _, worker = self.request(self.path)
        self.assertEqual(code, 200)
        self.assertEqual(self.request(self.path + '/runs')[2]['runs'][0]['run_id'], worker['run_id'])
        runpath = self.path + '/runs/' + worker['run_id']
        for path in (runpath, runpath + '/output'):
            code, headers, value = self.request(path)
            self.assertEqual(code, 200)
            self.assertEqual(value['run_id'], worker['run_id'])
            self.assertNotIn('engine', value)
            self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertIn('<a href="https://example.org">link</a>', value['output']['text'])
        cursor = value['output']['next_cursor']
        self.assertEqual(self.request(runpath + '/output?cursor=' + cursor)[2]['output']['text'], '')
        with self.fixture.log.open('a') as out: out.write('append\n')
        self.assertEqual(self.request(runpath + '/output?cursor=' + cursor)[2]['output']['text'], 'append\n')
        self.assertEqual(self.request(runpath + '/output?cursor=' + cursor)[2]['output']['text'], 'append\n')

    def test_http_lifecycle_first_output_buffered_verification_and_completion(self):
        import fcntl
        self.fixture.log.write_bytes(b'')
        value = self.request(self.path)[2]
        self.assertEqual(value['output']['state'], 'first_output_wait')
        self.assertEqual(value['source']['state'], 'running')
        self.fixture.log.write_text('worker prose says done\n')
        self.assertEqual(self.request(self.path)[2]['source']['state'], 'running')
        self.fixture.finish()
        # Native verify holds the same lock and buffers its child's output.
        lock = (self.root / 'coord/.locks' / (self.fixture.worker + '.lock')).open('a')
        self.addCleanup(lock.close)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        value = self.request(self.path)[2]
        self.assertEqual(value['source']['state'], 'succeeded')
        self.assertEqual(value['verification']['state'], 'not_run')
        self.assertEqual(value['observed_phase'], 'unknown')
        self.assertEqual(value['observed_liveness'], 'unknown')
        self.assertIn('worker prose says done', value['output']['excerpt'])
        self.fixture.native['validation'].update(state='passed', scope='OK', checks_run=2,
            checks_failed=0, reasons=[], revision=self.fixture.revision)
        self.fixture.save()
        value = self.request(self.path)[2]
        self.assertEqual(value['verification']['state'], 'passed')
        self.assertEqual(value['review']['state'], 'not_run')
        self.assertEqual(value['acceptance']['state'], 'unavailable')
        self.fixture.finish(3)
        value = self.request(self.path)[2]
        self.assertEqual(value['source']['state'], 'failed')
        self.assertEqual(value['source']['exit_code'], 3)

    def test_host_origin_session_refusal(self):
        for headers in ({'Host': 'evil.example'}, {'Host': 'localhost:' + str(self.server.server_port)},
                        {'Origin': 'null'}, {'Origin': 'https://evil.example'},
                        {'X-Unio-Session': ''}, {'X-Unio-Session': 'wrong'}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request(self.path, headers=headers)[0], 403)
        self.assertEqual(self.request(self.path, headers={'Origin': self.server.origin})[0], 200)
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        connection.request('GET', self.path)
        self.assertEqual(connection.getresponse().status, 403)
        connection.close()

    def test_strict_malformed_query_paths_and_body_framing(self):
        worker = self.request(self.path)[2]
        output = self.path + '/runs/' + worker['run_id'] + '/output'
        bad = ['/api/progress', '/api/progress/workers?', '/api/progress/workers?root=secret',
               self.path + '?cursor=x', self.path + '/runs/invalid',
               self.path + '/runs/' + worker['run_id'] + '?cursor=x', output + '?limit=2',
               output + '?cursor=a&cursor=b', output + '?cursor=%61', output + '?cursor=',
               output + '?cursor=x&path=secret', '/api/progress/workers/../private',
               '/api/progress/workers/%2e%2e', '/api/progress/workers/' + self.identity.upper()]
        for path in bad:
            with self.subTest(path=path): self.assertEqual(self.request(path)[0], 400)
        for headers in ({'Content-Length': '0'}, {'Content-Length': '-1'}, {'Transfer-Encoding': 'chunked'}):
            with self.subTest(headers=headers): self.assertEqual(self.request(output, headers=headers)[0], 400)
        for method in ('POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'):
            with self.subTest(method=method): self.assertEqual(self.request(output, method=method)[0], 405)
        self.assertEqual(self.request('/api/jobs', method='POST', body='{}')[0], 405)

    def test_duplicate_security_and_framing_headers(self):
        for extra in ('Host: evil.example', 'Origin: null', 'X-Unio-Session: wrong',
                      'Content-Length: 0\r\nContent-Length: 0'):
            with self.subTest(extra=extra):
                request = ('GET ' + self.path + ' HTTP/1.1\r\nHost: 127.0.0.1:' + str(self.server.server_port)
                    + '\r\nX-Unio-Session: ' + self.server.session_token + '\r\n' + extra + '\r\nConnection: close\r\n\r\n')
                with socket.create_connection(self.server.server_address, timeout=3) as client:
                    client.sendall(request.encode())
                    first = client.recv(4096)
                self.assertTrue(b' 403 ' in first or b' 400 ' in first)

    def test_cursor_mismatch_unknown_ids_private_failures(self):
        value = self.request(self.path)[2]
        runpath = self.path + '/runs/' + value['run_id'] + '/output'
        self.assertEqual(self.request('/api/progress/workers/' + '0' * 64)[0], 404)
        self.assertEqual(self.request(self.path + '/runs/' + '0' * 64)[0], 404)
        self.assertEqual(self.request(runpath + '?cursor=x')[0], 409)
        value = self.request(runpath)[2]
        self.fixture.log.write_text('short\n')
        self.assertEqual(self.request(runpath + '?cursor=' + value['output']['next_cursor'])[0], 409)
        with patch.object(self.progress, 'get', side_effect=RuntimeError('PRIVATE /native/auth SECRET')):
            code, _, error = self.request(self.path)
        self.assertEqual(code, 503)
        self.assertEqual(error, {'schema_version': 1, 'error': 'progress_unavailable'})

    def test_malformed_or_spoofed_public_errors_remain_fixed(self):
        from progress import ProgressError
        class Foreign:
            @property
            def code(self): raise AssertionError('foreign fields accessed')
            @property
            def status(self): raise AssertionError('foreign fields accessed')
        class ForeignError(Exception):
            __class__ = ProgressError
            code = 'invalid_request'
            status = 400
        for error in (ForeignError('PRIVATE'), ProgressError('invalid_request')):
            if type(error) is ProgressError:
                error.status = 200
            with patch.object(self.progress, 'get', side_effect=error):
                code, _, value = self.request(self.path)
            self.assertEqual(code, 503)
            self.assertEqual(value['error'], 'progress_unavailable')
        handler = server.ActivityHandler.__new__(server.ActivityHandler)
        with patch.object(handler, 'error_response') as respond:
            handler.progress_error_response(Foreign())
        respond.assert_called_once_with(503, 'progress_unavailable')

    def test_session_rotation_requires_new_session_without_dispatch(self):
        value = self.request(self.path + '/runs/' + self.request(self.path)[2]['run_id'] + '/output')[2]
        old = self.server.session_token
        self.server.session_token = 'new-local-session'
        self.assertEqual(self.request(self.path, headers={'X-Unio-Session': old})[0], 403)
        self.assertEqual(self.request('/api/session')[2]['token'], 'new-local-session')
        path = self.path + '/runs/' + value['run_id'] + '/output?cursor=' + value['output']['next_cursor']
        self.assertEqual(self.request(path)[0], 200)

    def test_default_manual_execution_do_not_imply_output_authority(self):
        for mode in ('default', 'manual', 'execution'):
            plans = object() if mode == 'manual' else None
            execution = type('Execution', (), {'close': lambda _: None})() if mode == 'execution' else None
            instance = server.ActivityServer(0, NoEffects(), plans=plans, execution=execution)
            thread = threading.Thread(target=instance.serve_forever, daemon=True); thread.start()
            try:
                conn = http.client.HTTPConnection('127.0.0.1', instance.server_port, timeout=3)
                conn.request('GET', '/api/session'); response = conn.getresponse()
                session = json.loads(response.read())
                self.assertFalse(session['progress_output'])
                if mode == 'default': self.assertIsNone(session['token'])
                conn.request('GET', self.path, headers={'X-Unio-Session': session['token'] or 'none'})
                response = conn.getresponse(); response.read()
                self.assertEqual(response.status, 404)
                conn.close()
            finally:
                instance.shutdown(); thread.join(3); instance.server_close()

    def test_startup_partial_optin_refuses_before_any_service(self):
        # main is run in-process with every dispatch boundary patched.
        for flags in (['--enable-progress-output'], ['--progress-binding', 'codex-owned:SOURCE-1'],
                      ['--enable-progress-output', '--progress-binding', 'bad/worker:SOURCE-1'],
                      ['--enable-progress-output', '--progress-binding', 'x:t', '--progress-binding', 'y:t']):
            args = ['server.py', '--project', str(self.root), '--engine', str(self.fixture.log)] + flags
            with patch.object(sys, 'argv', args), patch.object(server, 'serve_preview') as serve, patch('sys.stderr'):
                with self.assertRaises(SystemExit) as error: server.main()
            self.assertEqual(error.exception.code, 2)
            serve.assert_not_called()


if __name__ == '__main__': unittest.main(verbosity=2)
