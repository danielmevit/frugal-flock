# Unio roadmap and development priorities

Small plans. Big ideas.

Checkpoint rule: one bounded correction at a time; test, commit, then
update [the continuation prompt](continue-with-ai-prompt.md) with the exact
candidate SHA, evidence, blockers, active workers and one next task.
All project-owned work stays inside `/mnt/d/Vibe Coding/_vm/frugal-flock`.
The main checkout is its `repo/` folder; workers use `wt/NAME/`.
Follow [the standing workspace rules](WORKSPACE-RULES.md).
Current owner direction (2026-10-06): finish the browser milestone and publish
Unio v0.5.3 after checks. The browser execution service is gated and pushed;
large-prompt transport, API, UI, a real browser demonstration and shipping
checks follow. Checkpoint continuation remains v0.5.4. Use the
[current continuation prompt](continue-with-ai-prompt.md) for active workers
and exact evidence. The [2026-10-05 closing handoff](../SESSION-HANDOFF-2026-10-05.md)
is preserved as an earlier checkpoint.

## Earlier checkpoint (2026-10-05)

- 2026-10-05: Claude is the lead. The waiting-job JobStore library/tests
  were built through the installed Frugal Flock 0.4.0 (legacy build tool) pipeline (GLM 5.3 worker,
  two approved runs, Claude lead review), merged and pushed as 2539c64.
  Owner direction: use Codex, OpenCode GLM, Grok and Antigravity for flock
  work with cross-vendor reviews. Next: approval plus reservation/recovery
  slice (no executor) and job_store_test.py in the routine gate.
- Name and tagline approved by the owner.
- Canonical CLI: `unio` (old aliases `frugal-flock`, `frgl-flc`, and `agentteam` are removed). The Linux `flock` utility must remain untouched.
- Naming contract: [Brand](../BRAND.md).
- UX proposal: [UX direction](../UX-DIRECTION.md). The proposed graphical
  app is not implemented yet.
- Research and evidence: [Findings index](../RESEARCH-FINDINGS.md),
  [competitor comparison](../../research/COMPETITIVE-REVIEW.md), and
  [engine findings](../ENGINE-FINDINGS.md).
- Continue with another AI: [copy-paste prompt](continue-with-ai-prompt.md).
- The rename implementation, commit
  `9314639e79dc8bb9edde151f54cfdf35837c3024`, and the UX documents are now
  integrated into `main` at the owner's explicit request. Existing Git
  history is retained. This work has not installed anything into the
  user's live command/configuration directories.
- Lead verification passed: scope OK, all five frozen validation commands
  passed, one task commit touching 20 paths. Worker checks also passed:
  40/40 selftests, 14/14 adversarial probes, branding smoke, ShellCheck,
  documentation lint, and whitespace checks. Both Word manuals were rebuilt.
  An independent read-only review found no remaining runtime blockers;
  its command-spelling corrections are included in the final commit.
- The first native worker stopped at a provider limit; its edits were
  preserved and handed to a finishing worker. History is in
  `../coord/reports/FF-BRAND-codex.md`; the latest CLI log is in the sibling
  `.log` file. That interrupted run is historical, not the final task
  outcome; see the later verification and completion handoff in the report.
