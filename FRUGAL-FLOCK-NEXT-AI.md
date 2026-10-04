# Frugal Flock — next AI, start here

Living checkpoint, updated 2026-10-04. Update this file with EVERY small
checkpoint so another AI can continue without the previous conversation.

## Current checkpoint

- Public repo: https://github.com/danielmevit/frugal-flock.
- Stable runtime/latest handoff docs: `main`, runtime baseline 0.3.1.
- Unmerged quality candidate: `agent/kimi`, commit
  `80feafb15049411238b864cace7077af3f43376b`.
- Candidate checkout is clean; no implementation worker is active.
- Final frozen task gate: scope OK, 5/5 Validate commands passed.
- Independent focused run: 16 basic + 64 contract checks passed. The gate
  also reran the full runner: 40 selftests, 14 adversarial probes, branding,
  installed-runtime ShellCheck, protocol identity, syntax and docs checks.
- **M1 is NOT complete.** Two correctness gaps, documentation and coverage
  still need work. Candidate version 0.4.0 is not an accepted release.
- App folder renamed to `/mnt/d/Vibe Coding/_vm/frugal-flock`; linked Git
  worktrees repaired. Implementation checkout stays `../wt/kimi`.

## Prompt to paste into the next AI

```text
Continue Frugal Flock at https://github.com/danielmevit/frugal-flock.
Read FRUGAL-FLOCK-NEXT-AI.md from latest main FIRST, followed by
docs/SESSION-HANDOFF-2026-10-04.md, docs/M1-STATUS.md, and the frozen
docs/QUALITY-M1-CONTRACT.md. Preserve existing changes and follow the
applicable AGENTS.md/MASTER.md/WORKER.md lead-versus-worker rules.
Use CodeGraph only if .codegraph exists; do not create an index unasked.

The implementation is NOT on main. It is on agent/kimi at
80feafb15049411238b864cace7077af3f43376b. Fetch and inspect actual state;
do not reset work or rebuild completed features. Locally the main folder
is now /mnt/d/Vibe Coding/_vm/frugal-flock and worker is ../wt/kimi.
No worker was active at this checkpoint, but recheck before dispatching.

Finish quality M1 before UX. NEXT SMALL CHECKPOINT: close the hidden-index
flag gap. Actual contents are hashed, but Git diff/status-derived scope
and review material may omit assume-unchanged/skip-worktree edits. Reject
unsupported flags conservatively or prove complete coverage. Add regression
tests, keep result staleness detection working, and commit this one fix
before taking on another issue.

NEXT: preserve actual worker exit/final state when the post-run snapshot
fails; add the nonzero-worker/unsupported-file regression described in the
report. Then finish contract coverage, help/completion, dependency/schema/
command docs, protocol copies, changelog and affected Word manuals.

Work in SMALL checkpoints: one bounded correction, targeted tests, exact
diff review, named-path commit, then update FRUGAL-FLOCK-NEXT-AI.md and
M1-STATUS with the candidate SHA, actual tests, gaps, active workers and
ONE next task. Save progress before approaching a usage limit. If lead
and worker scopes differ, the lead updates this file immediately after
the worker commit in the same checkpoint batch. Clearly label partial
work; never present a passing old suite as full milestone acceptance.

Run bash tests/frugal-flock-quality.sh, bash tools/quality-check.sh,
installer syntax, docs lint, and git diff --check. Use mock providers and
temporary installs only. In the native local setup also run the frozen
agentteam verify gate. Record actual results rather than reusing counts.
Inspect the real diff. Do not claim M1 complete while known gaps remain.

Preserve frugal-flock, frgl-flc, legacy agentteam, AGENTTEAM_* variables,
existing config paths, and Linux flock. No global installation, credential
changes, paid fallback, merge or release without owner authorization.
Confirm authority for future pushes; prior approval covered publication
of the saved checkpoint, not unlimited later external changes.

The owner especially values capacity-aware task sizing and safe continued
work after provider limits. Read docs/CAPACITY-AWARE-CONTINUATION.md on
main; it is future work, not a shipped scheduler or universal quota API.
M1 handoff is CONTEXT for the same checkout, not a dirty-file backup or
automatic migration. Future UI follows UX-DIRECTION/TOOLCRAFT-REFERENCE:
original components only, no copied Toolcraft scaffold/code/assets.
```

## Checkpoint discipline

Do not save all progress for the end of a long session. Keep each fix
reviewable and tested. Update this file whenever its implementation SHA,
verification, blocker, active-worker state, or next task changes. Publish
the candidate and handoff together when authorized. Historical detail
belongs in the [continuation report](docs/SESSION-HANDOFF-2026-10-04.md).
