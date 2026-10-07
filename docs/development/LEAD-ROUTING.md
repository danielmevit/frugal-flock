# Lead routing, reasoning effort and spending

Read this policy and [the model effort guide](MODEL-EFFORT.md) before planning
assignments and at the start of each new lead session. Follow the owner's
current instructions and the selected project's rules. These defaults apply
whenever Unio is active; they are not permission to spend beyond an owner's
approved plans, task scope or invocation budget.

## Match the agent to the work

Read [the standing model roles](../ai/MODEL-ROLES.md) before each session.
Grok, Antigravity/Gemini, Claude Code and Codex are the main implementation
agents. Use available workers from that group for product features, core
behavior, UI, complex debugging and substantive security corrections. The
owner's designated lead plans, coordinates, reviews and integrates.

Use the [verified free worker pool](../FREE-MODELS.md) only for routine
support: documentation, formatting, inventories, mechanical changes,
boilerplate, predefined checks and supplementary observations. Free routes
must never lead, own main feature implementation, decide final acceptance or
replace the lead during a cooldown. Increasing effort does not promote a
free model into another role. Escalate difficult findings to a main worker.
This is a standing owner policy, not an invented reasoning-score ranking.

Choose using task fit and current availability. Low tier counts the lead's
workflow, so do not launch a second independent job on its shared allowance.
If Codex leads and Claude is exhausted, use available Grok and
Antigravity/Gemini for implementation. Antigravity (`agy`) is a multi-model
CLI; record its selected model and AI lab. A past capacity failure is dated
evidence: check the owner's new availability report instead of treating it
as permanent, while preserving invocation and no-paid-fallback rules.

Do not invent chores merely to keep workers busy. Use parallel agents for
independent scopes and blind reviews; keep dependent changes ordered. The
lead compares findings, inspects the complete change and verifies the result.

## No extra token charges by default

Use the owner's existing funded subscriptions. OpenCode subscription models
use the `opencode-go` route. Do not substitute a pay-as-you-go model or buy
credits, top up, change billing, create an account or alter authentication
to get around a limit. Those actions require explicit owner authorization.

The eleven exact Zen free routes in [the inventory](../FREE-MODELS.md) are
an owner-approved exception for worker assignments while prices remain zero.
Before each new assignment, check current official pricing and native input,
output and cache costs. Missing, conflicting or nonzero cost means the route
is ineligible. Pin the primary model and any title/helper `small_model` to
the same eligible free model. Do not enable paid fallback or silently replace
an unavailable free model. Exo's local eligibility is still unestablished.
See [OpenCode's pricing](https://opencode.ai/docs/zen/#pricing).

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
the project's current owner instructions decide the review count and the
lead always performs its own assessment. The current Unio session uses
personal lead review without extra reviewer workers, under the owner-selected
YOLO mode. Preserve that explicit exception in review receipts.
Prepare reviewers separately with complete material and no peer verdicts.
Supplementary routine checks do not replace a competent final security review.
Fixes require fresh reviews of the changed candidate. Reviews reduce risk;
they cannot guarantee every error will be found.

Run the checks frozen for the task and push the exact accepted revision.
Under the current YOLO cadence, use focused checks per coherent feature and
reserve the full repository gate for release or demonstrated need. Keep releases and installation within the owner's authorization.
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
