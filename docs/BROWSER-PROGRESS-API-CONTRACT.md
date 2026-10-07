# Protected native progress API — schema 1

BROWSER-PROGRESS-API-1 adds a Source output observer to the source bridge at
version 0.5.3. This contract describes the implemented backend for the later
console worker. No console UI, files view, terminal input or process control
is implemented here. The [execution contract](BROWSER-EXECUTION-CONTRACT.md)
retains its existing authority and routes.

## Startup authority and discovery

Output requires its own trusted startup switch and allowlist:

```bash
python3 -B bridge/server.py --project '/path/to/workspace' \
  --engine '/path/to/native/unio' --enable-progress-output \
  --progress-binding 'codex-owned:SOURCE-1'
```

Repeat `--progress-binding WORKER:TASK` for up to 32 distinct tasks. Labels
must match `[A-Za-z0-9][A-Za-z0-9_-]{0,79}`. A task may appear only once,
because native Source output is task-named, not worker-named. Missing,
partial, ambiguous or invalid output settings refuse startup. These entries
are explicit owner grants for those known native workers/tasks; they are not
browser selectors. The fixed engine path is used only to check background
PID identity; progress never invokes it. Workspace, engine and bindings
are chosen by trusted startup, never HTTP. No auth or agent configuration
is read by progress.

Output mode is independent of manual drafts and execution. It can operate
with no spending authority. Draft or execution mode alone never grants output
visibility. Default mode remains off. Old ActivityServer callers retain their
arguments; its optional final `progress` argument accepts ProgressService.
Shutdown closes the observer's workspace descriptor without stopping workers.

`GET /api/session` retains schema_version, manual_drafts, execution and token,
and adds `progress_output`, a boolean. Token is non-null when any explicit
protected capability is enabled, including output alone. A client discovers
capability here, then supplies the current `X-Unio-Session` to every progress
GET. Session retrieval itself does not observe logs. Refresh/session rotation
is read-only; rejected sessions must be refreshed explicitly, without action
replay. Session rotation leaves valid output cursors usable in that same server.

## Routes and strict requests

All routes require exact loopback Host and exactly one current session header.
An omitted Origin is allowed for GET; a supplied Origin must exactly match the
server's bound origin. Duplicate Host, Origin or session headers refuse.
All responses are no-store JSON with nosniff and the bridge security headers.
No progress GET accepts Content-Length or Transfer-Encoding, including zero
length; bodies and ambiguous framing refuse without reads. Progress routes
accept GET only. POST and other supported mutation methods return 405.
Existing execution POST body/framing, mode, Origin and session checks remain.

| GET route | Response |
| --- | --- |
| `/api/progress/workers` | `{schema_version:1, workers:[view-or-unavailable]}` |
| `/api/progress/workers/W` | Current latest bound attempt view |
| `/api/progress/workers/W/runs` | `{schema_version:1, runs:[view]}`; at most one latest attempt |
| `/api/progress/workers/W/runs/R` | View only if R is still this binding's latest attempt |
| `/api/progress/workers/W/runs/R/output` | View with output page from byte zero |
| `/api/progress/workers/W/runs/R/output?cursor=C` | View with the next bounded page |

W and R are exactly 64 lowercase hex characters. C is 1..512 base64url
characters without padding. No other query, duplicate query, trailing slash,
percent encoding, unknown path segment, body, limit, path, root, executable,
ref, alias or command selector is accepted. Unknown valid identifiers return
404. Old native attempts are unavailable after retry state replaces them;
the task log is not historical run storage. Earlier pages within the current
log generation remain readable by retaining a previously returned cursor or
requesting byte zero again.

## Ownership and native receipts

Progress reads only explicitly bound `wt/WORKER` directory existence,
`coord/tasks/TASK.md`, `coord/results/WORKER/TASK.json`,
`coord/retries/TASK/state.json`, a bounded tail of `coord/reports/ledger.jsonl`,
`coord/reports/TASK.log` and optional `coord/reports/TASK.pid`. No worker lock
is opened or acquired. Fixed component traversal uses directory descriptors
and no-follow opens, rejects symlinks at every component, special files and
hard-linked files. A worktree directory alone does not grant visibility:
matching native result, genuine retry UUID, matching Source task hash and
latest owned run_start ledger evidence are also required. These are trusted
local native receipts, not cryptographic proof against a local account owner
who can forge all evidence. Worktree contents and Git internals are not read.

