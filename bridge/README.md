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
node --check bridge/worker_console.js
node --check bridge/tests/browser.cjs
python3 -B bridge/tests/worker_files_test.py
```

Optional browser checks use the same workspace-local Playwright tooling as
[the prototype](../prototype/README.md). Set `M2_PLAYWRIGHT_MODULE`,
`M2_CHROMIUM_PATH`, and workspace-local `TMPDIR`, then run:

```bash
node bridge/tests/browser.cjs
node bridge/tests/drafts_browser.cjs
node bridge/tests/execution_browser.cjs
node bridge/tests/worker_console_browser.cjs
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

If the session refresh itself fails, execution capability is cleared and the
visible draft status asks for an explicit reload. The saved request, selection
and complete action intent remain available; reconnecting reads the saved job
without replaying approval, start or review. A successful session refresh still
requires an explicit job read before an unconfirmed action can be chosen again.

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

## BROWSER-UI-READINESS-FIX-1 correction (2026-10-06)

Fresh mandatory verification of the preserved completion failed 6/7: the
execution browser check registered its injected approval URL before an
asynchronous response observer assigned the prepared job ID. The real approval
POST used the correct rendered ID and missed that interceptor. The private
delayed-observer diagnostic exited 1; the private rendered-ID comparison exited
0, with a nonfailing shutdown broken-pipe warning. Those fixtures are diagnostic
evidence, not product verification or a real provider run. Original source and
verification receipts remain unchanged.

The corrected browser check awaits the successful prepare response, validates
its opaque job ID and checks that the rendered ID matches before registering
the approval interceptor. It asserts that exactly one POST reaches that exact
URL, receives the injected 403 and carries the saved approval key. A promise
gate holds the response observer unassigned through session refresh and the
explicit GET-only job refresh, then confirms the observer eventually sees the
same ID. This forces the scheduling race without sleeps, retries or changed
timeouts. All original execution, literal rendering, saved-intent, busy,
keyboard, mobile and native revision/readiness assertions remain in place;
runtime UI files are unchanged.

The focused execution Chromium suite passed on its first corrected run,
including the gated observer regression and every original journey assertion.
The coherent correction was committed as `bf0c96ad341581f9401d3d7265ec2e14ef1d52da`
before the remaining slower checks. Default Activity, manual draft and prototype
Chromium suites also passed on their first runs for this correction.

The execution API suite then ran alone, after all browser suites exited:
20/21 tests passed in 188.553 seconds, with exit 1. Its unchanged happy-path
test timed out at line 258 waiting for the acceptance response under the
existing 15-second HTTP timeout. The server subsequently attempted a 200
response and logged a broken pipe after the client disconnected. Acceptance
rechecks bindings and reads native evidence twice, each result call having its
own 15-second deadline; this identifies the response path, not a proven cause
of the elapsed time. The isolated failure means concurrent browser checks
cannot explain this run. No API/service file or timeout was changed, and the
failed check was not retried. Its raw failure remains in the native Source
tool output. Resolving this separate API acceptance latency requires a scoped
follow-up; the browser interception correction does not establish that the
mandatory validation gate is clear.

Scoped documentation lint and whitespace checks passed. Six of the seven
Validate commands passed; the execution API command remains failed.

The complete inherited UI still has Google + OpenAI author labs. Fresh native
verification, two independent nonauthor subscription-lab reviews and the
lead's own review remain required before integration. These offline checks do
not establish acceptance, a live provider demonstration or public shipping.

## BROWSER-SESSION-RECOVERY-1 coverage (2026-10-07)

The original readiness correction remains failed: its native verification
passed 6/7, but the execution browser timed out after 30 seconds at line 257
waiting for "Session refreshed" after the intended approval 403. Its source
API run separately passed 20/21 with the unchanged acceptance-response timeout
described above. The later native API pass does not resolve that latency or
erase the source failure. A private, zero-provider diagnostic passed that
403/session-200/explicit-job-GET/next-approval sequence, then reached later
steps before its overall 180-second bound ended with exit 124. It was not a
complete test pass or a provider demonstration. Original tasks and receipts
remain unchanged.

