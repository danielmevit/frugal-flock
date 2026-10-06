# Frugal Flock — Codex closing handoff to Claude

Updated 2026-10-05 by Codex, exact model gpt-6.1-sol, xhigh, working in
wt/codex on agent/codex. The owner asked to bench this session, save/push
current files, and continue in a new Claude session. Pre-close main was
c94e21c; this document ships in its own closing merge. Use current main,
not a historical SHA, for the next implementation baseline.

## Read first and current operating state

Read local coord/AGENT-LOG.md FIRST. Then read the current
[continuation prompt](development/continue-with-ai-prompt.md), this handoff,
[workspace rules](development/WORKSPACE-RULES.md), the Near-term roadmap and section
1.5 in [Roadmap](development/ROADMAP.md), [dogfood workflow](DOGFOOD-WORKFLOW.md), and the
[next queue contract](JOB-QUEUE-STORE.md).

The enclosing workspace is /mnt/d/Vibe Coding/_vm/frugal-flock. Its main
checkout is repo/; source edits use an agent's own branch under wt/.
All project scratch, receipts and fixtures remain under tmp/. Native CLIs,
authentication stores and shared caches remain in their system locations.
Do not overwrite or delete old worktrees, branches, role cards or reports.
The agent log is append-only; after every checkpoint prepend a dated entry
with local UTC offset, exact model, branch/SHA, actual tests and ONE next
step, and update the tracked continuation prompt.

Project coord/STOP is deliberately set. Native status reported no active
workers. Queue worker and reviewer invocation counts are both ZERO.
The earlier quota question is superseded by the owner's bench instruction;
there is no approval to launch either queued option. Global agents were not
switched off, and global configuration/authentication was not changed.
A fresh session is not evidence of provider capacity or a quota reset.

Installed Frugal Flock remains v0.4.0. The newer loop brake, watch, OpenCode
compatibility and bridge code are published source, not a new global install
or release. Keep dogfooding on the installed release while building the next
version. Ask before any provider quota, fallback, retry, install or release.
The owner already authorized each finished tiny step's own no-ff main merge
and push; include latest main first and retain original histories.

## What is already published

M1 is complete, accepted and released. All five initial M1.5 stability
items are complete in source. The broader application roadmap is ongoing.
Preserve the owner's README/BRAND/GitHub branding updates from 81b587c.

| Step | Published merge | Evidence and limits |
|---|---|---|
| AGPL license and attribution | d0645ed | LICENSE/NOTICE, Daniel Mitev; public Daniel Mevit (@danielmevit), Frugal Flock origin notices |
| Six live canaries | 6e16947 | Antigravity 22s, Grok 35s, GLM 24s, Kimi 45s, Sonnet 23s, Codex 26s; seven worker calls plus one Grok reviewer, original interruption preserved |
| Engine loop brake | 959fb0c | Corrected candidate d930a87; full gate: 40 selftests, 120 existing regressions, 22 brake checks, 14 probes, packaging/ShellCheck/docs |
| Read-only watch | 64160c5 | 26 focused checks; real canary observation without coordination writes; unknown completion stays unknown |
| Fresh OpenCode defaults | 8532f56 | --auto compatibility, offline dispatch/diagnosis/profile preservation; existing profiles unchanged |
| Original mock prototype | 5d40d68 | Five connected sample-data moments, four state tests and Chromium journey; no real execution |
| Prototype keyboard enhancement | 5a9b037 | GLM native attempt failed; root finished directly; state/browser checks passed |
| Claude user-test guide | cdcfad0 | Real native Claude docs task, 83s, exit 0, verify 2/2, in-session Codex review; blank feedback records |
| Read-only Activity bridge | 41f5b77 | Loopback observation, HTTP/browser checks, actual project read without writes |
| Optional browser opening | 2b9bb32 | Opt-in --open-browser/manual fallback, eleven HTTP/observer/opening checks |
| Owner feedback waiver | 4747000 | Two-person prerequisite explicitly waived; no user sessions fabricated |
| Immutable manual draft store | 7c6be5a | Eight stdlib checks, restart/hash/concurrency/path refusal |
| Protected opt-in manual API | 4104409 | Eight API checks, eleven HTTP checks, default browser and actual restart/token rotation |
| Manual Save/reopen form | 0158039 | Default/manual Chromium journeys, duplicate/failed save behavior, literal text, mobile screenshots |
| Native dogfood task preparation | 402f538, c94e21c | Frozen JobStore contract, two clean options; neither worker launched |

The manual draft UI saves literal text and can reopen saved IDs. Default
bridge mode remains read-only. Saving is not an AI-generated plan, approval,
native task, job dispatch or integration. Last saved ID is in the URL
fragment; unconfirmed/unsaved text can be lost on refresh. The owner waived
two new-user sessions because testers are unavailable; no actual sessions
occurred. This waiver does not waive quota or evidence gates.

Still absent: durable queue implementation, task compilation, approval/
reservation/recovery, live execution controls, packaged project launcher/
folder selection/setup, and checkpointed cross-provider continuation.
M1's context packet is not a backup of dirty files or automatic migration.

## Honest dogfood evidence

