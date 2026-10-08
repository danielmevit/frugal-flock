# Unio: approved next milestones

Current status, 2026-10-08: steps1–3 below shipped through v0.5.3. Step4 is
implemented in main: manual/automatic saving, authorized continuation and the
first supported [lead cooldown runtime](LEAD-COOLDOWN.md). Real subscription-limit
restart acceptance and combined shipping checks remain before v0.5.4 publication. Read the [milestone review](development/FUNCTIONALITY-FIRST-PLAN.md)
and [current roadmap](development/ROADMAP.md) first. The original sequence and
dated contracts below remain history; newer work/review and publication policy
in the [version plan](VERSION-PLAN.md) supersedes older session defaults.

The owner approved these five steps on 2026-10-05 after the rename landed at
be9e257. The owner then approved installed migration before these milestones.
Unio 0.5.0 is installed as of 2026-10-05; the lead delegates through `unio`,
with pinned models, bounded one-call tasks, another AI lab's review,
then the lead's full review. Source merges receive the full quality gate and
are pushed only on PASS. Release publication and billing changes need separate
approval. See [version plan](VERSION-PLAN.md) for the owner-approved sequence.

Validation update, 2026-10-08: see [completed checks, preserved failures and
remaining release work](development/RECOVERY-ACCEPTANCE-2026-10-08.md). Component coverage does
not replace the final versioned release gate.

## Final review policy

Owner direction on 2026-10-05: each final candidate from this point receives
at least two separate AI reviews, followed by the lead's own review. Use
different reviewer AI labs from each other and from the candidate's source
authors. Reviewers receive the complete frozen task and diff independently;
do not give one reviewer another's verdict before its assessment.

Run those independent reviews concurrently when provider capacity permits.
Give each a separate disposable review workspace and receipt, with exactly
the same candidate/base/task/worktree revision and complete material hash.
Imported verification must preserve the genuine original evidence and record
its provenance; never invent a successful run or verification. Separate
review locks/results prevent contention in the native one-worker review gate.
Compare both back to the unchanged source before aggregating or integrating.

The lead combines the findings into one overview tied to the exact candidate
SHA, tests and review receipts. Resolve blocking findings through concrete
bounded correction tasks; preserve rejected evidence. Changed candidates
receive fresh independent reviews, never inherited approval. Add targeted
reviewers when coverage gaps or unresolved disagreements require them.
Tests and reviews reduce mistakes; they are not proof that every bug is found.
Keep one invocation per review task, no automatic paid retry, and the full
merged-tree quality gate before each push. Completed earlier checkpoints
are not reopened solely by this prospective rule.

For the current 2026-10-07 session, the owner's latest instruction is personal
lead review without spawning extra reviewer workers. Preserve real historical
reviews, but do not claim fresh independent AI-lab approval for that exception.

## Order and estimates

1. Limit-policy hardening: roughly 1–3 working hours.
2. Queue approval, reservation and recovery: roughly half a working day.
3. One real browser-to-worker workflow: roughly 1–2 working days.
4. Checkpoint-based provider continuation: roughly 1–2 working days.
5. Shipping preparation: roughly half a working day.

These are planning ranges, not deadlines. Reviews, integration checks and
provider availability affect elapsed time. Run and integrate step 1 first,
then prepare step 2 from that base. Each slice owns its version bump and
matching existing branding assertion: 0.5.1 for step 1 and 0.5.2 for step 2.
The installer version is the only runtime edit in the queue-library slice.
Later steps are dependent slices. Preparation does not authorize publication.

## 1. Limit-policy contract

The earlier frozen LIMIT-WALL-2 proposal remains in coordination history.
This contract supersedes its automatic-benching proposal: empty work plus
printed text cannot authenticate a provider's limit signal.

- The limit matcher remains a conservative text heuristic. Its warning and
  ledger wall=1 mean suspected limit language, never confirmed capacity.
- Consider a run failed for this helper when its actual exit is nonzero, or
  the existing empty-work check finds zero commits against the base and zero
  uncommitted files. Preserve the real process exit in all receipts.
- A successful run with work has wall=0 even when it prints limit language.
- Extract one final 60-line window, normalize ANSI escapes and carriage
  returns, and use the same normalized text for report display and matching.
  Keep the full raw native log as the original evidence.
