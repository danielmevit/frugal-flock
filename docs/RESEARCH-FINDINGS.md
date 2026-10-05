# Unio — findings index

Recorded 2026-10-03. Start here when continuing without the original chat.
Before this handoff, branding, UX, and next steps were already saved;
the competitor comparison and engine review were not consolidated into
separate reusable documents. They are now linked below.

## Findings, evidence, and decisions

| Finding | Conclusion and status | Detail |
|---|---|---|
| F1 — The category | Human-supervised teams of coding agents from different providers already exist. Observed overlap, not a uniqueness claim. | [Competitive review C1–C2](../research/COMPETITIVE-REVIEW.md) |
| F2 — Why keep building? | Simple supervision for people using modest plans is a useful hypothesis, not proven savings or superiority. | [Positioning and validation C3–C5](../research/COMPETITIVE-REVIEW.md) |
| F3 — Product identity | Unio; Small plans. Big ideas.; canonical and short CLI aliases approved and implemented. | [Brand contract](BRAND.md) |
| F4 — UX barrier | Exposing tasks, branches, and commands first makes onboarding difficult. Recommended response: one project conversation with plan, activity, and review cards. Needs user testing. | [UX direction](UX-DIRECTION.md) |
| F5 — Trustworthy results | Process exit, checks, reviewer decision, human acceptance, and integration are different outcomes. Current engine gaps remain open. | [Engine findings E1–E3](ENGINE-FINDINGS.md) |
| F6 — Safety | Git worktrees and scope checks are not OS isolation; broad-permission defaults need explicit boundaries. | [Engine finding E4](ENGINE-FINDINGS.md) |
| F7 — Capacity and continuity | No universal quota meter; automatic checkpointed provider continuation is not yet implemented. | [Engine findings E5–E6](ENGINE-FINDINGS.md) |
| F8 — Delivery sequence | Owner revised priority: M1 quality first, then mock UX, protected read-only bridge, bounded live runs, checkpointed continuation. | [M1 status](M1-STATUS.md) · [Prioritized next steps](../TODO.md) |
| F9 — Discovery language | Explain a group of different AI assistants working on one project, not only technical orchestration terms. | [README keywords](../README.md#keywords) |
| F10 — Related workflow types | Explain supervisor/worker, parallel, sequential, writer/reviewer, races, and continuation; distinguish unsupported consensus and quota pooling. | [Plain-language workflows](AI-TEAM-WORKFLOWS.md) |
| F11 — Useful competitor ideas | Adopt evidence packages and separate result states in M1; defer expensive councils and cloud services. Original implementation only. | [Feature decisions](FEATURE-DECISIONS.md) |
| F12 — Visual reference | Toolcraft-inspired working area and compact inspector, without copying source/templates/assets. UI follows M1. | [Toolcraft reference](TOOLCRAFT-REFERENCE.md) |
| F13 — Capacity-aware continuation | Owner-endorsed direction: choose finishable tasks based on honest capacity signals and preserve work before limits. Proposed, not implemented. | [Continuation design](CAPACITY-AWARE-CONTINUATION.md) |
| F14 — Live multi-AI testing (2026-10-05) | Effort setting drives speed more than model choice; GLM 5.3 high won a five-model race; second-company reviews each caught real issues; dogfooding found and fixed two engine bugs. | [Findings 2026-10-05](FINDINGS-2026-10-05.md) |

## Current state

The repository is public at
[danielmevit/unio](https://github.com/danielmevit/unio),
renamed in place from `unio-docs`. The reviewed published baseline
is `f962b6a`; this handoff adds documentation on top. Existing commit
history was preserved and completed implementation work was merged into
main at the owner's explicit request.

The software is still a Bash CLI. The graphical app, local service,
durable job queue, and automatic recovery experience are not shipped.
No frontend framework has been selected in this review.

## How to interpret the evidence

- Competitor claims are supported by linked primary repository docs,
  not hands-on installations or comparative benchmarks.
- Engine findings cite the reviewed source revision and propose tests;
  documenting them does not mean they have been fixed.
- UX and positioning are proposals. They need observed user feedback.
- Passing current regressions is not proof of unrestricted safety or
  complete evidence handling; one old selftest preserves permissive behavior.
- The [older Claude architecture review](../research/multi-agent-claude-review.md)
  is historical. Do not reuse its pricing, account-policy, model-access,
  or isolation claims as current truth without verification.
- Local coordination logs are not required to continue from a fresh
  clone and are not copied into the public repository.

## Continue with another AI

Use [AI-HANDOFF.md](AI-HANDOFF.md). It includes the next bounded milestone,
acceptance criteria, compatibility requirements, and a copy-paste prompt.
The prompt does not authorize live provider usage, automatic integration,
or a full backend build.