Native schema 1 result sections use the execution service's existing strict
validator and whitelist. Duplicate JSON keys, unsupported states/reasons,
inconsistent exits/readiness, corrupt retry state, changed task bytes,
foreign latest run_start, a task with retry entries for multiple workers,
missing receipts or evidence outside the bounded ledger window refuse.
Review raw directories, peer material, handoffs, native auth/configuration,
Git internals, reports Markdown and arbitrary logs are excluded.

W is SHA-256 of worker, NUL and task. R is SHA-256 of W, the genuine latest
retry attempt UUID and Source task SHA-256. No UUID is guessed from a PID,
lock, prose or elapsed time. When native process state is running, log mtime
must be at least both the running receipt and latest run_start timestamps:
this rejects the old log in
the native interval between publishing start evidence and opening/truncating
Source output. For ended Source, log mtime must fall between its latest
run_start timestamp and the result update timestamp. Retry/result ordering and pending/state must also agree. Native update
stamps precede its final snapshot and ledger publication, so a running
run_start can legitimately be later than its result timestamp; no invented
one-second startup bound is applied. Uncertain logs remain unavailable.

The inspected live Source receipt had recorded running state, a genuine
32-hex retry UUID, a task-named Source log and no PID file.
Actual foreground parent PIDs matched the installed engine SHA-256
`002c8e65f0d559870fcc15c34edddb9ad5dff78aff2dc49e82e658c807be4275`.
The installed runner and dependency source differ in version/prompt transport
areas; inspected receipt/log/lock layouts agree. No engine change is needed.

## Exact view schema and truthful lifecycle

A full view has exactly these fields:

```text
schema_version, worker_id, worker, task, run_id, observed_at, recorded_at,
observation_stale, source, verification, review, acceptance,
recorded_evidence_stale, observed_liveness, observed_phase, output
```

schema_version is integer 1. Identifiers and labels are strings as above.
Dates are timezone-aware ISO 8601 strings. observation_stale is a boolean,
true when the receipt update is more than 30 seconds old. observed_at is the
current successful observation time; recorded_at is the native update time.
recorded_evidence_stale is the native validated stale boolean, not a fresh
Git snapshot. No observation recomputes current worktree revisions or native
readiness. A changed worktree may make otherwise recent recorded evidence
outdated. These observations are independent snapshots, not atomic lifecycle
transitions or proof of current readiness.

source is exactly state, exit_code, revision; verification is exactly state,
scope, checks_run, checks_failed, reasons, revision; review is exactly state,
reviewer, process_exit_code, material_complete, reasons, revision. These are
recorded, strictly validated native evidence, with states and revision schema
from the frozen execution contract. No private producer extras are returned.
Acceptance is exactly `{state:"unavailable"}`. Native human pending is not
browser acceptance evidence; this observer does not inspect execution-service
acceptance records. Use the existing protected job API for that separate
evidence when execution authority is enabled.

observed_liveness is running or unknown. Running requires the optional native
background PID file plus bounded `/proc/PID/cmdline` identity with exact
`bash ENGINE run WORKER TASK` argument boundaries and cwd=workspace/repo.
Only that matching observation together with recorded running Source
sets observed_phase to source. An ended Source runner may still be alive
during later phases; its observed phase remains unknown.
Otherwise phase and liveness are unknown. A missing or reused PID, no PID,
ended result or held worker lock does not prove that all children ended.
Foreground Source has no PID file. Verification and review share the worker
lock and publish no reliable running marker. Verification buffers check
output/results until checks end. Consequently its active phase, liveness and
live output stay unavailable; old Source output is never labelled verification
output. Recorded succeeded requires actual native exit zero; failed exposes
its recorded nonzero or unknown exit. Prose saying done has no state effect.
No percentage, inferred timeout progress or AI summary exists.

The workers collection substitutes an unavailable object for unreadable
binding evidence, with exactly schema_version, worker_id, worker, task and
state="unavailable". A direct request for that binding returns 503 instead.
A fresh failed request must be treated as connection/observation failure;
it does not grant fresh age to the client's earlier cached snapshot.

## Output and cursor semantics

Output has exactly state, generation, observed_at, modified_at, excerpt,
text, next_cursor, at_end and partial_record. State is available, quiet,
first_output_wait, missing or unavailable. Quiet means log mtime older than
30 seconds; it does not mean failure or completion. Empty logs mean first
output wait, including buffering; only lifecycle receipts establish execution
success/failure. Missing means no Source log. Unsafe or unbound logs mean
unavailable. generation, modified_at, next_cursor and at_end are null when
missing/unavailable; excerpt/text are empty and partial_record is false.

