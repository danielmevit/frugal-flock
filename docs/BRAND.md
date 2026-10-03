# Frugal Flock

Small plans. Big ideas.

## Name and promise

The owner selected Frugal Flock as the product name and approved the
tagline above. The product helps people build with the AI plans they can
afford, coordinating different coding agents under human supervision.

The promise is to reduce the interruption and coordination work caused by
limited plans. Provider limits still apply. More agents do not guarantee
better code, and using a different provider does not transfer the first
provider's quota or conversation memory.

## Naming contract

| Surface | Name |
|---------|------|
| Product and window title | Frugal Flock |
| Tagline | Small plans. Big ideas. |
| Canonical terminal command | `frugal-flock` |
| Short terminal command | `frgl-flc` |
| Compatibility command | `agentteam` |
| New installer entrypoint | `frugal-flock-install.sh` |

Do not use `flock` as an executable name. It is the Linux locking utility
used by the orchestration engine.

The naming change preserves existing `AGENTTEAM_*` environment variables,
the default `~/.config/agentteam` configuration, project coordination data,
and existing automation. The current GitHub URL and local directory name
remain accurate references; changing either is a separate migration.

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
