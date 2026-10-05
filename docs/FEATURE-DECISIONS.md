# Useful ideas from comparable tools

Decision log, 2026-10-03. This selects ideas from the
[primary-source competitor review](../research/COMPETITIVE-REVIEW.md), not
copied implementations. None of these comparisons is a performance benchmark.

| Idea and reference | Decision for Unio | Why / acceptance boundary |
|---|---|---|
| Proof/evidence packages — [AWO](https://github.com/ystepanoff/awo) | Adopt a bounded original version in M1. | Revision-bound checks and a manual context packet make human review and switching AI clearer. Not a backup or automatic acceptance. |
| Explicit worker lifecycle — [Agent Orchestrator](https://github.com/Untrivial-ai/agent-orchestrator) | Adopt separate CLI result states in M1; visual workspace later. | Process, checks, review, and integration must not collapse into one green tick. No cloud daemon required now. |
| Supervisor, parallel and sequential work — [CAO](https://github.com/awslabs/cli-agent-orchestrator) | Explain existing task coordination now; automate only measured gaps later. | Useful vocabulary, but a general autonomous workflow engine would expand scope and usage. |
| Multiple native sessions and isolated edit branches — [Claude Squad](https://github.com/smtg-ai/claude-squad) | Keep existing native tools/worktrees; simplify their presentation in M2. | Build on the existing engine. Worktrees remain coordination, not OS security. |
| Cross-provider review flows — [Claude Octopus](https://github.com/nyldn/claude-octopus) | Keep optional independent review; defer multi-round councils. | An extra reviewer can help, but repeated discussion spends scarce allowance and votes are not tests. |

M1 implementation must pass [the frozen contract](QUALITY-M1-CONTRACT.md)
before any adopted idea is described as shipped. Track actual completion
in [M1 status](M1-STATUS.md). Do not import competitor source or assets.

Later candidates: compact task inspector, readable activity, explicit stop
controls, preserved checkpoints, and guided provider replacement. Defer
automatic consensus, accounts/hosted services, an infinite workflow canvas,
and silent model routing. They do not yet justify their complexity for a
person working with basic plans.

The owner particularly endorsed clean continuation after provider limits.
The proposed next layer is [capacity-aware task sizing and continuation](CAPACITY-AWARE-CONTINUATION.md):
supported usage readings or manual input, conservative scheduling, and
tested checkpoints. This is design work, not a shipped capability or a
change to M1's frozen scope.
