# Model scoreboard and delegation guide

Updated 2026-10-08 from real Unio work. Read this before delegation, alongside
the project's latest capacity notes and owner instructions. Select by task
fit and checked outcomes; an unavailable or owner-reserved model is not a
fallback. Start at high or the supported middle and keep GLM at high.

## Two views of the evidence

`unio score` already summarizes the append-only ledger: runs, process success
and failure, limit walls, verification, merges and measured duration per worker.
It makes no model call. Worker names can be aliases, historical merge records
can have no matching run, and process success is not acceptance. Do not turn
those columns into a model quality percentage or rank AI labs by merge totals.

This guide adds a curated, task-specific view for the lead. The examples below
are selected checked cases, not every task in the ledger or a controlled model
comparison. Counts describe only the named examples. Different scopes, routes
and efforts limit comparison. Model-specific automatic aggregation and routing
remain planned in the
[model-experience feature](https://github.com/danielmevit/unio/blob/main/docs/development/MODEL-EXPERIENCE.md).

## What to delegate where

| Work | Starting choice | Guardrails and reason |
| --- | --- | --- |
| State preservation, shell/Git boundaries, lifecycle and difficult debugging | Available Codex, Grok or Claude main worker | Codex has accepted targeted correctness repairs here. Grok is the owner's preferred reasoning worker; that preference does not prove universal superiority. Respect owner holds. |
| UI structure, interaction and visual implementation | Available Claude or Codex main worker | Opus completed the accepted map identity correction. Validate actual interaction and inspect the rendered result. |
| Small mechanical edits with explicit expected outputs | Gemini or another eligible main worker | Gemini completed bounded fixture work, but recent stateful/UI corrections required substantial rework. Keep scope concrete and inspect the actual diff. |
| Documentation, formatting and inventories | Verified-free routine worker, such as LongCat or MiMo | Small documentation samples completed; this does not qualify them for security design or main features. Check exact free pricing and availability first. |
| Running predefined supplementary checks | Eligible routine worker or local scripts | Keep expected commands and results explicit. A check runner does not own test design, implementation or acceptance. |
| A correction that defeated its first worker and one suitable replacement | The existing lead directly | Reuse saved work and fix the remaining gap. Do not add another session on the lead's budget in low tier. |

These are routing defaults, not permanent model classes or benchmark scores.
The project can override them with newer checked evidence. Free models remain
supporting workers only. Exact controls and routes are in
[model effort](https://github.com/danielmevit/unio/blob/main/docs/development/MODEL-EFFORT.md),
[model roles](https://github.com/danielmevit/unio/blob/main/docs/ai/MODEL-ROLES.md)
and the [free inventory](https://github.com/danielmevit/unio/blob/main/docs/FREE-MODELS.md).

## Selected project outcomes

| Exact model / route / requested effort | Selected cases | Checked outcome and routing lesson |
| --- | --- | --- |
| `gpt-6.1-sol` / Codex CLI / xhigh | `QUEUE-INVARIANTS-1`; `RELEASE-TIMEOUT-CODEX-1` | 2 accepted corrections: queue invariants passed 8 focused checks plus recorded reviews; timeout repair passed 3 focused checks and personal lead review. Suitable evidence for targeted correctness work, not a full-model success rate. |
| `claude-opus-5-5` / Claude Code / high | `BROWSER-MAP-IDENTITY-OPUS-1`; `WORK-SAVING-MANUAL-OPUS-1` | 1 accepted UI correction; 1 saving candidate requiring changes after two demonstrated lead findings despite passing its initial 5 checks. Strong implementation still needs real review. |
| `gemini-3.1-pro-high` / Antigravity CLI / high | `RELEASE-LAUNCH-OBSERVATION-1`; `BROWSER-THEME-MAP-1`; `BROWSER-THEME-MAP-FIX-1`; `BROWSER-MAP-IDENTITY-1`; `WORK-SAVING-PRESERVE-LOCKS-1` | 1 accepted bounded fixture correction; 2 UI candidates required further fixes; 1 connection failure without edits; 1 saving correction failed native scope verification despite 5 passing check commands; lead review found incomplete unsafe-lock inspection and took over. Repeated fixture mistakes and premature success messages added rework. Prefer smaller mechanical assignments. |
| Existing Codex lead / same session / exact serving variant not exposed | `WORK-SAVING-LEAD-FINALIZE-1`; `WORK-SAVING-LOCK-OBSERVATION-1` | Takeover accepted in source after one self-authored full-suite failure exposed shared-lock observation, then 4/4 focused native checks and personal review. Full suite on the corrected revision remains required before release. Same-session lead work is not an independent review or delegated Source. |
| `grok-4.7` / Grok Build / high | Rename slice D; saving contract draft; `WORK-SAVING-RUNTIME-1` | Accepted license/rename work, a contract draft needing lead amendment, and a separate usage-exhausted run without edits. Useful contributions and rework both count; the capacity failure is not a code-quality sample. |
| `opencode/longcat-2.5-preview-free` / OpenCode Zen / high and medium | `ROADMAP-PRIORITIES-1`; `LEAD-POLICY-STARTUP-DOCS-1` | 2 completed bounded documentation assessments. This small sample supports routine documentation help, not independent final security acceptance. |
| `opencode/mimo-v2.6-flash-free` / OpenCode Zen / no exposed override | `LEAD-POLICY-STARTUP-DOCS-1`; `WORK-POLICY-1` | 1 completed documentation assessment; 1 broad state/CLI task timed out without edits. Keep it on routine support. |

Requested effort is not proof of effective effort. Keep the original pin and
response evidence when the CLI cannot establish the effective setting. Other
models remain untested for these task types until checked project work supplies
evidence; a catalog entry or a model name establishes no quality score.

Public candidate anchors include the
[queue repair](https://github.com/danielmevit/unio/commit/ec256d1f39a330ac3ea92b5e5367412ffc9d96e2),
[Codex timeout repair](https://github.com/danielmevit/unio/commit/c5957063bffe35ffcce68e1cd8d40b2d814370f9),
[Gemini launch observation](https://github.com/danielmevit/unio/commit/7fed7cd7f811f246b891e862139d3497ae75f878),
[accepted UI correction](https://github.com/danielmevit/unio/pull/3)
and the [saving work and subsequent lead corrections](https://github.com/danielmevit/unio/pull/4).
The free inventory records the routine assessments. Original tasks, process
results, verification, reviews and exact revisions stay in private workspace
receipts; do not publish raw prompts or logs to fill this table.

## Update it after actual work

Record exact model/version, CLI/gateway, requested/effective effort, task type
and scope, receipt/task/candidate references, actual Source exit, verification,
acceptance/integration, demonstrated rework, takeover and observed duration.
Keep operational failures separate. Preserve unknown quota, cost and timing;
sleep-affected wall time is not active work time. An interim report is not a
final result. Update pending cases when their run and review actually finish.

Before each assignment, use relevant accepted examples and rework burden,
current availability, account grouping and owner preferences together. State
why the worker fits. Follow
[worker → replacement → lead takeover](https://github.com/danielmevit/unio/blob/main/docs/ai/LEAD-ESCALATION.md)
when progress stops. Do not run extra benchmark or reviewer fleets merely to
populate this guide, and do not reset unsuccessful task history with a new ID.
