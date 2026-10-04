# Frugal Flock — quality milestone

Milestone 1 is in progress, not an accepted release. Implemented and
tested so far: strict verification, automatic verification exit propagation,
persisted revision-bound results (`result`), conservative review parsing,
JSON availability (`agents --json`) and same-checkout context packets
(`handoff`). See [M1-STATUS.md](M1-STATUS.md) for what is still open.

## Verification exits

Use `frugal-flock verify WORKER TASK`. Exit 0 means scope is present,
at least one validation command ran, all checks passed, and the existing
scope, tamper, empty-work and base checks passed. Missing scope or checks
produces INCOMPLETE and exit 2. Actual failures produce a nonzero failure,
normally exit 1. Failure takes precedence over incomplete evidence.
Reasons remain visible individually in the terminal and append-only report.
Milestone 1 has no waiver mechanism.

With `AGENTTEAM_AUTO_VERIFY=1`, a successful worker process followed by
failed or incomplete verification returns the verification's nonzero exit.
A worker process failure keeps its own nonzero exit. Without automatic
verification, process success alone still does not establish readiness.

## Unsupported worktree states

Revision evidence hashes real file contents, but scope checks, review
material and handoff summaries list changed paths through Git. Git skips
paths marked assume-unchanged or skip-worktree (sparse checkout uses the
latter), so `verify`, `review` and `handoff` refuse a worktree with either
flag instead of claiming a complete list. Clear the flags with
`git update-index --no-assume-unchanged --no-skip-worktree` on those paths,
or `git sparse-checkout disable`, then run the command again.

The snapshot itself refuses FIFOs, devices, sockets, nested repositories
and submodules. If that happens right after a worker finishes, `run` still
records the worker's real exit code, writes the report and ledger line
(`snapshot_failed` is 1), skips automatic verification, and returns the
worker's nonzero exit, or 2 if the worker succeeded. The stored result is
marked `post_run_snapshot: failed` and stays stale and not ready, even
after cleanup. Remove the unsupported file, then run the task again.

## Isolated checks

Run `bash tools/quality-check.sh`. It installs only in temporary
directories and runs mocks, existing probes, branding checks, ShellCheck and
documentation lint. No provider is invoked. Python 3 and ShellCheck are
checked locally; no dependency is downloaded.

## Current execution limits

Worktrees and temporary directories are coordination mechanisms, not OS
sandboxes. Configured provider commands may have host-level access. Human
acceptance and integration remain separate decisions controlled by the owner.
