# Milestone 1 — trustworthy engine results and manual handoff

Status: implementation contract, not a completion claim. The owner's
2026-10-03 request moves reliability ahead of the UX prototype.

## Scope and explicit limits

Fix findings E1–E3, add revision-bound machine-readable evidence and a
manual handoff packet, and make execution/availability limitations explicit.
This is a CLI quality milestone. No frontend, provider purchase, new hosted
service, OS sandbox, or automatic cross-provider migration is included.
Do not mark E4 or full E6 resolved by warnings or a context export.

The existing public commands and configuration remain compatible in name.
Strict verification/review exit semantics are an intentional behavior change
and must be documented. Preserve old reports and ledger history. A new
Python 3 standard-library helper is permitted for safe JSON and hashing;
no downloaded runtime dependencies. Preflight any new dependency before a
provider starts. Keep the installer self-contained and aliases shared.

## 1. Fail closed on absent verification evidence

`verify WORKER TASK` reports PASS and exits 0 only when scope is present,
at least one Validate command ran, all ran successfully, and existing
scope/tamper/empty/base safeguards pass. Missing scope or missing Validate
commands produce INCOMPLETE and exit 2, never PASS. Actual check failures,
scope violations, tampering, empty work, and unavailable base remain failure
with a nonzero exit (normally 1). Preserve failure reasons individually.

No waiver mechanism ships in M1: a worker must not self-authorize skipping
evidence. A task that needs a different check should specify it explicitly.
Update the old no-Validate selftest to expect the new incomplete result.

## 2. Separate outcomes and bind evidence to work

Persist schema-versioned JSON under
`coord/results/WORKER/TASK.json`, with atomic replacement while holding the
existing worker lock. Retain the append-only reports and ledger. Minimum
fields (additional descriptive fields are allowed):

- `schema_version`: 1; `worker`, `task`, `updated_at`.
- `revision`: `candidate_commit`, `base_commit`, `task_sha256`,
  `worktree_sha256`. The worktree hash covers index/working tracked changes
  and nonignored untracked path/content/type information; filenames alone
  are insufficient. Handle spaces, Unicode, symlinks, and JSON escaping.
- `process`: `state` (not_run, running, succeeded, failed), `exit_code`
  (null if unknown).
- `validation`: `state` (not_run, passed, failed, incomplete), scope state,
  checks run/failed, and reasons. Include its evidence revision.
- `review`: `state` (not_run, approved, changes_requested, unknown, failed),
  reviewer ID, process exit code, and its evidence revision.
- `human`: `state: pending`; `integration`: `state: not_attempted`.
  M1 does not implement human acceptance or integration commands.
- `stale`: boolean; `ready_for_human_review`: boolean. This is never a
  claim that a human accepted or integration is authorized.

`result WORKER TASK` emits JSON only on stdout and makes no provider call.
Recompute current revision; changed commit, base, task, index, tracked or
nonignored untracked content makes prior evidence stale and not ready.
Missing/malformed result files must fail closed with a clear error. Do not
backfill old PASS text as trusted structured evidence.

Before/after verification and review snapshots must match. A changed
candidate while checks/review run cannot receive fresh valid evidence.
Safe readiness requires successful worker process, passed validation,
approved review, all evidence for the current revision, and no stale state.
Keep unknown or not-run states visible rather than manufacturing success.

Starting a new run resets old validation/review readiness. With automatic
verification, preserve both worker exit and verification outcome. Worker
failure remains nonzero; worker success plus verification failure/incomplete
must also return nonzero. With automatic verification off, a successful
run may still exit 0 but has validation not_run and readiness false.

## 3. Parse independent review conservatively

Parse exactly one standalone verdict line from reviewer stdout:
`VERDICT: APPROVE` or `VERDICT: REQUEST-CHANGES`. A missing, malformed, or
multiple verdict is unknown; reviewer process failure is failed regardless
of its text. Preserve raw output locally but do not execute or interpret it
as shell. Stderr must not manufacture an approval.

Review exits: 0 only for a valid, current approval; 1 for changes requested
or process failure; 2 for unknown/incomplete/stale evidence. Persist the
actual reviewer process exit separately. Require current passed validation
before invoking a reviewer. Hold the worker lock to exclude tool-mediated
concurrent writes; compare before/after revisions as well. Human acceptance
stays pending. Report clipped or incomplete review material; do not silently
approve a partial diff as if it covered the entire candidate.

## 4. Honest availability and execution boundary

Add `agents --json`: each configured agent has binary presence, bench state,
operator retry time if set, `authentication: unknown`, `capacity: unknown`,
and `execution_boundary: trusted_host`. Never probe sign-in or quota in
this local command. Handle leading environment assignments or `env` in
configured commands without executing them; ambiguous shell wrappers are
unknown, not a false connected state.

Human-readable availability output must distinguish installed from usable
and avoid calling a timed bench a provider-confirmed reset. Before a live
run/review/smoke, state that configured commands may have host-level access.
Do not claim a temporary directory or worktree is a sandbox. Preserve
existing authenticated CLI use; do not alter the user's global config.
Full OS isolation requires its own threat model and negative tests.

## 5. A next-AI packet, not an automatic restore

`handoff WORKER TASK` must refuse a locked/running worker and otherwise
write a new unique packet under `coord/handoffs/WORKER/TASK/`. Include the
task text, a structured current result (or explicit not_run/unknown states
if none exists), revision identity, changed-file summary, and HANDOFF.md
with completed checks, outstanding issues, and next safe actions.

The packet is for another AI continuing in the same existing checkout.
It is context and evidence, NOT a backup or automatic migration. List
uncommitted and untracked work as still residing in the original worktree;
do not claim those contents have been preserved elsewhere. Do not copy
credentials, agents.conf, ignored files, raw provider logs, or home folders.
Task text itself may contain sensitive information: warn the user to review
the local packet before sharing it. Never upload or invoke a replacement.

Use atomic output and compare before/after revisions. Paths stay under the
coordination root, symlinks must not escape it, prior packets stay intact,
and invalid worker/task IDs fail. The handoff must state that old evidence
needs rechecking after new edits or when moving to another machine.

## Acceptance gate

Add a focused mock-only regression script and a repeatable isolated check
runner. Cover missing scope/checks, true failures, auto-verify outcome
propagation, positive and negative review decisions, stderr/multiple/no
verdicts, stale commits/base/task/dirty content, untracked content changes,
JSON-special filenames, persistence reload, run/review/handoff locking,
atomic packet creation, and truthful no-network availability.

Run installed selftest, existing adversarial probes, branding smoke,
ShellCheck, installer syntax, and docs lint. Preserve existing regression
guards and the exact embedded/source protocol identity. If engine behavior
requires doc/example updates, update them and regenerate affected manuals.
Do not mark completion with known failing checks or unimplemented clauses.

## Useful competitor ideas and later work

Adopt the principle of inspectable evidence packets (as seen in AWO) and
explicit per-worker lifecycle state (as seen in AO/CAO). Implement original
code for this engine; no competitor source or assets are copied. Defer
autonomous councils, voting-based approval, hosting, and a large dashboard.
The later UI may take visual inspiration from Toolcraft, but its scaffolder,
runtime, UI source, templates, and assets must not be imported into this repo.
