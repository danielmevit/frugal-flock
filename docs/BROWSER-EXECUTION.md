# Browser execution service — Unio 0.5.3

The stdlib library in bridge/execution_service.py implements the service slice
of [the frozen browser contract](BROWSER-EXECUTION-CONTRACT.md). It composes
PlanStore and schema-2 JobStore with explicit native operations. The HTTP
routes and browser controls are separate slices; this checkpoint does not
claim the browser milestone or its live demonstration is complete.

## Startup and preparation

Construct ExecutionService(workspace, engine, worker, reviewer, config_dir,
template_path, worker_company, reviewer_company) using owner-selected startup
values. The workspace contains repo/, coord/ and wt/. The executable, template
and configuration must use real paths and regular files. Company labels must
differ; labels do not authenticate a provider. Call close() when finished.

The worker must already exist on its agent branch and share the repository's
Git common directory. Preparation and the first start require a clean worker
at the current configured base in coord/base (main when absent). Hidden index
flags, sparse checkout and unmerged entries are refused. Opening the service
does not require this initial cleanliness, so already started jobs remain
inspectable after work has changed. No operation synchronizes a branch.

The owner supplies a JSON template with exactly schema_version, instructions,
scope and validate. For example:

```json
{
  "schema_version": 1,
  "instructions": "Implement the saved request within this fixed scope.",
  "scope": ["source.txt"],
  "validate": ["test -s 'source.txt'"]
}
```

Instructions contain 1 through 12000 characters. Scope contains 1 through 100
distinct relative paths without traversal, controls or line breaks. Validate
contains 1 through 30 nonempty single-line owner-authored commands, each at
most 2000 characters. The template cannot contain native Allowed scope or
Validate headings in its instructions. Saved requests are compiled as one
JSON string, with escaped newlines and Unicode separators, followed by the
instructions and fixed native sections. Browser prose cannot replace scope,
checks, provider selections or startup paths.

prepare(draft_id, expected_hash, request_key) checks the exact saved draft,
enqueues it for the configured worker, and persists its complete immutable
binding. Its preview includes the literal request, task ID/hash, scope,
checks, worker/reviewer and company labels. preview_hash is SHA-256 of the
sorted, compact, ASCII JSON preview with the preview_hash field omitted and
without a trailing newline. Preparation does not publish a native task or
invoke an engine. Identical request-key replay returns the same binding;
conflicting reuse refuses.

## Explicit operations

- approve(job_id, expected_hash, approval_key, preview_hash) rechecks the
  draft, preview and bindings, then uses JobStore's approval transition.
- start(job_id, approval_key, reservation_key) reserves the approved job,
  persists intent, exclusively publishes coord/tasks/ui-JOBID.md and calls
  the fixed executable with run, -b, worker and task ID as separate arguments.
  Only newly_reserved=true authorizes that call. Exit zero means the launcher
  accepted the request; it does not establish completed AI work.
- verify(job_id, action_key) requires current successful ended native process
  evidence and checks the exact task/template/configuration/engine bindings
  before any Validate command. It calls native verify once for that key and
  retains its actual exit in the private action record.
- review(job_id, action_key) requires current passed verification and reserves
  one paid review intent per job before calling native review. A duplicate,
  another key, concurrent request or service restart cannot buy a second
  review. Failure or uncertainty requires another explicitly scoped task.
- accept(job_id, revision_hash, action_key) requires current nonstale readiness
  and the exact candidate commit. It records the entire current revision,
  including base, candidate, task hash and worktree hash. It leaves native
  human and integration fields untouched and performs no merge or install.
- stop(job_id, action_key) calls native kill with this binding's task ID only.
  An uncertain termination remains unknown and retains worker ownership.
- cancel(job_id) cancels an unreserved waiting or approved job and releases
  its binding. It never asserts that a worker was killed.
- get(job_id) and jobs() expose only jobs with service bindings. They may read
  the bounded native result; they cannot run, approve, review, repair ownership
  or retry. jobs() preserves the queue's creation-time/ID ordering.

