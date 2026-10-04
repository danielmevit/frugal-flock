# Copy this prompt to continue with another AI

When you change AI tools or start a new chat, this file tells your next
helper where the project stands. Open the **Prompt to paste** section below,
copy the text inside the box, and paste it into that AI. If it cannot open
GitHub, attach this file and the handoff documents it names.

Living checkpoint, updated 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh). Update this file with EVERY small
checkpoint so another AI can continue without the previous conversation.

## Current checkpoint

- M1.5 step 2 complete, 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh),
  wt/codex on agent/codex source candidate `d930a87`: corrected frozen full
  gate passed, 40 selftests, 16 + 78 + 26 existing regressions, 22 brake
  cases, 14 probes held, packaging/aliases/completion, ShellCheck, syntax
  and docs. No quota/global changes. First gate's protocol mismatch and
  reassignment gap corrected. Receipt: tmp/m15-loop-brake-20261004/
  quality-check-corrected.log. Publishing as its own merge/push.
  Watch draft is ready: 26 focused checks and packaging passed, direct
  signal delivery, local recorded states, unknown completion on free locks,
  no evidence rewrites or readiness/quota claims. M2 draft has four state
  tests and the full browser journey passing; source only after stability
  checkpoints. Next: watch publication, then the fresh-install OpenCode
  `--auto` compatibility fix. Native help confirms --auto with no quota use.

- M1.5 step 2 correction, 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh),
  wt/codex on agent/codex candidate `3a68a8a`: frozen full gate passed
  40 selftests, 16 + 78 + 26 regressions, 18 brake checks and all 14 probes,
  then failed standalone branding because docs/PROTOCOL.md differed from
  the embedded template. Corrected both copies. Source review also found
  interrupted starts were reconciled only on the same worker; reconcile
  lost starts across workers while leaving held locks alone. Added four
  focused reassignment/active-lock checks (22 total) before a new frozen
  full gate. No provider call/global changes. A separate watch draft passed
  24 focused mock checks after fixing CLI signal delivery; final 25-check
  source suite includes the honest runner-pattern limit explanation.
  Next: corrected brake full gate/publication, then watch and the stale
  fresh-install OpenCode flag fix, each as its own merge/push.

- M1.5 step 2 draft, 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh),
  wt/codex on agent/codex based on main `6e16947`: loop brake implemented
  in source, 18 focused mock checks passed. Covers real exit preservation,
  failure deduplication, task-wide history, one retry grant, validation and
  interrupted failures, corrupt state, concurrency and zero provider calls
  after refusal. Syntax and whitespace passed. Documentation preparation
  initially expected two template anchors but found one; corrected that
  assertion before the frozen full gate. No global install/config changes
  or paid calls. Next: full gate, own merge/push, then step 3 watch.

- M1.5 step 1 complete, 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh):
  owner-approved Codex retest passed in 26s using native gpt-6.1-sol/high,
  throwaway `93c4cc9`, one file/commit, clean branch, scope OK, verify 2/2.
  Full task/diff approved here, then the approved live Grok review passed
  in 82s, exit 0/APPROVE, current ready result. All six latest canaries
  ready/current; human pending/integration not attempted. Seven worker
  invocations/one live reviewer total, one specifically approved retest,
  no automatic retries. Original Codex interruption preserved under
  live/receipts/codex/attempt-1; retest under attempt-2. Fixture STOP, no
  active worker; installed runtime/global config hashes unchanged. Source
  canary completion merged/pushed as `6e16947`; every finished step gets
  its own merge/push.
  The owner asked to continue the list without stopping. Next: M1.5 step 2,
  engine loop brake, then watch, using local mocks/source builds. Further
  provider calls need fresh quota approval. Keep the recorded interruption
  activity-observation limitation for a separate mock-tested fix.

Historical checkpoints below preserve how this state was reached; the
newest bullet above governs readiness, quota authorization and next work.

- The owner approved the pending bounded retest on 2026-10-04: one fresh
  Codex worker invocation (180s), then one Grok review only after passed
  validation (120s), no further retries. Root also reviews the full diff
  here. Original interrupted Codex evidence archived under live/receipts/
  codex/attempt-1/ before the native latest-run log is replaced. Main is
  `090cfd3`; installed runtime/global config unchanged. Retest is next;
  the interrupted-activity observation fix remains a separate mock task.
