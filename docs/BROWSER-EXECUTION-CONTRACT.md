# Unio 0.5.3 browser execution contract

Frozen by Codex lead on 2026-10-05 23:02:22 +0200 against gated Unio 0.5.2
source 1bddeabfa25db09522020f238febb89fced92cde. The owner approved this
milestone and its bounded native demonstration. Each worker receives a
separate exact task; this contract alone does not launch a provider.

## Outcome and startup authority

One saved request can become an explicitly approved native task, run once,
be verified, receive another company's review and be accepted at its current
revision. Acceptance does not merge, install or publish. Default Activity
remains read-only; manual-only mode stores drafts without worker calls.

ExecutionService(workspace, engine, worker, reviewer, config_dir,
template_path, worker_company, reviewer_company) is a Python stdlib service.
All arguments come from trusted startup, never HTTP request selectors.
The companies are explicit configuration labels and must differ; they do
not authenticate a provider. The engine is a fixed executable. Its calls
use an argv list with cwd=workspace/repo, stdin closed, bounded output and
deadlines, UNIO_CONF_DIR=config_dir, UNIO_AUTO_OFF=0, UNIO_AUTO_VERIFY=0 and
UNIO_AUTO_SYNC=0. No shell interpolation or automatic resume/sync/retry.

The real workspace has repo/, coord/ and wt/. The worker must already exist
on `agent/<worker>`, clean at the configured project's current base before
preparation and first start, with no unmerged entries, sparse checkout or
assume-unchanged/skip-worktree flags hiding tracked edits. Startup must still permit inspecting already
started jobs on a changed worker; it must not require a clean branch just to
read/restart the service. Identical start replay reads its recorded attempt
without demanding the original clean snapshot again. Refuse unsupported paths, symlink state,
corrupt records, STOP or uncertain worker ownership. One active binding per
worker; no overlapping writers. Explicit cancel before reservation or a current
accept releases that binding for a future job. An unresolved/unknown binding
remains owned and cannot be replaced by preparation or a service restart. Startup/read/restart never starts a task.

The bounded JSON template has exactly schema_version=1, instructions,
scope and validate. Instructions are 1..12000 characters, scope contains
1..100 distinct relative paths without traversal, control characters or
line breaks, and validate contains 1..30 nonempty single-line owner-authored
commands of at most 2000 characters each. Commands remain trusted startup
configuration. Neither browser text nor a job can replace them.

Compile a complete task with the saved request as a single JSON string,
then the template instructions and fixed Allowed scope/Validate sections.
Request newlines must never become machine-readable task headings. Refuse
template instructions containing machine-readable Allowed scope/Validate
section headings, so the compiled task has exactly the intended sections
and the preview matches the native parser. Startup configuration is trusted
input, but ambiguous task compilation is still refused. Task ID
is `ui-<job_id>`; write `coord/tasks/<task_id>.md` exclusively and refuse existing
conflicting bytes. Do not change the queue-library interface or invoke AI
planning while preparing a preview.

## Durable binding and operations

Use JobStore schema 2 and PlanStore as frozen at the gated queue checkpoint.
Open a JobStore in each calling thread/operation. Use a process-safe lock
and durable validated records under coord/ui-execution/ for bindings,
worker ownership and action intents/outcomes. File publication is atomic,
bounded and refuses symlinks. Keep credentials and raw private logs out of
these records and HTTP. close() releases this service's owned descriptors.

An immutable binding includes draft ID/hash, initial base/worker revisions,
worker/reviewer/company labels, compiled task bytes/hash and template,
engine and config-content hashes. Hash regular configuration files recursively, at most 128 files and 8 MiB
total; refuse symlink inputs and special files. Limit template and durable
JSON documents to 128 KiB each, native JSON/stdout to 1 MiB and native calls
to bounded deadlines (result 15s, run launch 30s, verify 900s, review 1200s,
kill 30s). Bound capture while reading; checking length after an unbounded
capture is insufficient. On timeout do not repeat a possibly started action. Approval and actions must recheck current bindings.
preview_hash is SHA-256 over the canonical public preview without that hash
field. Store it durably. No action trusts a task hash printed in worker prose.

Methods take positional or keyword arguments with these exact names. Opaque
IDs/action keys are 32-character lowercase hex; hashes are 64-character
lowercase hex. All methods below except jobs() and close() return a job view.