Opaque IDs and action keys are 32 lowercase hex characters. Draft/preview/task
hashes are 64 lowercase hex characters. Acceptance uses a 40- or 64-character
lowercase Git object ID. Public methods accept only their fixed arguments.

## Persistence, restart and evidence

Validated bindings, worker ownership, action intents and outcomes live under
coord/ui-execution/. A process-safe lock serializes service writers; each
operation opens its own JobStore connection. Files are published atomically,
fsynced and bounded, with symlink and special-file refusal. Immutable task and
request/scope/check companions allow the full template limits while keeping
each JSON document within 128 KiB. A worker has one
active binding. Only explicit cancellation before reservation or current
acceptance releases it. Reading, restart and an unresolved response never
release an uncertain binding or start another attempt.

Intents bind the action key, job, immutable binding, inputs and relevant full
revision. Identical replay returns recorded/current state without invoking
the action again. Conflicting reuse refuses. A launcher timeout or possible
start failure uses JobStore.mark_unknown and never requeues. An interrupted
intent remains unknown after restart, even when a later read finds output.
Raw launcher/check/reviewer output and credentials are not durable public
records. Native logs remain native private artifacts.

The public view has exactly schema_version, job, preview, execution,
native_result, acceptance and warnings. Job is the exact schema-2 queue row.
execution contains state and launcher_exit. Native result is null if missing,
unavailable or malformed; otherwise only the fixed contract fields and nested
evidence are exposed. Arbitrary producer fields, raw logs and native human or
integration sections are omitted. Reasons must be existing fixed native codes.

Readiness requires a succeeded process with exit zero, passed validation with
scope OK and at least one check and zero failures, and an approved review with
exit zero and complete material. Every evidence revision must equal the
current revision, and stale must be false. A producer's ready flag alone,
launcher receipt or old report prose cannot establish readiness. Acceptance
becomes stale after any full revision or binding change. Reads show fixed
warnings for missing, invalid, stale or unknown evidence without private text.

ExecutionError exposes only code and status. Invalid inputs return
invalid_request/400; missing bound jobs return job_not_found/404. Conflicts,
staleness, STOP, unavailable workers, missing readiness and uncertainty use
the contract's fixed 409 codes. Storage and native availability failures use
storage_unavailable/503 and native_unavailable/503. Internal error text never
becomes a public warning or error message.

## Bounds and execution boundary

Configuration hashes cover recursively read regular files, including a native
project-local coord/agents.conf override, with at most 128 files and 8 MiB in
total. Template and durable JSON documents are limited to 128 KiB; compiled
task artifacts are bounded to 1 MiB. Native
capture is bounded while draining stdout/stderr, with a 1 MiB combined cap.
Deadlines are result 15 seconds, run launch 30 seconds, verify 900 seconds,
review 1200 seconds and kill 30 seconds. Timeout never grants a retry.

Subprocesses use argument lists, closed stdin and cwd=workspace/repo, with
UNIO_CONF_DIR fixed to startup configuration and UNIO_AUTO_OFF,
UNIO_AUTO_VERIFY and UNIO_AUTO_SYNC all set to zero. Owner-authored native
checks and configured agents have the existing trusted-host boundary; Git
worktrees are not operating-system sandboxes. There is no automatic paid
retry, fallback, sync, resume, publication or integration.

## Offline verification

The suite uses real PlanStore/JobStore, disposable Git repositories/worktrees
and a strict executable native mock. It covers every method, the complete
queue-backed run/verify/review/result/accept flow, two-process starts/reviews,
lost responses, restart and unresolved intents, binding drift, hidden edits,
malicious request headings/selectors, malformed output, bounded calls,
acceptance invalidation and no provider effects from preparation, approval,
reads, listing or reopening. No real provider is called.

```text
TMPDIR='/mnt/d/Vibe Coding/_vm/frugal-flock/tmp' python3 -B bridge/tests/execution_service_test.py
```

The suite is registered in tools/quality-check.sh alongside the existing
bridge and native suites. Independent Google and Anthropic reviews, followed
by the lead overview and final merged-tree gate, remain lead-owned work.
