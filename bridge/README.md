# Unio local project workspace

This source-only workspace has three explicit startup modes: read-only
Activity by default, local manual drafts, and live execution. Default mode
turns `watch --once --json` into a read-only local browser view. It shows
recorded task decisions, worker-lock observations, operator limits, STOP and
recent events. Default mode does not dispatch providers or write coordination
files. Authentication and capacity remain unknown.
Recorded approval is separate from current readiness and human acceptance.

Python 3.9 or newer with the standard library is the only server dependency.
The preview defaults to the `unio` engine on PATH. Pass `--engine` to
override that with an explicit trusted executable that supports `watch`.
This source preview does not change an installed release.
Use a disposable source build in workspace `tmp/`, following
[the preview contract](../docs/BRIDGE-ACTIVITY.md).

From the repository root:

```bash
python3 -B bridge/server.py --project '/path/to/workspace'
```

To override the engine, pass an absolute executable path:

```bash
python3 -B bridge/server.py --project '/path/to/workspace' \
  --engine '/path/to/workspace/tmp/activity-build/bin/unio'
```

The command prints its `http://127.0.0.1:PORT` address. Open that address in
a browser, or add `--open-browser` to request opening it automatically.
Opening is opt-in; if the machine has no configured browser (including some
WSL setups), the service keeps running and prints the manual URL. A slow
browser opener does not block observations. Ctrl-C stops the service. The default port is selected by the OS;
`--port` can select a local port. The page polls every two seconds and has a
Refresh button. A failed observation clears the old display and says activity
is unavailable. Refreshing the page performs only another observation.

Default mode serves the static workspace assets, `GET /api/activity` and a
same-origin capability document at `GET /api/session`. The server
binds 127.0.0.1; Host must match its actual address, and an Origin header
must match that same origin. No cross-origin access, request-selected folder,
engine, command or task exists. Default mode has no mutation endpoint. The selected
engine runs on the trusted host; this is not an OS sandbox or a packaged
launcher. Project data is sensitive to anyone with local account access.
No remote exposure, global reinstall, native credential access, or release
is needed to use the preview.

The default view cannot approve, start, stop, retry, review, apply or merge work.
Use CLI `result WORKER TASK` separately to recheck current readiness. A free
worker lock with a recorded running result means completion is unknown;
it does not rule out detached processes. Operator retry times are reminders,
not confirmed provider reset times. Snapshots observe files independently.
The owner waived the two-person feedback prerequisite on 2026-10-04;
no sessions occurred. The next slices use judgment/automated checks and
explicit run/quota approval. Live controls require the explicit execution
mode described below.

## Checks

```bash
python3 -B bridge/tests/server_test.py
python3 -B bridge/tests/plan_store_test.py
python3 -B bridge/tests/plan_api_test.py
node --check bridge/activity.js
node --check bridge/drafts.js
node --check bridge/jobs.js
node --check bridge/tests/browser.cjs
```

Optional browser checks use the same workspace-local Playwright tooling as
[the prototype](../prototype/README.md). Set `M2_PLAYWRIGHT_MODULE`,
`M2_CHROMIUM_PATH`, and workspace-local `TMPDIR`, then run:

```bash
node bridge/tests/browser.cjs
node bridge/tests/drafts_browser.cjs
node bridge/tests/execution_browser.cjs
```

The browser checks launch loopback test servers and local watch/execution
fixtures; they make no provider calls. It checks recorded failure and
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

The explicit execution mode requires `--enable-execution` (which also enables manual drafts) and all of its concrete startup arguments: `--worker`, `--reviewer`, `--worker-company`, `--reviewer-company`, `--config-dir`, and `--task-template`. The server binds loopback only and requires the exact Host, same-origin Origin for POST and the per-start session token; configured worker, reviewer and Validate commands run with the operator's host access, and worktrees are not OS sandboxes.

Example startup:

```bash
python3 -B bridge/server.py --project '/path/to/workspace' --enable-execution \
  --worker claude-worker --worker-company Anthropic --reviewer gemini-reviewer --reviewer-company Google \
  --config-dir '/path/to/workspace/config' --task-template '/path/to/workspace/template.json'
```

