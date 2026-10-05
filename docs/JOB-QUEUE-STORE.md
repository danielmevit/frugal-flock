# Durable job-queue store: explicit approval and reservation

bridge/job_store.py is a persistent JobStore library with stdlib tests. Its
current storage is schema 2. It records jobs, explicit caller approval, one
reservation per job, recorded uncertainty and cancellation. It does not run
anything: there is no executor, task compilation, worker or provider call,
process start, HTTP/UI queue control, auto-resume, retry or integration
action. The effective contract is section 2 of
[the milestone contracts](NEXT-MILESTONE-CONTRACTS.md).

## Storage and safety

JobStore(workspace) selects exactly coord/ui-jobs.sqlite3 in a real enclosing
workspace. It uses Python sqlite3 with parameterized statements, schema
marker user_version 2, transactions, a finite busy timeout and committed
durable writes. It rejects symlink/nonregular database or coordination paths.
It stays within the trusted host boundary and does not protect against a
malicious local account.

Draft/job/request/approval/reservation IDs are 32 lowercase hex characters;
hashes are 64 lowercase hex characters. Worker IDs are lowercase
letters/digits/hyphen/underscore, beginning with a letter, at most 64
characters. These are data, never commands or paths. There is no dynamic SQL
or shell/provider invocation. The store creates an opaque random job ID and
timezone-aware UTC timestamps. Raw native task text, credentials, commands
and provider output are not stored.

## Schema recognition and corruption refusal

Opening a database is decided inside one immediate transaction:

- An empty file or an empty SQLite database is initialized to schema 2.
- Schema 2 is accepted only when the jobs table has exactly the expected
  columns, order, types, NOT NULL flags and defaults, a binary primary key on
  id, and binary unique constraints on request_key, approval_key and
  reservation_key, with no other tables, indexes, triggers or views. Matching
  column names alone are not enough. Generated columns, extra CHECK
  constraints and unknown table options are refused. Definition matching
  ignores SQL whitespace and handles SQLite's quoted migration table name.
- Schema 1 is migrated only when it has exactly the layout the first slice
  created. Every legacy record is validated first: hex IDs and hash, worker
  ID, a parseable creation time with a timezone, and state
  awaiting_owner_approval. The migration copies every old field unchanged,
  sets the new fields to null, verifies the schema-2 layout and the copied
  records, and only then commits.
- Any other version, unknown layout or corrupt legacy record is refused with
  ValueError. Nothing is deleted, rewritten or reinitialized; the database
  file stays byte-for-byte unchanged.

Schema 2 records are validated again on every read. A corrupt record makes
that read or transition fail without rewriting the stored record.

## States and metadata

| State | Meaning | Required metadata |
| --- | --- | --- |
| awaiting_owner_approval | Waiting; no provider approved | No transition metadata |
| approved | Explicit caller approval for this draft and worker | approval_key, approved_at |
| reserved | One claim; execution may or may not have started | Approval plus reservation_key, reserved_at |
| completion_unknown | Reserved attempt needs reconciliation | Reservation plus unknown_at |
| cancelled | Waiting or approved job cancelled before reservation | cancelled_at; prior approval retained if present |

These metadata lists are exhaustive: every other transition field must be
null. Approval and reservation keys always appear with their corresponding
timestamp. Cancelled jobs retain either both approval fields or neither,
and never contain reservation or uncertainty metadata.

Records are JSON-ready dictionaries with id, request_key, draft_id,
draft_sha256, worker, created_at, state, approval_key, approved_at,
reservation_key, reserved_at, unknown_at and cancelled_at. No record claims
a process exit, validation, review or completion.

## Methods

- enqueue(draft_id, expected_hash, worker, request_key) records a job
  awaiting approval after matching the draft's current PlanStore hash.
- get(job_id) returns the job; a missing valid ID returns None.
- pending() returns only waiting jobs in creation-time/ID order.
- jobs() returns all jobs in the same order with their stored state.
- approve(job_id, expected_hash, worker, approval_key) approves a waiting job
  whose stored inputs match exactly and whose draft still has that hash.
- reserve(job_id, approval_key, reservation_key) claims an approved job after
  rechecking the draft. It returns a dictionary with job and newly_reserved.
- mark_unknown(job_id, reservation_key) records uncertainty for that reserved
  attempt. Nothing is requeued or restarted.
- cancel(job_id) cancels a waiting or approved job. Reserved and
  completion_unknown jobs may have started and cannot be cancelled.

Each transition is a compare-and-change operation in one immediate
transaction. A refused call leaves the database unchanged.

## Replay and draft freshness

request_key, approval_key and reservation_key make calls idempotent. The same
key with the same inputs returns the existing result, including after a
restart. Conflicting reuse fails and preserves the original. Concurrent
duplicate submissions create one job, and concurrent reservations produce
exactly one newly_reserved=true result.

Every enqueue, approve and reserve call rereads the draft, including identical
replays. If the draft has changed, the call fails unchanged instead of
returning an older job, approval or reservation. A successful identical
reserve replay returns newly_reserved=false. Only the first approved-to-reserved
transition returns true, and reopening storage never grants another dispatch
from a reserved job. A reserved, completion_unknown or cancelled job cannot
be approved again or reset.

Reading a stored job does not certify that its draft is still current.
Approval records the caller's explicit intent. This library does not
authenticate a human or assert that a native task has started.

## Limitations

There is still no executor. Nothing here dispatches, starts or monitors work,
and nothing reconciles a completion_unknown job. A later checkpoint must
freeze the protected job API, task compilation, executor lifecycle and UI
evidence before any dispatch exists.

## History

The first queue slice created schema 1, which held only waiting records
and had no approval, reservation or cancellation. Its task was implemented
through the legacy Frugal Flock v0.4.0 run cycle; see
[the closing handoff](SESSION-HANDOFF-2026-10-05.md). QUEUE-APPROVAL-1 added
schema 2 and the transitions above. QUEUE-APPROVAL-FIX-1 added exact layout
recognition, validation of legacy records before migration, and draft
rechecks on approve and reserve replays. These notes are historical and are
not current operating instructions.
