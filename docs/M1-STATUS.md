# Milestone 1 — quality checkpoint

## Status

In progress, **not accepted**. On 2026-10-04 the owner merged the four
FF-QUALITY commits (`agent/codex` at `80feafb`) into main as `5d70223`
and published them. That merge is not M1 acceptance. The runtime prints
0.4.0, but that is not an accepted release; the accepted baseline is 0.3.1.

Frozen requirements: [QUALITY-M1-CONTRACT.md](QUALITY-M1-CONTRACT.md)
at `e230ad4`. Current work: branch `agent/claude` in `../wt/claude`,
relative to the main `repo/` checkout. It was made by Claude Code (Claude
Opus 5.5) on 2026-10-04, branched from main `5d70223`, and is NOT merged:

- `e9bfb1a`: item 1 below (hidden index flags) fixed, with regressions.
- `38f6cf6`: the flaky CodeGraph selftest fixed; the full runner passes.
- `9d48b76`: item 2 below (post-run snapshot failure) fixed, with regressions.
- The docs checkpoint after these: this file, the usage doc, the changelog
  fragment, the continuation prompt and the agent-log rule.

Every agent reads the local `../coord/AGENT-LOG.md` first and adds a dated
entry after each checkpoint. See [WORKSPACE-RULES.md](../WORKSPACE-RULES.md).
The former `agent/codex` and `agent/kimi` branches are historical.

## Resume locally

```bash
cat ../coord/AGENT-LOG.md
git -C ../wt/claude status --short --branch
git log --oneline main..agent/claude
```

Inspect the current work without changing either checkout:

```bash
git diff main...agent/claude --stat
git diff main...agent/claude -- agentteam-install.sh tests/
```

Continue on top of `agent/claude`, or start from main once the owner has
merged it. Review the real diff, not just the report. Never reset a dirty
worktree or restart an interrupted implementation from scratch.

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
`docs/QUALITY-USAGE.md` was later updated in part; see item 4 below.

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

No live provider was called. The native frozen `agentteam verify` gate was
not rerun: the installed global tool is still 0.3.1 and was left alone.

## Remaining before M1 can be accepted

1. DONE on `agent/claude` (`e9bfb1a`): the hidden-index-flag gap. Verify,
   review and handoff refuse assume-unchanged/skip-worktree flags, and
   changed() disables fsmonitor.
2. DONE on `agent/claude` (`9d48b76`): post-run snapshot failure. Run keeps
   the real exit, report and ledger, and marks the result unbound and stale.
3. Expand missing acceptance coverage, especially binary/oversized review
   material, interrupted packet publication, and a systematic audit
   against every frozen contract clause.
4. Update help/completion for `result`, `handoff` and `agents --json`,
   Python dependency/setup instructions, result schema and command docs,
   changed review exits/constraints, operational protocol copies, and
   affected Word manuals. `docs/QUALITY-USAGE.md` and the changelog
   fragment now cover items 1 and 2 but are otherwise incomplete.
5. Run all gates again, including the native frozen verify gate, inspect
   the exact final diff, and obtain owner acceptance/integration before
   claiming M1 complete or starting live UX.

Do not repeat the completed rename, research, or first increment. The
runtime embeds its own helper; the older scratch prototype in
`artifacts/legacy-prototypes/agentteam-quality.py` is obsolete and must
not replace it. A fresh clone needs no private logs or old conversation.

## Boundaries

M1 adds dependable CLI evidence and a manual context packet. It does not
add a GUI, automatic provider migration, full dirty-file backup, an OS
sandbox, or automatic merging. No global installation is part of this task.
Use [the continuation prompt](../continue-with-ai-prompt.md) to start the
next AI session; [AI-HANDOFF.md](AI-HANDOFF.md) is supporting product context.
