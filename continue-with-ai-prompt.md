# Copy this prompt to continue with another AI

When you change AI tools or start a new chat, this file tells your next
helper where the project stands. Open the **Prompt to paste** section below,
copy the text inside the box, and paste it into that AI. If it cannot open
GitHub, attach this file and the handoff documents it names.

Living checkpoint, updated 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh). Update this file with EVERY small
checkpoint so another AI can continue without the previous conversation.

## Current checkpoint

- Antigravity live evidence is committed at `13e70e9` on `agent/codex` in
  `wt/codex`, merged and pushed as `0426f0c`.
- Codex worktree synced with main `81b587c`; read and preserve the owner's
  README and BRAND description/topics updates. On 2026-10-04 the owner
  authorized one Grok canary and one OpenCode Go canary using GLM 5.3.
  Installed model registry confirms `opencode-go/glm-5.3`. Run sequentially,
  180 seconds each, no retries; this Codex session reviews both without
  additional provider calls. Global provider configuration stays unchanged.
- Grok evidence candidate: `2203b3b` on `agent/codex`. Grok passed in
  35 seconds: throwaway commit `868036f`, scope OK, 2/2
  checks, in-session Codex review approved and a current ready result.
  Total live worker calls: two (Antigravity and Grok); no extra reviewer
  calls, retries or Claude calls. Fixture stopped. Next: publish this Grok
  checkpoint, then the authorized OpenCode Go GLM 5.3 canary.
- M1.5 preparation is merged and pushed as `d991350` (candidate `4b8e1a9`
  plus `61327ec`). The owner-approved README rewrites `4565cfd` and `f6f0ed9` are also
  on main and included in this Codex worktree; preserve it.
  [Canary plan and evidence](docs/M1.5-LIVE-CANARY.md). The isolated live
  fixture is `tmp/m15-canary-20261004/live/`, with all six workers including
  Antigravity at the owner's explicit request. **Antigravity passed in
  22 seconds**, one commit `66793a1`, verify 2/2, this session's Codex code
  review approved through a sealed local adapter, current ready result.
  One live worker invocation, no extra reviewer call or retry. The earlier
  silent stall did not recur. Receipts stay local; its STOP file is active.
  M1.5 step 1 remains incomplete: OpenCode's GLM 5.3 call has not started;
  codex/kimi/claude canaries also remain unrun.
  The installed 0.4.0 passed the mock run/verify/review/result rehearsal,
  including review gating and stale-result checks. The full offline gate
  passed: 40/40 selftests, 16 + 78 + 26 quality checks, 14 probes held,
  branding, ShellCheck, installer syntax and docs lint. Whitespace clean.
  No worker is active. Next: the authorized OpenCode Go GLM 5.3 canary.
  Claude is owner-reported limited for five hours (avoid through
  22:42 +0200 on 2026-10-04, an operator interval, not a confirmed reset).
  Codex does the main implementation and reviews in-session. Other worker
  calls beyond those two need quota approval; no separate provider reviewer call authorized.
  The owner authorized each finished checkpoint's own merge and push.
- Public repo: https://github.com/danielmevit/frugal-flock.
- **M1 is complete and accepted by the owner (2026-10-04)** and released as
  v0.4.0 (tag and GitHub release; notes in [CHANGELOG.md](CHANGELOG.md)).
  0.4.0 is installed globally; the 0.3.1 files are backed up locally.
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

NEXT: the M1.5 stability phase, approved by the owner on 2026-10-04, in this
order, one small tested checkpoint each:
1. Live canary: a throwaway repo, one tiny task per agent through run,
   verify, review and result. Tiny tasks only; it uses provider quota.
   Preparation was merged/pushed as d991350; read docs/M1.5-LIVE-CANARY.md.
   The fixture is tmp/m15-canary-20261004/live; all six workers are ready,
   including Antigravity at the owner's request to recheck its earlier error.
   Antigravity passed in 22 seconds (run/verify/lead review/result); one
   worker call, zero extra reviewer calls, no retry. STOP is active again.
   Grok also passed in 35 seconds (one call, verify 2/2, lead review, ready
   result). OpenCode Go (`opencode-go/glm-5.3`) is authorized next, one
   call with no retries. The Codex lead reviews in-session; do not
   call Claude before 22:42 +0200 on 2026-10-04 (operator interval, not a
   provider-confirmed reset). Other worker calls need approval.
   Ask before spending provider quota; no retries or fallback calls.
2. Loop brake in the engine: a task that failed twice is refused until
   the owner explicitly allows another attempt.
3. Live monitor (`frugal-flock watch`): runs, verdicts, failures and limits
   as they happen; it later becomes the app's Activity view.
4. The flock runs on the installed release while it builds the next
   version in the repo; reinstall only at deliberate releases.
5. Bench Antigravity for dogfooding until it passes the canary (2 of 2
   earlier live runs failed). Include it in step 1 as the owner requested.
Then dogfood on M2 (the mock-data prototype): one worker plus a reviewer,
owner merges; widen after a few clean cycles.

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
