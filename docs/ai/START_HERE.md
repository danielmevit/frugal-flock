# Start a Unio AI session

Identify your role before taking action. A lead reads MASTER.md and the
project's own instructions; a worker reads WORKER.md and its one assigned
task. Do not turn a worker session into a competing lead or start additional
AI calls outside that task.

## Leads: read these before planning or delegation

Read [lead routing and spending](../development/LEAD-ROUTING.md),
[bounded escalation](LEAD-ESCALATION.md),
[model scoreboard and task fit](../development/MODEL-SCOREBOARD.md),
[model effort](../development/MODEL-EFFORT.md),
[standing model roles](MODEL-ROLES.md),
[work modes and subscription tiers](../WORK-MODES.md), and
[workspace rules](../development/WORKSPACE-RULES.md). Run `unio policy`
before planning or delegation: the mode shapes scope and review planning
and the tier strictly caps independent concurrent native workflows per shared budget
(low 1, medium 2, high 4, lead included), rejecting over-dispatch. The installed copy is
`coord/docs/WORK-MODES.md` after `unio init`. Then use the
[current handoff](../development/continue-with-ai-prompt.md), the newest
workspace coordination log and actual current worker receipts. Existing
MASTER.md reading instructions name this startup file; it supplies the
public repository entry point instead of relying on unpublished role cards.

Main implementation belongs to available Grok, Antigravity/Gemini, Claude
Code or Codex workers. Keep the designated lead on planning, coordination
and final assessment by default. If a worker and one suitable replacement
struggle, the lead directly completes the correction in its existing session.
Low tier must not create another independent session on the lead's allowance.

Use the [verified free OpenCode pool](../FREE-MODELS.md) only for routine
support such as docs, formatting, inventories, boilerplate and predefined
checks. Free models must not lead, own main features or replace the lead
through a cooldown. This rule persists in every session. OpenCode subscription
models use Go; free routes require current zero prices and pinned free helper
models. No paid fallback, extra token charges, purchases or billing/auth changes.

Start reasoning at high or the supported middle; only escalate supported
levels for demonstrated difficulty, up to xhigh. Never request max or ultra;
use high when xhigh is unavailable. Read [task budgets](../development/TASK-TIME-BUDGETS.md)
before setting token, price and time limits. An
installed model or an elapsed reset estimate does not establish quota.
Preserve frozen tasks, one-invocation rules, early commits, actual checks,
independent reviews and owner control. Read the complete guides for exceptions.

The guide documents operating policy. The current runner does not enforce
pricing or adaptive effort automatically, and new standalone installer guide
packaging remains shipping work. On this machine, an owner-authorized local
lead-template update points to readable installed guide copies; that manual
update is not a new runtime release. Existing custom projects retain their
owner instructions and need an explicit readable guide reference when updated.

## Optional subscription routes

Read the [adapter guides](../integrations/README.md) before assigning Mistral
Vibe or Perplexity work. Vibe is an explicitly pinned implementation CLI;
Perplexity researches and saves draft code proposals for a separate capable
implementation agent to review, apply and validate. Keep same-subscription
aliases in one budget group and never count an unknown effective model as
independent cross-lab acceptance. External installation and sign-in are manual.
No adapter authorizes paid fallback or an extra lead-provider workflow.

## Workers: follow the assigned scope

Use the assigned task and role card, preserve other workers' files and commit
coherent changes early. Report actual source exit and checks separately.
Do not merge, publish, change billing, retry a frozen task or create other
AI calls unless the task and owner explicitly authorize it. A source commit
alone does not establish verification, review, acceptance or public delivery.