- Mock diagnosis, 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh): source
  includes main `b8625c7` (passing Claude evidence, candidate `7511197`),
  with Codex recovery published as `aadc005` and Kimi as `9fadc8a`.
  CodeGraph returned no relevant installer code; inspected the embedded
  quality helper and runner. A fresh workspace-local interruption fixture
  reproduced stale running/null-exit status using the unchanged installed
  0.4.0, one local mock invocation and zero provider calls. Killed only
  that harness's own runner/mock groups; verify acquired the released lock,
  exited 1/2/empty_work, result not ready. Handoff acquired the free lock
  and published a complete packet with its existing interruption warning.
  No runtime or live result changed; both fixtures STOP, no active worker.
  Local receipts: tmp/m15-interruption-20261004/receipts/. Five live canaries
  passed; six approved attempts used, Codex interrupted, no extra provider
  reviews/retries. Fresh Codex (180s) plus conditional Grok review (120s)
  quota approval was subsequently granted for those two bounded calls above.
  Diagnosis is recorded for its own merge. Next: a mock-tested interruption
  activity observation fix; preserve unknown exit and the distinction between a free
  worker lock and the possible existence of detached processes.
- Claude canary, 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh): explicit
  Claude Sonnet 5.5 (`claude-sonnet-5-5`), medium, passed in 23 seconds.
  Native JSON confirms Sonnet; throwaway commit `4163ce4`, one file/commit,
  exact marker, clean branch, scope OK, verify 2/2. Full task/diff inspected
  here, approved with no findings and transported through the sealed local
  adapter; native review exit 0, current ready result, human pending,
  integration not attempted. Local agent entries restored; global native
  agents.conf/installed 0.4.0 hashes unchanged. Six worker invocations total,
  zero additional provider reviewers, no retries; all approved calls used.
  Five ready canaries; Codex remains interrupted, zero commits/verify 1/2,
  native process still running despite no surviving worker. M1.5 step 1 is
  incomplete. Fixture STOP active, no worker active. Claude evidence merged
  and pushed as `b8625c7`. Interruption status subsequently reproduced with mocks above. Any Codex rerun needs fresh quota approval; native review needs a
  different vendor. Sonnet success does not prove the Opus limit cleared.
- Access recovery checkpoint, 2026-10-04 by Codex (`gpt-6.1-sol`, xhigh):
  the owner restored unrestricted execution after the session sandbox failed
  on a `.aws` symlink rule and excluded this workspace from writable roots.
  Shell commands now work. Main is `9fadc8a`, with the Kimi merge published;
  installed 0.4.0 and global agents.conf hashes are unchanged. Recovered
  evidence shows a fifth worker invocation: Codex (`gpt-6.1-sol`, high)
  already started before interruption. No completion, exit or reliable
  duration captured; unchanged clean baseline, zero commits, verify 1/2
  failed. Native process still says running despite no surviving worker;
  result not ready. Preserve this interrupted-run recovery gap, no retry.
  Fixture STOP active. Codex evidence merged/pushed as `aadc005`. Next:
  Claude's single approved Sonnet 5.5/medium canary subsequently passed above.
  The interrupted-run status gap is the remaining local finding.
- Owner resumed M1.5 on 2026-10-04: “do all in one go” approves one
  remaining Kimi and Codex worker invocation each; no retries or separate
  provider reviewer calls. He additionally explicitly approved one Claude
  test with a simpler model and medium/high effort despite its earlier limit.
  Selected Claude Sonnet 5.5 (`claude-sonnet-5-5`), medium; installed CLI
  help and official docs confirm the flags. Kimi's native model is
  `opencode-go/kimi-k3`, using current `--auto` instead of the obsolete
  native permission flag, with global settings unchanged. The throwaway
  fixture's missing agent entries were repaired locally; doctor now passes
  with only intentional STOP. Codex reviews here; its own worker cannot
  receive native approval from the same vendor and may retain pending review.
  Kimi K3 passed in 45 seconds: throwaway `6e98e46`, one commit/file,
  scope OK, 2/2 checks, complete diff approved here, sealed local review,
  current ready result. Worker invocations were four at Kimi's
  checkpoint; now five including interrupted Codex above. Zero extra
  provider reviewers. Kimi was merged/pushed as `9fadc8a`; own worktree
  includes it. Claude subsequently passed; all approved calls now used.
