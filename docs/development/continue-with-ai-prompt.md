# Continue Unio

Read [the development index](README.md), [lead routing](LEAD-ROUTING.md),
[work modes and tiers](../WORK-MODES.md), [model effort](MODEL-EFFORT.md),
[bounded escalation](../ai/LEAD-ESCALATION.md), [model scoreboard](MODEL-SCOREBOARD.md),
[model roles](../ai/MODEL-ROLES.md) and [workspace rules](WORKSPACE-RULES.md).
In an existing team workspace, read the newest coordination log and actual
worker branches before changing anything. Preserve prior work and failures.


Validation update, 2026-10-08: see [completed checks, preserved failures and
remaining release work](RECOVERY-ACCEPTANCE-2026-10-08.md). Component coverage does
not replace the final versioned release gate.

## Current delivery checkpoint — 2026-10-08

Owner requested a functionality-first milestone review after the completed map
polish. Read the [audit and delivery plan](FUNCTIONALITY-FIRST-PLAN.md) and the
front of the [roadmap](ROADMAP.md). Automatic baseline/periodic/final saving,
one authorized continuation and the first [lead cooldown runtime](../LEAD-COOLDOWN.md)
are accepted and pushed in main. The original combined gate failed a stale
completion expectation; the corrected manual suite passed 186 checks. Automatic
saving passed 61 checks and cooldown passed 106 offline assertions. Full
continuation acceptance is pending. Real
subscription-limit restart acceptance, final release packaging and upgrade
checks remain before v0.5.4 publication and installation. Further UI work and
scan optimization are deferred until recovery is complete; later releases have
no newly assigned numbers.

