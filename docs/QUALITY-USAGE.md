# Frugal Flock — quality milestone

The first tested increment implements strict verification and automatic
verification exit propagation. Persisted revision-bound results, conservative
review parsing, honest JSON availability and handoff packets are still pending
until their implementation and regression tests are committed.

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

## Isolated checks

Run `bash tools/quality-check.sh`. It installs only in temporary
directories and runs mocks, existing probes, branding checks, ShellCheck and
documentation lint. No provider is invoked. Python 3 and ShellCheck are
checked locally; no dependency is downloaded.

## Current execution limits

Worktrees and temporary directories are coordination mechanisms, not OS
sandboxes. Configured provider commands may have host-level access. Human
acceptance and integration remain separate decisions controlled by the owner.
