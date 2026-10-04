# First durable job-queue slice: waiting for owner approval

Implement this bounded code step through the installed Frugal Flock v0.4.0
run/verify/review/result cycle. The current lead reviews in-session with no
paid reviewer, respecting the native different-agent gate. Codex prepared the
task; the owner benched it to continue with Claude. Prepared options have zero
calls and must be refreshed from latest main with actual reviewer identity.
See [the closing handoff](SESSION-HANDOFF-2026-10-05.md).
A native worker invocation requires fresh owner quota approval. No new global
install, release, profile or credential change is part of this task.

This slice supplies only a persistent JobStore library and stdlib tests.
There is no HTTP/UI queue endpoint, task compilation, worker execution,
approval transition, auto-resume, cancellation, retry or integration action.
A queued record must have state awaiting_owner_approval and no process exit,
validation, review or completion claims. This is the first queue foundation,
not the completed durable executor.

## Frozen interface

JobStore(workspace) selects exactly coord/ui-jobs.sqlite3 in a real enclosing
workspace. Use Python sqlite3 with parameterized statements, a schema-1 marker,
transactions, a finite busy timeout and committed durable writes. Reject
symlink/nonregular database or coordination paths, unsupported schema and
corrupt storage without deleting/reinitializing them. Stay within the trusted
host boundary; this does not protect against a malicious local account.

- enqueue(draft_id, expected_hash, worker, request_key) returns a JSON-ready
  record containing id, draft_id, draft_sha256, worker, request_key, created_at
  and state awaiting_owner_approval. Read the existing PlanStore draft and
  match its current content_sha256 before creating or replaying a job.
- get(job_id) returns the recorded job; a missing valid ID returns None.
- pending() returns waiting jobs in deterministic creation-time/ID order.

Draft/job/request-key IDs are 32 lowercase hex characters; hashes are 64
lowercase hex characters. Worker IDs are lowercase letters/digits/hyphen/
underscore, beginning with a letter, at most 64 characters. These are data,
never commands or paths. There is no dynamic SQL or shell/provider invocation.
An opaque random job ID and UTC creation time are created by the store.

request_key is an idempotency key: the same key and exact inputs return the
same job, including after restart; conflicting reuse fails and preserves the
original. Concurrent duplicate submissions create exactly one record.
An edited/stale draft fails even on replay. Reading a stored job does not
claim its referenced draft is still current or approved for dispatch.
Do not store raw native task text, credentials, commands or provider output.

## Required checks

Use workspace-local TMPDIR and no external dependencies. Prove:

- a real stored manual draft can be queued, reopened identically after a
  new JobStore instance, and listed while still awaiting owner approval;
- repeated identical and concurrent submissions return one record;
- conflicting request-key reuse and stale/edited draft hashes fail without
  adding or overwriting a job;
- bad IDs/hash/worker fields cannot select paths or become SQL;
- missing IDs are honest, unknown schema/corrupt database fail closed, and
  symlink/nonregular database or coordination paths are refused;
- no native task, provider invocation or process/validation/review result is
  created by enqueue/get/pending. Tests use only disposable scratch fixtures.

The next bounded task will define explicit approval and reservation/recovery
before any executor. Dispatch must eventually recheck the exact draft/task/
revision, record the owner's provider approval, preserve real exit/evidence,
and never automatically dispatch a possibly started job after interruption.
