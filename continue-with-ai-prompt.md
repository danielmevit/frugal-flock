# Copy this prompt to continue with another AI

When you change AI tools or start a new chat, this file tells your next
helper where the project stands. Open the **Prompt to paste** section below,
copy the text inside the box, and paste it into that AI. If it cannot open
GitHub, attach this file and the handoff documents it names.

Living checkpoint, updated 2026-10-04 by Claude Code (Claude Opus 5.5). Update this file with EVERY small
checkpoint so another AI can continue without the previous conversation.

## Current checkpoint

- Public repo: https://github.com/danielmevit/frugal-flock.
- **M1 is complete and accepted by the owner (2026-10-04).** All five items
  are merged into main and published. Runtime 0.4.0; no release tag yet.
  The owner's global install is still 0.3.1 until the owner reinstalls.
- Work was done by Claude Code (Claude Opus 5.5) as lead plus three
  parallel Claude subagents, each in its own worktree. Every step is its own
  revertable merge on main: `fade423`, `45803c1`, `ce3d57f`, `ec5fdee`,
  `dba78ce`, then the final status docs. Details and authors are in
  [M1-STATUS.md](docs/M1-STATUS.md).
- Final gate on `dba78ce`: the frozen task's 5 Validate commands all passed;
  its scope check failed only on 15 lead-written Markdown documents outside
  the frozen worker scope. Full quality-check on that tree: 40/40
  selftests, 16 + 78 + 23 quality checks, 14 probes held, branding,
  ShellCheck, docs lint. No live provider was called.
- After acceptance, audit findings F1 and F2 were fixed with regressions;
  see [M1-ACCEPTANCE-AUDIT.md](docs/M1-ACCEPTANCE-AUDIT.md).
- No worker is active. Older `agent/*` branches are history.
- Everything stays under `/mnt/d/Vibe Coding/_vm/frugal-flock`: `repo/`,
  `wt/`, `coord/`, `artifacts/`, `tmp/`. Read
  [WORKSPACE-RULES.md](WORKSPACE-RULES.md).
- Agent log rule: read the local `coord/AGENT-LOG.md` first; add a dated
  entry (agent, exact model, branch, SHA, tests, next task) after every
  checkpoint.

## Prompt to paste

```text
Continue Frugal Flock at https://github.com/danielmevit/frugal-flock.
Locally, read coord/AGENT-LOG.md in the enclosing frugal-flock folder
FIRST: newer work may be on another agent's branch. Then read, from main:
continue-with-ai-prompt.md, docs/M1-STATUS.md, docs/M1-ACCEPTANCE-AUDIT.md,
WORKSPACE-RULES.md and the frozen docs/QUALITY-M1-CONTRACT.md. Follow the
applicable MASTER.md/WORKER.md lead-versus-worker rules. Use CodeGraph only
if .codegraph exists; do not create an index unasked.

State: M1 is complete, merged into main and accepted by the owner. Do not
rebuild finished work. Locally the main
folder is /mnt/d/Vibe Coding/_vm/frugal-flock/repo and worktrees are under
../wt. ALL project-owned work stays inside the enclosing frugal-flock
folder; use its tmp directory for checks. Installed tools and credentials
stay in their system locations; never copy credentials.

NEXT: wait for the owner's direction. Candidates the owner may choose:
reinstall 0.4.0 globally (affects every project using the agentteam
command), a small live provider smoke run, a v0.4.0 release tag, or M2
(the mock-data UI prototype in TODO.md). Do not start M2 unasked.

Say what you will do, then work in SMALL checkpoints: targeted tests,
exact diff review, named-path commit, then a dated entry at the top of
coord/AGENT-LOG.md (agent, exact model, worktree/branch/SHA, tests
actually run, next task) and an update of this file and M1-STATUS on your
branch. Save progress before approaching a usage limit.

Run bash tests/frugal-flock-quality.sh, bash tools/quality-check.sh,
installer syntax, docs lint and git diff --check, with TMPDIR set to the
workspace tmp folder. Mock providers and temporary installs only. Record
actual results rather than reusing counts.

Preserve frugal-flock, frgl-flc, legacy agentteam, AGENTTEAM_* variables,
existing config paths, and Linux flock. No global installation, credential
changes, paid fallback, merge, push or release without owner authorization.

The owner especially values capacity-aware task sizing and safe continued
work after provider limits. Read docs/CAPACITY-AWARE-CONTINUATION.md; it
is future work, not a shipped scheduler. The M1 handoff is CONTEXT for the
same checkout, not a dirty-file backup or automatic migration. Future UI
follows UX-DIRECTION/TOOLCRAFT-REFERENCE: original components only, no
copied Toolcraft scaffold, code or assets.
```

## Checkpoint discipline

Do not save all progress for the end of a long session. Keep each fix
reviewable and tested. Update this file and the local agent log whenever
the newest branch/SHA, verification, blocker, active-worker state, or next
task changes. Publish only when the owner authorizes it. Historical detail
belongs in the [continuation report](docs/SESSION-HANDOFF-2026-10-04.md),
which describes the state before the owner's merge and is kept unchanged.