| Method | Arguments after self | Required behavior |
| --- | --- | --- |
| prepare | draft_id, expected_hash, request_key | Enqueue the exact saved draft for the fixed worker and persist its complete binding. Identical replay returns it; conflicts refuse. No provider call. |
| approve | job_id, expected_hash, approval_key, preview_hash | Recheck preview/draft/bindings and call the queue's approval transition. No native run. |
| start | job_id, approval_key, reservation_key | Recheck STOP, draft, immutable bindings and clean initial worker; reserve under ownership. Only newly_reserved=true may publish and call fixed engine run -b worker task_id argv. Persist intent before that call. Replay never starts again, even after lost response/restart. |
| verify | job_id, action_key | Check immutable task, template, config and engine before any Validate command. Require ended successful native process; call fixed native verify once for this key, retain real exit, and read current result. |
| review | job_id, action_key | Require current passed verification. Durably reserve exactly one paid review per job before invoking fixed native review worker task_id reviewer. Concurrent callers, duplicate/new keys and restart cannot spend a second time. Preserve failures/uncertainty; correction requires another explicitly scoped task. |
| accept | job_id, revision_hash, action_key | Require current nonstale ready_for_human_review=true. revision_hash is current_revision.candidate_commit (40 or 64 lowercase hex Git object ID). Record acceptance for the entire current_revision, never edit native human/integration fields. |
| stop | job_id, action_key | Explicit native kill of this binding's task only. Retain uncertainty when completion/termination cannot be established. No broad process matching. |
| cancel | job_id | Queue cancellation of an unreserved waiting/approved job only; replay idempotent. Never claim that cancellation killed a possibly live worker. |
| get | job_id | Read honest stored state and bounded current native result; no run/review/approval/provider effect. |
| jobs | none | Return a list of job views in the queue's creation-time/ID order. |

Durable action records bind key, inputs and revision; identical replay returns
recorded/current view without repeating its operation. Conflicting keys or
inputs refuse. A launcher exit zero is launch acceptance, not worker success.
After possible-started failure record completion_unknown using mark_unknown;
never requeue. Restart with an unresolved action intent remains unknown and
does not grant another attempt. Reads can reconcile evidence but cannot clear
unknown ownership automatically. Allow GET to show stale/unknown evidence
without running validation or silently repairing an immutable binding.

Accept only well-formed native schema-1 result documents for this worker and
task. Verify/review need current_revision equality with evidence sections.
Acceptance is stale after any revision/binding change. No missing native
result, launcher receipt or old report text can imply current readiness.

Only jobs with this service's durable bindings are exposed by get/jobs; an
unbound queue row is job_not_found, not authority to synthesize a task.

## Public view and errors

Each view has exactly schema_version=1, job, preview, execution,
native_result, acceptance and warnings. Job is the queue's exact validated
schema-2 record. Preview has exactly request, task_id, task_sha256,
preview_hash, scope, validate, worker, reviewer, worker_company and
reviewer_company. It intentionally exposes the exact owner-selected scope
and check commands. Engine/config/template host paths and private logs remain
internal; the template owner must choose commands suitable for local preview.

execution has exactly state and launcher_exit. State is not_started,
launch_accepted, launch_failed or completion_unknown; exit is integer or null.
native_result is null when unavailable, otherwise the fixed native schema-1
fields worker, task, updated_at, current_revision, process, validation,
review, stale and ready_for_human_review. Whitelist and validate nested native evidence: current_revision and each
non-null evidence revision have exactly base_commit, candidate_commit,
task_sha256 and worktree_sha256. Git IDs are 40/64 lowercase hex; hashes 64.
Process exposes state, exit_code and revision; validation exposes state,
scope, checks_run, checks_failed, reasons and revision; review exposes state,
reviewer, process_exit_code, material_complete, reasons and revision. Check
explicit native states (process: not_run/running/succeeded/failed;
validation: not_run/passed/failed/incomplete; review:
not_run/approved/changes_requested/unknown/failed), exact scope states,
numeric/bool types, bounded lists/strings and readiness consistency: succeeded process exit 0, passed validation scope OK and zero
failures, at least one check and no passed-validation reasons, approved review exit
0/material_complete true with no decision reasons, all three evidence
revisions equal current_revision and stale false are required for readiness.
Native reason lists accept only the existing fixed codes: missing_scope,
missing_validate, scope_violation, check_failed, empty_work, task_tampered,
candidate_changed_during_validation, reviewer_process_failed, unknown_verdict
and candidate_changed_during_review. Unsupported reason text makes the
result unavailable with a fixed warning, never exposes private strings.
Do not trust a producer's ready flag alone. Omit human, integration, raw logs
and arbitrary extra producer fields.
acceptance has exactly state (pending, accepted, stale) and revision (null or
the accepted full current_revision). warnings is a bounded list of fixed
messages; no raw exception text, commands, credentials or filesystem paths.

