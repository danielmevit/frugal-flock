# Work modes and subscription tiers

Unio has two independent settings: the pace of work and the budget available
for coordinating it. Choose them deliberately; a larger subscription does
not require a slower workflow, and a smaller one should not exhaust the lead.

Implementation status: approved command and behavior contract on 2026-10-07;
runtime implementation is in progress. Released Unio 0.5.2 does not yet have
these switches. Commands below describe the new development functionality.

## Choose the pace

| Mode | How the lead organizes work | Checks and review |
| --- | --- | --- |
| `yolo` | Finish a useful feature in a coherent batch. Delegate implementation and keep coordination brief. | Focused checks for changed behavior, a real smoke check where relevant, and a brief lead review. Avoid routine extra reviewer calls. Run the full required gate at a release boundary. |
| `medium` | Deliver manageable feature batches with more integration attention. | Focused checks plus relevant integration checks. Ask for an independent review when the change or an unresolved finding warrants it. |
| `safe` | Use smaller checkpoints and inspect interfaces and failure paths carefully. | Broader integration checks and the project's full gate at integration boundaries. Arrange independent reviews from different AI labs according to the project's review policy, followed by the lead's assessment. |

`medium` is the default. A mode shapes the next task's scope, validation and
review plan; it never silently removes an already frozen task's Validate
commands. Required checks must actually pass. Repeat or broaden checks only
when changed code, a failure or an unresolved concern justifies it. Record
what was checked and what remains unchecked.

Modes do not alter sandbox permissions, authorization, billing, automatic
retries, worker limit handling or acceptance rules. They do not interpret
an AI's output as an instruction to change policy. Releases still need their
required quality gate and the owner's authorization.

## Choose a coordination budget

These tiers describe the usable subscription budget for this project's lead
and workers. They are owner-selected planning profiles, not particular paid
plans, prices, model quality levels, reasoning levels or measured quota.

| Tier | Native Source workers at once | Instructions for the lead |
| --- | --- | --- |
| `low` | 1 | Delegate feature implementation. Keep the lead on planning, a concise review, integration and handoffs. Do not spawn extra agents on the lead's own subscription for routine work. Prefer an eligible worker on another existing funded subscription where available. |
| `medium` | 2 | Delegate implementation and parallelize independent tasks when useful. Use at most one additional agent on the lead's subscription when its expected value and observed capacity justify it. |
| `high` | 4 | Allow more independent work in parallel. Use at most two additional agents on the lead's subscription when useful; a high tier is not permission to create busywork or run every task at maximum effort. |

`low` is the default. Native Source concurrency is enforced across foreground
and background `unio run` calls in the same workspace. A busy budget rejects a
new dispatch before a provider call; it does not queue, retry or kill existing
workers. Changing a tier does not cancel active runs. New dispatches use the
new tier and count all already occupied native slots.

Lead self-delegation and effort guidance are instructions, not a claim that
Unio controls an already running lead CLI. External agents launched directly
outside Unio are not covered by its native concurrency limit. Different
workers can share the same subscription; creating another worker does not
create more quota. Supported capacity readings and dated manual readings
remain distinct from this chosen profile. Missing capacity stays Unknown.

Start model effort at high or the supported middle, with a supported middle
for routine coordination. Escalate only for demonstrated reasoning difficulty
and reserve max for an occasional bounded problem. Keep route-specific
exceptions, including GLM 5.3 at high. Read the
[model effort guide](development/MODEL-EFFORT.md) rather than guessing model
controls. Never automatically downgrade a model, change a wrapper, purchase
credits or add a paid fallback because a tier changed.

## Commands and visibility

From a Unio project, the command surface is:

```bash
unio mode yolo
unio tier low
unio policy
unio policy --json

# Change just one setting; the other persists.
unio mode medium
unio tier high

# Show the current value without changing it.
unio mode
unio tier
```

Allowed mode values are exactly `yolo`, `medium`, `safe`; allowed tier values
are exactly `low`, `medium`, `high`. Reject extra arguments and invalid values.
Both settings are workspace-wide and persist across sessions in
`coord/work-policy.json`. A missing file means the documented defaults;
malformed, unknown-schema or unsafe policy files fail locally instead of
silently resetting settings. Setter operations validate before writing and
replace the file atomically under a shared lock.

The policy JSON has schema 1 with `mode`, `tier`, an optional update timestamp,
the effective native worker limit, lead delegation guidance and an explicit
capacity value of `unknown`; it does not manufacture subscription readings.
Human output states the active mode, tier, worker limit and lead expectations.
`unio init`, `unio status` and help expose the controls. Completion offers
valid switch values.

Fresh lead templates instruct the lead to read `unio policy` before planning
or delegation and point to the installed copy of this guide. Initialization
preserves custom MASTER.md content and adds an idempotent readable policy
reference. Repository AI onboarding and the lead routing guide link here.
Existing projects can read their policy without reinitializing workers.

Each new run snapshots its chosen policy in a local run receipt and supplies
the guidance with the task through the existing file/stdin prompt transport.
The original task remains unchanged and is still the task-hash and scope
validation authority. Wrappers that need the original task path use
`UNIO_ORIGINAL_TASKFILE`; `TASKFILE` identifies the effective worker prompt.
No long prompt is inserted into argv or environment variables. Existing
runs retain their snapshot when a setting changes.

Unio does not autonomously choose arbitrary tests or launch additional AI
reviewers from a mode switch. The lead uses the selected guidance to design
the next task, and the native runner enforces its explicit validation rules
and Source concurrency. Browser selectors and per-account scheduling can
build on the same policy later; this first implementation establishes the
core CLI, persistence, visibility and worker instructions.

## Current Unio development workflow

Owner direction on 2026-10-07 is **YOLO + low tier**, with implementation
delegated through Unio and personal lead review. Complete visible feature
batches, use focused native validation and reuse still-valid evidence. Do
not run the whole repository suite after every small source or docs change.
Run the full repository gate before publishing a release, or earlier when
actual changes or failures warrant it. Already running frozen checks keep
their original evidence; historical review and test failures remain recorded.

The [roadmap](development/ROADMAP.md) and [version plan](VERSION-PLAN.md)
describe delivery sequencing. Runtime completion is recorded in the command
implementation's changelog and tests, not inferred from this contract.
