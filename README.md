# Frugal Flock: your AI coding tools, working as one team

**Small plans. Big ideas.**

You describe what you want built. A lead AI turns it into a plan and hands
small tasks to helper AIs. Think of them as subagents, except yours can
come from different companies: Claude Code, Codex, Grok, Antigravity, or
OpenCode with models such as Kimi, each running on a plan you already
have. Every helper works in its own copy of your project, its work gets
checked, and nothing goes into your project until you say yes.

**Available today:** a command-line tool for Linux, including Windows
through WSL. A point-and-click app is [planned](docs/UX-DIRECTION.md).

[How it works](#how-it-works) · [Try it free](#try-it-free-no-ai-calls) ·
[Under the hood](#for-the-curious-and-the-nerdy) · [What's next](#whats-next)

## Why use it

- **Keep building past usage limits.** When one AI runs out of allowance
  halfway through a project, give the next task to another instead of
  stopping for the day.
- **Get a second opinion.** One AI builds, a different one reviews.
- **Stay in charge.** Every task has a clear brief, a list of files it may
  change, and checks it must pass. You see the actual changes and decide
  what to keep.
- **Use what you already have.** Start with one tool and add more when
  they help. You do not need every company's biggest plan.

## How it works

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

## Keywords

The idea in one line: **different AI agents working together as one team on
your project, with a person directing them.** Working together here means
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
