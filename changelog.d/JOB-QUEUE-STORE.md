# Durable waiting-job queue

Add bridge/job_store.py: jobs awaiting owner approval persisted in
coord/ui-jobs.sqlite3 with an explicit schema-1 marker, parameterized SQL,
BEGIN IMMEDIATE serialized writers, a UNIQUE request_key idempotency rule,
a finite busy timeout and durable rollback-journal commits (no WAL on this
Windows drive mount). enqueue rechecks the current PlanStore draft
content hash before every create and replay, mints an opaque random ID and
UTC creation time, and always records state awaiting_owner_approval;
identical resubmissions replay one record across restarts and concurrency,
while conflicting key reuse or an edited draft fails without touching the
original. get/pending revalidate every stored row, and unknown schema,
corrupt, symlinked or nonregular databases and coordination paths are
refused without deleting or reinitializing anything. Stdlib tests in
bridge/tests/job_store_test.py cover restart identity, single-record
concurrency (eight workers), deterministic ordering, conflict and stale
draft refusal, invalid inputs, missing IDs, fail-closed corruption and
storage shapes, and no native task/result/provider side effects. No
dispatch, approval transition, executor, retry or cancellation exists yet.
