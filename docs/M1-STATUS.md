# Milestone 1 — quality checkpoint

## Status

**M1 is complete: all five items are implemented, merged into main and
published, and the owner accepted M1 on 2026-10-04**, including the
documentation-only scope result of the final gate. It is released as
**v0.4.0** (see [CHANGELOG.md](../CHANGELOG.md)) and installed globally on
the owner's machine, with the 0.3.1 files backed up in the local
workspace's `artifacts/backups/`.

Frozen requirements: [QUALITY-M1-CONTRACT.md](QUALITY-M1-CONTRACT.md)
at `e230ad4`. Clause-by-clause evidence:
[M1-ACCEPTANCE-AUDIT.md](M1-ACCEPTANCE-AUDIT.md).

Every step went to main as its own merge commit, so each can be reverted
alone with `git revert -m 1` and the merge SHA:

| Merge | What it brought | Made by |
|---|---|---|
| `5d70223` | FF-QUALITY increments from `agent/codex` (strict verify, results, review gate, availability, handoff) | Codex workers; merged at the owner's request |
| `fade423` | Item 1 (hidden index flags), item 2 (post-run snapshot failure), CodeGraph selftest race | Claude Code, Claude Opus 5.5 |
| `45803c1` | Item 4: help, completion, doctor, PROTOCOL copies | subagent claude-help, Claude Opus 5.5 |
| `ce3d57f` | Item 4: QUALITY-USAGE, SETUP, README, HANDBOOK, GUIDEBOOK and its Word file, changelog | subagent claude-docs, Claude Opus 5.5 |
| `ec5fdee` | Item 3: 23 coverage regressions and the acceptance audit | subagent claude-tests, Claude Opus 5.5 |
| `dba78ce` | Agent binary resolution, deterministic timing tests, selftest cleanup race | Claude Code lead, Claude Opus 5.5 |

Every agent reads the local `../coord/AGENT-LOG.md` first and adds a dated
entry after each checkpoint. See [WORKSPACE-RULES.md](../WORKSPACE-RULES.md).

## Final gate (item 5), 2026-10-04

Run by Claude Code (Claude Opus 5.5) on main `dba78ce` from a temporary
install of the candidate (the global 0.3.1 tool was not used or changed).
The native frozen task gate `verify` for `FF-QUALITY-kimi` was run with
base `e230ad4`, the commit that froze the contract:

- Validate: **5/5 passed**: both installer syntax checks,
  `bash tests/frugal-flock-quality.sh`, `bash tools/quality-check.sh` and
  `bash tools/check-docs.sh`.
- Scope: **VIOLATION, so the machine verdict is FAIL.** All 15 out-of-scope
  paths are Markdown documents written by lead sessions, not by the
  implementation worker: README, TODO, WORKSPACE-RULES, the continuation
  prompt, this file, the audit, and the research, handoff and UX notes.
  Every code, test, tool and Word file that changed is inside the frozen
  scope. The frozen task was not edited to make the gate pass.
- Separately, on the exact merged tree of `dba78ce`:
  `tools/quality-check.sh` passed with 40/40 selftests, 16 + 78 + 23
  quality checks, 14 adversarial probes held, branding and protocol
  identity, ShellCheck and docs lint.

The owner decides whether the documentation-only scope result is
acceptable. No live provider was called by any test.

## Resume locally

```bash
cat ../coord/AGENT-LOG.md
git log --first-parent --oneline -8 main
bash tools/quality-check.sh
```

Main contains all M1 work. Older worker branches (`agent/codex`,
`agent/kimi`, `agent/claude-*`) are history. Review the real diff, not
just a report. Never reset a dirty worktree.

## First increment — independently checked

Candidate `9f296da` adds strict missing-scope/check handling (INCOMPLETE,
exit 2), preserves real-failure precedence, and propagates automatic
verification failures while keeping the worker's own failure exit.
Reasons remain in terminal output and append-only reports.

Independent checks on 2026-10-04:

- `bash tests/frugal-flock-quality.sh`: 16 focused regressions passed.
- `bash tools/quality-check.sh`: passed, including 40 selftests, those
  16 focused regressions, 14 adversarial probes, installer syntax,
  installed-runtime ShellCheck, branding/aliases/protocol identity, and
  documentation lint. Repeated successfully after the manual corrections.
- `git diff --check`: clean. `docs/GUIDEBOOK.docx` regenerated.
- Source inspection confirms the bounded E1/exit-propagation changes;
  the full milestone contract is not yet implemented.

The frozen gate passed on `9f296da` and `4b8296c`: scope OK and all five
Validate commands passed. Final-checkpoint results are recorded in the
continuation report. A passing gate does not prove that every contract
edge is covered. No owner integration has occurred.

Final candidate `80feafb` also passed the native frozen gate (scope OK,
5/5 commands). Independent focused results: 16 basic + 64 contract checks.
The exact next small task and checkpoint-maintenance rule are in the root
[continuation prompt](../continue-with-ai-prompt.md).

## Later implementation checkpoints

- `4b8296c`: embedded Python-stdlib snapshots, atomic result storage,
  separate outcomes, conservative reviewer parsing/gating, availability
  JSON, trusted-host warnings, and manual handoff packets.
- `ef44611`: broader mock acceptance cases plus prompt/dispatch fixes.
- `80feafb`: regression proving an extra public verify argument cannot
  bypass a held worker lock.

These are implemented candidates, not claims of complete reliability.
`docs/QUALITY-USAGE.md` is now the complete M1 reference (merge `ce3d57f`).

## Claude checkpoints, 2026-10-04

Results from `../wt/claude` at `9d48b76`, run by Claude Code (Claude Opus
5.5) with TMPDIR set to the workspace `tmp/` folder:

- `bash tests/frugal-flock-quality.sh`: 16 basic + 75 contract checks
  passed (11 new: 5 for item 1, 6 for item 2).
- Each new regression failed on the unfixed code: verify reported PASS
  over an assume-unchanged edit, and run returned 2 instead of the
  worker's real exit 7 after a FIFO broke the post-run snapshot.
- `bash tools/quality-check.sh`: all checks passed: 40/40 selftests, 14
  adversarial probes held, branding/aliases/protocol identity, installed
  runtime ShellCheck, installer syntax and docs lint. Before `38f6cf6` it
  stopped at the CodeGraph selftest race, on main as well.
- `git diff --check`: clean.

No live provider was called. The native frozen gate was run later, from a
temporary install; see the final gate section above.

## Open findings and limits

None of these block the contract. After acceptance, at the owner's request,
the audit findings were fixed (see the audit for regressions):

- F1, fixed: `verify` with an unavailable base now exits 1 (FAIL), checked
  before the snapshot; it still records nothing.
- F2, fixed: the next handoff removes `.pending-*` scratch left by an
  interrupted handoff, and the next locked result write removes `.result-*`
  scratch left by a killed writer.
- Not mock-testable: real accounts or global configuration. A kill during
  the result-file write is covered only by the atomic rename and the sweep.
- `agents` reports `unknown` (not "missing") for wrappers such as
  `bash -c`, pipes or `$(...)` in the program word, by design.
- A live provider run is still an owner decision; every check so far uses
  mock agents.

M2 (the UI prototype, see TODO) may start when the owner asks for it.

## Boundaries

M1 adds dependable CLI evidence and a manual context packet. It does not
add a GUI, automatic provider migration, full dirty-file backup, an OS
sandbox, or automatic merging. No global installation is part of this task.
Use [the continuation prompt](../continue-with-ai-prompt.md) to start the
next AI session; [AI-HANDOFF.md](AI-HANDOFF.md) is supporting product context.