Inspection found that `jobs.js` awaits the `refresh-session` promise supplied
by `drafts.js`. Successful session JSON updates capability through
`unio-session`, then resolves that promise; only afterward does the action
report "Session refreshed" and release its busy state. A refresh failure
clears capability, rejects the promise and retains the pending action in tab
storage. The existing failure status requests explicit reload. No runtime
defect has been demonstrated, so this task changes coverage and whitespace,
with no product, service or timeout changes.

The execution regression now holds the session GET until busy state, disabled
write/read controls and absence of a premature recovery announcement are
checked, then releases the real response and requires completed UI recovery.
The delayed prepared-response observer remains gated through that original
403 and explicit GET-only job recovery. A second explicit approval receives
403 with the same saved key; its gated session GET receives a mandatory 503.
Repeated synthetic execution clicks and draft submits must produce no writes
in both pending and failed states. The literal saved request, selection,
request key, complete approval inputs and pending intent must survive. An
explicit reload then performs only session/job reads and restores the saved
preview before the next explicit approval. Neither recovery calls run or
review, and all fixtures spend zero provider allowance. The original execution,
readiness, literal, busy, keyboard, mobile, cancel and stop journeys remain.

On failure, the test reports its phase, bounded request/response/finish timings,
HTTP status, fixed UI status labels, capability events and control state, then
rethrows the original error. Endpoint IDs are redacted; bodies, session tokens,
event details and opaque action keys are excluded from this diagnostic. The
seven inherited trailing-space lines are removed. Whitespace validation uses
the complete delta from frozen base
`0d633772b2b810a83a8c33fe4aa6855edf1cfaf0`, including committed inherited UI.

The first new execution-browser run reached both the successful recovery and
the mandatory failed session GET, then exited 1: the disabled-approval assertion
used a role locator that excluded the execution panel after capability was
cleared and the panel hidden. Its diagnostics showed session 503, capability
false, busy false and disabled approval/refresh controls. The assertion now
uses the exact element ID to inspect the hidden disabled control. This is a
test selector correction, with the same mandatory assertion; it does not
demonstrate a runtime defect or resolve the historical native timeout.

The corrected-selector run passed both complete session scenarios and advanced
through explicit approval, run, verification, review, acceptance, readiness
fixtures and lost-prepare recovery. It then exited 1 after waiting-job
cancellation when the mock engine's call-log reader encountered malformed JSON.
Inspection found one invalid record among 93 lines. The fixture now locks before
opening its append handle and holds the same lock during evidence snapshots;
all records must still parse, with none filtered or ignored. This narrow fixture
diagnostic correction uses Python's existing standard-library file locking and
does not change product/native-engine behavior or retry any call.

The locked-fixture run then passed both session scenarios but exited 1 at the
next explicit approval: the synchronous busy state was set before Playwright's
request event reached the POST counter (actual 4, expected 5). The diagnostic
showed the approval status and busy controls with no next-approval request yet.
The double-click regression now registers and awaits that exact POST boundary
before checking the original count and busy assertions, while the response is
still held. No assertion or timeout was removed or relaxed.

The final execution-browser check passed the complete journey, including both
gated session scenarios, exact intent retention, blocked writes, explicit
read-only reconnect, locked fixture evidence and the next-approval boundary.
The three earlier new-candidate failures remain documented above; each subsequent
execution check followed a concrete test correction rather than an unchanged
failure retry. The initial coherent source checkpoint was committed as
`53b8bee090529564a11004fc6e15e252fad597a2` within the 600-second preservation
target, followed by the request-boundary correction
`ee639222c0cf19f54f288ce2338fd67d0caf9de6` before remaining browser checks.
Default Activity, manual draft and prototype Chromium suites passed on their
first current-candidate runs. The execution API check ran once,
after all browser processes exited. It passed 21/21 in 179.914 seconds, exit 0,
including the happy-path acceptance response. That current pass does not
establish the cause or resolution of the earlier source/native failures.
Final scoped docs lint and the complete frozen-base whitespace check passed.
All seven final-candidate Validate commands passed; the earlier failed checks
and original receipts remain evidence. No check called a live provider.

