# Optional subscription adapters

These adapters run from a Unio source checkout. They are not included in the
v0.5.7 standalone installer. Install and sign in to the external tool manually;
the adapter does not purchase credits, change billing or fall back to another
paid service.

| Route | Use it for | Guide |
| --- | --- | --- |
| Mistral Vibe 2.26.1 | Implementation tasks using GLM 5.3 or Mistral Medium 3.5, explicitly pinned at high effort | [Vibe worker setup](MISTRAL-VIBE.md) |
| Perplexity Pro web | Research and draft code proposals using GLM 5.3, Kimi K3 or the connector's GPT-6 Sol Thinking route | [Perplexity setup and proposal workflow](PERPLEXITY-WEB.md) |

Perplexity supplies research, citations and proposed code from selected context.
A capable implementation agent checks that proposal, applies suitable changes
in its own Unio worktree and runs the assigned validation. The lead reviews
the actual diff and evidence. Generating a proposal does not accept a change.
The adapter never executes suggested commands or applies a patch automatically.

Keep aliases on the same subscription in one shared budget group. Perplexity,
Mistral Vibe and OpenCode are separate account routes even when they offer the
same underlying model. In low tier, each shared budget permits one independent
native workflow, including a lead when that account hosts it.

Both adapters passed focused offline tests. The corrected Vibe configuration
also passed an offline check against the installed CLI schema. No live
Perplexity account entitlement, remaining allowance, response quality or
effective model identity has been verified. The pinned connector names GPT-6
Sol, not GPT-6.1 Sol; do not silently equate the two.
