# Unio

Small plans. Big ideas.

## Name and promise

The owner selected Unio as the product name and approved the
tagline above. Unio connects AI coding tools from different
companies into one workspace: one AI leads, the others work as its
subagents in separate copies of the project, and a person approves what is
merged. The name explains it: a flock of AIs from different companies, run
frugally on the plans people already have.

The promise is to reduce the interruption and coordination work caused by
limited plans. Provider limits still apply. More agents do not guarantee
better code, and using a different provider does not transfer the first
provider's quota or conversation memory.

## Naming contract

| Surface | Name |
|---------|------|
| Product and window title | Unio |
| Tagline | Small plans. Big ideas. |
| One-sentence description (README title, GitHub) | Connect AI coding tools from different companies into one workspace |
| Canonical terminal command | `unio` |
| Installer entrypoint | `unio-install.sh` |

GitHub repository metadata, set 2026-10-04. Keep the description, README
title and these topics consistent when the product description changes:

- Description: "Connect AI coding tools from different companies into one
  workspace: Claude Code, Codex, Grok, Antigravity and OpenCode (Kimi) work
  as a lead and subagents, each in its own copy of your project, with
  checked results and you approving every merge."
- Topics: 10 precise tags, not the maximum of 20. Each must describe what
  Unio does; generic filler (llm, ai-workflow) and jargon
  (human-in-the-loop) dilute it: ai-orchestration, agent-orchestration,
  multi-agent, subagents, ai-agents, coding-agents, agentic-coding,
  multi-llm, claude-code, codex.

Do not use `flock` as an executable name. It is the Linux locking utility
used by the orchestration engine.

The naming change preserves existing `UNIO_*` environment variables,
the default `~/.config/unio` configuration, project coordination data,
and existing automation. The canonical repository is now
[danielmevit/unio](https://github.com/danielmevit/unio),
renamed in place from the historical `agentteam-docs` and `frugal-flock` repositories with its history retained. Existing
local directories need not be renamed; keeping them avoids breaking
worktree paths (for example, the legacy local path `/mnt/d/Vibe Coding/_vm/frugal-flock` stays intact). Point their Git remote at the new URL.

## Voice

Friendly, resourceful, clear. Use the bird theme in identity and small
illustrations, while keeping task actions literal: Start, Pause, Review,
Request changes, and Apply changes. People should not need to learn bird
metaphors to understand what a button does.

Show the real provider beside every agent. A role such as Reviewer must
still say whether Claude, Codex, or another provider is doing the work.

Useful product copy:

- What would you like to build?
- Review the plan before your flock starts.
- This agent reached its limit. Your work is saved.
- Continue with another available agent.
- The agent finished. Checks are still running.
- Ready for your review.

Only claim work is saved after a durable checkpoint exists. When usage
information is unavailable, say Unknown instead of inventing a percentage.

## Product direction

See [UX direction](UX-DIRECTION.md) for the proposed interface and delivery
sequence. The product name is decided; the interface described there is a
design proposal, not a claim that a graphical app already ships.
