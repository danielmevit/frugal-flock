# Unio local Activity preview

This source-only preview turns `watch --once --json` into a read-only local
browser view. It shows recorded task decisions, worker-lock observations,
operator limits, STOP and recent events. It does not dispatch providers or
write coordination files. Authentication and capacity remain unknown.
Recorded approval is separate from current readiness and human acceptance.

Python 3.9 or newer with the standard library is the only server dependency.
The preview defaults to the `unio` engine on PATH. Pass `--engine` to
override that with an explicit trusted executable that supports `watch`.
The installed v0.4.0 release has no watch command and remains unchanged.
Use a disposable source build in workspace `tmp/`, following
[the preview contract](../docs/BRIDGE-ACTIVITY.md).

From the repository root:

```bash
python3 -B bridge/server.py --project /path/to/workspace
```

To override the engine, pass an absolute executable path:

```bash
python3 -B bridge/server.py --project /path/to/workspace \
  --engine /path/to/workspace/tmp/activity-build/bin/unio
```

The command prints its `http://127.0.0.1:PORT` address. Open that address in
a browser, or add `--open-browser` to request opening it automatically.
Opening is opt-in; if the machine has no configured browser (including some
WSL setups), the service keeps running and prints the manual URL. A slow
browser opener does not block observations. Ctrl-C stops the service. The default port is selected by the OS;
`--port` can select a local port. The page polls every two seconds and has a
Refresh button. A failed observation clears the old display and says activity
is unavailable. Refreshing the page performs only another observation.

Default mode serves the four static assets, `GET /api/activity` and a
same-origin capability document at `GET /api/session`. The server
binds 127.0.0.1; Host must match its actual address, and an Origin header
must match that same origin. No cross-origin access, request-selected folder,
engine, command or task exists. Default mode has no mutation endpoint. The selected
engine runs on the trusted host; this is not an OS sandbox or a packaged
launcher. Project data is sensitive to anyone with local account access.
No remote exposure, global reinstall, native credential access, or release
is needed to use the preview.

The view cannot approve, start, stop, retry, review, apply or merge work.
Use CLI `result WORKER TASK` separately to recheck current readiness. A free
worker lock with a recorded running result means completion is unknown;
it does not rule out detached processes. Operator retry times are reminders,
not confirmed provider reset times. Snapshots observe files independently.
The owner waived the two-person feedback prerequisite on 2026-10-04;
no sessions occurred. The next slices use judgment/automated checks and
explicit run/quota approval. This preview still has no live controls.

## Checks

```bash
python3 -B bridge/tests/server_test.py
python3 -B bridge/tests/plan_store_test.py
python3 -B bridge/tests/plan_api_test.py
node --check bridge/activity.js
node --check bridge/drafts.js
node --check bridge/tests/browser.cjs
```

Optional browser checks use the same workspace-local Playwright tooling as
[the prototype](../prototype/README.md). Set `M2_PLAYWRIGHT_MODULE`,
`M2_CHROMIUM_PATH`, and workspace-local `TMPDIR`, then run:

```bash
node bridge/tests/browser.cjs
node bridge/tests/drafts_browser.cjs
```

The browser check launches only a loopback test server and a strict local
watch fixture; it makes no provider calls. It checks recorded failure and
unknown completion, text escaping, observation failure/recovery, refresh,
mobile layout and absence of external requests or browser errors. HTTP checks
cover the fixed command/cache, invalid observations, method/path/Host/Origin
refusal before observation, assets and unavailable responses.

Copyright (C) 2026 Daniel Mitev; public attribution Daniel Mevit
(@danielmevit). Original: [Unio](https://github.com/danielmevit/unio).
AGPL-3.0-only; see LICENSE and NOTICE for attribution/origin terms. No warranty.

## Manual plan-draft foundation

plan_store.py supplies durable immutable manual drafts in the selected
workspace's coord/ui-plans/. Default mode stays read-only. Optional --enable-plan-drafts exposes only
protected manual create/read endpoints and the manual browser form. Saving
only stores literal text; no AI plan or worker starts. Each complete draft has an opaque
ID, creation time, request text, draft state and a hash of its saved bytes.
It contains no AI-generated plan, approval, native task or job. Text is
stored literally and never interpreted as a command. See the
[bounded contract](../docs/PLAN-DRAFTS.md).

For manual-draft API mode, add --enable-plan-drafts at startup. This creates
coord/ui-plans/ in that fixed workspace. GET /api/session supplies a fresh
session token; POST /api/plans requires that token in X-Unio-Session,
an exact same-origin Origin header, and JSON with only the request field.
GET /api/plans/ID requires the same token. Saving returns draft state and a
content hash; no AI-generated plan, native task, approval or execution occurs.
Restart rotates the token; saved drafts remain readable under the new session.
The mode does not automatically open a browser or dispatch providers.

In enabled mode the browser shows Save draft and Reopen draft. Empty or
whitespace requests are rejected. Saving displays the literal text and puts
only its opaque ID in the URL fragment; reloading safely reopens by ID with
a new session. The token stays in memory. Repeated submit events produce
one save, and a failed save/session refresh keeps typed text without an
automatic retry. Draft text is not backed up until the server confirms a
save; refreshing after an unconfirmed save can lose unsaved input. No extra
provider worker was used for this UI source step.

## Execution mode

The explicit execution mode requires `--enable-execution` (which also enables manual drafts) and all of its concrete startup arguments: `--worker`, `--reviewer`, `--worker-company`, `--reviewer-company`, `--config-dir`, and `--task-template`. This enforces a strict trusted-host/local-session boundary. The fixed startup configuration dictates the exact engine, project, worker, reviewer, companies, template and configurations to use. The HTTP request and local browser session can never provide or select paths, identifiers, bindings or templates. The loopback UI can only instruct the service to act on the immutable startup configuration and its tracked draft bindings.