The fixed startup configuration selects the engine, workspace, worker, reviewer, companies, template and configuration paths. Browser requests supply opaque draft/job IDs, hashes and action keys to identify saved drafts and tracked jobs and request explicit actions. They cannot choose engine, workspace, worker, reviewer, template or configuration paths or override immutable bindings. In execution mode, Start can launch one real configured provider run and Review one configured reviewer call, which use provider allowance; there is no automatic retry.

The workspace places the request composer beside selected work on desktop,
and stacks them on narrow screens. Reopen saved work exposes draft/job IDs;
job identity, hashes, exact native results and full revisions live in
keyboard-accessible details. The exact literal request, allowed scope, Validate
commands and configured lab labels stay visible before run approval. The
stage strip marks the current stage with `aria-current="step"`; its help
explains the next permitted action. No progress or provider capacity is inferred.

Save draft and Prepare preview do not call providers. Approve run permits
spending without starting a worker. Start once and Request review are distinct
explicit actions. Verify changes requires current successful native process
evidence; Request review requires current passed checks. Accept current revision
requires exact matching process/check/review revisions, native readiness and
nonstale evidence. Acceptance records source approval and does not merge,
install or publish. Stop task targets only a reserved/uncertain task; Cancel
job is available only before reservation. Launch/verify/review/stop messages
report received responses, with the actual result displayed separately.

Opaque action keys and complete action inputs are saved in same-origin tab
session storage before a single POST. The selected job ID also enters the URL
fragment. Reload restores job context with GET only. Session rotation never
retries a POST; unconfirmed responses keep context and block further mutation
until an explicit read (Stop remains available for uncertain live work).
Refreshing a saved draft can find its already prepared job by the same request
key, without creating another intent. Conflicting saved inputs or revisions
refuse rather than generating replacement keys. Storage failures prevent the
write. Server-side durable bindings remain authoritative if browser storage is
lost; tab storage is not a cross-browser backup. Tokens stay in memory.

Mode notice/footer copy comes from the session capability, including manual
and default mode restoration. Long literal requests, hashes, errors and logs
wrap within their region. Controls have visible keyboard focus and 44px minimum
height; status regions announce updates, busy actions lock selection controls,
and reduced-motion preferences disable transitions. Missing, failed, stale,
unknown and live evidence have separate help and honest results.


## BROWSER-UI-DESIGN-1 audit evidence (2026-10-06)

The worker read the frozen design brief, execution contract and model-effort
research, then applied the existing-project audit workflow to the inherited
Google UI commit `1788aa06`. The audit found conflicting read-only/live copy,
a long sequence of forms, bare stage verbs, horizontally scrolling preview
text, and busy-state cleanup that could enable controls without current native
evidence. This pass uses original vanilla HTML/CSS/JS and system fonts. The
lead inspected the private Toolcraft reference; this worker read that reference
brief rather than copying its code, assets, tokens or templates. No dependency,
runtime/API change or global installation is part of this source slice.

Private evidence is under workspace
`tmp/unio-next/receipts/browser-ui-design-1-visual/`, outside the product tree.
The lead's `ui-baseline-before-*-20261006.png` images and JSON were inspected.
The worker captured and inspected its own `before-*-desktop.png` / `narrow.png`
and `final-*-desktop.png` / `narrow.png` at 1440×900 and 390×844:

- `actual-default-recorded`: the actual project observer, with no fixtures and
  zero POSTs; timestamps and recorded tasks can change during this source run.
- `mock-execution-composer`, `mock-execution-preview-error` and
  `mock-execution-stage-error`: intercepted mock execution API views over the
  actual read-only observer. Save/prepare/refused-approval produce three mock
  POSTs, with zero provider calls. They show literal long requests, exact scope,
  checks, lab labels, unknown outcome, retained input and disabled mutations.
- `before-audit.json` and `final-audit.json` record viewport, state, source,
  request counts and limitations. Fixture browser regressions also capture
  current-ready, live, stale and session-error states in `final-regressions/`.

