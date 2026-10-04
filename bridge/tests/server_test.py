# Frugal Flock — Copyright (C) 2026 Daniel Mitev; Daniel Mevit (@danielmevit)
# https://github.com/danielmevit/frugal-flock
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE. No warranty.
import concurrent.futures
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import subprocess
import threading
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location('activity_server', Path(__file__).parents[1] / 'server.py')
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)


def sample():
    return dict(schema_version=1, observed_at='2026-10-04T21:00:00Z', stopped=True,
                agents=[], results=[], retries=[], recent_events=[], warnings=[],
                evidence='recorded; use result to recheck revision and readiness')


class ObserverTests(unittest.TestCase):
    def observer(self):
        return server.Observer(Path('/fixed/workspace'), Path('/fixed/engine'), timeout=3)

    def test_fixed_read_only_command_and_cache(self):
        observer = self.observer()
        document = sample(); document['raw_log'] = 'PRIVATE OMIT'
        process = subprocess.CompletedProcess([], 0, json.dumps(document).encode(), b'PRIVATE STDERR')
        with patch.object(server.subprocess, 'run', return_value=process) as invoke:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as workers:
                values = list(workers.map(lambda _: observer.read(), range(8)))
        self.assertEqual(invoke.call_count, 1)
        args, options = invoke.call_args
        self.assertEqual(args, (['/fixed/engine', 'watch', '--once', '--json'],))
        self.assertEqual(options['cwd'], Path('/fixed/workspace/repo'))
        self.assertEqual(options['stdin'], subprocess.DEVNULL)
        self.assertEqual(options['timeout'], 3)
        self.assertTrue(options['capture_output'])
        self.assertNotIn('shell', options)
        self.assertNotIn('raw_log', values[0])
        self.assertTrue(all(value == values[0] for value in values))

    def test_failed_observation_clears_cached_success(self):
        observer = self.observer()
        with patch.object(server.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(sample()).encode())):
            self.assertIsNotNone(observer.read())
        observer.expires = 0
        with patch.object(server.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, b'PRIVATE STDOUT', b'PRIVATE STDERR')) as invoke:
            self.assertIsNone(observer.read())
            self.assertIsNone(observer.read())
            self.assertEqual(invoke.call_count, 1)

    def test_invalid_or_unavailable_engine_fails_closed(self):
        bad = [b'not json', b'[]', b'{}', json.dumps({**sample(), 'schema_version': True}).encode(),
               json.dumps({**sample(), 'schema_version': 2}).encode(),
               json.dumps({**sample(), 'results': {}}).encode(), b'x' * (8 * 1024 * 1024 + 1)]
        for output in bad:
            with self.subTest(output=output[:50]):
                with patch.object(server.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, output)):
                    self.assertIsNone(self.observer().read())
        for exception in (OSError('PRIVATE PATH'), subprocess.TimeoutExpired('/fixed/engine', 3)):
            with self.subTest(exception=type(exception).__name__):
                with patch.object(server.subprocess, 'run', side_effect=exception):
                    self.assertIsNone(self.observer().read())


class StubObserver:
    def __init__(self):
        self.calls = 0
        self.value = sample()

    def read(self):
        self.calls += 1
        return copy.deepcopy(self.value)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.observer = StubObserver()
        self.server = server.ActivityServer(0, self.observer)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def request(self, method='GET', path='/api/activity', headers=None):
        connection = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=3)
        try:
            connection.request(method, path, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_activity_and_assets_are_loopback_only(self):
        self.assertEqual(self.server.server_address[0], '127.0.0.1')
        code, headers, body = self.request(headers={'Origin': self.server.origin})
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body), sample())
        self.assertEqual(headers['Cache-Control'], 'no-store')
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        self.assertNotIn('Access-Control-Allow-Origin', headers)
        for path, kind in (('/', 'text/html'), ('/activity.js', 'text/javascript'), ('/activity.css', 'text/css')):
            with self.subTest(path=path):
                code, headers, body = self.request(path=path)
                self.assertEqual(code, 200)
                self.assertTrue(headers['Content-Type'].startswith(kind))
                self.assertTrue(body)
        self.assertEqual(self.observer.calls, 1)

    def test_remote_host_origin_and_request_paths_never_observe(self):
        for headers in ({'Host': 'evil.example'}, {'Host': 'localhost:' + str(self.server.server_port)},
                        {'Origin': 'https://evil.example'}, {'Origin': 'null'}):
            with self.subTest(headers=headers):
                self.assertEqual(self.request(headers=headers)[0], 403)
        for path in ('/api/activity?engine=evil', '/api/run', '/server.py', '/../server.py', '/%2e%2e/coord/AGENT-LOG.md'):
            with self.subTest(path=path):
                self.assertEqual(self.request(path=path)[0], 404)
        self.assertEqual(self.observer.calls, 0)

    def test_mutating_methods_are_refused_without_observation(self):
        for method in ('POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS', 'HEAD'):
            with self.subTest(method=method):
                self.assertEqual(self.request(method=method)[0], 405)
        self.assertEqual(self.observer.calls, 0)

    def test_unavailable_observation_has_no_stale_or_raw_payload(self):
        self.assertEqual(self.request()[0], 200)
        self.observer.value = None
        code, _, body = self.request()
        self.assertEqual(code, 503)
        self.assertEqual(json.loads(body), dict(schema_version=1, error='activity_unavailable'))
        self.assertNotIn(b'observed_at', body)



class PreviewLaunchTests(unittest.TestCase):
    def test_default_does_not_open_browser(self):
        preview = Mock(origin='http://127.0.0.1:12345')
        with patch.object(server.webbrowser, 'open') as opener, patch('builtins.print'):
            server.serve_preview(preview)
        opener.assert_not_called()
        preview.serve_forever.assert_called_once_with()
        preview.server_close.assert_called_once_with()

    def test_opt_in_opens_only_fixed_bound_origin(self):
        preview = Mock(origin='http://127.0.0.1:12345')
        opened = threading.Event()
        def opener(origin, new):
            self.assertEqual(origin, preview.origin)
            self.assertEqual(new, 2)
            opened.set()
            return True
        preview.serve_forever.side_effect = lambda: self.assertTrue(opened.wait(1))
        with patch.object(server.webbrowser, 'open', side_effect=opener) as launch, patch('builtins.print'):
            server.serve_preview(preview, open_browser=True)
        launch.assert_called_once_with(preview.origin, new=2)
        preview.server_close.assert_called_once_with()

    def test_browser_failures_leave_manual_url(self):
        for exception in (None, server.webbrowser.Error('unconfigured browser'), OSError('missing browser')):
            with self.subTest(exception=exception):
                with patch.object(server.webbrowser, 'open', return_value=False, side_effect=exception), patch('builtins.print') as output:
                    server.open_preview('http://127.0.0.1:12345')
                self.assertIn('Open http://127.0.0.1:12345 manually', output.call_args.args[0])

    def test_slow_opener_does_not_block_service_or_shutdown(self):
        preview = Mock(origin='http://127.0.0.1:12345')
        started, release = threading.Event(), threading.Event()
        def slow_opener(*args, **kwargs):
            started.set()
            release.wait(2)
            return True
        try:
            with patch.object(server.webbrowser, 'open', side_effect=slow_opener), patch('builtins.print'):
                preview.serve_forever.side_effect = lambda: self.assertTrue(started.wait(1))
                server.serve_preview(preview, open_browser=True)
                self.assertFalse(release.is_set())
                preview.server_close.assert_called_once_with()
        finally:
            release.set()


if __name__ == '__main__':
    unittest.main(verbosity=2)