Available pages use a random 64-hex generation, log modification ISO date,
signed opaque next_cursor, boolean at_end and boolean partial_record.
Worker/run views return only a bounded tail excerpt; output routes return
text and an empty excerpt. at_end means the consumed byte offset equals this
observation's file size, not execution completion. A short incomplete record
is held until newline, including partial UTF-8. An unterminated final record
remains partial even after recorded Source exit. Invalid complete UTF-8
records are replaced by a fixed exclusion notice.

Cursors are server-HMAC authenticated and bind R, generation, byte offset
and long-record discard state. Clients must treat them as opaque, never
construct byte positions. Reusing an earlier cursor is a stable earlier page
within the same generation; appends do not advance another client's cursor.
Reads never rescan the complete Source log. Long records are discarded in
bounded chunks until newline. The excerpt discards a partial leading record.
Partial trailing data can cause an empty page with the same byte position;
clients should wait for another observation, not busy-loop.

Observed truncation, inode replacement, changed prefix/end anchors, same-size
metadata change or changed native attempt starts a new generation. A missing
or refused log invalidates remembered generation. Earlier cursors then return
409; they never silently reset or join another attempt. Generation changes
identify replacement/rotation without claiming preserved historical output.
There is no filesystem mutation journal: a truncate-and-regrow wholly between
observations that preserves both bounded anchors and looks like an append is
not distinguishable from an append in this native layout. Identical rewritten
bytes are likewise indistinguishable. Native Source writes append-only within
an attempt; arbitrary local rewrites are outside that writer contract. Server
restart rotates the cursor signing key and generations: old cursors refuse;
a client rediscovers the same latest R and explicitly requests byte zero.

## Limits and sensitive-output policy

Each operation has a cooperative two-second deadline including lock wait.
Regular local filesystem syscalls cannot be preempted by Python; a stalled
filesystem can exceed that wall deadline before a fixed 503 is returned.
There are at most 32 startup bindings and 32 remembered generations. Each
receipt/task read is at most 128 KiB. Each ledger read is at most the last
64 KiB and at most 256 complete records; older ownership is unavailable.
Each Source page/excerpt reads at most 16 KiB and rechecks that same
bounded window once, plus bounded 256-byte prefix and end anchors. Public
page text is at most 16384 Unicode characters, including exclusion notices;
record boundaries advance only for the returned records. The excerpt is at most 1024 Unicode characters. Complete
records over 4096 bytes are replaced with a fixed notice. Each successful
view rechecks ownership, file identity and the captured content after the output read; collection reads check the
deadline between bindings. All capture bounds apply before decoding.

ANSI CSI/OSC and complete terminal string escapes are removed. Other control,
format and surrogate characters are removed, retaining tab/newline. Text is
JSON data: emitted HTML and ordinary links stay literal untrusted text.
Consumers must use textContent or equivalent; never HTML insertion, link
activation, command execution or terminal interpretation.

Deterministic whole-line exclusions cover authorization, bearer credentials,
password/passwd/secret, common API-key and access/refresh/session-token labels,
private-key markers, agents.conf, .ssh/.git paths, peer-review/material labels,
URLs containing user/password, known sk-/GitHub/AWS key prefixes, long token
strings and standalone base64-looking lines of 32 or more characters. These
rules run per complete bounded record, before serving it. Notices are fixed,
not private exception text. Short unlabeled secrets, split/multiline values,
unknown credential formats and arbitrary prose can evade these rules; benign
lines can be excluded. This is bounded filtered output, not unrestricted raw
logs or a promise of perfect secret detection. Owners must opt in only for
Source output appropriate for their local browser session.

## Fixed errors and effects

JSON errors have exactly schema_version=1 and error, a fixed string:

| Status | Errors |
| --- | --- |
| 400 | invalid_request |
| 403 | host_refused, origin_refused, session_refused |
| 404 | not_found when capability is off; progress_not_found for unknown owned IDs |
| 405 | read_only |
| 409 | cursor_mismatch |
| 503 | progress_unavailable |

No private exception, path, command, credential or arbitrary producer text
appears in an error. Every progress route and session discovery is an
observation only: no native invocation, provider call, dispatch, run, verify,
review, accept, retry, restart, signal, process stop, writer lock or project
write. Offline module/HTTP tests use native-shaped receipts and mock process
identity, refuse subprocess effects, and cover the supported uncertainty and
output cases. Full native verification, personal lead review and the merged
quality gate remain separate delivery requirements.
