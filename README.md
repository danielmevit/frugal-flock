# Frugal Flock

**Small plans. Big ideas.**

A small team of AI coding tools, working on your project, with you in charge.

Frugal Flock helps you coordinate the AI tools you already use. Ask a lead
assistant to plan a change, give different assistants focused tasks, and
review what they produce before accepting it. Mix providers or start small
with one. You do not need every company's biggest plan to explore the idea.

**Available today:** a terminal-based tool for Ubuntu/Linux, including
Ubuntu on Windows through WSL. Setup still takes some technical confidence.
A simpler point-and-click app is [planned, not built yet](docs/UX-DIRECTION.md).

[How it works](#how-it-works) · [Try it](#try-it-without-spending-ai-quota) ·
[Technical details](#for-the-curious-and-the-nerdy) · [Next steps](TODO.md)

## Why this exists

Sometimes your idea is ready to go, but your AI plan is not. A usage limit
arrives halfway through a change. Another tool is available, but bringing
it up to speed means more copying, explaining, and checking.

Frugal Flock gives that work a shared structure: clear tasks, separate
working copies, recorded results, and a human deciding what gets accepted.
The aim is to make modest resources easier to work with and interruptions
less confusing.

It does not bypass usage limits, combine subscriptions into one allowance,
or guarantee cheaper or better results. Provider access, pricing, and
terms still apply. More assistants are useful only when their work is useful.

## Is it for me?

- **Learning or building a side project?** Start with the plain-language
  walkthrough and a practice run that uses no real AI calls.
- **A designer, maker, or small-team builder?** Use the workflow to turn
  an idea into reviewable software changes. You still need terminal setup
  help if you are not comfortable with it; this is not yet a no-code app.
- **Already comfortable with coding agents?** Coordinate different tools,
  inspect their actual changes, and keep task history outside their chats.

An *agent* here simply means an AI coding tool that can work on project
files. The *lead* plans and coordinates; *workers* carry out specific tasks.
You remain responsible for reviewing and accepting the result.

## How it works

Imagine you want to add search to a small website:

1. **Describe the result** to the lead assistant in its usual terminal
   session: "Help people find an article by title."
2. **Approve a plan.** The lead proposes small tasks, who should do them,
   which files may change, and how to check the work.
3. **Let the workers work.** Each gets its own Git working copy, so their
   edits can be inspected separately before being brought together.
4. **Check the result.** Read the changes and test results. Optionally ask
   a different provider to review them too.
5. **Decide what to keep.** Accept and merge the changes, ask for revisions,
   or leave them out. A finished AI run is not proof that the work is right.

If a provider reaches its limit, you can mark it unavailable and prepare
work for another agent. Today that handoff needs supervision: conversation
memory does not transfer automatically. Saved checkpoints and a guided
"continue with another agent" experience are on the roadmap.

## Try it without spending AI quota

### 1. Get the tool

You need Ubuntu/Linux with Bash, Git, and standard utilities including
`flock`, `awk`, and `timeout`. The practice test does not need an AI account.
Real project work also needs a configured Git name/email and at least one
installed coding CLI with a supported sign-in. AI tools are not bundled.

For live AI work, use a disposable Linux VM without production credentials.
Workers can run commands with broad permissions: separate Git copies are
not a security sandbox, and WSL alone does not isolate your host files.

In your Linux terminal:

```bash
git clone https://github.com/danielmevit/frugal-flock.git
cd frugal-flock
bash frugal-flock-install.sh
export PATH="$HOME/.local/bin:$PATH"
frgl-flc selftest
frgl-flc version
```

The installer adds commands under `~/.local/bin` and settings under
`~/.config/agentteam`. The PATH line makes the commands available in this
terminal; [setup instructions](docs/SETUP.md) cover making that permanent.
The self-test rehearses the workflow with pretend agents in a temporary
project. It does not call a provider or use your AI allowance.

`frgl-flc` is the short command. `frugal-flock` does exactly the same thing.

### 2. Choose your next step

- **Show me the whole idea:** [read the worked-example tour](docs/EXAMPLE.md).
- **Help me set it up:** [follow the complete guide](docs/GUIDEBOOK.md),
  including signing in to your tools and choosing which ones to use.
- **I know terminals already:** [use the compact setup reference](docs/SETUP.md).

The shipped configuration includes entries for Claude Code, Codex,
Antigravity, OpenCode, and Grok. Use only the ones you have installed and
are entitled to use. Their flags and authentication support can change;
check your installed tools rather than assuming every account works.

### 3. Start with one worker

Once your chosen coding CLI is installed and signed in, use a separate
project you are comfortable experimenting on. For example, with Codex:

```bash
# Replace the URL with your own Git repository, which must have a commit.
frgl-flc new YOUR_REPOSITORY_URL my-project codex
cd my-project/repo
frgl-flc doctor
frgl-flc agents
```

Run this from the folder where you want `my-project` created. Then open
your preferred coding assistant in `my-project/repo` and ask it:

```text
Read MASTER.md and the project instructions. Help me plan one small change.
Check which workers are available, explain how you will test the result,
and wait for my approval before starting work. Do not merge for me.
```

Start with one provider; add another when you want a second perspective.
`agents` checks installed commands and availability settings, not remaining
quota or successful login. `smoke` makes live test calls and consumes
provider capacity, so run it deliberately, not as a free practice test.

## For the curious and the nerdy

Frugal Flock is a Bash orchestration layer around existing coding CLIs.
It is not a new model or a hosted AI service. The default invocation
templates use the tools' own sign-ins rather than a shared API-key service.

- **Separate workspaces:** each worker uses a Git worktree and an
  `agent/NAME` branch. A worktree is another working folder sharing the
  repository's history, not an isolated virtual machine.
- **Explicit task contracts:** Markdown task files carry instructions,
  allowed file paths, validation commands, and a definition of done.
- **Inspectable evidence:** diffs, append-only reports, live logs, a
  JSONL event ledger, and a revision-bound JSON result per task (`result`)
  let you inspect more than an assistant's final claim.
- **Cross-provider experiments:** independent reviews, competing attempts
  at a task, and rotating defect-hunting runs are available. These use
  additional provider capacity; they are optional, not the default goal.
- **Availability controls:** manually or temporarily bench a provider.
  Optional limit-message detection helps flag failed runs; it is not a
  universal quota meter or a confirmed reset-time service.

Useful commands once a project is set up:

```bash
frgl-flc help             # discover commands
frgl-flc status           # tasks, reports, review queue, running work
frgl-flc tail             # follow the latest run's log
frgl-flc score            # inspect the recorded worker scorecard
frgl-flc result codex T7  # stored run/verify/review evidence as JSON
frgl-flc handoff codex T7 # context packet for the next AI, same checkout
frgl-flc agents --json    # local availability; no login or quota probe
frgl-flc off codex 5h     # your chosen retry interval, not a quota guarantee
frgl-flc on codex         # make that provider available again
```

`stop` prevents new runs; it does not stop an already running process.
Use `kill TASK_ID` for a specific background run. A successful process,
passing checks, a reviewer's approval, and your acceptance are different
things. Read the evidence before merging; missing checks need attention.
`verify` exits 2 (INCOMPLETE) when a task has no scope or Validate lines,
and `review` runs only after a current passing `verify`. See the
[quality reference](docs/QUALITY-USAGE.md) for every exit code and field.

Coordination files stay on your machine, but coding tools can send prompts
and project content to their providers. Keep secrets out of task files and
repositories; review each provider's data handling before using private work.

### Coming from agentteam?

This is the same project, renamed from `agentteam-docs`, with its Git
history retained. You do not need to move your existing local clone.

- `frugal-flock`, `frgl-flc`, and legacy `agentteam` share one implementation
  and Bash completion. There are not three separate versions to maintain.
- `agentteam-install.sh` still works. The new `frugal-flock-install.sh`
  forwards to it, so keep both installer files together.
- Existing `AGENTTEAM_*` environment overrides, `~/.config/agentteam`,
  `agents.conf`, and project state names remain compatible.
- The implementation remains at `~/.local/bin/agentteam`; the new commands
  are links to it. Linux `flock` remains the unrelated locking utility.

To update an existing clone, run these inside its current folder:

```bash
git remote set-url origin https://github.com/danielmevit/frugal-flock.git
git pull --ff-only
bash frugal-flock-install.sh
frgl-flc selftest
```

If Git reports local changes or diverged history, stop and resolve that
before reinstalling; do not discard your work just to update.

### Find the right level of detail

| I want to… | Start here |
|---|---|
| Understand the workflow step by step | [Complete guide](docs/GUIDEBOOK.md) · [Word copy](docs/GUIDEBOOK.docx) |
| Look up everyday commands or troubleshoot | [Handbook](docs/HANDBOOK.md) |
| See a worked example | [Replayable tour](docs/EXAMPLE.md) |
| Understand task contracts and coordination | [Agent protocol](docs/PROTOCOL.md) |
| Work on Frugal Flock itself | [Maintainer handoff](docs/HANDOFF.md) · [Documentation conventions](docs/DOC-CONVENTIONS.md) |
| Test the engine's guardrails | [Test plan](docs/TESTPLAN.md) · [Word copy](docs/TESTPLAN.docx) |
| Read the background and original ideas | [Architecture research](research/multi-agent-claude-review.md) · [Original plan](docs/MASTER-PLAN.md) |

For contributors, checks that do not call live providers:

```bash
bash tools/quality-check.sh   # everything below plus selftest and ShellCheck
bash tests/frugal-flock-quality.sh
bash tests/frugal-flock-branding.sh
bash tests/agentteam-probes.sh
bash tools/check-docs.sh
```

Python 3 (standard library only) is required at run time for the evidence
commands. CodeGraph is optional; an unindexed project stays unindexed.
Pandoc is only needed to regenerate the Word manuals with
`tools/make-docx.sh`.
See the [project setup playbook](docs/ai-project-setup-playbook.md) and
[build recipe](docs/ai-full-build-recipe.md) for the development workflow.

## What comes next

**First: a reliable core.** The current milestone tightens checks and
review decisions, saves revision-bound evidence, and prepares a manual
next-AI context packet. See the [M1 checkpoint](docs/M1-STATUS.md); these
changes are in progress, not a claim of automatic recovery or OS isolation.

After that, make the tool easier to understand:

1. A simple project workspace: describe work, approve a plan, follow
   progress, and review the result.
2. Clear states for running, blocked, checked, reviewed, and accepted work.
3. A local app launcher and guided connection to tools you already use.
4. Checkpointed handoffs when a provider becomes unavailable.

These are planned features. Read the [UX proposal](docs/UX-DIRECTION.md)
and [prioritized next steps](TODO.md) for their scope and order.
The [brand notes](docs/BRAND.md) explain the name and the promise behind it.

Continuing with another AI? Open [the continuation prompt](continue-with-ai-prompt.md),
copy its prompt section, and paste it into your next AI chat. It explains
what is saved, what is unfinished, and where to continue. The
[build handoff](docs/AI-HANDOFF.md) provides additional context.
The [workspace rules](WORKSPACE-RULES.md) explain where project files belong:
one enclosing Frugal Flock folder, including its working copies and reports.
The [M1 status](docs/M1-STATUS.md) lists what is merged, the verified
results and what still needs the owner. The
[2026-10-04 report](docs/SESSION-HANDOFF-2026-10-04.md) records the earlier state.
The [findings index](docs/RESEARCH-FINDINGS.md) connects the competitor
comparison, technical review, product decisions, and unfinished work.

## Keywords

The bigger idea is **different AI agents working together as a group on
one project, with a person directing the team**. Here, working together
means coordinated tasks and reviewed handoffs, not automatically shared
conversation memory. Different people describe that idea differently:

Looking for “can I glue a few AI tools together in one main console?”
That is the goal: one place to direct separate helpers, each keeping its
own provider and limits. The [plain-English workflow guide](docs/AI-TEAM-WORKFLOWS.md)
explains the different kinds and which ones work today.

- **AI teamwork in plain language:** use different AI agents as a group,
  make AI assistants work together, build a team of AI helpers, coordinate
  AI tools from different companies, use multiple AI models on one project,
  manage your own AI coding team, let one AI build and another review,
  direct a group of AI assistants, human-controlled AI collaboration.
- **Everyday goals:** build with AI on a budget, AI help for a side project,
  manage multiple AI assistants, organize AI coding work, work with limited
  AI plans, handle AI usage limits, review AI-generated changes.
- **One place to steer the team:** glue AI tools together, mix different
  AI models in one workflow, control multiple AIs from one console,
  coordinate Claude Code and Codex, bring AI coding assistants together,
  one command center for different AI providers, switch AI when a limit
  interrupts a project, continue a project with another AI.
- **Ways of working:** one AI builds and another checks, split work between
  AI helpers, run independent tasks in parallel, pass a task from one AI
  to the next, compare two AI solutions, ask an AI to find bugs, supervise
  a team of agents. See the workflow guide for current versus planned support.
- **People and projects:** learners, hobby projects, independent makers,
  designers building software, small teams, solo developers, indie apps,
  creative coding, learning to build with AI.
- **Technical terms:** multi-agent collaboration, AI agent teams,
  multi-agent orchestration, multi-model workflow, LLM teams,
  heterogeneous agents, cross-provider coding agents, human-in-the-loop AI, Git worktrees,
  CLI orchestration, task delegation, agent review, validation gates,
  subscription-based coding tools, quota-aware coordination.
- **Related ideas explained, not all implemented:** sequential agents,
  parallel agents, supervisor–worker workflows, writer–reviewer pipelines,
  agent relay, competitive agents, best-of-N, cross-provider handoff,
  agent swarms and AI councils. This is not model merging, shared subscription
  quotas, or an automatic consensus engine.
- **Names and commands:** Frugal Flock, frugal-flock, frgl-flc, agentteam,
  agentteam-docs, Claude Code, Codex, Antigravity, OpenCode, Grok.