- Current owner request: AGPL-3.0-only for the public release, with optional
  separate paid agreements for proprietary use. The owner explicitly chose
  true open source on 2026-10-04 after being told compliant commercial forks
  may be sold without paying him. Copyright holder: Daniel Mitev; public
  attribution: Daniel Mevit (@danielmevit). Full unmodified GNU text in
  LICENSE; section 7(b)/(c) attribution/origin terms in NOTICE and referenced
  by source headers. The owner clarified credit applies to copies and
  variants of Frugal Flock itself, not independent projects made with it.
  Preserve the tool name, Daniel's credit and original URL in covered
  material or appropriate legal notices; mark variants and do not
  misrepresent origin. The self-contained
  installer bundles both under the config directory's legal/ folder;
  `frugal-flock license` prints them. README and [licensing guidance](docs/LICENSING.md)
  explain notices/source obligations, lawful sales, independently developed
  projects, legal limits and separately agreed proprietary permissions.
  Licensing source candidate: `b83f767` on agent/codex in wt/codex.
  Full frozen-source quality gate passed: 40/40 selftests, 16 + 78 + 26
  regressions, 14 probes held, standalone legal-file packaging and all
  three aliases, ShellCheck, installer syntax and full docs lint. Official
  LICENSE hash and embedded legal-file equality verified; whitespace clean.
  Log: tmp/license-checkpoint-20261004/quality-check-frozen.log. The first
  interrupted run is retained in quality-check.log and the append-only agent
  log. This is one owner-authorized licensing integration; find its merge
  on main's first-parent history. Source checkpoint complete; next work is
  M1.5 canary follow-up: all six attempts used, five passed, Codex interrupted.
  Global installed 0.4.0 and all canary evidence remain unchanged; no quota call.
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
  Grok was merged/pushed as `c06f808`.
- OpenCode Go `opencode-go/glm-5.3` passed in 24 seconds, throwaway commit
  `2b847ac`. Runtime model confirmed, scope OK, 2/2 checks, complete diff
  approved by this Codex session through the sealed local adapter, current
  ready result. Worker calls at that checkpoint: three; no extra reviewer calls, retries
  or Claude calls. Fixture stopped. This checkpoint was merged/pushed as
  `7761737`. Codex was subsequently interrupted; Claude subsequently passed.
  Its source evidence candidate is `17c4959` on `agent/codex`.
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
  M1.5 step 1 remains incomplete: Codex was interrupted without a completed
  change; Claude Sonnet 5.5/medium passed its explicitly approved exception
  in 23 seconds. Kimi K3 has passed.
  The installed 0.4.0 passed the mock run/verify/review/result rehearsal,
  including review gating and stale-result checks. The full offline gate
  passed: 40/40 selftests, 16 + 78 + 26 quality checks, 14 probes held,
  branding, ShellCheck, installer syntax and docs lint. Whitespace clean.
  No worker is active. All approved calls used; future calls need approval.
  Claude evidence is published; mock diagnosis above records the status limitation.
  Claude is owner-reported limited for five hours (avoid through
  22:42 +0200 on 2026-10-04, an operator interval, not a confirmed reset).
  The owner explicitly permits this one Sonnet 5.5/medium Claude canary.
  Codex does the main implementation and reviews in-session. Other worker
  calls need fresh quota approval; no separate provider reviewer call authorized.
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
   result). OpenCode Go (`opencode-go/glm-5.3`) passed in 24 seconds, one
   call, verify 2/2, lead review and ready result. Kimi K3 passed in 45s.
   Claude Sonnet 5.5/medium passed in 23 seconds. Codex's original call
   was interrupted; its explicitly approved retest passed in 26 seconds,
   verify 2/2, lead approval and live Grok review (82s), current ready result.
   All six latest canaries passed: step 1 complete. Seven worker calls and
   one live reviewer total; one specifically approved retest, no automatic
   retries. Fixture stopped, global settings unchanged. Preserve original
   interruption evidence and mock diagnosis of stale running activity;
   fix that observation separately without inventing worker exits.
   Continue step 2 (loop brake), then step 3 (watch), with mocks. No further
   provider call currently authorized.
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
