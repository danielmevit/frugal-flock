# Unio — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit).
# https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
import http.client
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


server = load('activity_server', 'server.py')
store = load('plan_store', 'plan_store.py')


class NeverObserve:
    def read(self):
        raise AssertionError('draft endpoint must never invoke watch or a provider')


class PlanAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='plan-api-')
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        (self.workspace / 'coord').mkdir()
        self.plans = store.PlanStore(self.workspace)
        self.addCleanup(self.plans.close)
        self.api = server.ActivityServer(0, NeverObserve(), plans=self.plans)
        self.thread = threading.Thread(target=self.api.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        self.origin = self.api.origin
        self.token = self.api.session_token
        self.directory = self.workspace / 'coord/ui-plans'

    def close(self):
        self.api.shutdown()
        self.thread.join(timeout=2)
        self.api.server_close()

    def request(self, method='GET', path='/api/session', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.api.server_port, timeout=3)
        try:
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            raw = response.read()
            return response.status, dict(response.getheaders()), json.loads(raw) if raw else None
        finally:
            conn.close()

    def headers(self):
        return {'Origin': self.origin, 'X-Unio-Session': self.token, 'Content-Type': 'application/json'}

    def create(self, value='Small request'):
        return self.request('POST', '/api/plans', json.dumps({'request': value}), self.headers())

    def test_opt_in_save_read_restart_never_observes_or_dispatches(self):
        code, headers, session = self.request()
        self.assertEqual(code, 200)
        self.assertTrue(session['manual_drafts'])
        self.assertEqual(session['token'], self.token)
        self.assertNotIn('Access-Control-Allow-Origin', headers)
        request = '<img src=x>\n$ never execute this\n- ../../outside'
        code, _, draft = self.create(request)
        self.assertEqual(code, 201)
        self.assertEqual(draft['state'], 'draft')
        self.assertEqual(draft['request'], request)
        code, _, restored = self.request(path='/api/plans/' + draft['id'], headers={'X-Unio-Session': self.token})
        self.assertEqual(code, 200)
        self.assertEqual(restored, draft)
        with store.PlanStore(self.workspace) as reopened:
            self.assertEqual(reopened.get(draft['id']), draft)
        self.assertEqual({p.name for p in (self.workspace / 'coord').iterdir()}, {'ui-plans'})

    def test_default_mode_is_read_only_without_store_creation(self):
        self.api.plans = None
        self.api.session_token = None
        self.assertFalse(self.request()[2]['manual_drafts'])
        self.assertIsNone(self.request()[2]['token'])
        self.assertEqual(self.create()[0], 405)
        self.assertEqual(self.request(path='/api/plans/' + 'a' * 32)[0], 404)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_cross_origin_missing_wrong_token_host_and_session_are_refused(self):
        valid = self.headers()
        variants = [dict(valid, Origin='https://evil.example'), dict(valid, Origin='null'),
                    {k: v for k, v in valid.items() if k != 'Origin'},
                    {k: v for k, v in valid.items() if k != 'X-Unio-Session'},
                    dict(valid, **{'X-Unio-Session': 'wrong'}), dict(valid, Host='evil.example')]
        for headers in variants:
            with self.subTest(headers=headers):
                self.assertEqual(self.request('POST', '/api/plans', '{"request":"x"}', headers)[0], 403)
        self.assertEqual(self.request(headers={'Origin': 'https://evil.example'})[0], 403)
        self.assertEqual(self.request(path='/api/plans/' + 'a' * 32)[0], 403)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_json_bounds_fields_and_types_are_checked_before_save(self):
        for body, code in [('{"request":"x","request":"y"}', 400), ('broken', 400), ('[]', 400), ('{}', 400), ('{"request":null}', 400),
                           ('{"request":"   "}', 400), ('{"request":"x","engine":"evil"}', 400),
                           (json.dumps({'request': 'x' * 4001}), 400), ('x' * 32769, 413)]:
            with self.subTest(body=body[:50]):
                self.assertEqual(self.request('POST', '/api/plans', body, self.headers())[0], code)
        headers = self.headers(); headers['Content-Type'] = 'text/plain'
        self.assertEqual(self.request('POST', '/api/plans', '{"request":"x"}', headers)[0], 415)
        headers = self.headers(); headers['Transfer-Encoding'] = 'chunked'
        self.assertEqual(self.request('POST', '/api/plans', '', headers)[0], 400)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_ambiguous_missing_and_partial_body_framing_is_refused(self):
        cases = [([], 411), (['Content-Length: 1', 'Content-Length: 1'], 400),
                 (['Content-Length: -1'], 400), (['Content-Length: 32769'], 413),
                 (['Content-Length: 2'], 400)]
        for extra, expected in cases:
            with self.subTest(extra=extra):
                conn = http.client.HTTPConnection('127.0.0.1', self.api.server_port, timeout=3)
                try:
                    conn.connect()
                    lines = ['POST /api/plans HTTP/1.0', 'Host: ' + self.origin.removeprefix('http://'),
                             'Origin: ' + self.origin, 'X-Unio-Session: ' + self.token,
                             'Content-Type: application/json', *extra, '', 'x']
                    conn.send('\r\n'.join(lines).encode())
                    conn.sock.shutdown(1)  # premature EOF must fail, never save partial input
                    response = conn.response_class(conn.sock, method='POST')
                    response.begin()
                    self.assertEqual(response.status, expected)
                    response.read()
                    response.close()
                finally:
                    conn.close()
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_methods_paths_and_ids_cannot_write_or_select_files(self):
        for method in ('PUT', 'PATCH', 'DELETE', 'OPTIONS'):
            self.assertEqual(self.request(method, '/api/plans', '{}', self.headers())[0], 405)
        for path in ('/api/run', '/api/plans?project=outside', '/api/plans/approve'):
            self.assertEqual(self.request('POST', path, '{"request":"x"}', self.headers())[0], 404)
        for identity in ('../../outside', 'A' * 32, 'a' * 32 + '?x=1'):
            self.assertEqual(self.request(path='/api/plans/' + identity, headers=self.headers())[0], 400)
        self.assertEqual(self.request(path='/api/plans/' + 'a' * 32, headers=self.headers())[0], 404)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_storage_errors_and_corruption_never_expose_paths_or_approval(self):
        with patch.object(self.plans, 'create', side_effect=OSError('PRIVATE SECRET PATH')):
            code, _, data = self.create()
        self.assertEqual(code, 503)
        self.assertEqual(data, {'schema_version': 1, 'error': 'draft_unavailable'})
        draft = self.create()[2]
        (self.directory / (draft['id'] + '.json')).write_text('{"state":"approved"}')
        code, _, data = self.request(path='/api/plans/' + draft['id'], headers=self.headers())
        self.assertEqual(code, 503)
        self.assertEqual(data, {'schema_version': 1, 'error': 'draft_unavailable'})

    def test_restart_rotates_session_and_old_token_cannot_write(self):
        replacement = server.ActivityServer(0, NeverObserve(), plans=self.plans)
        self.assertNotEqual(replacement.session_token, self.token)
        self.api.session_token = replacement.session_token
        replacement.server_close()
        self.assertEqual(self.create()[0], 403)  # old session token is rejected
        self.assertEqual(list(self.directory.iterdir()), [])
        self.token = self.api.session_token
        self.assertEqual(self.create()[0], 201)


if __name__ == '__main__':
    unittest.main(verbosity=2)
