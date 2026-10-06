# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.

import http.client
import json
import importlib.util
from pathlib import Path
import tempfile
import threading
import subprocess
import unittest
from unittest.mock import patch
import uuid
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))
from plan_store import PlanStore
from execution_service import ExecutionError, ExecutionService
import server

# We can import MOCK from execution_service_test directly since it's just a test helper
spec = importlib.util.spec_from_file_location('execution_service_test', Path(__file__).parent / 'execution_service_test.py')
es_test = importlib.util.module_from_spec(spec)
spec.loader.exec_module(es_test)
MOCK = es_test.MOCK

class NeverObserve:
    def read(self):
        return dict(schema_version=1, observed_at='2026-10-04T21:00:00Z', stopped=True,
                    agents=[], results=[], retries=[], recent_events=[], warnings=[],
                    evidence='recorded; use result to recheck revision and readiness')

class ExecutionAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='execution-api-')
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        for name in ('repo', 'coord/tasks', 'wt', 'config'):
            (self.workspace / name).mkdir(parents=True)
        self.repo = self.workspace / 'repo'
        self.git(self.repo, 'init', '-q', '-b', 'main')
        self.git(self.repo, 'config', 'user.email', 'mock@invalid')
        self.git(self.repo, 'config', 'user.name', 'Mock')
        (self.repo / 'source.txt').write_text('base\n')
        self.git(self.repo, 'add', 'source.txt')
        self.git(self.repo, 'commit', '-qm', 'base')
        self.wt = self.workspace / 'wt/mock-worker'
        self.git(self.repo, 'worktree', 'add', '-q', '-b', 'agent/mock-worker', str(self.wt))
        (self.workspace / 'coord/base').write_text('main\n')
        self.engine = self.workspace / 'engine'
        self.engine.write_text(MOCK)
        self.engine.chmod(0o700)
        self.config = self.workspace / 'config'
        (self.config / 'agents.conf').write_text('mock=NEVER_REAL_PROVIDER\nother=NEVER_REAL_PROVIDER\n')
        self.template = self.workspace / 'template.json'
        self.template.write_text(json.dumps(dict(schema_version=1, instructions='Implement the literal saved request.',
            scope=['source.txt'], validate=["test -s 'source.txt'"])))

        self.plans = PlanStore(self.workspace)
        self.addCleanup(self.plans.close)
        
        self.execution = ExecutionService(self.workspace, self.engine, 'mock-worker', 'other', self.config,
                          self.template, 'Mock Company', 'Another Company')
        self.addCleanup(self.execution.close)
        
        self.api = server.ActivityServer(0, NeverObserve(), plans=self.plans, execution=self.execution)
        self.thread = threading.Thread(target=self.api.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.origin = self.api.origin
        self.token = self.api.session_token

    def git(self, directory, *args):
        return subprocess.check_output(['git', '-C', str(directory), *args], stderr=subprocess.PIPE).decode().strip()

    def close(self):
        self.api.shutdown()
        self.thread.join(timeout=2)
        self.api.server_close()

    def request(self, method='GET', path='/api/session', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.api.server_port, timeout=15)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            raw = response.read()
            return response.status, dict(response.getheaders()), json.loads(raw) if raw and response.getheader('Content-Type', '').startswith('application/json') else raw.decode()
        finally:
            conn.close()

    def headers(self):
        return {'Origin': self.origin, 'X-Unio-Session': self.token, 'Content-Type': 'application/json'}

    def assert_execution_error(self, error, status=503, code='native_unavailable'):
        """Exercise every HTTP boundary with a backend that cannot launch work."""
        job_id, draft_id, key, digest = 'a' * 32, 'b' * 32, 'c' * 32, 'd' * 64
        routes = [
            ('jobs', 'GET', '/api/jobs', None),
            ('get', 'GET', f'/api/jobs/{job_id}', None),
            ('prepare', 'POST', '/api/jobs', dict(draft_id=draft_id, expected_hash=digest, request_key=key)),
            ('approve', 'POST', f'/api/jobs/{job_id}/approve', dict(expected_hash=digest, approval_key=key, preview_hash=digest)),
            ('start', 'POST', f'/api/jobs/{job_id}/start', dict(approval_key=key, reservation_key=key)),
            ('verify', 'POST', f'/api/jobs/{job_id}/verify', dict(action_key=key)),
            ('review', 'POST', f'/api/jobs/{job_id}/review', dict(action_key=key)),
            ('stop', 'POST', f'/api/jobs/{job_id}/stop', dict(action_key=key)),
            ('accept', 'POST', f'/api/jobs/{job_id}/accept', dict(revision_hash='e' * 40, action_key=key)),
            ('cancel', 'POST', f'/api/jobs/{job_id}/cancel', {}),
        ]
        for method, verb, path, body in routes:
            with self.subTest(method=method):
                with patch.object(self.execution, method, side_effect=error) as invoke:
                    response_status, headers, response = self.request(
                        verb, path, json.dumps(body) if body is not None else None, self.headers())
                self.assertEqual(response_status, status)
                self.assertEqual(response, dict(schema_version=1, error=code))
                self.assertEqual(headers.get('Cache-Control'), 'no-store')
                self.assertTrue(headers.get('Content-Type', '').startswith('application/json'))
                arguments = dict(body or {})
                if method not in ('jobs', 'prepare'):
                    arguments['job_id'] = job_id
                invoke.assert_called_once_with(**arguments)
        self.assertFalse((self.workspace / 'calls.jsonl').exists())

    def test_foreign_same_name_errors_are_internal(self):
        for base in (Exception, ValueError):
            with self.subTest(base=base.__name__):
                foreign_type = type('ExecutionError', (base,), {})
                error = foreign_type('PRIVATE exception text /private/path')
                error.code, error.status = 'ROOT_PRIVATE_ERROR_MARKER', 499
                self.assert_execution_error(error)

    def test_foreign_error_fields_are_never_accessed(self):
        accessed = []

        def unreadable(error, field):
            if field in ('code', 'status', '__class__'):
                accessed.append(field)
                raise RuntimeError('PRIVATE property failure')
            return Exception.__getattribute__(error, field)

        foreign_type = type('ExecutionError', (Exception,), {'__getattribute__': unreadable})
        self.assert_execution_error(foreign_type('PRIVATE exception text'))
        self.assertEqual(accessed, [])

    def test_foreign_class_attribute_cannot_impersonate_public_error(self):
        foreign_type = type('ExecutionError', (Exception,), {
            '__class__': property(lambda error: ExecutionError),
            'code': 'conflict', 'status': 409,
        })
        self.assert_execution_error(foreign_type('PRIVATE exception text'))

    def test_valid_public_error_pairs_are_preserved(self):
        pairs = dict(invalid_request=400, job_not_found=404, conflict=409, draft_stale=409,
                     binding_stale=409, worker_unavailable=409, stopped=409, not_ready=409,
                     outcome_unknown=409, storage_unavailable=503, native_unavailable=503)
        for code, status in pairs.items():
            with self.subTest(code=code):
                self.assert_execution_error(ExecutionError(code), status, code)

    def test_generic_backend_exceptions_are_internal(self):
        for exception_type in (Exception, ValueError, TypeError, OSError, RuntimeError):
            with self.subTest(exception=exception_type.__name__):
                error = exception_type('PRIVATE exception text /private/path')
                error.code, error.status = 'conflict', 409
                self.assert_execution_error(error)

    def test_malformed_public_error_fields_are_internal(self):
        class StringField(str):
            pass

        class IntegerField(int):
            pass

        malformed = [
            ('code', 'ROOT_PRIVATE_ERROR_MARKER'), ('code', None), ('code', 409),
            ('code', ['conflict']), ('code', {'private': 'path'}), ('code', b'conflict'),
            ('code', StringField('conflict')),
            ('status', 499), ('status', 400), ('status', None), ('status', '409'),
            ('status', 409.0), ('status', True), ('status', [409]),
            ('status', {'private': 'path'}), ('status', IntegerField(409)),
        ]
        for field, value in malformed:
            with self.subTest(field=field, value=value):
                error = ExecutionError('conflict')
                setattr(error, field, value)
                self.assert_execution_error(error)
        for field in ('code', 'status'):
            with self.subTest(missing=field):
                error = ExecutionError('conflict')
                delattr(error, field)
                self.assert_execution_error(error)

    def test_public_error_property_failures_are_internal(self):
        for field in ('code', 'status'):
            for exception_type in (AttributeError, ValueError, RuntimeError):
                with self.subTest(field=field, exception=exception_type.__name__):
                    def unreadable(error, name):
                        if name == field:
                            raise exception_type('PRIVATE property failure /private/path')
                        return Exception.__getattribute__(error, name)

                    public_type = type('UnreadableExecutionError', (ExecutionError,), {
                        '__getattribute__': unreadable,
                    })
                    self.assert_execution_error(public_type('conflict'))

    def test_happy_request_mapping(self):
        code, _, draft = self.request('POST', '/api/plans', json.dumps({'request': 'foo'}), self.headers())
        draft_id = draft['id']
        expected_hash = draft['content_sha256']
        request_key = uuid.uuid4().hex

        # POST /api/jobs
        code, _, job = self.request('POST', '/api/jobs', json.dumps({
            'draft_id': draft_id, 'expected_hash': expected_hash, 'request_key': request_key
        }), self.headers())
        self.assertEqual(code, 201)
        job_id = job['job']['id']
        
        # GET /api/jobs
        code, _, jobs = self.request('GET', '/api/jobs', headers=self.headers())
        self.assertEqual(code, 200)
        self.assertEqual(len(jobs['jobs']), 1)
        
        # GET /api/jobs/ID
        code, _, job_get = self.request('GET', f'/api/jobs/{job_id}', headers=self.headers())
        self.assertEqual(code, 200)
        
        # POST /api/jobs/ID/approve
        approval_key = uuid.uuid4().hex
        preview_hash = job['preview']['preview_hash']
        code, _, job = self.request('POST', f'/api/jobs/{job_id}/approve', json.dumps({
            'expected_hash': expected_hash, 'approval_key': approval_key, 'preview_hash': preview_hash
        }), self.headers())
        self.assertEqual(code, 200)
        
        # POST /api/jobs/ID/start
        reservation_key = uuid.uuid4().hex
        code, _, job = self.request('POST', f'/api/jobs/{job_id}/start', json.dumps({
            'approval_key': approval_key, 'reservation_key': reservation_key
        }), self.headers())
        self.assertEqual(code, 200)

        # POST /api/jobs/ID/verify
        action_key = uuid.uuid4().hex
        code, _, job = self.request('POST', f'/api/jobs/{job_id}/verify', json.dumps({'action_key': action_key}), self.headers())
        self.assertEqual(code, 200)

        # POST /api/jobs/ID/review
        action_key2 = uuid.uuid4().hex
        code, _, job = self.request('POST', f'/api/jobs/{job_id}/review', json.dumps({'action_key': action_key2}), self.headers())
        self.assertEqual(code, 200)

        # POST /api/jobs/ID/accept
        revision_hash = job['native_result']['current_revision']['candidate_commit']
        action_key3 = uuid.uuid4().hex
        code, _, job = self.request('POST', f'/api/jobs/{job_id}/accept', json.dumps({
            'revision_hash': revision_hash, 'action_key': action_key3
        }), self.headers())
        self.assertEqual(code, 200)

    def test_cancel_endpoint(self):
        code, _, draft = self.request('POST', '/api/plans', json.dumps({'request': 'foo2'}), self.headers())
        request_key = uuid.uuid4().hex
        code, _, job = self.request('POST', '/api/jobs', json.dumps({
            'draft_id': draft['id'], 'expected_hash': draft['content_sha256'], 'request_key': request_key
        }), self.headers())
        job_id = job['job']['id']
        code, _, job = self.request('POST', f'/api/jobs/{job_id}/cancel', '{}', self.headers())
        self.assertEqual(code, 200)

    def test_stop_endpoint(self):
        code, _, draft = self.request('POST', '/api/plans', json.dumps({'request': 'foo3'}), self.headers())
        request_key = uuid.uuid4().hex
        code, _, job = self.request('POST', '/api/jobs', json.dumps({
            'draft_id': draft['id'], 'expected_hash': draft['content_sha256'], 'request_key': request_key
        }), self.headers())
        job_id = job['job']['id']
        
        approval_key = uuid.uuid4().hex
        self.request('POST', f'/api/jobs/{job_id}/approve', json.dumps({
            'expected_hash': draft['content_sha256'], 'approval_key': approval_key, 'preview_hash': job['preview']['preview_hash']
        }), self.headers())
        
        reservation_key = uuid.uuid4().hex
        self.request('POST', f'/api/jobs/{job_id}/start', json.dumps({
            'approval_key': approval_key, 'reservation_key': reservation_key
        }), self.headers())
        
        action_key = uuid.uuid4().hex
        code, _, job = self.request('POST', f'/api/jobs/{job_id}/stop', json.dumps({'action_key': action_key}), self.headers())
        self.assertEqual(code, 200)

    def test_wrong_missing_token_origin_host(self):
        valid = self.headers()
        variants = [dict(valid, Origin='https://evil.example'), dict(valid, Origin='null'),
                    {k: v for k, v in valid.items() if k != 'Origin'},
                    {k: v for k, v in valid.items() if k != 'X-Unio-Session'},
                    dict(valid, **{'X-Unio-Session': 'wrong'}), dict(valid, Host='evil.example')]
        for headers in variants:
            with self.subTest(headers=headers):
                self.assertEqual(self.request('POST', '/api/jobs', '{"draft_id":"a","expected_hash":"b","request_key":"c"}', headers)[0], 403)
        self.assertEqual(self.request(headers={'Origin': 'https://evil.example'})[0], 403)

    def test_body_ambiguity_timeout(self):
        # Already covered largely by plan_api_test.py, but we test the job endpoint for invalid selectors
        code, _, body = self.request('POST', '/api/jobs', '{"draft_id":"a","expected_hash":"b","request_key":"c","extra":"d"}', self.headers())
        self.assertEqual(code, 400)
        
    def test_default_manual_no_effects(self):
        # Restart server without execution
        self.api.shutdown()
        self.thread.join()
        self.api.server_close()
        
        self.api = server.ActivityServer(0, NeverObserve(), plans=self.plans)
        self.thread = threading.Thread(target=self.api.serve_forever, daemon=True)
        self.thread.start()
        self.origin = self.api.origin
        self.token = self.api.session_token
        
        code, _, _ = self.request('GET', '/api/jobs', headers=self.headers())
        self.assertEqual(code, 404)
        
        code, _, _ = self.request('POST', '/api/jobs', '{}', self.headers())
        self.assertEqual(code, 404)

    def test_startup_partial_settings(self):
        import argparse
        from unittest.mock import patch
        with patch('sys.argv', ['server.py', '--project', str(self.workspace), '--enable-execution']):
            with self.assertRaises(SystemExit):
                server.main()
                
    def test_server_shutdown_closes_service(self):
        self.assertFalse(self.execution._closed)
        self.api.server_close()
        self.assertTrue(self.execution._closed)

    def test_service_error_mapping(self):
        code, _, job = self.request('POST', '/api/jobs', json.dumps({
            'draft_id': 'invalid_id', 'expected_hash': 'b', 'request_key': 'c'
        }), self.headers())
        self.assertEqual(code, 400)

    def test_query_strings_refused(self):
        code, _, draft = self.request('POST', '/api/plans', json.dumps({'request': 'foo4'}), self.headers())
        request_key = uuid.uuid4().hex
        
        # GET /api/jobs
        self.assertEqual(self.request('GET', '/api/jobs?q=1', headers=self.headers())[0], 400)
        
        # POST /api/jobs
        self.assertEqual(self.request('POST', '/api/jobs?q=1', json.dumps({'draft_id': draft['id'], 'expected_hash': draft['content_sha256'], 'request_key': request_key}), self.headers())[0], 404)
        
        # Create a job to test ID routes
        code, _, job = self.request('POST', '/api/jobs', json.dumps({'draft_id': draft['id'], 'expected_hash': draft['content_sha256'], 'request_key': request_key}), self.headers())
        job_id = job['job']['id']
        
        # GET /api/jobs/ID
        self.assertEqual(self.request('GET', f'/api/jobs/{job_id}?q=1', headers=self.headers())[0], 400)
        
        # POST /api/jobs/ID/cancel
        self.assertEqual(self.request('POST', f'/api/jobs/{job_id}/cancel?q=1', '{}', self.headers())[0], 404)

    def test_unknown_missing_fields_post(self):
        code, _, draft = self.request('POST', '/api/plans', json.dumps({'request': 'foo5'}), self.headers())
        request_key = uuid.uuid4().hex
        valid_body = {'draft_id': draft['id'], 'expected_hash': draft['content_sha256'], 'request_key': request_key}
        
        # missing field
        missing = {k: v for k, v in valid_body.items() if k != 'draft_id'}
        self.assertEqual(self.request('POST', '/api/jobs', json.dumps(missing), self.headers())[0], 400)
        
        # unknown field
        unknown = dict(valid_body, unknown='field')
        self.assertEqual(self.request('POST', '/api/jobs', json.dumps(unknown), self.headers())[0], 400)

    def test_get_routes_origin_cache_control(self):
        # omitted Origin accepted, Cache-Control no-store
        headers = self.headers()
        del headers['Origin']
        code, h, _ = self.request('GET', '/api/jobs', headers=headers)
        self.assertEqual(code, 200)
        self.assertEqual(h.get('Cache-Control'), 'no-store')
        
        # mismatched Origin rejected
        headers['Origin'] = 'http://evil.example'
        code, _, _ = self.request('GET', '/api/jobs', headers=headers)
        self.assertEqual(code, 403)

    def test_list_route_error_mapping(self):
        from unittest.mock import patch
        with patch.object(self.execution, 'jobs', side_effect=ValueError("Test Value Error")):
            code, _, body = self.request('GET', '/api/jobs', headers=self.headers())
            self.assertEqual(code, 503)
            self.assertEqual(body['error'], 'native_unavailable')
            
        from execution_service import ExecutionError
        with patch.object(self.execution, 'jobs', side_effect=ExecutionError('storage_unavailable')):
            code, _, body = self.request('GET', '/api/jobs', headers=self.headers())
            self.assertEqual(code, 503)
            self.assertEqual(body['error'], 'storage_unavailable')

    def test_startup_mode_labels(self):
        from unittest.mock import patch
        import io
        import sys
        
        class MockServer:
            origin = 'http://127.0.0.1:8000'
            def serve_forever(self): pass
            def server_close(self): pass
        
        # execution mode
        srv = MockServer()
        srv.execution = True
        out = io.StringIO()
        with patch('sys.stdout', out):
            server.serve_preview(srv)
        self.assertIn('explicit execution preview; an approved job can start one configured worker run and one configured review', out.getvalue())
        self.assertNotIn('no provider dispatch', out.getvalue())
        
        # manual mode
        srv = MockServer()
        srv.plans = True
        out = io.StringIO()
        with patch('sys.stdout', out):
            server.serve_preview(srv)
        self.assertIn('manual draft preview; no provider dispatch', out.getvalue())
        
        # default read-only mode
        srv = MockServer()
        out = io.StringIO()
        with patch('sys.stdout', out):
            server.serve_preview(srv)
        self.assertIn('read-only Activity preview; no provider dispatch', out.getvalue())

if __name__ == '__main__':
    unittest.main(verbosity=2)
