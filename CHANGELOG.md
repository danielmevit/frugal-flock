# Changelog

Release notes for Unio. Between releases, each task writes a short
fragment in `changelog.d/`; the fragments are rolled into this file when a
version is released.

## 0.5.0 — Unio rename (UNRELEASED)

- The project is renamed to Unio.
- The command is `unio` (all old aliases like `frugal-flock` and `agentteam` are removed).
- Configuration folder is now `~/.config/unio`. Environment variables are prefixed with `UNIO_`.
- Updated installer to `unio-install.sh`.
- The legacy Frugal Flock 0.4.0 build tool remains in use until owner approval.

## 0.4.0 — 2026-10-04 — trustworthy results (M1)

The first published release under the Frugal Flock name. It completes M1,
the quality milestone, which the owner accepted on 2026-10-04. Frozen
contract: [QUALITY-M1-CONTRACT.md](docs/QUALITY-M1-CONTRACT.md); evidence
per clause: [M1-ACCEPTANCE-AUDIT.md](docs/M1-ACCEPTANCE-AUDIT.md).

### Upgrade notes

- **Stricter verification.** `verify` passes only with at least one
  `- path` line under `## Allowed scope` and at least one `$ command` line
  under `## Validate`. A task missing either now ends INCOMPLETE (exit 2)
  instead of PASS. Real failures exit 1.
- **Review is gated.** `review` needs a current passing `verify` and clean,
  committed, text-only work of at most 300000 bytes, and accepts exactly one
  standalone `VERDICT:` line from the reviewer's stdout. Exits 0/1/2.
- **Python 3 is required** (standard library only, nothing downloaded) for
  run, verify, review, smoke, agents, result and handoff.
- Existing commands, `agentteam`, `AGENTTEAM_*` variables, config paths and
  the Linux `flock` dependency all keep working.

### Name and commands

- The product is now Frugal Flock: "Small plans. Big ideas." New commands
  `frugal-flock` and the short `frgl-flc`, with completion; `agentteam`
  remains as a compatible alias. The GitHub repository is now
  `danielmevit/frugal-flock`, with a plain-language README.

### Reliability (M1)

- `verify` fails closed: missing scope or checks are INCOMPLETE, never PASS;
  a missing base branch is a failure. With `AGENTTEAM_AUTO_VERIFY`, a worker
  failure keeps its own exit and failed or incomplete checks make a
  successful run nonzero.
- Structured results: each worker/task gets a schema-versioned JSON result in
  `coord/results/`, read with `result`. Process, validation and review
  states are separate and bound to a revision of the commit, base, task file
  and worktree contents, so any change marks old evidence stale.
  `ready_for_human_review` is never human acceptance.
- `review` parses the verdict conservatively and records it per revision.
- `agents --json` reports local availability without running agents or
  probing sign-in or quota; programs are resolved past quoted shell syntax.
  `doctor` checks for Python 3 and handles environment-prefixed agent lines.
- `handoff` writes a same-checkout context packet for the next AI. It is
  context, not a backup.
- Live commands state the `trusted_host` boundary: worktrees are not OS
  sandboxes.
- Unsupported worktree states fail closed: assume-unchanged/skip-worktree
  index flags (they hid edits from scope and review), FIFOs, devices,
  sockets, nested repositories and submodules. If the snapshot fails right
  after a run, `run` still records the worker's real exit, report and
  ledger line (`snapshot_failed`).
- Scratch left by an interrupted handoff or a killed result write is
  removed by the next locked operation.

### Engine fixes and tests

- `init` no longer blocks on CodeGraph indexing; it is detached and
  time-boxed (CG-1).
- A sandboxed adversarial probe suite (`tests/agentteam-probes.sh`, 14
  probes) demonstrated 11 defects, all closed (SABAT-1).
- `tools/quality-check.sh` runs every check in temporary directories:
  40 selftests, 120 mock-only quality checks, the probes, branding,
  ShellCheck and docs lint. Timing-dependent tests and a selftest cleanup
  race no longer fail on slow drives.

### Documentation

- Help, completion and the operational protocol cover the new commands and
  exits. `docs/QUALITY-USAGE.md` is the complete M1 reference; SETUP,
  HANDBOOK, GUIDEBOOK (and its Word file) and the README match the release.
- A single living continuation prompt (`continue-with-ai-prompt.md`), the
  one-folder workspace rules, the agent-log rule, research findings and the
  UX direction preserve context across AI tools and usage limits.
