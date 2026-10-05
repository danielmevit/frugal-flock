# Durable waiting-job queue

Add bridge/job_store.py: jobs awaiting owner approval persisted in
coord/ui-jobs.sqlite3 with an explicit schema-1 marker, parameterized SQL,
BEGIN IMMEDIATE serialized writers, a UNIQUE request_key idempotency rule,
a finite busy timeout and durable rollback-journal commits (no WAL on this
Windows drive mount). Every open decides inside one BEGIN IMMEDIATE
transaction: a file holding no data yet (user_version 0 and an empty
sqlite_master, including a just-created or crash-interrupted 0-byte file)
gets the jobs table, user_version 1 and a commit, so concurrent first
opens on a brand-new workspace all initialize exactly once; anything else
is verified against the exact schema 1 and refused with the file bytes
untouched. A failed COMMIT always rolls back first, so no open
transaction survives and the store stays usable. enqueue rechecks the
current PlanStore draft content hash before every create and replay, mints
an opaque random ID and UTC creation time, and always records state
awaiting_owner_approval; identical resubmissions replay one record across
restarts, eight threads racing to enqueue the same new request key all
receive that one record, and conflicting key reuse or an edited draft
fails without touching the original. get/pending revalidate every stored
row, and unknown schema, corrupt, garbage, symlinked or nonregular
databases and coordination paths are refused without deleting or
reinitializing anything. Stdlib tests in bridge/tests/job_store_test.py
cover restart identity, the eight-thread first-open and same-new-key
create races, interrupted and bare database recovery, failed-commit
rollback, deterministic ordering, conflict and stale draft refusal,
invalid inputs, missing IDs, fail-closed corruption and storage shapes,
and no native task/result/provider side effects. No dispatch, approval
transition, executor, retry or cancellation exists yet.