Native verification of this candidate has not run in this worker.
The complete inherited UI still has Google + OpenAI
author labs; the owner's 2026-10-07 instruction replaces additional reviewer
scheduling with the lead's personal review. Fresh native verification, the
lead's complete assessment and full merge gate remain required. Source checks
are separate from verification, acceptance, integration and release; no push,
merge, live provider demonstration, install or public release occurs here.

## Bounded Git observation optimization (API-GIT-SNAPSHOT-OPT-1)

The next native verification of recovery candidate `620105a` failed 6/7:
all four Chromium suites, docs and full-base whitespace passed, while the
API suite passed 20/21 and timed out after 188.691 seconds. Its retained tail
does not identify the complete failing traceback or an exact failing line.
The earlier source acceptance timeout, this native failure and the source
21/21 pass in 179.914 seconds remain historical evidence.

The lead's unchanged, isolated offline HTTP diagnostic then passed once with
the original 15-second client timeout and assertions. Acceptance took 12.228
seconds, including 8.767 seconds in 40 service subprocesses and two native
result reads; no measured fsync exceeded 20ms. That single pass established
repeated Git overhead and narrow headroom, without proving the complete cause
of the failures.

The service now uses four rather than seven Git subprocesses per worker
observation, before the unchanged preparation/start clean/base queries: one fixed
`rev-parse` reads the owned common directory, peeled
HEAD commit and full branch name; one `ls-files --stage -v -z` reads both
unmerged stages and hidden-edit flags. The repository common directory and
sparse configuration remain fresh separate reads. Strict framing, field and
cardinality checks refuse malformed or ambiguous output, detached/wrong
branches, foreign repositories, unmerged stages, hidden flags and sparse
state. Literal filenames remain NUL-delimited data, including tabs/newlines.
Clean/base checks, safe argv, bounded output/deadlines, immutable bindings,
STOP/ownership locks and durable action keys retain their existing behavior.

Every `_check`, `_native` and response observation still reads current Git
state. Acceptance retains five worker observations, two fresh native result
reads, all four revision fields and the native writer lock. No observations
are cached, combined across calls or moved after acceptance. Replays still
cannot launch or spend again; all client/browser/native deadlines are unchanged.

The new cost regression invokes the inherited real HTTP happy path unchanged,
including all assertions and the 15-second client timeout. Its first measured
pass (32.330 seconds overall) produced the following evidence. Focused service
guard tests also ran during this measurement; elapsed times depend on current
filesystem and machine load. Subprocess counts use the same service `_call`
boundary as the preserved diagnostic, excluding mock-engine internal calls.

| Action | Before seconds / calls | After seconds / calls | After subprocess seconds |
| --- | --- | --- | --- |
| Start | 11.128 / 37 | 5.269 / 25 | 4.350 |
| Verify | 11.602 / 41 | 5.717 / 26 | 4.628 |
| Review | 11.314 / 41 | 6.749 / 26 | 5.356 |
| Accept | 12.228 / 40 | 6.617 / 25 | 4.375 |

The cost regression also passed inside the complete API suite, run after the
service suite and before any browser suite. That second measurement recorded
start 9.130s/25 calls, verify 8.641s/26, review 8.962s/26 and accept 9.410s/25
(6.125 seconds in acceptance subprocesses). Both runs retain two acceptance
result reads and five worker observations. The regression prints raw JSON
rows with request timings, statuses, subprocess/Git counts and time, result
reads and fresh observation counts for retention with source check output.

The regression bounds subprocess counts while requiring the original fresh
observation and result-read counts. Additional guards exercise malformed
metadata/index/config output, real foreign repositories and unmerged indices,
fresh HEAD/branch changes, all four acceptance revision changes, disappearing
readiness and hidden-index changes between native observations. Existing UI
journeys and regressions are unchanged. Timing is measured evidence, not a
guarantee for every filesystem or a substitute for security checks.

