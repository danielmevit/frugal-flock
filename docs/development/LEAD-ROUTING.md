# Lead routing, reasoning effort and spending

Read this policy and [the model effort guide](MODEL-EFFORT.md) before planning
assignments and at the start of each new lead session. Follow the owner's
current instructions and the selected project's rules. These defaults apply
whenever Unio is active; they are not permission to spend beyond an owner's
approved plans, task scope or invocation budget.

## Match the agent to the work

Use the verified-free MiMo and LongCat routes for useful, bounded routine
work: documentation, formatting, mechanical file/link inventories, boilerplate
and supplementary checks. Give them precise scopes and verify their output.
Free pricing does not establish model quality or current availability.

Prefer stronger available subscription agents for architecture, complex
coding, UI design, difficult debugging, security and final release assessment.
Choose using supported capabilities and actual task results, not a permanent
ranking. Codex, Claude, Grok and Antigravity are possible routes, not guarantees
that their accounts have usable capacity. Antigravity (`agy`) is a multi-model
CLI; record its selected model and AI lab as well as the CLI name.

Do not invent chores merely to keep workers busy. Use parallel agents for
independent scopes and blind reviews; keep dependent changes ordered. The
lead compares findings, inspects the complete change and verifies the result.

## No extra token charges by default

Use the owner's existing funded subscriptions. OpenCode subscription models
use the `opencode-go` route. Do not substitute a pay-as-you-go model or buy
credits, top up, change billing, create an account or alter authentication
to get around a limit. Those actions require explicit owner authorization.

The following exact Zen routes are an exception for routine supporting work
while their prices remain zero:

- `opencode/mimo-v2.6-flash-free`
- `opencode/longcat-2.5-preview-free`

Both were listed free in official pricing and native cost metadata on
2026-10-06. This is a dated observation, not a promise that they stay free.
Before every new free-route assignment, check current official pricing and
native input, output and cache costs. Missing, conflicting or nonzero cost
means the route is ineligible. Pin the primary model and any title/helper
`small_model` to the same eligible free model. Do not enable a paid fallback
or silently replace an unavailable free model. Other Zen routes are not
covered by this exception. See [OpenCode's pricing](https://opencode.ai/docs/zen/#pricing).

## Start at high or the supported middle

Choose high, or the model's supported middle level, for ordinary work.
Medium is appropriate for routine chores on models that expose it. Keep
GLM 5.3 at high. LongCat's observed low/medium/high scale permits medium for
routine work; MiMo V2.6 Flash exposes no effort variant on this route, so
record the inherited/effective setting as unknown rather than inventing one.

Raise effort only when evidence shows reasoning difficulty. Use a supported
next level, such as high to xhigh, and reserve max for an occasional narrow,
important problem. Record the reason, time bound and current allowance.
Return ordinary later tasks to the default. Authentication, quota, transport
and missing-tool failures need their actual causes resolved; more reasoning
will not fix them. Read the model effort guide for route-specific exceptions.

## Check capacity and preserve work

An installed CLI or model catalog does not prove sign-in, quota or availability.
Use supported account metadata when available; otherwise record Unknown or a
dated owner reading. Distinguish five-hour, weekly and monthly limits, and
keep a reset estimate separate from actual restored capacity. Never repeatedly
call a known unavailable route to test whether waiting fixed it.

Freeze each task, scope, model, effort, configuration and time bound before
its authorized invocation. Record actual requested/effective settings, route,
AI lab, allowance evidence and its age. Respect one-invocation/no-retry rules;
a concrete defect may justify a new scoped correction, not an unchanged retry.
Resume Unio before authorized calls and stop it afterward. Preserve failures.

Make coherent scoped commits early, before lengthy final checks, and maintain
clear handoffs. Do not rely on the final AI response to preserve work. Treat
unfinished recovery data as unverified. Supervisor-owned automatic saving and
portable checkpoint recovery remain planned work; these instructions do not
claim that those features are implemented.

## Independent reviews and owner control

Keep source execution, checks, review, acceptance, merge and publication distinct.
Use independent agents from different AI labs under the project's review rules;
this project requires two nonauthor labs, then the lead's own complete review.
Prepare reviewers separately with complete material and no peer verdicts.
Supplementary routine checks do not replace a competent final security review.
Fixes require fresh reviews of the changed candidate. Reviews reduce risk;
they cannot guarantee every error will be found.

Run the required full merged-tree quality gate and push the exact passing
revision. Keep releases and installation within the owner's authorization.
The owner remains in control of plans, spending and published changes.

## Where leads find these instructions

In the Unio source repository, this file and the model effort guide are in
`docs/development/`; the development index and continuation prompt link here.
The local workspace entry instructions and installed lead template should
point to readable copies before any assignment. Preserve existing owner role
cards when adding those references; do not replace custom instructions.

This document is an operating policy for the lead. The current runner does
not automatically enforce these routing choices, read pricing, escalate
reasoning effort or expose a fleet-wide quota meter. Standalone installer
packaging of the guides is part of shipping work; do not infer its completion
from the presence of a repository document or a manual local guide update.
