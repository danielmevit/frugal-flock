# Model roles — standing Unio instructions

Read this before assigning work in every new lead session. These defaults
apply across sessions, handoffs and cooldown recovery; they are not a temporary
choice for one run. The owner can explicitly change the policy.

| Role | Agents | Work they own |
| --- | --- | --- |
| Lead | The owner's designated subscription agent | Planning, contracts, delegation, coordination, personal final review and authorized integration |
| Main implementation workers | Grok, Antigravity/Gemini, Claude Code and Codex | Product features, core behavior, architecture within the assigned scope, complex debugging, UI and substantive security corrections |
| Routine supporting workers | The verified-free OpenCode Zen pool | Documentation, formatting, inventories, mechanical edits, boilerplate, running predefined checks and supplementary observations |

The free pool must **never lead, own main feature implementation, perform
final acceptance or replace a subscription lead during a cooldown**. A free
worker follows a precise bounded task and reports results to the lead. If a
routine assignment reveals a design problem, difficult bug or security issue,
preserve the findings and give the substantive work to a main implementation
worker. Raising a free model's effort does not change its permitted role.

The distinction is an owner-selected routing policy, not a claim that every
listed model has a measured quality or reasoning score. See the exact free
routes and checked outcomes in [the inventory](../FREE-MODELS.md).

## Choose available workers without duplicating the lead

Choose among the main implementation agents by task fit, current allowance
and the owner's latest availability information. Antigravity (`agy`) is the
multi-model platform used for Gemini here; record its actual selected model.
Do not silently substitute a different account, CLI or paid API route.

In low tier, an agent already serving as lead occupies its shared budget's
single independent workflow. For example, a Codex lead must not launch a
second independent Codex implementation session. Other available budgets
can work concurrently. Authorized helpers inside one workflow are allowed;
they do not turn it into several independent features or test assignments.
Read the separate [mode and tier guide](../WORK-MODES.md).

Capacity changes are temporary; role definitions persist. If Claude has hit
a weekly limit and Codex leads, assign substantive work to available Grok
and Antigravity/Gemini. Revisit dated failures when the owner reports restored
availability, using supported metadata or one authorized task invocation.
An installed CLI or model list alone does not prove usable quota. Preserve
actual failures; never blindly retry a frozen task or promote a free worker
because a main implementation route is unavailable.

## Spending and verification

Use existing owner-approved subscriptions. Free workers require current
official and native zero prices, with primary and helper models pinned to
the same eligible free route. No paid fallback, purchases, billing or
authentication changes. Follow the [routing and effort guide](../development/LEAD-ROUTING.md).

Use the selected work mode and the task's frozen checks. A supporting worker's
output, successful script run or approval does not replace the lead's review
or establish acceptance. Record real outcomes rather than running a separate
benchmark campaign to fill a scorecard. These are instructions for agents;
the runtime does not automatically identify a model's class from its name.
