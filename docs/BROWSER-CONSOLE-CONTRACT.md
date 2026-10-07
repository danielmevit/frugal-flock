# Browser worker output and files — frozen interface

Implementation contract for completing the browser 0.5.3 milestone. Existing
UI, execution API and [progress API](BROWSER-PROGRESS-API-CONTRACT.md) remain
the base. The interface below stays frozen. Implementation status is recorded
at the end of this document.

## Worker output

Show the latest actual filtered Source excerpt, observation age and recorded
state for each explicitly enabled worker. Clicking opens a read-only output
panel with bounded pages from the existing API. Render literal text only;
no terminal input, command execution, automatic links or invented AI summary.
Keep connection/liveness distinct from native Source, verification, review
and acceptance. Empty/quiet output does not prove completion or failure.

Add trusted startup `--progress-worker WORKER` grants for browser-generated
tasks. Keep existing `--progress-binding WORKER:TASK`. Total grants at most32,
unique and validated. Either grant requires `--enable-progress-output`; no
grant is derived from HTTP. A worker grant selects its latest owned native
run from bounded genuine ledger/result/retry evidence. It must pass the same
task-hash/worker/attempt checks as fixed bindings. Unknown, ambiguous, stale
or unbound output remains unavailable; no arbitrary-task or host-path access.

Existing progress view/output schemas, redaction, cursor ownership, bounds
and GET protections remain unchanged. Worker discovery yields server-issued
IDs; the UI rediscovers when the latest task changes. Source-only observation
works without execution authority. It makes no provider or native command call.

## Optional worktree files

Separate trusted startup `--enable-worker-files` and repeatable
`--files-worker WORKER` grants (at most32), required together. Default off.
Add boolean `worker_files` to session discovery, default false; enabled files
need a session token even without drafts/execution/output. All file API GETs
share exact Host/Origin/session checks, no request bodies, no-store headers
and read-only method refusals. Existing spending routes remain unchanged.

| GET route | Schema1 response |
| --- | --- |
| `/api/worker-files/workers` | workers: list of worker_id, worker and worktree_label (`wt/WORKER`) |
| `/api/worker-files/workers/W/files` | worker_id, worker, files: list of file_id and relative path, plus truncated boolean |
| `/api/worker-files/workers/W/files/F` | worker_id, file_id, relative path, observed_at, text and truncated boolean |

W/F are opaque64-lowercase-hex IDs supplied by discovery; they never accept a
path, executable, ref, command or root. Trusted worker worktrees are fixed at
startup. Files are selected only from tracked source text, maximum256 entries
and64KiB preview bytes plus one sentinel byte. Use bounded fixed-argument Git
listing of the confirmed worktree directory descriptor. Drain its stdout under
a 2 second deadline from spawn, at most 1 MiB plus one byte, and kill and reap
that process group on deadline, overflow or error. A replaced worktree is
unavailable. Never interpolate HTTP text into a command.
Use no-follow descriptor traversal for content, reject unsafe components,
symlinks, special files and hardlinks. Exclude Git/auth/credential paths and
known secret filenames; binary/invalid UTF-8 content is unavailable. File
view is an observation, not an atomic revision or acceptance proof. Filename
exclusions do not establish that arbitrary source text is secret-free.

File errors are fixed schema1 error objects: invalid_request400,
host_refused/origin_refused/session_refused403, files_not_found404,
read_only405 and files_unavailable503. Capability off returns not_found404.
No private exception, absolute path, command or credentials in errors.
Listing/preview cannot write, invoke a provider, verify/review or control a
process. Source filenames/content remain literal text in the browser. File preview
shows the returned text in full; the separate Source page bound must not
shorten it or call that shortening a full observation. Server truncation stays
labeled at 64 KiB.

## UI and delivery

Keep the existing UI design and workflow. Add worker output and files panels
with clear disabled/unavailable/connection states. Automatic polling must not
repeat a failed action, renew cached evidence age, busy-loop on partial output
or accumulate unlimited text. Preserve selected worker/page when appropriate;
reset explicitly on changed run/generation. Session failures follow existing
explicit refresh with no action replay.

A focused offline module/HTTP suite and one Chromium journey exercise a mock
native worker writing progressive lines, output click-through, safe file view,
session rotation and no duplicate launch/review. This is not a model benchmark.
The owner will use funded main implementation workers; free Zen routes remain
routine support only. Full release gate, real provider journey and publication
are separate proof. No claim 0.5.3 released until those steps actually complete.

## Implementation status

BROWSER-CONSOLE-1 implements the worker grants, file routes and browser
panels specified above. Existing progress views, cursors, redaction, read
bounds and GET protections are unchanged. A worker grant resolves only the
latest owned native task; a files grant lists only tracked text under the
startup worktree. This source change is not a 0.5.3 release. The real
provider journey, the final whole release gate and publication remain
separate.