- Worker text must never call off or write availability/configuration state.
  UNIO_AUTO_OFF remains accepted for compatibility but does not authorize
  policy changes from heuristic output. Explicit operator off/on remains.
- Document this change in help, quality guidance and both protocol copies.
  No new trusted provider signal is claimed or invented in this slice.
- Mock regressions must cover exit-zero empty work, successful committed
  work, failed committed work, ANSI/carriage returns, a phrase 50 lines from
  the end, printed repository text, and AUTO_OFF=1 without availability writes.
  Existing expectations of heuristic auto-benching must change explicitly.

## 2. Queue-library contract

Extend bridge/job_store.py; no executor, provider calls, HTTP controls or UI
controls in this slice. PlanStore remains the authority for immutable drafts.
Preserve enqueue/get and their data validation, idempotency and path protections.

Schema 2 migrates recognized schema-1 waiting records transactionally without
losing IDs, request keys, draft hashes, worker IDs or timestamps. Unknown or
corrupt schemas fail without reinitializing storage. New nullable fields are
approval_key, approved_at, reservation_key, reserved_at, unknown_at and
cancelled_at. Approval and reservation keys are opaque 32-character lowercase
hex IDs with unique non-null values. Timestamps include a timezone.

States and required metadata:

| State | Meaning | Required metadata |
| --- | --- | --- |
| awaiting_owner_approval | Waiting; no provider approved | No transition metadata |
| approved | Explicit caller approval for this draft and worker | approval_key, approved_at |
| reserved | One claim; execution may or may not have started | Approval plus reservation_key, reserved_at |
| completion_unknown | Reserved attempt needs reconciliation | Reservation plus unknown_at |
| cancelled | Waiting or approved job cancelled before reservation | cancelled_at; prior approval retained if present |

Methods use validated IDs and transactional compare-and-change operations:

- approve(job_id, expected_hash, worker, approval_key): validate the exact
  stored inputs and the draft's current hash, then approve once. Identical
  replay returns the same approval; conflicting replay fails unchanged.
  A reserved, unknown or cancelled job cannot be approved or reset.
- reserve(job_id, approval_key, reservation_key): validate approval and current
  draft. Return an envelope with job and newly_reserved. Only the first
  approved-to-reserved transition has newly_reserved=true. Identical replay
  returns false; another reservation key fails. Reopening storage never grants
  a fresh dispatch from an already reserved job.
- mark_unknown(job_id, reservation_key): explicitly record uncertainty for
  that reserved attempt; replay is idempotent. No automatic requeue or restart.
- cancel(job_id): allow waiting or approved jobs only; replay of cancelled is
  idempotent. Refuse cancellation of a possibly started reserved/unknown job.
- pending(): waiting jobs only, deterministic creation-time/ID order.
- jobs(): all jobs in the same deterministic order, with honest stored state.

Reading approval does not certify that the draft is still current. Recheck it
at approval/reservation boundaries. Caller approval is explicit intent; this
library does not authenticate a human or assert that a native task has started.

Test schema migration, restart persistence, exact-input approval, stale drafts,
concurrent reservations and replay, unknown/cancel transitions, invalid or corrupt
metadata, and absence of native tasks/processes/provider side effects.

## Later contracts

The owner added [lead CLI cooldown restart](development/LEAD-COOLDOWN-RESTART.md)
on 2026-10-07 as a continuation slice after automatic work saving in v0.5.4.
A supervisor outside the lead process waits for its actual reset plus one
minute, or five hours and one minute when a known five-hour reset is unknown,
then starts the configured lead from its saved handoff. Repeated lead limits
create new waits. Explicit stop and completion prevent further restarts.
Worker benching, routing and retry policy stay unchanged. Freeze the adapter,
durable state, ownership and mock-clock acceptance contract before dispatch.

Before step 3 dispatch, freeze the protected job API, task compilation,
executor lifecycle and truthful UI evidence interfaces in another checkpoint.
Default activity remains read-only; new execution requires explicit approval.
Before step 4, freeze checkpoint contents and restoration/reverification rules.
The installed rename and its rollback are already approved and complete.
Before public release, provide reviewable release artifacts and obtain the
owner's separate approval. Keep versioned checkpoints even before publication.
