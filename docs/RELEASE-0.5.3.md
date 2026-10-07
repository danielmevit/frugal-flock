# Unio 0.5.3 — one workspace for your AI team

This release brings the local browser workflow and configurable work policy
together. Use your existing AI subscriptions, let a lead delegate tasks,
and keep the changes, checks and review evidence in one workspace.

- **Run a task from the browser.** Save a request, inspect its scope and
  checks, approve spending, and start the configured worker once. Run
  approval and acceptance of the resulting changes remain separate steps.
- **Follow the actual work.** See short worker updates, open protected
  Source output, and browse tracked worktree files. Observation does not
  start another AI session. Quiet output is shown without inventing progress.
- **Choose your delivery pace.** `unio mode yolo`, `medium` or `safe`
  records how the lead should plan, validate and review work. The modes
  preserve the task's frozen checks and the owner's authority.
- **Protect shared subscription budgets.** `unio tier low`, `medium` or
  `high` sets native workflow capacity. Low allows one independent workflow
  per budget group, including the lead. Account mappings let aliases share
  that group; internal helpers on the same assignment share its allowance.
- **Keep decisions tied to real evidence.** Native results bind Source,
  checks and review to a revision. Failed, missing or stale evidence cannot
  establish readiness. Refreshing the browser reads state without silently
  replaying a spending action.

The browser is a local source preview, available in the release source
archive. The installer installs the command-line tool. Read
[the browser startup guide](https://github.com/danielmevit/unio/blob/v0.5.3/bridge/README.md) for the default read-only
view and the explicitly enabled draft, execution, output and files modes.
The preview uses loopback and the Python standard library.

Start with [work modes and tiers](https://github.com/danielmevit/unio/blob/v0.5.3/docs/WORK-MODES.md),
[lead routing](https://github.com/danielmevit/unio/blob/v0.5.3/docs/development/LEAD-ROUTING.md) and
[task time budgets](https://github.com/danielmevit/unio/blob/v0.5.3/docs/development/TASK-TIME-BUDGETS.md). Larger implementation
tasks can receive 90 minutes or up to two hours, with bounded checks and
early saved commits. Those allocations are distinct from subscription
cooldowns and must be set consistently across native and CLI wrappers.

Automatic recovery saves and restarting the lead after its cooldown remain
the next planned milestone, v0.5.4. Existing worker limit handling continues
to apply. See the [version plan](https://github.com/danielmevit/unio/blob/v0.5.3/docs/VERSION-PLAN.md).

The official release contains the installer, full source archive, license,
attribution notice, provenance and checksums. Publish only the exact source
that passes the required release gate; keep failed runs and their partial
work in the workspace history.
