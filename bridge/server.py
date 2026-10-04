#!/usr/bin/env python3
# Frugal Flock — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/frugal-flock
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
"""Loopback-only read-only Activity preview; no dispatch or project writes."""
import argparse
import hmac
import json
import re
import secrets
from pathlib import Path
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ASSETS = Path(__file__).resolve().parent
TOP_FIELDS = {'schema_version','observed_at','stopped','agents','results','retries','recent_events','warnings','evidence'}


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError('duplicate JSON field')
        value[key] = item
    return value


class Observer:
    def __init__(self, project, engine, timeout=10):
        self.project, self.engine, self.timeout = project, engine, timeout
        self.lock = threading.Lock()
        self.cached = None
        self.expires = 0

    def read(self):
        with self.lock:
            if time.monotonic() < self.expires:
                return self.cached
            self.cached = None
            try:
                result = subprocess.run([str(self.engine),'watch','--once','--json'],
                    cwd=self.project/'repo', stdin=subprocess.DEVNULL, capture_output=True, timeout=self.timeout)
                if result.returncode or len(result.stdout) > 8 * 1024 * 1024:
                    raise ValueError('observer failed')
                data = json.loads(result.stdout)
                if (not isinstance(data,dict) or type(data.get('schema_version')) is not int or data['schema_version'] != 1
                    or type(data.get('stopped')) is not bool or any(not isinstance(data.get(k),list)
                        for k in ('agents','results','retries','recent_events','warnings'))):
                    raise ValueError('unsupported observer document')
                # Producer is the fixed owner-selected CLI. Never include arbitrary
                # stdout/stderr or unexpected top-level fields in an HTTP response.
                self.cached = {k:v for k,v in data.items() if k in TOP_FIELDS}
            except (ValueError,OSError,subprocess.TimeoutExpired):
                self.cached = None
            self.expires = time.monotonic() + 1
            return self.cached


class ActivityServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, port, observer, plans=None):
        super().__init__(('127.0.0.1',port), ActivityHandler)
        self.observer = observer
        self.plans = plans
        self.session_token = secrets.token_urlsafe(32) if plans is not None else None
        self.origin = 'http://127.0.0.1:' + str(self.server_port)


class ActivityHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # no request paths or query strings copied into task history

    def respond(self, code, data, content_type='application/json; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(data)

    def error_response(self, code, error):
        self.respond(code,json.dumps(dict(schema_version=1,error=error)).encode())

    def origin_allowed(self, write=False):
        if self.headers.get_all('Host') != [self.server.origin.removeprefix('http://')]:
            self.error_response(403, 'host_refused')
            return False
        origins = self.headers.get_all('Origin') or []
        if origins != [self.server.origin] and (write or origins):
            self.error_response(403, 'origin_refused')
            return False
        return True

    def token_allowed(self):
        supplied = self.headers.get_all('X-Frugal-Flock-Session') or []
        if (len(supplied) != 1 or self.server.session_token is None
                or not hmac.compare_digest(supplied[0].encode(), self.server.session_token.encode())):
            self.error_response(403, 'session_refused')
            return False
        return True

    def do_GET(self):
        if not self.origin_allowed():
            return
        if self.path == '/api/session':
            return self.respond(200, json.dumps(dict(schema_version=1,
                manual_drafts=self.server.plans is not None, token=self.server.session_token)).encode())
        if self.server.plans is not None and self.path.startswith('/api/plans/'):
            if not self.token_allowed():
                return
            identity = self.path.removeprefix('/api/plans/')
            if re.fullmatch('[0-9a-f]{32}', identity) is None:
                return self.error_response(400, 'invalid_plan_id')
            try:
                draft = self.server.plans.get(identity)
            except FileNotFoundError:
                return self.error_response(404, 'plan_not_found')
            except (ValueError, OSError):
                return self.error_response(503, 'draft_unavailable')
            return self.respond(200, json.dumps(draft, ensure_ascii=True).encode())
        if self.path == '/api/activity':
            snapshot = self.server.observer.read()
            if snapshot is None: return self.error_response(503,'activity_unavailable')
            return self.respond(200,json.dumps(snapshot,ensure_ascii=True).encode())
        routes = {'/':('index.html','text/html; charset=utf-8'),
                  '/activity.js':('activity.js','text/javascript; charset=utf-8'),
                  '/drafts.js':('drafts.js','text/javascript; charset=utf-8'),
                  '/activity.css':('activity.css','text/css; charset=utf-8')}
        if self.path not in routes: return self.error_response(404,'not_found')
        name,content_type = routes[self.path]
        return self.respond(200,(ASSETS/name).read_bytes(),content_type)

    def do_POST(self):
        if self.server.plans is None:
            return self.error_response(405, 'read_only')
        if not self.origin_allowed(write=True) or not self.token_allowed():
            return
        if self.path != '/api/plans':
            return self.error_response(404, 'not_found')
        if self.headers.get('Transfer-Encoding') is not None:
            return self.error_response(400, 'invalid_body')
        lengths = self.headers.get_all('Content-Length') or []
        if not lengths:
            return self.error_response(411, 'length_required')
        if len(lengths) != 1 or re.fullmatch('[0-9]{1,6}', lengths[0]) is None:
            return self.error_response(400, 'invalid_body')
        length = int(lengths[0])
        if length > 32768:
            return self.error_response(413, 'body_too_large')
        if self.headers.get('Content-Type', '').split(';', 1)[0].strip().lower() != 'application/json':
            return self.error_response(415, 'json_required')
        try:
            self.connection.settimeout(5)
            raw = self.rfile.read(length)
            if len(raw) != length:
                return self.error_response(400, 'invalid_body')
            body = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
        except TimeoutError:
            return self.error_response(408, 'body_timeout')
        except (ValueError, OSError):
            return self.error_response(400, 'invalid_body')
        if not isinstance(body, dict) or set(body) != {'request'}:
            return self.error_response(400, 'invalid_request')
        try:
            draft = self.server.plans.create(body['request'])
        except ValueError:
            return self.error_response(400, 'invalid_request')
        except OSError:
            return self.error_response(503, 'draft_unavailable')
        return self.respond(201, json.dumps(draft, ensure_ascii=True).encode())

    def reject_method(self):
        self.error_response(405,'read_only')

    do_PUT = do_PATCH = do_DELETE = do_OPTIONS = do_HEAD = reject_method



def open_preview(origin):
    try:
        opened = webbrowser.open(origin, new=2)
    except (webbrowser.Error, OSError):
        opened = False
    if not opened:
        print('Browser could not be opened. Open ' + origin + ' manually.', flush=True)


def serve_preview(server, open_browser=False):
    mode = 'manual draft preview' if getattr(server, 'plans', None) is not None else 'read-only Activity preview'
    print(server.origin + ' — ' + mode + '; no provider dispatch', flush=True)
    if open_browser:
        # A slow desktop opener must not delay the listening observation service.
        threading.Thread(target=open_preview, args=(server.origin,), daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main():
    parser = argparse.ArgumentParser(description='Frugal Flock read-only local Activity preview')
    parser.add_argument('--project',type=Path,required=True,help='enclosing workspace with repo/, coord/, wt/')
    parser.add_argument('--engine',type=Path,required=True,help='explicit CLI executable supporting watch --once --json')
    parser.add_argument('--port',type=int,default=0,help='loopback port, 0 chooses an unused port')
    parser.add_argument('--open-browser',action='store_true',help='optionally open this loopback read-only preview in the default browser')
    parser.add_argument('--enable-plan-drafts',action='store_true',help='opt in to manual draft storage only; never starts workers')
    options = parser.parse_args()
    if not 0 <= options.port <= 65535: parser.error('port must be 0 through 65535')
    project = options.project.absolute()
    if project.is_symlink() or project.resolve() != project or any(not (project/p).is_dir() for p in ('repo','coord','wt')):
        parser.error('project must be a real enclosing Frugal Flock workspace')
    engine = options.engine.absolute()
    if not engine.is_file(): parser.error('engine executable not found')
    plans = None
    try:
        if options.enable_plan_drafts:
            from plan_store import PlanStore
            plans = PlanStore(project)
        server = ActivityServer(options.port, Observer(project, engine), plans=plans)
        serve_preview(server, options.open_browser)
    finally:
        if plans is not None:
            plans.close()


if __name__ == '__main__':
    main()
