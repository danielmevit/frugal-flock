# Copy this prompt to continue with another AI

When you change AI tools or start a new chat, this file tells your next
helper where the project stands. Open the **Prompt to paste** section below,
copy the text inside the box, and paste it into that AI. If it cannot open
GitHub, attach this file and the handoff documents it names.

Living checkpoint, updated 2026-10-04 by Claude Code (Claude Opus 5.5). Update this file with EVERY small
checkpoint so another AI can continue without the previous conversation.

## Current checkpoint

- Public repo: https://github.com/danielmevit/frugal-flock.
- Main: `5d70223`, the owner's merge of the four FF-QUALITY commits
  (`agent/codex` at `80feafb`), published 2026-10-04. Runtime prints 0.4.0,
  but it is not an accepted release. **M1 is NOT complete.**
- Newest work: branch `agent/claude` in `wt/claude`, by Claude Code (Claude
  Opus 5.5) on 2026-10-04, merged into main at the owner's request. It has
  `e9bfb1a` (M1 item 1, hidden index flags), `38f6cf6` (flaky CodeGraph
  selftest) and `9d48b76` (M1 item 2, post-run snapshot failure), followed
  by a docs checkpoint.
- Tests on `9d48b76`: 16 basic + 75 contract checks passed; the full
  `tools/quality-check.sh` passed (40/40 selftests, 14 probes, branding,
  ShellCheck, syntax, docs lint). The native frozen verify gate was not
  rerun because the global tool is still 0.3.1. No provider was called.
- Remaining M1 work: items 3 to 5 in [M1-STATUS.md](docs/M1-STATUS.md):
  acceptance coverage, help/completion and docs/Word manuals, final gates.
- No worker is active. `agent/codex` and `agent/kimi` are historical.
- Everything belonging to this project stays under
  `/mnt/d/Vibe Coding/_vm/frugal-flock`: main checkout `repo/`, worktrees
  `wt/`, tasks/reports `coord/`, private artifacts `artifacts/`, temporary
  checks `tmp/`. Read [WORKSPACE-RULES.md](WORKSPACE-RULES.md).
- Agent log rule: read the local `coord/AGENT-LOG.md` first; add a dated
  entry (agent, exact model, branch, SHA, tests, next task) after every
  checkpoint.

## Prompt to paste

```text
Continue Frugal Flock at https://github.com/danielmevit/frugal-flock.
Locally, read coord/AGENT-LOG.md in the enclosing frugal-flock folder
FIRST: the newest work may be on another agent's branch. Then read
continue-with-ai-prompt.md and docs/M1-STATUS.md from the newest branch
named there (currently agent/claude), followed by WORKSPACE-RULES.md and
the frozen docs/QUALITY-M1-CONTRACT.md. Preserve existing changes and
follow the applicable MASTER.md/WORKER.md lead-versus-worker rules.
Use CodeGraph only if .codegraph exists; do not create an index unasked.

State: main is 5d70223 (FF-QUALITY merged by the owner, M1 NOT complete).
agent/claude, by Claude Code (Claude Opus 5.5), adds fixes for M1 items 1
and 2 plus a selftest race fix and docs, merged into main. Fetch and
inspect the actual state; do not reset work or rebuild completed fixes.
Locally the main folder is /mnt/d/Vibe Coding/_vm/frugal-flock/repo and
worktrees are under ../wt. ALL project-owned work stays inside the
enclosing frugal-flock folder; use its tmp directory for checks. Installed
tools/credentials stay in their system locations; never copy credentials.

Say what you will do, then work in SMALL checkpoints. NEXT: M1 item 3,
missing acceptance coverage (binary/oversized/partial review material,
interrupted handoff publication) and an audit against every frozen
contract clause. Then item 4: help/completion for result, handoff and
agents --json; Python dependency, JSON schema, review exits, protocol
copies, changelog and affected Word manuals. Then item 5: all gates.

After EVERY checkpoint: targeted tests, exact diff review, named-path
commit, then add a dated entry at the top of coord/AGENT-LOG.md (agent,
exact model, worktree/branch/SHA, tests actually run, next task) and
update continue-with-ai-prompt.md and M1-STATUS on your branch. Save
progress before approaching a usage limit. Clearly label partial work;
never present a passing old suite as full milestone acceptance.

Run bash tests/frugal-flock-quality.sh, bash tools/quality-check.sh,
installer syntax, docs lint, and git diff --check, with TMPDIR set to the
workspace tmp folder. Use mock providers and temporary installs only.
Record actual results rather than reusing counts. Do not claim M1
complete while known gaps remain.

Preserve frugal-flock, frgl-flc, legacy agentteam, AGENTTEAM_* variables,
existing config paths, and Linux flock. No global installation, credential
changes, paid fallback, merge, push or release without owner authorization.

The owner especially values capacity-aware task sizing and safe continued
work after provider limits. Read docs/CAPACITY-AWARE-CONTINUATION.md; it
is future work, not a shipped scheduler or universal quota API. M1
handoff is CONTEXT for the same checkout, not a dirty-file backup or
automatic migration. Future UI follows UX-DIRECTION/TOOLCRAFT-REFERENCE:
original components only, no copied Toolcraft scaffold/code/assets.
```

## Checkpoint discipline

Do not save all progress for the end of a long session. Keep each fix
reviewable and tested. Update this file and the local agent log whenever
the newest branch/SHA, verification, blocker, active-worker state, or next
task changes. Publish only when the owner authorizes it. Historical detail
belongs in the [continuation report](docs/SESSION-HANDOFF-2026-10-04.md),
which describes the state before the owner's merge and is kept unchanged.
