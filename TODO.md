# Frugal Flock — next steps

Small plans. Big ideas.

## Current handoff

- Name and tagline approved by the owner.
- Canonical CLI: `frugal-flock`; short CLI: `frgl-flc`; compatibility CLI:
  `agentteam`. The Linux `flock` utility must remain untouched.
- Naming contract: [Brand](docs/BRAND.md).
- UX proposal: [UX direction](docs/UX-DIRECTION.md). The proposed graphical
  app is not implemented yet.
- The rename is complete on `agent/codex` in `../wt/codex`, commit
  `9314639e79dc8bb9edde151f54cfdf35837c3024`. The worker checkout is clean.
  The owner controls the final merge, per `AGENTS.md`; it has not been
  merged or installed into the user's command/configuration directories.
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
  GitHub repository has not been renamed or published by this work.

## 1. Complete the rename handoff

- Review commit `9314639` on `agent/codex` and the recorded validation.
- Owner merges the accepted branch. Then install with
  `bash frugal-flock-install.sh` and check `frgl-flc version`.
- Keep old configuration paths, environment overrides, and command
  compatibility. Decide separately whether to rename the GitHub repo.

## 2. Prototype one simple project workspace

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

Use the calm minimal direction in the UX proposal. Keep technical logs and
advanced controls in detail views. Test the prototype with two people who
have not used the CLI before wiring up live execution.

## 3. Make result states trustworthy

Before enabling UI actions against real work:

- Separate process completion, validation, reviewer decision, human
  acceptance, and integration outcome.
- Missing scope or checks must be incomplete or explicitly waived; a
  plain PASS must not hide missing evidence.
- Preserve verification failures separately from the worker process exit.
- Parse reviewer decisions into approved, changes requested, or unknown.
- Associate evidence and approval with exact revisions and worktree state.

These are follow-up behavior changes, separate from the naming work.

## 4. Add the local application bridge

Start with read-only project, agent, and activity views. Then add a fixed,
validated set of operations for plans and runs, a durable job queue, and
progress that survives browser refreshes. Keep credentials in native CLI
authentication stores and bind control to the local machine.

Package a launcher that starts the service and opens the browser. Specify
folder selection, missing-engine setup, provider installation/sign-in,
and failure recovery before claiming a command-free first use.

## 5. Build reliable provider handoff

After a run stops, capture committed and uncommitted work, task context,
completed checks, and unfinished work. Let the user select another
available agent and continue from that checkpoint. Recheck the continued
result before owner acceptance.

Display available, limited, unavailable, or unknown capacity. Show reset
times only when reported by the provider. Do not invent universal quota
percentages or silently enable paid API fallbacks.

## 6. Measure the benefit before expanding

Compare a small set of real tasks with the existing CLI workflow and one
capable coding agent. Measure accepted correct changes, active human time,
rework, and recovery from interruptions. Include dependent tasks as well
as easy parallel ones.

Defer a full desktop wrapper, hosted accounts, multi-user collaboration,
advanced races, and additional provider integrations until this basic
journey is useful and understandable.
