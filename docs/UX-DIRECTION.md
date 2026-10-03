# Frugal Flock — UX direction

Small plans. Big ideas.

## Status and intended user

This is the first UX proposal. Frugal Flock currently ships a command-line
engine; the screens and interactions below are not yet implemented.

Design for a person with an existing project and a few basic AI plans who
wants to describe a result, stay in control, and keep building when one
provider becomes unavailable. The first successful use should not require
learning task-file syntax, worktrees, worker IDs, or shell commands.

The recommended first surface is a local browser app backed by a local
service on the same machine as the existing engine. A desktop wrapper can
follow if native installation and window management prove valuable. A
remote VM requires an explicit connection setup; do not expose its control
service publicly as a shortcut.

## The main journey

1. Open a project and connect the coding tools already installed.
2. Describe a concrete change in normal language.
3. Review a proposed plan, suggested agents, and checks.
4. Start the approved work and follow a readable activity timeline.
5. Resolve questions or provider limits with a specific next action.
6. Review the result, checks, and changes; request revisions or explicitly
   apply the accepted changes to the project.

The interface keeps one project and one meaningful next action in focus.
A persistent conversation lets the user describe work, revise a plan, or
ask what is stuck. Plan, Activity, and Review are cards or states within
that workspace, not separate primary navigation tabs. Start, Stop, and
Apply remain explicit actions beside the relevant result.

The lead can manage delegation after approval. The human keeps plan and
integration control. Publishing and releasing are separate actions.

## Navigation and screen responsibilities

| Area | User question | Main action |
|------|---------------|-------------|
| Project | What am I building, and what needs me? | Describe a change |
| Plan | What will happen, and which agents will help? | Approve and start |
| Activity | What is happening, and is anything stuck? | Respond or pause |
| Review | Does this result work and meet my request? | Apply or request changes |
| My flock | Which tools can work right now? | Connect or choose an agent |

Keep advanced controls such as races, sabotage rotation, raw logs,
branches, and shell commands available in detail views. They should not
compete with the first task journey.

## First-use setup

The proposed packaged entrypoint is a Frugal Flock launcher or shortcut.
It starts the local service and opens the browser at the local app. If the
service cannot start, the launcher explains the failure and offers a retry.
The first release should target a local machine or WSL installation; a
remote VM is an advanced connection flow. A browser URL alone does not
fulfil the promise of setup without shell commands.

On first launch, a folder selector handled by the local application asks
the user to choose an existing project. Validate that choice before
creating workspaces and explain what will be added. Offer recent projects
on subsequent launches. If the engine is absent, show a setup step before
asking the user to create work.

Ask for a project and detect available coding tools. Each provider has an
explicit state: Not installed, Sign-in needed, Connected, Limited,
Unavailable, or Unknown. An installed binary is not proof of a valid
login, and a valid login is not proof of remaining capacity.

Explain the exact action required to connect a tool. Continue through its
native supported authentication flow; do not request subscription passwords
in Frugal Flock or copy authentication tokens into the browser. Starting a
live test call must disclose that it uses provider capacity.

Start with the tools the user already has. One connected agent is enough
to try the workflow; more providers are optional. Avoid an onboarding flow
that requires buying several subscriptions before producing a result.

## The project workspace

The project view combines an outcome brief, current work, and the next
decision. It is not primarily a terminal viewer or a wall of usage charts.

```text
Frugal Flock                         My flock     Settings
Small plans. Big ideas.

Project: Garden journal
What would you like to build?
[ Add a search box so I can find previous entries.       ]
                                           [Create plan]

Needs your attention
Search entries: plan ready                  [Review plan]

Recent work
Entry editor: accepted
Image upload: checks running                [View activity]
```

Create plan invokes the selected lead only when a live connection is
available. A prototype must label its sample scenario instead of pretending
to generate a real plan.

## Plan and supervision

Translate the current task schema into a readable plan: intended result,
small work items, who will work on them, what may change, and how the
result will be checked. Generate task files behind the interface.

Offer a recommended small team and an expandable agent selector. For the
first version, default to one active worker and an optional independent
reviewer. Let the user set maximum simultaneous workers and which connected
providers are allowed. Never silently upgrade plans or enable paid API
fallbacks.