Cooldown runtime merged at
[df716a5](https://github.com/danielmevit/unio/commit/df716a56231d73a8af35be2c615c8e136056f525).
Its original native five checks and bounded daemon correction passed; personal
material-bound review approved. One actual read-only account/rate-limit probe
and current Codex CLI/configuration compatibility check passed without a model
call. This is not evidence of a real limit-to-restart cycle. The current lead
must end before enabling another Codex workflow under low tier. Source is
`not_run` for this existing-lead implementation; no independent lab approval
is claimed. The one fresh Opus contract attempt succeeded after the CLI update;
its original OAuth failure is retained and Opus is reserved again.

Browser observation correction merged at
[bea0759](https://github.com/danielmevit/unio/commit/bea075920eee58cb7230add2e05dbccd9fc96c97).
The source defaults to 30 seconds and offers `--observer-timeout` (1–120).
Stable native acceptance passed three checks and personal review; the original
revision-changing verification remains INCOMPLETE in private receipts. One real
default HTTP observation returned 200/schema1 in 9.754 seconds. This confirms
availability without a private override, not faster scans. Published/installed
v0.5.3 remains unchanged; keep original 503 diagnostics.

[Unio 0.5.3](https://github.com/danielmevit/unio/releases/tag/v0.5.3) is published and installed from exact source
`ae61bf3d11ffc0701d32c1efcf90bccd18b267a6`. It delivers the real browser-to-worker workflow,
protected output and tracked files, work modes and native shared-budget
workflow capacity. The full merged-tree gate, five packaged installer
checks, upgrade/configuration preservation and backup restoration passed.
All six downloaded release assets matched their prepared hashes.

Codex gpt-6.1-sol at xhigh completed the owner-authorized timeout fixture
correction, with all three native checks and personal lead approval.
Keep earlier failed runs and rejected drafts; the temporary extra Codex
workflow exception is complete and normal low-tier rules apply.

The next release is 0.5.4. Accepted in main: dark/system themes and live work
map, fluid screen-width layout, the approved “Your AIs, in sync.” tagline,
GitHub/license footer links, startup escalation guidance and the task-fit
scoreboard. Manual save creation, inspection and exact restore are also integrated
from [PR4](https://github.com/danielmevit/unio/pull/4), including the existing
lead's retained-file and lock-safety corrections. These additions are not in
the published or installed 0.5.3 release.

Automatic native-run saving is integrated at
[01be5a5](https://github.com/danielmevit/unio/commit/01be5a5eb5ef8e314060b7362423d0c47138a6a0).
Baseline precedes provider startup; changed periodic captures occur no more
often than every sixty seconds; final capture follows success, failure, timeout
or graceful interruption. Actual attempt IDs/exits, previous good evidence and
worker/account ownership are preserved. Public cancellation permits final-save
cleanup and rejects malformed PID evidence before any signal probe. The offline
saving suite passed 61 assertions; the final PID correction passed 12 isolated
safety cases and all five native checks, followed by personal material-bound
lead review. Reused unchanged timer evidence was not replayed for the PID guard.
Preserve the initial periodic/session failures and refused local adapter alias
transport. Direct Source remains not run; this was existing-lead implementation
under the owner's self-review exception, with no independent AI-lab verdict.
The corrected full manual suite passed 186 checks; final versioned release
checks remain required. The lead
cooldown runtime is now implemented in source, with real restart acceptance pending.

Authorized continuation is integrated at
[940d0dd](https://github.com/danielmevit/unio/commit/940d0dd35dd377c4c7423c88906ea0ae600d899c).
`unio save continue SAVE_ID DESTINATION NEW_TASK` requires exact previously
restored state and a separately frozen task with actual scope/checks. It binds
full task SHA256 and effective prompt authority, preserves native account
admission/retry/STOP/actual exits and skips auto-sync only for continuation.
One durable claim prevents replay after completion, refusal or Unknown. Original
source state/result stay intact; checks and review are fresh. Initial fixture
failures remain preserved; corrected focused checks and personal material-bound
lead review passed. No extra AI reviewer or delegated Source is claimed.
These commands remain unreleased until the completed v0.5.4 gate.

Preserve the saving review history: original and replacement findings, the
lead's full-suite shared-lock observation failure, and the final focused
correction's scope/checks PASS and personal approval. A later stale completion
assertion was corrected at main43a45b1; the full manual suite then passed186checks.
The original failing gates stay preserved; final versioned release checks remain.
The direct lead tasks have no delegated Source, and self-review is not an
independent AI-lab verdict.

Follow-up correction [ab8d2f1](https://github.com/danielmevit/unio/commit/ab8d2f1da3c494bd38f268f377efc633b177cc4a)
fixes empty-index restore found by the combined installer smoke. Its native
scope and five focused checks passed, followed by personal review. Standalone
packaging, canonical guide/legal parity, custom instructions, save/inspect/restore
and unchanged source/global executable passed. The real local dashboard also
passed at five widths from 320px to 1920px, with API200, full available page
width, correct footer and no page errors. Preserve the initial failed smoke.

Interactive radial map [4a0da73](https://github.com/danielmevit/unio/commit/4a0da73171b7c4c19b6ea73c90d11ab4c962930b)
is now accepted and pushed in main: bounded viewport, 5–300% zoom, Fit/Reset,
mouse/touch panning, keyboard controls and pointer-centred wheel zoom. Manual
camera and exact selection survive polling, view switches and resizing. Light
and Dark use the approved neutral grayscale palette. Native scope and all five
checks passed; 28 Chromium assertion groups and four desktop/mobile screenshots
were inspected, followed by personal lead review. Preserve the initial long
Chromium socket-path failure and the test's fractional pointer-coordinate
correction. Fit is an overview; use zoom, filters or List to read dense pages.
No additional AI, dependency, backend capability or global install was added.
See the [map controls](../../bridge/README.md#interactive-radial-viewport-browser-map-viewport-1).

The actual local dashboard passed at desktop1440px and phone390px with new
zoom controls, API200, full available width and no page errors. Its separate
10-second observer cutoff was too short for a measured10.37-second native scan;
the local read-only preview now uses a30-second Observer budget. The source observation budget correction above supersedes the private override;
no released CLI option or scan-speed improvement is claimed. The [observation finding](LIVE-WORKSPACE-VIEW.md#large-workspace-observation-follow-up)
is tracked for the performance milestone; preserve original503 diagnostics.

Selected-task sidebar [a05e39a](https://github.com/danielmevit/unio/commit/a05e39a296758932b41f9a49bd490a14fd3060f0)
is accepted and pushed: clicking a task opens details in the right-hand quarter
of the map area on wide screens (1100px+), leaving three-quarters for the map.
Clear selection closes it and restores full width; narrow screens stack details
below. Long desktop details scroll. Native scope6 and all four checks passed,
including29 browser assertion groups, followed by four screenshot inspections
and personal lead approval. Source JS/backend/grants and installed0.5.3 are
unchanged. These remain unreleased0.5.4 source additions.

Every-node details [eb70a63](https://github.com/danielmevit/unio/commit/eb70a63cf4dd53c9e46e1c5cef93138005d6de57)
are accepted and pushed: task, worker and Project hub selections all open the
panel. Worker/hub summaries use actual observed records; empty/missing evidence
is explained. Output/files controls stay visible, gray and disabled when no route
is available. Native scope7 and seven checks passed, including30 Work map groups
and the protected-console browser journey, followed by personal lead review.
Actual desktop/mobile preview confirmed all node kinds, quarter width, stacking,
clear action and no errors. No grant/backend/dependency change or extra AI call.

Status strips and mouse navigation [4bc2ea9](https://github.com/danielmevit/unio/commit/4bc2ea9cbb52fa30df0960607482fe066172ef7e)
are accepted and pushed: thin right-edge green marks require passed checks and
approved review; explicit failures are red, other attention yellow, active or
missing evidence gray. Worker/hub marks explicitly summarize all observed tasks,
including history. The owner's color exception is limited to these small semantic
marks and their text legend; surfaces and selection remain neutral. Colors are
terminal-style; the host's exact terminal palette is not read. Ordinary wheel
zooms at the pointer over the map; hold the middle mouse button and drag to pan.
Left/touch drag and keyboard controls remain; wheel outside scrolls the page.
Native scope8 and five checks passed, including32 Chromium groups and four
inspected desktop/mobile Light/Dark screenshots, followed by personal review.
Both direct-lead tasks retain Source not_run; no independent lab verdict or
standard combined readiness is claimed. Published/installed0.5.3 is unchanged.

Recovery runtime slices are implemented under the frozen
[work-saving contract](WORK-SAVING-CONTRACT.md) and
[lead cooldown contract](LEAD-COOLDOWN-CONTRACT.md). Next: finish continuation
acceptance, then the final versioned gate,
real subscription-limit restart acceptance and final shipping checks. Existing worker limit
handling stays unchanged. Future Marathon-inspired UI uses UX/layout/control
shapes in black, white, charcoal and neutral gray, with the small semantic status
marks as the owner-approved color exception;
Settings remains a proposal. Opus stays reserved until the owner reintroduces it.
Read the [version plan](../VERSION-PLAN.md) and actual latest state before dispatch.

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
