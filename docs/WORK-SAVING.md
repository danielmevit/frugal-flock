# Automatic work saving — planned for v0.5.4

Owner requirement recorded 2026-10-06 after a worker reached its allowance
limit with useful edits but no final commit. This is an implementation plan,
not a feature available in the current release. See the
[version plan](VERSION-PLAN.md) and [roadmap](development/ROADMAP.md#approved-delivery-priorities).

## The intended behavior

Unio should save recoverable checkpoints throughout a run, preserving
unfinished work when an AI stops unexpectedly. The native supervisor saves
local file state at the start, periodically when edits change, and after a
provider failure or timeout. Saving needs no AI request. Each save records
its worker, task, run, revisions, file hashes and actual observation time.

Workers receive guidance to commit coherent, scoped changes regularly. A
finish reserve leaves time to validate and commit before the run deadline
or a known allowance boundary. Use supported readings and timestamped manual
input where available; missing quota information remains Unknown. This
cannot predict every provider cutoff, so saving works independently of the
AI answering a final request.

Show the last successful save and its age, plus unsaved, stale, refused or
failed capture states. A failed final save must leave the previous valid
save available. Atomically publish bounded snapshots and retain bounded
history. Concurrent edits can prevent an exact latest capture; never claim
those changing bytes were saved successfully.

## Recovery and acceptance

A recovery snapshot contains actual supported committed, staged, unstaged
and nonignored untracked content, modes and deletions. It is not just a
summary. Validate the manifest and content hashes before restoring into a
separate idle worker. Keep the original branch, files and failed run intact.
Use a new bounded task and exclusive continuation ownership, followed by
fresh checks and independent reviews. Do not inherit earlier readiness.

Saving never automatically commits arbitrary dirty files or accepts code.
A coherent source commit is still subject to checks and reviews. A recovery
snapshot is explicitly unverified. Restore and inspection make no provider
calls; a continuation is one separately authorized worker invocation.

Exclude credential paths, Git internals, ignored caches, unsupported file
types and excessive data. Refuse incomplete required content instead of
claiming a recoverable save. Enforce stable byte captures, safe path handling
and bounded local storage. Filename exclusions cannot guarantee arbitrary
source text is secret-free. Worktrees are trusted-host coordination, and a
private local save is not an off-device backup.

## Required checks

Use offline providers to prove abrupt quota failure, timeout, termination,
missing allowance telemetry and low reported allowance. Recover actual
staged, unstaged, untracked and deleted files. Test concurrent writes,
interrupted snapshot publication, secret-name exclusions, capture failures,
stale saves, retention bounds and exact restoration. Prove saving and
restoring make zero provider calls, preserve the original failed exit, and
do not authorize a second paid attempt or bypass current verification.