Once work starts, show events such as Building search, Checking results,
Waiting for your answer, and Ready for review. Show elapsed time, the
actual agent, and the most recent meaningful event. Do not fabricate a
completion percentage or estimated finish time from a running process.

Pause new work and Stop this run must be separate controls. The current
engine's STOP gate prevents new dispatches; it does not suspend running
processes. Explain that running work may finish after new work is paused.

## When an agent reaches its limit

This recovery interaction is central to the product:

1. Identify the affected task and distinguish a reported provider limit
   from a generic error, timeout, or expired login.
2. Let the affected run settle, or explicitly stop it, before inspecting
   the worker state. Persist a checkpoint: commits, uncommitted changes,
   task instructions, completed checks, and unfinished work.
3. Explain what is saved and what remains uncertain in plain language.
4. Offer Continue with another agent, Wait and retry, or Save for later.
5. After the user chooses, give the named replacement a self-contained
   handoff and an isolated workspace that preserves the recorded work.
   Keep saved changes and unfinished checks visible. Continued work must
   return to validation and human review before Apply becomes available.

Example: Codex reached its limit while adding search. The committed search
component is saved; keyboard tests are unfinished. Claude is connected.
Continue with Claude?

Do not silently restart the whole task and discard partial changes. A new
vendor does not inherit another vendor's conversation. The existing engine
supports timed benching and task runs; this full checkpoint-and-handoff
flow is additional product work, not an existing automatic capability.

Show a reset time only when the provider reports one. Distinguish an
operator's retry reminder from a confirmed provider reset. When remaining
quota is unknown, display Unknown; healthy/limited/unknown states are more
honest than invented universal quota meters.

## Review and apply

Start with a plain-language result summary and the acceptance checklist.
Offer a preview when the project supports one, then changed files and a
full diff for inspection. Give Request changes equal visibility with Apply
changes; the next action should depend on the actual result.

Keep these outcomes distinct in data and UI:

- Agent process finished or failed.
- Validation passed, failed, was not run, or was explicitly waived.
- Independent reviewer approved, requested changes, or returned no usable
  verdict.
- Human accepted or rejected the result.
- Integration succeeded, conflicted, or has not been attempted.

The current CLI can return success after automatic verification failed,
and review process exit codes do not encode the reviewer's decision.
The UI adapter must not convert exit zero into Ready to apply. Missing
scope and missing checks need an explicit incomplete or waived state.

Bind displayed evidence and human approval to the exact candidate commit,
base commit, and worktree state. Recheck them before integration; if work
changes after review, ask the user to review the new result. Applying
changes is an explicit owner action, with conflicts surfaced for a decision.

## Visual and language direction

Use a calm, minimal workspace: off-white canvas, charcoal text, white
surfaces, light dividers, and restrained pastel status accents. Use a clear
system sans-serif, readable body text, and visible keyboard focus. Status
meaning must be conveyed in words as well as color. Support reduced motion.

Use the flock motif sparingly in identity and empty states. Keep actual
provider names visible and actions literal. On a narrow screen, show the
task and next decision first; navigation and agent details can collapse.

## Delivery sequence

1. Validate the UX with a clickable prototype using clearly labeled sample
   data: first task, plan approval, a limit interruption, recovery, and
   review. No live workers or merges in this prototype.
2. Add a local adapter and read-only project/agent/activity views. Return
   structured states instead of screen-scraping the CLI's human output.
3. Connect plan approval and bounded worker runs. Add a durable job queue,
   cancellation semantics, validated project/task IDs, and reconnectable
   progress events. Keep provider credentials outside the frontend.
4. Add checkpointed handoff and review tied to exact revisions. Enable
   explicit owner integration only after its evidence gate works.
5. Test the entire journey with two people who have not used the CLI.
   Package a desktop window only if the browser/local-service experience
   leaves a meaningful installation or navigation problem.

The service should call a fixed set of engine operations with validated
arguments. Free-form text describes desired work; it must not become an
arbitrary shell endpoint. Keep control bound to localhost with protected
sessions, origin checks, and explicit authorization for external access.

## What success looks like

A new user can connect an existing tool, start one useful task, understand
its status, recover from a simulated limit, and review the result without
being taught shell commands. Observe where they hesitate and measure their
active setup, supervision, and review time. Compare that experience with
the current CLI before expanding the feature set.