ExecutionError has code and status attributes. Allowed codes/statuses:
invalid_request/400, job_not_found/404, conflict/409,
draft_stale/409, binding_stale/409, worker_unavailable/409,
stopped/409, not_ready/409, outcome_unknown/409, storage_unavailable/503 and
native_unavailable/503. Wrap internal OS/SQLite/native errors into these
public errors while retaining truthful private evidence. No automatic retry.

## HTTP and browser contract

ActivityServer(port, observer, plans=None, execution=None) retains its old
callers. --enable-execution also enables manual drafts. It requires --worker,
--reviewer, --worker-company, --reviewer-company, --config-dir and
--task-template, plus existing --project/--engine. Partial execution settings
without explicit mode refuse at startup. Session JSON adds execution bool;
token exists only when drafts/execution are explicitly enabled. Close the
execution service on shutdown. All mode labels must describe actual behavior.

All execution routes require exact loopback Host and current X-Unio-Session.
POST needs exact same-origin Origin; GET may omit Origin but must reject a
supplied mismatch. Reuse duplicate-key, framing, 32768-byte and body-deadline
guards. Strictly refuse unknown fields/query/path selectors without effects.
Return no-store schema-1 JSON and fixed errors. No mutation on GET/session.

| Route | Exact request fields | Response |
| --- | --- | --- |
| GET /api/jobs | none | 200 {schema_version:1,jobs:[views]} |
| GET /api/jobs/ID | none | 200 view |
| POST /api/jobs | draft_id, expected_hash, request_key | 201 view |
| POST /api/jobs/ID/approve | expected_hash, approval_key, preview_hash | 200 view |
| POST /api/jobs/ID/start | approval_key, reservation_key | 200 view |
| POST /api/jobs/ID/verify, review, stop | action_key | 200 view |
| POST /api/jobs/ID/accept | revision_hash, action_key | 200 view |
| POST /api/jobs/ID/cancel | empty object | 200 view |

Serve jobs.js and extend the existing Activity/draft page. In default/manual
modes hide all execution controls and preserve existing journeys. In explicit
execution mode a saved/reopened draft can be prepared, inspected, approved,
started, verified, reviewed and accepted through visible separate actions.
Support reopen by job ID and explicit refresh/stop/cancel. Show request,
scope/checks/provider labels before approval. Store stable opaque action keys
and job context so lost responses/reload do not silently create new attempts.
Refresh/session rotation may read state but must never retry a POST. Guard
double clicks, keep text/context on failure and render data as literal text.
Keyboard access and busy/status announcements must remain usable. Missing
evidence and uncertainty remain visible. Do not invent progress, quota,
authenticated human approval, process success or integration.

## Slices and evidence

1. ExecutionService, stdlib tests, execution docs/fragment, version/assertion
   0.5.3 and quality-gate registration. No server/browser edits.
2. Server startup/routes, HTTP tests, bridge README and fragment. No service
   or browser edits; use the exact service interface above.
3. jobs.js, index.html, activity.css, Chromium journey and fragment. No
   server/service changes; use exact API/view fields. Existing draft code may
   expose a literal saved-draft event only if needed by this slice, with old
   manual behavior preserved and retested.

Each slice gets native verify, two independent companies' reviews, lead review and
full merged-tree quality gate/push before its dependent slice is dispatched.
Version remains 0.5.3 throughout; do not claim it complete before all slices
and the demonstration pass. Automated checks use disposable project-local
mock engines/agents and no live providers. Cover concurrency/restart/lost
responses, stale bindings, STOP, malicious headings, refused selectors,
default/manual no-effects and current evidence/acceptance invalidation.

After all source slices pass, perform one real browser job, its configured
review, and a separate lead-dispatched review from another company through
native Unio with pinned models/efforts and private receipts. Resume
before this bounded journey and stop after it. Record actual IDs/calls/exits,
revision/checks/review/acceptance; no demonstration merge or public release.
The lead aggregates both reviews before accepting the demonstration. This
is an automated browser demonstration, not a real person usability test.