- Existing local commits from before this session were preserved. The
  Historical GitHub rename: `agentteam-docs` became
  [frugal-flock](https://github.com/danielmevit/frugal-flock). The rewritten
  README offers a beginner path, optional technical depth, and keywords.
- On 2026-10-05, the owner approved the subsequent rename to
  [Unio](https://github.com/danielmevit/unio); see [the rename contract](../RENAME-UNIO.md).

## 1. M1 — finish quality before UX

The owner explicitly moved reliability ahead of the prototype. Follow
[QUALITY-M1-CONTRACT.md](../QUALITY-M1-CONTRACT.md), frozen at `e230ad4`,
and [the current checkpoint](../M1-STATUS.md). Complete strict verification,
revision-bound results, reviewer verdict parsing, honest availability,
trusted-host warnings, and manual same-checkout context packets. Pass
mock-only regressions and independent source review before owner integration.

This is not full OS isolation, a dirty-file backup, automatic provider
migration, or automatic merging. Keep those limitations visible. Stop at
a verified, handoff-ready checkpoint before starting the UI.

All five M1 items are implemented and merged into main as of 2026-10-04:
strict verification, structured evidence, gated review, local availability,
manual context packets, both correctness fixes, the acceptance-coverage
audit, and updated help, protocol, docs and Word manuals. The final gate
results are in [the current checkpoint](../M1-STATUS.md). The owner
accepted M1 on 2026-10-04. M2 starts when the owner asks for it.

### Clean-clone baseline check

- Follow the README from a fresh clone. Install with
  `bash unio-install.sh`, then run `unio selftest` and
  `unio version` before connecting a live provider.
- Unio supports only `unio`, `UNIO_*` overrides and `~/.config/unio`.
  The installer copies legacy default config once when the new config is
  absent and no override is selected, preserving the old config. Old aliases
  and environment names are not supported; local clone folders stay intact.

## Near-term roadmap (owner-approved 2026-10-04)

Goal: build the Unio app WITH the installed Unio tool (dogfooding) and watch
its behaviour live, so build progress, bugs and errors are visible as they
happen. Only after a stability phase, so the team does not burn tokens in
bug loops.

Assessment of the plan (lead review, Claude Opus 5.5, 2026-10-04): the plan
is sound and on the right path. Reliability first was right, the honesty
rules (no invented quota, no sandbox claims) are right, and clean
continuation after provider limits is the real differentiator. Risks:

- Scope is large for one owner: local service, browser app, launcher,
  checkpointed cross-provider continuation. Deliver thin vertical slices
  and measure benefit before expanding (section 6).
- At that assessment, 0.4.0 had only mock verification. Live canary
  evidence is now recorded in section 1.5; limited real M2 cycles are recorded
  below, while broader dogfood reliability remains unproven.
- At that assessment, the loop brake was only a role-card rule. It is now
  implemented and mock-tested in unreleased source (section 1.5).
- Antigravity failed 2 of 2 live runs (about 55 minutes each).
- Checkpointed handoff (save and move partial work) is the hardest piece;
  the M1 handoff packet is context only.
- The repository now uses AGPL-3.0-only, with required notices and optional
  separate paid agreements for proprietary use (section 7).

Order: M1.5 below, then M2 built by the flock itself (mock-data prototype,
one worker plus a reviewer, owner merges, widen after a few clean cycles),
then the read-only local bridge (section 4), whose first view grows out of
`unio watch`, then capacity-aware handoff (section 5).

## 1.5 M1.5 — stability before dogfooding

Do the M1.5 stability phase, approved by the owner on 2026-10-04, in this
order, one small tested checkpoint each:
1. Live canary: a throwaway repo, one tiny task per agent through run,
   verify, review and result. Tiny tasks only; it uses provider quota.
   Offline preparation is recorded in [the canary checkpoint](../M1.5-LIVE-CANARY.md).
   Antigravity passed its first canary in 22 seconds on 2026-10-04;
   the earlier silent stall did not recur. One worker call, no retry.
   Grok also passed in 35 seconds, one worker call, 2/2 checks and lead review.
   OpenCode Go `opencode-go/glm-5.3` passed in 24 seconds, with the same
   checks and in-session lead review.
   Kimi (`opencode-go/kimi-k3`) also passed in 45 seconds with the same checks.
   Claude Sonnet 5.5/medium passed in 23 seconds, one commit/file, verify
   2/2, lead review and current ready result. Codex's original attempt was
   interrupted and archived; the owner's one approved retest passed in
   26 seconds, one commit/file, verify 2/2, lead approval and live Grok review
   (82s), current ready result. All six canaries now passed; step 1 complete.
   Seven worker invocations/one live reviewer; one explicitly approved
   retest, no automatic retries. Fixture stopped, global settings unchanged.
   The interrupted-activity label limitation is reproduced with mocks and
   recorded for a separate fix; readiness correctly fails closed.
2. Loop brake in the engine: a task that failed twice is refused until
   the owner explicitly allows another attempt.
   Source implementation complete at `d930a87`: one counted failure per
   started attempt across workers, including lost starts with free locks;
   one explicit owner grant via `allow-retry`. Full gate passed: 40 selftests,
   120 existing regressions, 22 brake checks, 14 probes, packaging, ShellCheck
   and docs. Installed 0.4.0 remains unchanged until a deliberate release.
3. Live monitor (`unio watch`): runs, verdicts, failures and limits
   as they happen; it later becomes the app's Activity view.
   Source implementation complete: 26 focused mock checks, standalone
   packaging/aliases/completion, ShellCheck/syntax and full docs lint passed.
   Observed all six recorded canaries without changing coordination hashes
   or calling providers. [Usage and JSON contract](../WATCH-USAGE.md).
   Current readiness still requires `result`; capacity stays unknown.
   Stability follow-up: fresh OpenCode source defaults/examples now use
   --auto, confirmed by current native help and Go canaries. Offline native
   dispatch/verify, no-call legacy diagnostic and reinstall preservation
   passed; packaging/ShellCheck/docs passed. Existing profiles stay untouched.
4. The flock runs on the installed release while it builds the next
   version in the repo; reinstall only at deliberate releases.
   Observed 2026-10-04: installed 0.4.0 executable/global agents.conf hashes
   unchanged through all stability work. New features are source-only.
5. Bench Antigravity for dogfooding until it passes the canary (2 of 2
   earlier live runs failed). The owner requested its inclusion in step 1.
   Canary passed in 22s; local diagnostics currently show enabled, with
   authentication/capacity unknown. Broader dogfooding remains unproven.
Then dogfood on M2 (the mock-data prototype): one worker plus a reviewer,
owner merges; widen after a few clean cycles.

## 2. M2 — prototype one simple project workspace after M1.5

Build a clickable prototype with clearly labeled sample data. One
conversation with the lead, with plan, progress, and review cards beside
it. Keep the main actions literal: Create plan, Approve and start, Stop,
Request changes, and Apply changes.

Cover five connected moments:

1. Open a project and connect an existing coding tool.
2. Describe a change and review a proposed plan.
3. Follow the work and answer a question.
4. Recover from a simulated provider limit using a named replacement.
5. Review the result and approve or request changes.

Use the calm minimal direction in the UX proposal and the
[Toolcraft composition reference](../TOOLCRAFT-REFERENCE.md). Build original
components; do not run its scaffold or import its implementation. Keep technical logs and
advanced controls in detail views. The original plan asked two people new
to the CLI to test the prototype before live execution. The owner explicitly
waived that feedback gate on 2026-10-04 because no testers are available:
use judgment and automated checks. No user sessions have taken place.

Prototype source is implemented in [prototype/](../../prototype/README.md),
2026-10-04 by Codex (`gpt-6.1-sol`, xhigh): original HTML/CSS/JS, no runtime
dependency, all five connected moments, sample data labeled in every state.
Four state tests and the full Chromium browser journey passed, including
explicit replacement/apply, revision invalidation, Stop, focus, escaped text,
mobile inspector collapse and no external requests/page errors. Refresh
restarts the demo; no real provider, checkpoint or project action occurs.
The owner waived the two-person feedback gate on 2026-10-04; the optional
[facilitator guide](../M2-USER-TEST.md) retains two blank records. No
feedback sessions are claimed. Installed-release dogfood: GLM's one keyboard worker
hit its 180s limit with zero work, preserved as failed; root finished locally
and the browser/state checks passed. Claude Opus 5.5/high's separate guide
cycle passed in 83s with 2/2 validation and in-session root review. No retries
or paid reviewer. [Evidence and limits](../M2-DOGFOOD-PLAN.md).
Proceed to small live-control slices using judgment and automated checks.
Explicit run/quota approval, truthful evidence and separate acceptance still apply.

## M1 acceptance details — trustworthy results

Before starting M2, not merely before enabling live UI actions:

- Separate process completion, validation, reviewer decision, human
  acceptance, and integration outcome.
- Missing scope or checks must be incomplete; M1 has no waiver bypass. A
  plain PASS must not hide missing evidence.
- Preserve verification failures separately from the worker process exit.
- Parse reviewer decisions into approved, changes requested, or unknown.
- Associate evidence and approval with exact revisions and worktree state.

These changes belong to M1, not a later frontend task. See the frozen
contract for exact exit codes and regression cases.

## 4. Add the local application bridge

Start with read-only project, agent, and activity views. Then add a fixed,
validated set of operations for plans and runs, a durable job queue, and
progress that survives browser refreshes. Keep credentials in native CLI
authentication stores and bind control to the local machine.

The first [read-only Activity preview](../../bridge/README.md) is implemented in
source: one fixed watch JSON observation endpoint and original browser view,
loopback only, no dispatch or coordination writes. Seven stdlib HTTP tests
and browser failure/recovery/escaping/mobile checks passed. An actual project
observation showed the preserved GLM failure and approved Claude guide,
with all 36 coordination-file hashes unchanged. Runtime/global profile
hashes remain unchanged. [Contract and source-build usage](../BRIDGE-ACTIVITY.md).
Folder selection/launcher/setup, durable queue and live controls are not
implemented. The owner waived the two-user feedback gate; provider calls
still require explicit quota approval. Optional --open-browser now opens the
bound read-only URL with a manual fallback; eleven focused checks passed.
The [manual draft storage foundation](../PLAN-DRAFTS.md) is implemented
and passed eight checks: persisted immutable records/content hashes, no
native tasks or approval/dispatch. A protected --enable-plan-drafts API now
adds only manual create/read, exact Origin/Host/session checks and bounded
JSON. Eight API checks, eleven existing HTTP checks, default browser journey
and actual restart/persistence/token rotation passed. No real-project draft
or provider call. The opt-in Save/reopen form now passes both default/manual
browser journeys, duplicate-submit and failed-session/save/no-retry checks.
Default stays read-only; no AI plan generation, worker/queue or merge control.
The owner reiterated the main build-with-the-flock goal on 2026-10-05.
The first [waiting-job queue slice](../JOB-QUEUE-STORE.md) was built with
the [native dogfood cadence](../DOGFOOD-WORKFLOW.md): a quota-approved GLM
worker, the Claude lead's in-session review and its own merge (2539c64).
Earlier direct root code is not worker success. The next queue slice
(approval plus reservation/recovery, no executor) follows the same cadence.


Package a launcher that starts the service and opens the browser. Specify
folder selection, missing-engine setup, provider installation/sign-in,
and failure recovery before claiming a command-free first use.

## 5. Build reliable provider handoff

The owner endorsed [capacity-aware task sizing and clean continuation](../CAPACITY-AWARE-CONTINUATION.md).
The [provider quota monitoring roadmap](../PROVIDER-QUOTA-MONITORING.md)
records the 2026-10-05 request for remaining five-hour, weekly and monthly
indicators, supported provider inputs, manual fallback and lead checks
before dispatch. A Codex read-only probe worked; fleet monitoring is not
implemented. Schedule this after the current approved milestones.
Preserve this design for a later milestone: periodic supported readings or
manual input, conservative scheduling, and tested recovery checkpoints.
M1's context packet is not a backup of uncommitted files.

After a run stops, capture committed and uncommitted work, task context,
completed checks, and unfinished work. Let the user select another
available agent and continue from that checkpoint. Recheck the continued
result before owner acceptance.

Display available, limited, unavailable, or unknown capacity. Show reset
times only when reported by the provider. Do not invent universal quota
percentages or silently enable paid API fallbacks.

## 6. Measure the benefit before expanding

Use the [feature decisions](../FEATURE-DECISIONS.md) to select relevant
competitor ideas. The [workflow guide](../AI-TEAM-WORKFLOWS.md) explains
common AI-team patterns without implying they are all implemented.

Compare a small set of real tasks with the existing CLI workflow and one
capable coding agent. Measure accepted correct changes, active human time,
rework, and recovery from interruptions. Include dependent tasks as well
as easy parallel ones.

Defer a full desktop wrapper, hosted accounts, multi-user collaboration,
advanced races, and additional provider integrations until this basic
journey is useful and understandable.

## 7. Make public participation easier

- License chosen and applied on 2026-10-04: AGPL-3.0-only, copyright
  Daniel Mitev, public attribution Daniel Mevit (@danielmevit). The owner
  explicitly chose true open source, allowing compliant commercial forks,
  with optional paid agreements for proprietary use. Section 7(b)/(c) terms
  preserve the Unio name/author credit and prohibit origin
  misrepresentation in covered copies/variants. Full terms/NOTICE
  ship with the installer; see [licensing guidance](../LICENSING.md).
- Add concise contribution and issue-reporting guidance.
- Define contributor permissions before accepting outside code if paid
  proprietary licensing is planned; AGPL alone does not grant relicensing rights.
- Collect onboarding feedback from both new builders and experienced
  users; keep the README's basic path separate from optional deep dives.
