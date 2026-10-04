# Frugal Flock local Activity preview

This source-only preview turns `watch --once --json` into a read-only local
browser view. It shows recorded task decisions, worker-lock observations,
operator limits, STOP and recent events. It does not dispatch providers or
write coordination files. Authentication and capacity remain unknown.
Recorded approval is separate from current readiness and human acceptance.

Python 3.9 or newer with the standard library is the only server dependency.
The owner chooses an enclosing workspace and an explicit trusted Frugal
Flock executable that supports `watch`. The installed v0.4.0 has no watch
command and remains unchanged. Use a disposable source build in workspace
`tmp/`, following [the preview contract](../docs/BRIDGE-ACTIVITY.md).

From the repository root, with absolute paths selected for this machine:

```bash
python3 -B bridge/server.py --project /path/to/frugal-flock \
  --engine /path/to/frugal-flock/tmp/activity-build/bin/frugal-flock
```

The command prints its `http://127.0.0.1:PORT` address. Open that address in
a browser; Ctrl-C stops the service. The default port is selected by the OS;
`--port` can select a local port. The page polls every two seconds and has a
Refresh button. A failed observation clears the old display and says activity
is unavailable. Refreshing the page performs only another observation.

Only the three static assets and `GET /api/activity` are served. The server
binds 127.0.0.1; Host must match its actual address, and an Origin header
must match that same origin. No cross-origin access, request-selected folder,
engine, command, task, or mutation endpoint exists. The fixed owner-selected
engine runs on the trusted host; this is not an OS sandbox or a packaged
launcher. Project data is sensitive to anyone with local account access.
No remote exposure, global reinstall, native credential access, or release
is needed to use the preview.

The view cannot approve, start, stop, retry, review, apply or merge work.
Use CLI `result WORKER TASK` separately to recheck current readiness. A free
worker lock with a recorded running result means completion is unknown;
it does not rule out detached processes. Operator retry times are reminders,
not confirmed provider reset times. Snapshots observe files independently.
Two real new-user sessions remain required before wiring live UI execution.

## Checks

```bash
python3 -B bridge/tests/server_test.py
node --check bridge/activity.js
node --check bridge/tests/browser.cjs
```

Optional browser checks use the same workspace-local Playwright tooling as
[the prototype](../prototype/README.md). Set `M2_PLAYWRIGHT_MODULE`,
`M2_CHROMIUM_PATH`, and workspace-local `TMPDIR`, then run:

```bash
node bridge/tests/browser.cjs
```

The browser check launches only a loopback test server and a strict local
watch fixture; it makes no provider calls. It checks recorded failure and
unknown completion, text escaping, observation failure/recovery, refresh,
mobile layout and absence of external requests or browser errors. HTTP checks
cover the fixed command/cache, invalid observations, method/path/Host/Origin
refusal before observation, assets and unavailable responses.

Copyright (C) 2026 Daniel Mitev; public attribution Daniel Mevit
(@danielmevit). Original: [Frugal Flock](https://github.com/danielmevit/frugal-flock).
AGPL-3.0-only; see LICENSE and NOTICE for attribution/origin terms. No warranty.
