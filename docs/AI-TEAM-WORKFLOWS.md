# Can I make different AIs work together?

Yes: Unio coordinates separate coding tools on one project, with
you in charge. Think **one place to direct several AI helpers**, not one
new model made by merging their brains. The current control surface is a
command line; a friendlier visual console is planned.

## Common ways people describe an AI team

| Everyday description | Common technical term | Fit today |
|---|---|---|
| I direct the team; helpers do assigned pieces. | Supervisor and workers; human-in-the-loop orchestration | Core workflow: explicit tasks, scoped work, owner review. |
| Several helpers work on different pieces at once. | Parallel agents; fan-out | Separate worker worktrees; dependencies and integration still need supervision. |
| One builds it, another checks it. | Writer–reviewer; independent review | Existing review command; M1 hardens decision parsing and evidence. |
| One finishes a step, then hands instructions to the next. | Sequential workflow; relay; pipeline | Manually coordinated tasks/reports; not an automatic workflow graph. |
| Give the same problem to two helpers and compare. | Competitive runs; best-of-N; agent race | Existing race command; a person picks a candidate, with extra provider usage. |
| Ask a helper to find problems in the result. | Adversarial testing; red-team review | Existing sabotage workflow for defect hunting, not a security guarantee. |
| Let another company's AI continue when mine runs out. | Cross-provider handoff; failover | Manual takeover is possible; M1 targets a context packet. Automatic checkpointed recovery is planned. |
| Have several AIs discuss, vote, and agree. | Council; debate; consensus; swarm | Not an implemented consensus engine. Agreement would not prove correctness. |
| Make all my subscriptions one shared allowance. | Quota pooling | Not supported. Each provider keeps its own limits, access rules, and billing. |
| Combine model weights into a smarter model. | Model merging; mixture-of-experts | Not this product. It coordinates tools rather than training or merging models. |

These are related search terms, not interchangeable promises. A task
handoff does not transfer private conversation memory automatically.

## Where to start

Use one worker and optional reviewer first. Add parallel work only when
tasks can be separated and the extra checking is worth the usage. Keep
provider names visible and use the tools/accounts you actually have.
Unio does not create subscriptions or bypass their limits.

For plain-language setup, start at the [README](../README.md). For product
comparisons, see the [sourced research](../research/COMPETITIVE-REVIEW.md).
For planned reliability changes, see [M1 status](M1-STATUS.md).
