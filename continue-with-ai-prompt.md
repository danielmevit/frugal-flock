# Copy this prompt to continue with another AI

When you change AI tools or start a new chat, this file tells your next
helper where the project stands. Open the **Prompt to paste** section below,
copy the text inside the box, and paste it into that AI. If it cannot open
GitHub, attach this file and the handoff documents it names.

Living checkpoint, updated 2026-10-04. Update this file with EVERY small
checkpoint so another AI can continue without the previous conversation.

## Current checkpoint

- Public repo: https://github.com/danielmevit/frugal-flock.
- Stable runtime/latest handoff docs: `main`, runtime baseline 0.3.1.
- Unmerged quality candidate: `agent/codex`, commit
  `80feafb15049411238b864cace7077af3f43376b`.
- Candidate checkout is clean; no implementation worker is active.
- Owner's latest instruction: project-state cleanup and handoff only.
  Implementation is paused pending an explicit request to resume.
- Earlier frozen task gate on this same candidate: scope OK, 5/5 Validate
  commands passed. These are recorded pre-relocation results, not new tests.
- Earlier independent focused run: 16 basic + 64 contract checks passed. The gate
  also reran the full runner: 40 selftests, 14 adversarial probes, branding,
  installed-runtime ShellCheck, protocol identity, syntax and docs checks.
- **M1 is NOT complete.** Two correctness gaps, documentation and coverage
  still need work. Candidate version 0.4.0 is not an accepted release.
- Everything belonging to this project stays under
  `/mnt/d/Vibe Coding/_vm/frugal-flock`: main checkout `repo/`, active Codex
  checkout `wt/codex/`, tasks/reports `coord/`, private artifacts `artifacts/`,
  temporary checks `tmp/`. Read [WORKSPACE-RULES.md](WORKSPACE-RULES.md).
- The existing commits were transferred intact into the Codex workspace.
  The old agent/kimi branch is historical, not the active continuation target.

## What was checked during this cleanup

- Documentation lint passed for all 27 root/docs files and five additional
  workspace/changelog files. All 74 local links in the handoff set resolved.
- Git's worktree list places the main checkout and all five linked workers
  inside the enclosing `frugal-flock` folder. Worker checkouts were clean;
  `agentteam status` reported no running jobs. Whitespace checks passed.
- No application code changed and no runtime tests or provider calls were
  run for this cleanup. Earlier implementation results above remain historical.

## Prompt to paste

```text
Continue Frugal Flock at https://github.com/danielmevit/frugal-flock.
Read continue-with-ai-prompt.md from latest main FIRST, followed by
WORKSPACE-RULES.md,
docs/SESSION-HANDOFF-2026-10-04.md, docs/M1-STATUS.md, and the frozen
docs/QUALITY-M1-CONTRACT.md. Preserve existing changes and follow the
applicable AGENTS.md/MASTER.md/WORKER.md lead-versus-worker rules.
Use CodeGraph only if .codegraph exists; do not create an index unasked.

The implementation is NOT on main. It is on agent/codex at
80feafb15049411238b864cace7077af3f43376b. Fetch and inspect actual state;
do not reset work or rebuild completed features. Locally the main folder
is /mnt/d/Vibe Coding/_vm/frugal-flock/repo; worker is ../wt/codex.
ALL project-owned work belongs under the enclosing frugal-flock folder.
Keep source, worktrees, tasks, reports, artifacts and scratch inside it.
Use its tmp directory for temporary checks; do not scatter work in sibling
folders or shared temporary storage. Installed tools/credentials stay in
their supported system locations; never copy credentials into the project.
No worker was active at this checkpoint, but recheck before dispatching.

The owner's latest request was ONLY to clean project state and prepare
handoff documentation. Confirm the actual state and wait for an explicit
request to resume implementation. Do not launch agents, implement fixes,
or start UX simply because this prompt lists unfinished work.

Once authorized, finish quality M1 before UX. NEXT SMALL CHECKPOINT: close the hidden-index
flag gap. Actual contents are hashed, but Git diff/status-derived scope
and review material may omit assume-unchanged/skip-worktree edits. Reject
unsupported flags conservatively or prove complete coverage. Add regression
tests, keep result staleness detection working, and commit this one fix
before taking on another issue. The lead should prepare a bounded Codex
task first; old FF-QUALITY-kimi task/reports are historical, not a new
assignment and not a reason to use a different provider's workspace.

NEXT: preserve actual worker exit/final state when the post-run snapshot
fails; add the nonzero-worker/unsupported-file regression described in the
report. Then finish contract coverage, help/completion, dependency/schema/
command docs, protocol copies, changelog and affected Word manuals.

Work in SMALL checkpoints: one bounded correction, targeted tests, exact
diff review, named-path commit, then update continue-with-ai-prompt.md and
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

This checkpoint changes documentation and workspace organization only;
it does not fix any of the remaining quality issues. The original four
quality commits and their test record are unchanged by
this workspace reorganization. Run the next task in the Codex checkout;
never switch the main checkout to an unfinished implementation branch.
