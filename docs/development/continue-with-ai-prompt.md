# Continue Unio

Read [the development index](README.md), [lead routing](LEAD-ROUTING.md),
[work modes and tiers](../WORK-MODES.md), [model effort](MODEL-EFFORT.md),
[model roles](../ai/MODEL-ROLES.md) and [workspace rules](WORKSPACE-RULES.md).
In an existing team workspace, read the newest coordination log and actual
worker branches before changing anything. Preserve prior work and failures.

## Current delivery checkpoint — 2026-10-07

Public and installed releases0.5.0,0.5.1 and0.5.2 are complete. The latest
public release remains0.5.2 at this checkpoint. Browser0.5.3 now includes the
real browser-to-worker workflow, protected output and tracked files, native
work modes and shared-budget workflow capacity. Focused checks and a real
funded AGY browser journey passed. The complete gate on e47d805 passed.

A separate shipping upgrade check exposed old completion retention and deletion
of aliases to unrelated targets. Gemini correction d13a98a passed frozen native
checks and the original upgrade/rollback procedure; Root reviewed and integrated
it. The subsequent combined gate exposed a timeout fixture measuring whole-command
Git bookkeeping rather than actual provider lifetime. Its scoped correction
remains under personal review: child observation must be mandatory and harness
failure paths bounded. Preserve earlier passed checks and rejected candidates;
none is a published0.5.3. The final accepted source still needs its full gate and
exact public assets before publication and installation. Read the [version plan](../VERSION-PLAN.md)
and current repository/release state before claiming delivery.

Next is0.5.4: actual recovery saves first, then checkpoint continuation and
[lead CLI cooldown restart](LEAD-COOLDOWN-RESTART.md). Follow the approved
[work-saving plan](../WORK-SAVING.md). No automatic save or restart is delivered
by0.5.3. Existing worker limit handling remains unchanged.

## How to continue

- Use native Unio for delegated runtime implementation. The lead owns contracts,
  coordination, personal review and integration. Resume before a Source/review
  and stop afterward. Freeze base, task, model, effort and per-run config.
- Use the selected mode and tier. This workspace uses YOLO+low: focused validation
  and personal review, then a full release gate before publication. Low allows
  one independent workflow per shared account, including the lead. Different
  accounts can advance independent tasks concurrently; keep dependencies in order.
- Newest owner review policy for this session is personal lead review without
  additional AI reviewer workers. Preserve historical independent reviews, and
  never claim another lab approved work when it did not.
- Main implementation roles are Codex, Claude Code, Grok and Antigravity/Gemini.
  Free OpenCode models handle routine support and never become lead, main feature
  owner, final approver or cooldown replacement. Recheck exact free eligibility.
- Use existing subscriptions only. No extra token payments, paid fallback or
  billing/authentication changes. Availability comes from actual dated signals.
  Do not retry an exhausted provider just because another allowance reset.
- Start at high or the supported middle. Escalate supported effort for actual
  reasoning difficulty; max is occasional and bounded. Gemini3.1Pro uses High
  or Low. Give substantial tasks90–120minutes with matching native/wrapper/CLI
  deadlines, bounded checks and early coherent commits.
- Keep one invocation per frozen task, with no automatic retry. A real defect
  gets a distinct scoped correction. Preserve failed exits and partial work.
  Source exit0 alone is not acceptance; require current scoped native checks
  and the selected review policy. Never replay an unknown spending action.
- Completed0.5.x publication, unattended sequential milestones and installation
  of the newest verified official release are authorized for this workspace.
  Install only when native work is idle, with exact public assets, backup and
  configuration preservation. No tag rewrite or protection change is authorized.
- Keep project files within the workspace, quote paths and take timestamps from
  date. Use CodeGraph only if already indexed. After every checkpoint update
  the coordination log and the actual lead's own continuation file.

## Private evidence when the workspace is available

Start with tmp/unio-next/manifest.json and receipts/ in the enclosing workspace.
Original receipts, task files and run logs determine actual outcomes; dated
controller labels can be stale after a session interruption. Current Root
handoff is in wt/codex-lead/docs/development/continue-with-ai-prompt.md. Never
merge that generic lead branch. No private logs, credentials or snapshots belong
in public release assets. Without the workspace, use the official Git history
and release metadata and prepare new bounded tasks from the current source.
