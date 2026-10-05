# Frugal Flock: connect AI coding tools from different companies into one workspace

**Small plans. Big ideas.**

Frugal Flock links AI coding tools from different companies, such as
Claude Code (Anthropic), Codex (OpenAI), Grok (xAI), Antigravity (Google)
and OpenCode (which runs models such as Kimi), into one shared work
environment for your project.

On their own, these tools never meet. Each works in its own window, on its
own subscription, unaware of the others. Frugal Flock gives them a common
place to work:

- **One leads, the others help.** One AI plans the work and hands out
  tasks; the others act as its subagents, whichever company makes them.
- **Each helper gets its own copy of the project**, so several can work at
  the same time without overwriting each other.
- **Tasks, results and history live in shared files**, not inside any one
  AI's chat, so any AI can see what the others did and pick up where they
  stopped.
- **Every result is checked**, and only you decide what goes into the real
  project.

The name says it: a **flock** of AIs from different companies, run
**frugally** on the plans you already have instead of one expensive one.

**Available today:** a command-line tool for Linux, including Windows
through WSL. A point-and-click app is [planned](docs/UX-DIRECTION.md).

[Step by step](#a-task-step-by-step) · [Try it free](#try-it-free-no-ai-calls) ·
[FAQ](#faq) · [Under the hood](#for-the-curious-and-the-nerdy) ·
[What's next](#whats-next)

## What this makes possible

- **Use the best of each company.** Let one company's AI build a feature
  and another company's AI review it, or give each the kind of task it
  handles best.
- **Keep going when one AI hits its limit.** Give the next task to an AI
  from another company instead of stopping for the day.
- **Run several AIs at once** on separate parts of the same project.
- **See everything in one place:** who did what, what passed its checks,
  and what still needs you.

## A task, step by step

Say you want to add search to a small website:

1. **Describe it** to the lead AI: "Help people find an article by title."
2. **Approve the plan.** The lead splits the work into small tasks and says
   who does each one, which files may change, and how it will be checked.
3. **The helpers work**, each in a separate copy of the project, so their
   changes never get mixed up.
4. **The work is checked.** Frugal Flock runs the agreed checks and keeps
   the evidence. A helper from another company can review the changes too.
5. **You decide.** Keep the changes, ask for fixes, or drop them. A
   finished AI run is not proof the work is right; the checks and your
   review are.

## Good to know

- Frugal Flock does not get around usage limits or pool subscriptions. Each
  tool keeps its own plan, limits, and terms.
- Switching AIs after a limit is supervised today: the next AI gets a
  written handoff, not the previous one's memory. Automatic continuation
  is on the roadmap.
- Helper AIs can run commands on your computer, and separate project copies
  are not a security sandbox. Use a spare Linux machine or virtual machine
  without important passwords or keys.
- AI tools send your prompts and code to their providers. Keep secrets out
  of tasks and repositories.

## Try it free (no AI calls)

### 1. Install and rehearse

You need Linux or WSL with Bash, Git, Python 3, and standard tools such as
`flock`. The rehearsal needs no AI account and uses no AI allowance.

```bash
git clone https://github.com/danielmevit/frugal-flock.git
cd frugal-flock
bash frugal-flock-install.sh
export PATH="$HOME/.local/bin:$PATH"
frgl-flc selftest
```

The self-test runs the whole workflow with pretend AIs in a temporary
project. `frgl-flc` is the short command; `frugal-flock` does the same. The
installer puts commands in `~/.local/bin` and settings in
`~/.config/agentteam`; the [setup guide](docs/SETUP.md) shows how to keep the
PATH change for future terminals.

### 2. Choose your path

- **Show me the whole idea:** [take the worked-example tour](docs/EXAMPLE.md).
- **Walk me through setup:** [follow the complete guide](docs/GUIDEBOOK.md),
  including signing in to your AI tools.
- **I know terminals:** [use the compact setup reference](docs/SETUP.md).

### 3. Your first real task

Install and sign in to at least one AI coding tool. The included settings
cover Claude Code, Codex, Antigravity, OpenCode, and Grok; use the ones you
have. Then try a project you do not mind experimenting on, for example
with Codex:

```bash
# Use your own Git repository URL; it needs at least one commit.
frgl-flc new YOUR_REPOSITORY_URL my-project codex
cd my-project/repo
frgl-flc doctor
frgl-flc agents
```

Open your favourite AI coding tool in `my-project/repo` and ask:

```text
Read MASTER.md and the project instructions. Help me plan one small change.
Check which workers are available, explain how you will test the result,
and wait for my approval before starting work. Do not merge for me.
```

Start with one helper and add another when you want a second perspective.
`agents` shows what is installed, not remaining quota or sign-in status.
`smoke` makes real test calls, so it uses some of your allowance.

If your AI tool keeps asking before each `frgl-flc` command, or refuses to
start the helpers, [allow those commands once](docs/SETUP.md#9-lead-ai-permissions)
instead of switching its safety checks off.

## FAQ

<details>
<summary>Do I have to pay for anything extra?</summary>

No. Frugal Flock is free and open source. It works with the AI plans you
already have, each signed in its own way, so you need no separate API keys.
The rehearsal (`frgl-flc selftest`) makes no AI calls at all. Real tasks use
your plans' normal allowance; optional extras, such as a second AI reviewing
the work, use a little more.

</details>

<details>
<summary>Which AI tools do I need?</summary>

One is enough to start. Settings are included for Claude Code, Codex,
Antigravity, OpenCode (for models such as GLM and Kimi) and Grok. Any
command-line AI that can take a task without a chat window can join with
one line in `~/.config/agentteam/agents.conf`, for example
`mycli=mycli -p "$(cat "$TASKFILE")"`. A second tool from another company
lets one AI review another's work.

</details>

<details>
<summary>Does it work on Windows or Mac?</summary>

Linux, yes. Windows, yes, through WSL (Ubuntu works well). Mac is not
supported yet: Frugal Flock relies on Linux tools such as `flock`.

</details>

<details>
<summary>Do the AIs talk to each other?</summary>

Not directly, and they share no memory. They coordinate through files in
your project: task orders, reports, results and handoff notes. Each AI
starts fresh, reads what the others left, and writes down what it did, so
another AI can continue from those notes.

</details>

<details>
<summary>Is it safe? Will it change my project without asking?</summary>

Helpers are given their own copies on their own branches, and their work
reaches your main branch when you merge it. The lead AI works in your main
copy, so tell it not to merge for you (the starter prompt above does).
Nothing enforces those boundaries, though: every AI runs commands on your
computer with your rights, and the copies are not a security sandbox. Use
a spare Linux machine or virtual machine without important passwords or
keys, keep secrets out of tasks and repositories, and remember that each AI
sends your prompts and code to its provider. `frgl-flc stop` blocks new runs;
`frgl-flc kill T7` ends task T7 if it is running.

</details>

<details>
<summary>How do I know the AI's work is actually right?</summary>

Every task names the files it may change and the checks that must pass.
`frgl-flc verify` re-runs those checks and fails the task if one fails or
anything changed outside the allowed files; nothing is undone, so you can
inspect it. Once verify passes, `frgl-flc review` can ask another company's
AI to judge the committed change. The result records separately whether the
AI finished, the checks passed and the review approved. Your own decision
comes last: a finished run is never taken as proof the work is right.

</details>

<details>
<summary>What happens when an AI hits its usage limit?</summary>

Pause it and give the next task to another company's AI.
`frgl-flc off codex 5h` stops new tasks from going to Codex for five hours,
and `frgl-flc handoff codex T7` writes a context note about task T7: what
was done, what passed and what is left. The lead then gives the work to
another AI with that note. The note is context only: unfinished, uncommitted
changes stay in Codex's copy. [Handoff packets](docs/QUALITY-USAGE.md#handoff-packets)
explain the details. Frugal Flock does not get around limits or share plans;
each tool keeps its own. Automatic switching is on the roadmap.

</details>

<details>
<summary>My lead AI keeps asking for permission, or a run is refused. What now?</summary>

First check who refused. Frugal Flock's own refusals say why, for example
`STOP is active`, an agent that is `OFF`, or a worker that is
`already running a task`; `frgl-flc status` shows the state. If instead the
AI tool asks or refuses, that is its own safety system. For Claude Code,
allow the `frugal-flock` commands once in a small settings file and
restart it; [setup step 9](docs/SETUP.md#9-lead-ai-permissions) shows the
file and what it does and does not allow. Other tools have similar approval
settings. Keep pushes and merges asking and approve them one at a time:
those decisions stay with you. Turning all safety checks off is only
sensible on a throwaway virtual machine.

</details>

## For the curious and the nerdy

Frugal Flock is a Bash orchestration layer around existing coding CLIs, not
a new model or a hosted service. Each tool uses its own sign-in; there is no
shared API-key service.

- **Separate workspaces:** each worker gets a Git worktree on an
  `agent/NAME` branch. A worktree shares the repository's history; it is not
  an isolated virtual machine.
- **Explicit task contracts:** Markdown task files hold instructions,
  allowed paths, validation commands, and a definition of done.
- **Inspectable evidence:** diffs, append-only reports, live logs, a JSONL
  event ledger, and a revision-bound JSON result per task.
- **Cross-provider options:** independent reviews, competing attempts, and
  rotating bug hunts. They use extra provider capacity and are optional.
- **Availability controls:** bench a provider by hand or for a set time.
  Limit-message detection flags failed runs; it is not a quota meter.

Everyday commands once a project is set up:

```bash
frgl-flc help             # discover commands
frgl-flc status           # tasks, reports, review queue, running work
frgl-flc tail             # follow the latest run's log
frgl-flc score            # per-worker scorecard from the event ledger
frgl-flc result codex T7  # stored run/verify/review evidence as JSON
frgl-flc handoff codex T7 # context packet for the next AI, same checkout
frgl-flc agents --json    # local availability; no login or quota probe
frgl-flc off codex 5h     # bench a provider for your chosen interval
frgl-flc on codex         # make it available again
```

A finished process, passing checks, a reviewer's approval, and your own
acceptance are separate results. `verify` exits 2 (INCOMPLETE) when a task
has no scope or Validate lines, and `review` runs only after a current
passing `verify`. `stop` blocks new runs; `kill TASK_ID` ends a running one.
Every exit code and field is in the [quality reference](docs/QUALITY-USAGE.md).

### Coming from agentteam?

Same project, renamed from `agentteam-docs`, with its Git history intact.

- `frugal-flock`, `frgl-flc`, and `agentteam` are one implementation with
  shared Bash completion, installed at `~/.local/bin/agentteam`.
- `agentteam-install.sh` still works; `frugal-flock-install.sh` forwards to
  it, so keep both files together.
- `AGENTTEAM_*` variables, `~/.config/agentteam`, `agents.conf`, and
  project state names are unchanged. Linux `flock` is an unrelated utility.

To update an existing clone, run inside it:

```bash
git remote set-url origin https://github.com/danielmevit/frugal-flock.git
git pull --ff-only
bash frugal-flock-install.sh
frgl-flc selftest
```

If Git reports local changes or diverged history, resolve that first; do
not discard your work just to update.

### Find the right level of detail

| I want to… | Start here |
|---|---|
| Understand the workflow step by step | [Complete guide](docs/GUIDEBOOK.md) · [Word copy](docs/GUIDEBOOK.docx) |
| Look up commands or troubleshoot | [Handbook](docs/HANDBOOK.md) |
| See a worked example | [Replayable tour](docs/EXAMPLE.md) |
| Understand task contracts and coordination | [Agent protocol](docs/PROTOCOL.md) |
| Read the release notes | [Changelog](CHANGELOG.md) |
| Work on Frugal Flock itself | [Maintainer handoff](docs/HANDOFF.md) · [Doc conventions](docs/DOC-CONVENTIONS.md) |
| Test the engine's guardrails | [Test plan](docs/TESTPLAN.md) · [Word copy](docs/TESTPLAN.docx) |
| Read the background research | [Architecture research](research/multi-agent-claude-review.md) · [Original plan](docs/MASTER-PLAN.md) |

Contributor checks, none of which call a live provider:

```bash
bash tools/quality-check.sh   # everything below plus selftest and ShellCheck
bash tests/frugal-flock-quality.sh
bash tests/frugal-flock-branding.sh
bash tests/agentteam-probes.sh
bash tools/check-docs.sh
```

CodeGraph is optional; an unindexed project stays unindexed. Pandoc is only
needed to rebuild the Word manuals with `tools/make-docx.sh`.

## What's next

- **Done, v0.4.0:** a reliable core. Strict checks, evidence tied to the
  exact version of the work, gated reviews, and a handoff file for the next
  AI. See the [release notes](CHANGELOG.md).
- **Now:** a stability phase with real AI providers, so that Frugal Flock
  can safely help build its own app.
- **Then:** a simple app to describe work, approve a plan, follow progress,
  and review results, followed by guided "continue with another AI" when
  one reaches its limit.

The [UX proposal](docs/UX-DIRECTION.md) and [next steps](TODO.md) explain the
scope and order; the [brand notes](docs/BRAND.md) explain the name.

Continuing this project with another AI? Paste the prompt from
[continue-with-ai-prompt.md](continue-with-ai-prompt.md) and follow the
[workspace rules](WORKSPACE-RULES.md). The [M1 status](docs/M1-STATUS.md)
and [findings index](docs/RESEARCH-FINDINGS.md) hold the details.

## License

Frugal Flock is licensed under **AGPL-3.0-only**, with attribution and origin
terms under sections 7(b) and 7(c). Copyright (C) 2026
**Daniel Mitev**, publicly **Daniel Mevit (@danielmevit)**. See
[LICENSE](LICENSE) and [NOTICE](NOTICE), or run `frugal-flock license`.

Commercial use and compliant forks are allowed. Covered redistributed
derivatives must preserve the **Frugal Flock** name and original author
credit in the reused material or appropriate legal notices, identify
modified versions, and meet the license's
source-sharing requirements; modified network versions must offer source
to their remote users. Merely using the tool to build an independent
project does not place that project under AGPL.

Companies seeking permissions for proprietary integration can request a
separate paid agreement. The software comes without warranty, and liability
limits apply subject to applicable law. Read the
[licensing and commercial-use guide](docs/LICENSING.md) for details.

## Keywords

The idea in one line: **AI coding tools from different companies, linked
into one workspace on your project, with a person directing them.** Working together here means
coordinated tasks and reviewed handoffs, not shared conversation memory.
The [plain-English workflow guide](docs/AI-TEAM-WORKFLOWS.md) explains which
patterns work today.

- **Subagents across providers:** subagents from different AI companies,
  multi-provider subagents, cross-vendor subagents, lead agent with
  subagents, delegate work to subagents, parallel subagents, subagent
  orchestration, Claude Code and Codex as subagents, AI coding agent fleet,
  orchestrator and worker agents.
- **AI teamwork in plain language:** make AI assistants work together, a
  team of AI helpers, coordinate AI tools from different companies, use
  several AI models on one project, one AI builds and another reviews,
  human-controlled AI collaboration.
- **Everyday goals:** build with AI on a budget, AI help for a side project,
  work with limited AI plans, handle AI usage limits, continue a project
  with another AI, review AI-generated changes.
- **One place to steer the team:** glue AI tools together, control several
  AIs from one console, one command center for different AI providers,
  coordinate Claude Code and Codex.
- **Ways of working:** split work between AI helpers, run tasks in
  parallel, pass a task from one AI to the next, compare two AI solutions,
  ask an AI to find bugs, supervise a team of agents.
- **People and projects:** learners, hobby projects, independent makers,
  designers building software, solo developers, small teams, indie apps.
- **Technical terms:** multi-agent orchestration, multi-agent collaboration,
  AI agent teams, multi-model workflow, heterogeneous agents, cross-provider
  coding agents, human-in-the-loop AI, Git worktrees, CLI orchestration,
  task delegation, agent review, validation gates, quota-aware coordination.
- **Related ideas, not all implemented:** supervisor–worker workflows,
  writer–reviewer pipelines, agent relay, best-of-N, cross-provider handoff,
  agent swarms, AI councils. Not model merging, shared quotas, or automatic
  consensus.
- **Names and commands:** Frugal Flock, frugal-flock, frgl-flc, agentteam,
  agentteam-docs, Claude Code, Codex, Antigravity, OpenCode, Grok, Kimi.
