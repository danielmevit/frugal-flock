# Changelog

Release notes for Unio. Between releases, each task writes a short
fragment in `changelog.d/`; the fragments are rolled into this file when a
version is released.

## 0.5.1 — truthful limit observations (UNRELEASED)

Unio 0.5.1 (unreleased): a run now counts as failed for the limit helper
only on a nonzero actual exit or the empty-work rule (zero commits against
the base and zero uncommitted files), preserving the real exit in every
receipt, and one normalized final 60-line window (ANSI/control escapes and
carriage returns stripped, never executing log text) drives both the
report display and matching while the raw log is kept. The warning and
ledger wall=1 mean suspected limit language, never a confirmed quota, and
a successful run with work stays wall=0. Worker text never benches an
agent or writes availability/configuration state: UNIO_AUTO_OFF is
accepted for compatibility and has no effect, while explicit unio off/on
remains the operator's control. Help, docs/PROTOCOL.md with its embedded
copy and docs/QUALITY-USAGE.md are updated, and tests/unio-limit-wall.py
replaces the automatic-bench expectations with regressions for genuine
phrases, printed repository text, exit-zero empty work, successful and
failed committed work, ANSI/carriage returns, a phrase 50 lines from the
end, and AUTO_OFF=1 with unchanged availability/config files.

Unio 0.5.1 (unreleased): guarantee 5 checks the failed mock's real exit and suspected-limit warning, unchanged availability with UNIO_AUTO_OFF=1, and explicit off/refusal/on behavior.
The adversarial demo honors UNIO_BIN_DIR and the incoming UNIO_CONF_DIR for its engine and template source while retaining isolated mock configuration and existing defaults.

## 0.5.2 — durable queue approval (UNRELEASED)

- Added schema-2 queue job store with durable approve, reserve, unknown and cancel states.

- Fixed the queue job store: it now refuses unknown or under-constrained schema-1 and schema-2 layouts and corrupt legacy records without changing the database, and identical approve/reserve replays recheck the current draft.

Reject impossible queue state metadata and unknown CHECK/generated layouts unchanged; preserve recognized migrations and valid replays with exhaustive corruption regressions.

## 0.5.3 — browser execution service (UNRELEASED)

- Unio 0.5.3: add explicit native ExecutionService with durable worker ownership, once-only launch/review intents and revision-bound evidence/acceptance.
- Add disposable Git/native-mock regressions and quality-gate registration; HTTP/browser integration and the live demonstration remain separate slices.

- Unio 0.5.3: prepare now checks the size of every document it will publish before it records worker ownership or adds a queue row. A document that cannot fit returns invalid_request without changing ownership, queue rows or earlier released evidence.
- Request/scope/check companions are stored as UTF-8 JSON, so maximum valid Unicode templates now prepare. Preview and binding hashes are unchanged, and older escaped records still read the same.

## 0.5.0 — Unio rename (UNRELEASED)

- The project is renamed to Unio.
- The command is `unio` (all old aliases like `frugal-flock` and `agentteam` are removed).
- Configuration folder is now `~/.config/unio`. Environment variables are prefixed with `UNIO_`.
- Updated installer to `unio-install.sh`.
- The installer copies existing default configuration into `~/.config/unio`, preserving the original. The development workspace migrated to Unio 0.5.0 with owner approval on 2026-10-05; publication is pending.

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