The main goal is to build Frugal Flock WITH Frugal Flock. After GLM failed,
root directly implemented several prototype/bridge/draft slices. Those are
published useful code, but must not be represented as native worker success.
The owner corrected this drift; follow the native cadence for next milestones.

GLM's one approved M2 keyboard invocation timed out at 180 seconds, exit 124,
with no edits/commits. Tool discovery consumed the window. Native validation
recorded empty work as failure; no retry occurred. Preserve the report and
partial-state history, even though root later finished the code directly.
Claude Opus 5.5/high's separate guide invocation succeeded in 83 seconds at
eaf24e6. Validation and root review passed; ready evidence was captured before
integration, not human acceptance. Its retained agent/claude-m2 commit was
cherry-picked as bf6b70f and integrated in cdcfad0; do not redo it because the
old branch still appears to have an unmerged commit.

Local receipts: tmp/m15-canary-20261004, tmp/m2-keyboard-20261004,
tmp/m2-claude-feedback-20261004, tmp/m2-bridge-20261004, tmp/bridge-plan-api,
tmp/bridge-plan-ui, tmp/job-queue-dogfood and tmp/session-close-20261005.
Native records remain in coord/reports and coord/results. They are local,
not published raw logs. Recheck result freshness; main movement can stale
historical evidence. Authentication/capacity remain unknown.

## ONE next implementation task

Implement bridge/job_store.py and bridge/tests/job_store_test.py following
[JOB-QUEUE-STORE](JOB-QUEUE-STORE.md), plus the named handoff/changelog files.
This first SQLite slice persists jobs only in awaiting_owner_approval,
requires a fresh matching PlanStore hash, and provides restart persistence
and transactional idempotency. No HTTP/UI wiring or provider execution.

Prepared local options are wt/claude-queue on agent/claude-queue and
wt/opencode-queue on agent/opencode-queue. Their original task files are
coord/tasks/JOB-QUEUE-STORE-claude-queue.md and
coord/tasks/JOB-QUEUE-STORE-opencode-queue.md. Manifests/config/wrappers are
under tmp/job-queue-dogfood/claude and tmp/job-queue-dogfood/opencode.
Original baseline c94e21c is now historical; task hashes are preserved.
Both manifests say benched_not_launched/deferred_by_owner, zero calls.

For Claude taking over as lead:

1. Read the log/current main; create or inspect your OWN lead worktree,
   for example wt/claude-lead on agent/claude-lead. Existing queue worktrees
   have worker-only role cards. Preserve old branches; do not rerun init.
2. Refresh ONE selected worker from current main while it is clean/unlocked.
   Reissue a NEW task ID and manifest pinned to that main, preserving the
   old frozen files. Update actual lead/reviewer and role-card instructions.
3. To review here with no extra paid reviewer, prefer a different provider
   worker (prepared GLM 5.3/max), so the native different-agent review gate
   remains truthful. Do not reuse a Codex-authored review adapter or present
   same-provider self-review as an independent different-provider review.
   A Claude worker instead needs an explicitly authorized review arrangement.
4. Ask for fresh quota: one chosen worker, 180 seconds, no retries. Do not
   resume STOP or launch on the basis of the expired pending question.
5. After approval, explicitly resume STOP and use installed v0.4.0 native
   run -> verify -> actual in-session full review -> result. Keep temporary
   config/TMPDIR local, AUTO_SYNC/AUTO_VERIFY/AUTO_OFF bounded, real exit/logs
   preserved. No extra provider reviewer is authorized by this handoff.
6. Capture current readiness before integration, then include main and
   publish the tiny finished step as its own no-ff merge/push. Update log/
   continuation with actual model, SHA/tests/outcome and one next task.

Do not silently implement this milestone directly while waiting for quota.
A failed run stays failed; propose a bounded finishing task through the flock.

## Checking or viewing existing source

Prior meaningful runtime/browser checks are described above and in their
contracts/receipts. This closing change updates documentation and local
bench metadata only. It does not rerun the full 20-minute runtime gate.
Fresh closing checks: docs lint, whitespace, branch/main state, zero-call
manifests, STOP/no active workers, and unchanged global file hashes.

For the preview, installed v0.4.0 has no watch command. An existing disposable
watch build is tmp/m2-bridge-20261004/runtime/bin/frugal-flock. From repo/:

```bash
python3 -B bridge/server.py \
  --project '/mnt/d/Vibe Coding/_vm/frugal-flock' \
  --engine '/mnt/d/Vibe Coding/_vm/frugal-flock/tmp/m2-bridge-20261004/runtime/bin/frugal-flock'
```

It prints a local URL. Add --enable-plan-drafts only for intentional manual
save mode. Do not confuse this source preview with a global installation.
Browser tests can reuse tmp/m2-browser-tests/node_modules/playwright and
/home/devmvt39/.cache/ms-playwright/chromium-1243/chrome-linux64/chrome.
Set M2_PLAYWRIGHT_MODULE, M2_CHROMIUM_PATH and workspace-local TMPDIR.
The queue task itself needs only Python3 stdlib/Bash, no browser dependencies.

Copyright (C) 2026 Daniel Mitev; public attribution Daniel Mevit (@danielmevit).
Original: Frugal Flock, https://github.com/danielmevit/frugal-flock.
AGPL-3.0-only; LICENSE and NOTICE apply. No warranty.
