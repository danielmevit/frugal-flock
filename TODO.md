# Frugal Flock — next steps

Small plans. Big ideas.

Checkpoint rule: one bounded correction at a time; test, commit, then
update [FRUGAL-FLOCK-NEXT-AI.md](FRUGAL-FLOCK-NEXT-AI.md) with the exact
candidate SHA, evidence, blockers, active workers and one next task.
The local main folder is now `/mnt/d/Vibe Coding/_vm/frugal-flock`.

## Current handoff

- Name and tagline approved by the owner.
- Canonical CLI: `frugal-flock`; short CLI: `frgl-flc`; compatibility CLI:
  `agentteam`. The Linux `flock` utility must remain untouched.
- Naming contract: [Brand](docs/BRAND.md).
- UX proposal: [UX direction](docs/UX-DIRECTION.md). The proposed graphical
  app is not implemented yet.
- Research and evidence: [Findings index](docs/RESEARCH-FINDINGS.md),
  [competitor comparison](research/COMPETITIVE-REVIEW.md), and
  [engine findings](docs/ENGINE-FINDINGS.md).
- Continue with another AI: [copy-paste build handoff](docs/AI-HANDOFF.md).
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
  GitHub repository was renamed in place from `agentteam-docs` to
  [frugal-flock](https://github.com/danielmevit/frugal-flock). The rewritten
  README offers a beginner path, optional technical depth, and keywords.

## 1. M1 — finish quality before UX

The owner explicitly moved reliability ahead of the prototype. Follow
[QUALITY-M1-CONTRACT.md](docs/QUALITY-M1-CONTRACT.md), frozen at `e230ad4`,
and [the current checkpoint](docs/M1-STATUS.md). Complete strict verification,
revision-bound results, reviewer verdict parsing, honest availability,
trusted-host warnings, and manual same-checkout context packets. Pass
mock-only regressions and independent source review before owner integration.

This is not full OS isolation, a dirty-file backup, automatic provider
migration, or automatic merging. Keep those limitations visible. Stop at
a verified, handoff-ready checkpoint before starting the UI.

Implementation checkpoint is `80feafb` on `agent/kimi`; it now includes
structured evidence, gated review, local availability and manual context
packets as well as strict verification. Full M1 is still incomplete.
Start with [the exact continuation report](docs/SESSION-HANDOFF-2026-10-04.md)
and repair its known correctness/documentation gaps before UI work.

### Clean-clone baseline check

- Follow the README from a fresh clone. Install with
  `bash frugal-flock-install.sh`, then run `frgl-flc selftest` and
  `frgl-flc version` before connecting a live provider.
- Keep old configuration paths, environment overrides, and command
  compatibility. Existing local clone folders need not be renamed.

## 2. M2 — prototype one simple project workspace after M1 acceptance

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
[Toolcraft composition reference](docs/TOOLCRAFT-REFERENCE.md). Build original
components; do not run its scaffold or import its implementation. Keep technical logs and
advanced controls in detail views. Test the prototype with two people who
have not used the CLI before wiring up live execution.

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

Package a launcher that starts the service and opens the browser. Specify
folder selection, missing-engine setup, provider installation/sign-in,
and failure recovery before claiming a command-free first use.

## 5. Build reliable provider handoff

The owner endorsed [capacity-aware task sizing and clean continuation](docs/CAPACITY-AWARE-CONTINUATION.md).
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

Use the [feature decisions](docs/FEATURE-DECISIONS.md) to select relevant
competitor ideas. The [workflow guide](docs/AI-TEAM-WORKFLOWS.md) explains
common AI-team patterns without implying they are all implemented.

Compare a small set of real tasks with the existing CLI workflow and one
capable coding agent. Measure accepted correct changes, active human time,
rework, and recovery from interruptions. Include dependent tasks as well
as easy parallel ones.

Defer a full desktop wrapper, hosted accounts, multi-user collaboration,
advanced races, and additional provider integrations until this basic
journey is useful and understandable.

## 7. Make public participation easier

- Choose and add a license before describing the project as open source.
- Add concise contribution and issue-reporting guidance.
- Collect onboarding feedback from both new builders and experienced
  users; keep the README's basic path separate from optional deep dives.