Image inspection confirms a compact header, visible composer, separate selected
work and readable evidence, with no page overflow in either viewport. Long
preview text wraps instead of requiring sideways scrolling. Current-stage help,
unknown/error copy and narrow stacked controls remain visible. Normal text,
primary button text and input borders have calculated contrast ratios of at
least 5.4:1, 8.0:1 and 3.4:1 respectively for the checked palette pairs.
Two intermediate full-page captures of the large real history timed out;
partial images remain private. The completed final audit uses the requested
viewport captures. There was no live provider demonstration or human usability
session, and screenshots do not establish source acceptance.

Offline checks used the task-pinned installed Playwright/Chromium and workspace
TMPDIR, with Python bytecode disabled. Default and manual browser regressions,
prototype browser/scenario checks and all API/store checks passed. Execution
browser regressions preserve the full explicit journey and add literal long
preview, current-stage accessibility, keyboard focus, 44px targets, responsive
wrapping, double-click/busy protection, stable keys, session rotation,
lost-start/lost-prepare reload recovery with no POST retry, missing/live/unknown/
stale/failed evidence, exact revision gating, waiting cancellation and exact-task
stop. The API suite passed 21 tests; server 15, plan API 8, plan store 8 and job
store 34. The execution service's first 51-case run had one timing-sensitive
failure: its 150ms review-timeout fixture recorded zero review calls. That case
passed in isolation, and the subsequent complete suite passed 51/51. The initial
failure is retained in the private audit; no service code or assertion changed.
Docs lint and diff whitespace checks passed. Version remains 0.5.3. Native
verification, two independent nonauthor lab reviews of the complete base-to-
candidate delta, and lead acceptance remain separate gates. Pending docs work
is not claimed reviewed or pushed.

## BROWSER-UI-DESIGN-COMPLETE-1 preserved completion (2026-10-06)

The original `BROWSER-UI-DESIGN-1` native Source exited 1 at its usage limit
without the scoped commit. That attempt remains failed. This separately
authorized completion starts at unchanged Google commit
`1788aa06d02bb347a6aef2b5ed0e351825cda794` and inherits the exact nine dirty
tracked files and design fragment preserved in workspace
`artifacts/ui-design-limited-20261006/manifest.json`; all ten starting file
hashes matched that archive. The complete change has Google + OpenAI author
labs. The inherited Google and design fragments remain unchanged.

This completion inspected the existing final desktop/narrow default observer,
mock composer, literal preview and refused-approval images in the evidence
directory above. It did not regenerate screenshots or redesign the layout.
Default observations and mock execution states retain their original labels.
The frozen execution contract retains SHA-256
`dd4d55cfe39d689e9dc92c92c88d04f41bc44067a317b072d0a7a168d57c22c3`.

All seven completion Validate commands ran once initially. The execution,
default Activity, manual draft and prototype Chromium suites passed, without
capturing new screenshots or calling providers. The initial API suite ran
21 tests in 268.890 seconds: 20 passed and the happy-path acceptance request
hit its unchanged 15-second HTTP timeout. The server subsequently logged a
broken pipe after that client disconnected. These checks ran concurrently;
the API suite alone was then rerun after every browser process had exited,
with the same command, assertions and timeouts. The initial API failure is
retained here, rather than treated as a passed run. Initial documentation
lint failed only because the completion fragment did not yet exist; the
initial diff whitespace check passed.

The isolated API suite passed 21/21 in 191.676 seconds. No API/service code,
browser behavior, test assertion or timeout changed during this completion;
removing concurrent browser checks was sufficient for that acceptance case
to pass, without establishing a definitive cause for the initial timeout.
All four browser checks passed on their initial run. Documentation lint
covers this README and all three scoped fragments; final whitespace checks
cover the completed changes. Only documentation and the new completion
fragment were added to the archived candidate.

These are offline regression results, not live workflow completion. The
original failed native Source remains failed. Version 0.5.3 remains pending,
with fresh native verification, two independent nonauthor-lab reviews and
the lead's full overview still required before integration.