The six focused service regressions passed in 77.646 seconds and the separate
cost journey passed once in 32.330 seconds. The full service suite passed 57/57
in 360.031 seconds; the full API suite passed 22/22 in 193.493 seconds, including
all 21 inherited cases plus the new cost journey. This total includes an extra
complete journey and is not directly comparable to the historical 21-case
suite duration. Execution, default Activity, manual drafts and prototype
Chromium suites all passed on their first changed-candidate runs, with every
inherited journey/regression unchanged. Final scoped docs lint and complete
frozen-base whitespace checks passed: all eight Source Validate commands
passed. The coherent runtime/tests/docs checkpoint was committed as
`f9ef4c6b3ca8e1de6f5b0a16aefa78dac86e559e` before slow full checks; a final
documentation commit records their actual outcomes. No live providers,
additional AI invocations or retries were used. Fresh native verification and
the owner's personal lead review remain required; this worker does not accept,
merge, push or release.

## Git sparse boolean correction (API-SPARSE-BOOLEAN-1)

Personal lead review demonstrated an inherited sparse-checkout guard defect:
an untyped `git config --get-all core.sparseCheckout` emits the same newline
for a bare key and an explicitly empty value. Git treats the bare key as true
and the explicit empty value as false, as documented in
[Git's boolean values](https://git-scm.com/docs/git-config#_values). The real
service probe confirmed that the prior parser allowed the bare true case.

The sparse read now uses fixed argv `git config --type=bool --get-all
core.sparseCheckout`. Only exit 0 with exactly one canonical `false` line, or
the existing missing-key result (exit 1 and empty output), permits the worker.
True, duplicate values (including two false values), malformed values,
unexpected framing and error results are refused. The change retains four
fresh Git queries per worker observation and the 15-second Git deadline.
Metadata, index, ownership, STOP and clean/base checks, durable action keys,
observation boundaries, both fresh acceptance result reads and all four
revision comparisons remain unchanged. The original 15-second HTTP client
deadline and other deadlines remain unchanged.

Three new real-repository semantic regressions passed in 70.493 seconds:
`test_sparse_boolean_bare_true_refused`,
`test_sparse_boolean_empty_false_allowed` and
`test_sparse_boolean_malformed_and_duplicate_refused`. They demonstrate
refusal before native calls, an explicit empty false launching the correct
current mock worker, missing-key handling, the four-query budget, and denial
of malformed or duplicate real Git values and unexpected output. No live
providers are used. The coherent runtime/test correction was saved as
`5e680c0bd31b842e8a0282e793cf9f38c202f616` immediately after these checks.

The existing complete HTTP cost journey passed once in 49.431 seconds with
all inherited assertions and the original 15-second client deadline:

| Action | Seconds | Subprocess calls | Subprocess seconds | Fresh worker observations | Result reads |
| --- | --- | --- | --- | --- | --- |
| Start | 8.734 | 25 | 7.184 | 4 | 1 |
| Verify | 8.598 | 26 | 6.957 | 5 | 2 |
| Review | 8.933 | 26 | 7.077 | 5 | 2 |
| Accept | 9.237 | 25 | 6.040 | 5 | 2 |

Scoped documentation lint (`bridge/README.md` and the new fragment) and
full-base whitespace against `0d633772b2b810a83a8c33fe4aa6855edf1cfaf0`
passed. These are the four focused Source commands, not a new full eight-check
Validate result. The lead's deterministic controller must run all eight
Validate commands freshly after this native Source finishes; personal lead
assessment, full merged quality gate and exact passing push remain required
before acceptance. This worker does not merge, push, install or release.

All previous failed receipts and the historical failures and measurements
above remain evidence. The boolean defect is demonstrated independently of
those timeouts; correcting it does not establish their complete cause.
Measured response times depend on filesystem/load and do not guarantee
headroom under the unchanged deadlines. No caches, sleeps, retries, deadline
expansion, extra AI invocations or live providers were used.

## Protected Source output observation (BROWSER-PROGRESS-API-1)

Output has separate trusted startup authority, independent of drafts and
execution. Add `--enable-progress-output --progress-binding WORKER:TASK`
for each explicitly owned native Source binding (at most 32 distinct tasks).
This works without spending authority; execution mode alone does not enable
output. `GET /api/session` adds `progress_output` and supplies a local session
token for output-only mode. Every progress GET requires that current token
and the existing exact Host/Origin checks. Default output capability is off.

The [progress API contract](../docs/BROWSER-PROGRESS-API-CONTRACT.md) defines
worker/run/output routes, exact schemas, limits, generation-bound cursors,
literal text and deterministic sensitive-line exclusions. Only latest native
attempts with owned receipts are available. Source logs remain Source output;
foreground liveness and active verification/review phase can be unknown.
Buffered verification does not imply completion, and browser acceptance stays
in the separate job API. No UI, raw-log download, terminal control, files view,
provider call or process action is added by observation. Redaction is limited;
opt in only to Source output suitable for the local browser session.

The Source checks run the complete new module/HTTP suites, existing server
and execution HTTP suites, scoped docs lint and frozen-base whitespace. The
lead controller runs all nine frozen Validate commands after Source and handles
native verification, personal review and the full merged quality gate. Version
remains 0.5.3; this source change does not establish release or acceptance.

Source preservation and checks (2026-10-07): the initial clean worktree was
`aeae9577de17d998613a82e1ee15fb5c8d325341`. Actual dependency receipts record
full-gate exit 0 and exact push of `940c376bf0cb0a34db10a7df212cdafe64984a6f`,
then docs-gate exit 0 and exact push of `aeae9577`, with the runtime tree
unchanged. Only five documentation paths differ between those dependencies.
The early coherent API/tests/docs checkpoint was saved as
`c2cffe31d4d42a1bc306ba5d89eb8b22942e0670` before slower validation. A second
checkpoint saved bounded content rechecks, native timestamp ordering and the
additional regressions as `3a5d4b3`.

The first 12-case module run had two fixture errors: its quiet case moved the
result timestamp without moving ledger evidence, and the concurrency test
shadowed Python's concurrent module. After those concrete corrections, the
changed-attempt fixture failed because its supposed new start timestamp still
predated the old log; the fixture was corrected to model native ordering.
These failures remain in the Source output. No failed unchanged test or
native task was retried to manufacture a pass.

An actual read-only observation initially returned unavailable for this live
Source. Inspection demonstrated a runtime defect in the new observer: the
native result was stamped at 08:26:12 UTC and its run_start ledger entry was
published at 08:26:14 UTC after the native snapshot completed. The observer's
one-second ordering assumption was invalid. The corrected ordering preserves
retry/result agreement and requires output to postdate both start evidences;
a permanent native-shaped regression covers the delay. The corrected live
observation reported recorded running Source, unknown foreground phase and
liveness, stale receipt and available output, without printing private output
or acquiring the worker writer lock. It made no provider/dispatch call.

The final complete progress module suite passed 18/18 in 5.448 seconds;
the final complete progress HTTP suite passed 10/10 in 8.408 seconds, both
with observation subprocess effects prohibited. The buffered-verification
regression uses one fixed local Python check child: it remains running with
empty stdout, then releases its buffered result before validation is published.
This fixture child is separate from observation and invokes no provider.
The preserved server suite passed 15/15
in 2.069 seconds. The existing execution API suite passed once, 22/22 in
82.038 seconds, retaining all original assertions/timeouts and the real offline
Git-budget journey. No existing test or execution-service behavior was changed.
Scoped docs lint and complete whitespace against the frozen dependency passed.
These are Source checks, not a native nine-command verification verdict.

Native logs lack a mutation journal: an unobserved truncate/regrow preserving
both bounded anchors can resemble append. This documented limitation remains;
observed shrink/replacement, changed anchors and same-size metadata changes
invalidate cursors. There is no perfect secret detector, current Git readiness
snapshot, live verification/review output or progress acceptance-store reader.
Buffered checks and a held lock remain unknown phase/liveness. Historical
attempts overwritten by the native layout are unavailable. Final native
verification, all nine controller Validate commands, personal complete lead
review, full merged gate and exact public push remain mandatory before acceptance.

## Worker output and worktree files (BROWSER-CONSOLE-1)

The browser console builds on the protected progress API. It does not replace
drafts, execution or the recorded Activity list. Output still requires
`--enable-progress-output`. Grants are explicit and startup-only: repeat
`--progress-binding WORKER:TASK` for a fixed task, or `--progress-worker WORKER`
for that worker's latest owned native task. The two forms share one limit of
32 unique grants. A worker grant is not an HTTP task, path or command selector.
It chooses the latest task only when the bounded ledger, result and retry
evidence agree, then applies the same task-hash, worker and attempt checks as
a fixed binding. Unknown, ambiguous or unbound output stays unavailable.

Tracked worktree text is a separate opt-in. `--enable-worker-files` and at
least one `--files-worker WORKER` are required together, with at most 32
workers. Default remains off. `GET /api/session` adds boolean `worker_files`.
Files mode supplies a session token even when drafts, execution and output are
off. The routes are `GET /api/worker-files/workers`,
`GET /api/worker-files/workers/W/files` and
`GET /api/worker-files/workers/W/files/F`. W and F are server-issued 64-hex
ids. Responses use `relative_path` for the tracked path and `worktree_label`
(`wt/WORKER`) rather than a host path. Listing comes from a fixed `git
ls-files -z` of the confirmed worktree directory descriptor
(`/proc/self/fd/N`), not a second lookup of the startup path. Stdout is
drained under a 2 second deadline measured from spawn, and at most 1 MiB plus
one byte. Deadline, overflow and errors kill and reap that owned process
group within a short grace, then release the service lock. A replaced
worktree is unavailable instead of an unrelated index. At most 256 entries
are returned. Preview reads at most 64 KiB plus one sentinel byte through
no-follow descriptors. Symlinks, special files, hardlinks, Git and auth
directories, and known secret filenames are excluded. Invalid UTF-8 is
unavailable. The view cannot edit, execute, verify or review.

The workspace page shows each granted worker's latest filtered excerpt,
observation age and recorded source, verification, review, acceptance,
liveness and phase. Quiet, missing, unavailable and connection failures keep
those names and do not become a summary or a completion claim. Choosing a
worker opens a read-only Output panel; Files is a separate tab. Polling is
GET-only, pauses while the tab is hidden, and backs off after a connection
failure. Source text stays within one bounded page of 16,384 characters.
File preview shows the returned API text literally, so a full observation
under the 64 KiB bound is not shortened or labeled as complete by that page
bound. Server file truncation is labeled at 64 KiB. A changed run or
generation resets the page explicitly. A refused session refreshes the
existing session and does not replay a launch, review or other action.

Offline checks are `bridge/tests/progress_test.py`,
`bridge/tests/progress_api_test.py`, `bridge/tests/worker_files_test.py`,
`bridge/tests/server_test.py`, `node --check bridge/worker_console.js` and
`bridge/tests/worker_console_browser.cjs`. The browser journey uses a mock
engine and must not call a provider. `tests/unio-work-policy.py` and
`tests/unio-work-policy-guard.py` are quality-gate entries owned on the
policy branch; this branch does not run or edit them. Version remains 0.5.3.
The real provider journey, the final whole release gate and publication are
still separate.

## Browser Themes and Work Map (BROWSER-THEME-MAP-1)

The workspace page supports three themes: System (default), Light, and Dark.
The chosen theme is stored locally and applied safely even if storage is
restricted. All native surfaces, UI states, output consoles, and the activity map
fully adapt to these themes using safe CSS variables without inline styles or
external assets, preserving the restrictive Content Security Policy.

A Work map view replaces the traditional flat list of tasks on large screens,
displaying a visual Project hub connected to recorded workers and their
owned tasks. The map prioritizes active, uncertain, and attention-requiring
work. A history toggle optionally reveals finished history. The view includes
deterministic layout, search, task/worker bounds, counts, and pagination (capped
at 24 expanded nodes). This uses the existing `/api/activity` feed without
backend, dependency, or route changes.

Selecting a task on the map opens its details. If the selected worker is also
granted in the local session for Source console tracking (`--progress-binding`
or `--progress-worker`), the console can be opened directly from the map
details. The detail view accurately labels if the granted protected output
belongs to a different (usually newer) task rather than implying it belongs
to the historical record you clicked on. The map is entirely read-only; it never
starts, reviews, or merges work. Observation failures clear the map alongside
the list and details.

Offline checks are included in `bridge/tests/work_map_browser.cjs`.
These UI enhancements are implemented-in-source; the published official version
remains 0.5.3.

### Browser Theme and Map Correction (BROWSER-THEME-MAP-FIX-1)

The browser map and themes underwent concrete corrections to actually resolve system theme preference dynamically, fix primary button contrast in dark mode, and enforce semantic `createElement` rendering for task details instead of interpolated HTML. The map accurately collapses only genuinely finished work lacking failed or unknown states. SVG nodes and console bindings now use exact worker and task identities instead of substring checks. Map controls, view states, and focus survive observation failures without resurrecting stale nodes, and recovery functions properly. Added worker and state filters. These corrections are verified offline via strengthened `bridge/tests/work_map_browser.cjs` checks.

### Map identity and console routing correction (BROWSER-MAP-IDENTITY-OPUS-1)

Map nodes are keyed by the exact worker/task tuple (JSON-encoded, so
`worker-1`/`TASK-10` and `worker-10`/`TASK-1` can never collide). A poll
reuses the same SVG group for the same tuple, removes only groups whose tuple
is gone and reorders around the focused group, so keyboard focus and the
selection stay on the same task when other tasks are inserted or removed.
Nodes are `role="button"` with a full `aria-label` and `aria-pressed`; Enter
and Space select them. Positions do not move when the topology is unchanged.

The details panel is built once per selected task and then updated in place,
so a focused **Clear selection** or console button survives polling. It shows
the current observation time separately from the recorded task time. When the
selected task is off-page, filtered out or no longer observed, the panel keeps
an explicit **Clear selection** action. An observation failure clears the map,
details, counts and pagination and drops the cached data; no view, filter,
search, history, paging, Fit or Reset control can bring the old state back.
**Fit view** and **Reset** are stored and reapplied after every poll; Reset
restores width and height. Worker filter options follow the observed workers.
A selected worker that disappears stays selected and is labelled
"(not in current observation)".

Only records whose process `succeeded`, validation `passed` and review
`approved` count as finished and collapse into history. That is still not your
acceptance. Running records with a held worker lock are shown as active. Every
other record needs attention and stays visible, including failed, unknown,
incomplete, not run, changes requested, completion unknown or stale evidence.
The **Finished** state filter shows finished records without the history
toggle.

A map console action is offered only when the page's console lists that exact
worker. The wording reflects that worker's actual grants: Source output and
files, output only, or files only. If the console's latest task differs from
the selected record, the action and its event name that actual latest task as
a different/latest task. The console accepts only a plain `{worker, task}`
detail that exactly matches a listed button, reuses its normal selection path
(opening Files for a files-only worker) and scrolls without animation when
reduced motion is preferred. The theme selector uses the live chosen preference
as authority, so an explicit Light or Dark choice ignores OS changes even when
storage is denied. Malformed stored values fall back to System.

Checks: `bridge/tests/work_map_browser.cjs`, the extended
`bridge/tests/worker_console_browser.cjs` (real `--progress-worker` and
`--files-worker` grants under the server's unchanged CSP) and
`bridge/tests/browser.cjs`. No backend, API, grant or dependency changed. The
published official version remains 0.5.3.
