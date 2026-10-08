# Restart the lead CLI after its cooldown

Owner requested on 2026-10-07. Planned as a bounded continuation slice after
automatic work saving in v0.5.4. The first supported Codex supervisor is now
implemented in source; see the [usage guide](../LEAD-COOLDOWN.md) and
[frozen contract](LEAD-COOLDOWN-CONTRACT.md). Offline acceptance and an actual
read-only allowance probe passed. A real subscription-limit restart and combined
release checks remain pending; published/installed v0.5.3 is unchanged.
The original milestone and acceptance goals below remain the delivery reference.


Validation update, 2026-10-08: see [completed checks, preserved failures and
remaining release work](RECOVERY-ACCEPTANCE-2026-10-08.md). Component coverage does
not replace the final versioned release gate.

## Intended behavior

Unio keeps a small supervisor running outside the lead AI's CLI process.
When the lead stops because its subscription allowance is exhausted, the
supervisor records the cooldown and waits without making AI requests.
Afterward it starts the configured lead CLI with the saved project handoff.
If the new session reaches a limit again, it records another cooldown and
repeats until the work finishes or the owner pauses or stops it.

Existing worker limit handling stays as it is. This feature restarts the
lead session; it does not change worker benching, routing, task retry counts
or the authority to start, review, merge and publish work.

## Waiting and restart rules

- Use a supported, current reset timestamp for the allowance that actually
  blocked the lead, then add a one-minute margin.
- For a known five-hour limit without a usable reset timestamp, wait **five
  hours and one minute from detection**. This is the default fallback, not
  a claim that every provider's window starts when Unio notices the limit.
- A weekly or longer limit uses its own supported reset time. Missing
  information remains visible; do not label a weekly limit as five hours.
- A repeated limit creates another persisted wait. An expired reset time
  must not cause a rapid restart loop; use fresh reset information or the
  configured fallback for the known limit type.
- Authentication failures, crashes, timeouts and network errors are distinct
  from exhausted allowance and must not silently enter the cooldown loop.
- Preserve the configured CLI, model, effort and subscription route. Do not
  install tools, change authentication, enable paid token usage or add
  execution privileges as part of restarting.

Automatic restart is an explicit owner-enabled mode. Show its state, reason,
next wake time and the age/source of that time. Provide pause, resume and stop.
An explicit stop or completed goal cancels the pending restart; a supervisor
restart must preserve that decision.

## Continue without duplicating work

Use [automatic work saving](../WORK-SAVING.md) to preserve recoverable files,
commits, decisions, checks and a continuation prompt before the lead runs out
of allowance. If it exits before writing a final handoff, retain the latest
existing checkpoint and its actual limitations.

The new lead reads the handoff and current coordination log, then checks
existing worker processes, branches and native receipts before delegating.
It must not redispatch completed tasks. Unknown outcomes require reconciliation,
not a new attempt. Restarting the lead grants no worker retry and invents no
successful result.

Keep wait state, launch receipts and wake times durable. Allow one supervisor
and one live lead CLI per project, including after competing launchers or a
supervisor restart. Record actual exits and restarts; retain earlier failures.

The supervisor must remain alive while the lead CLI is stopped. A sleeping
machine cannot run the lead; after waking, reconcile saved waits and process
ownership before launching. Operating-system startup integration is a separate
setup choice, not an assumed property of this milestone.

## Delivery and acceptance

Freeze an implementation contract before dispatch. Start with one supported
lead CLI and document its limit/reset evidence, then add adapters only when
verified. Connect to [allowance monitoring](../PROVIDER-QUOTA-MONITORING.md)
where supported; waiting must not depend on a live AI session.

Use a controllable clock and short mock CLI processes to verify:

1. A confirmed five-hour limit with unknown reset time waits exactly 18,060
   seconds before one new session; no AI request occurs while waiting.
2. A supported reset time uses that time plus 60 seconds; a longer allowance
   window does not use the five-hour fallback.
3. Repeated genuine limits create new cooldowns instead of immediate retries,
   including when a reported reset timestamp is stale.
4. Stop, pause, completion, supervisor restart, machine sleep and competing
   launchers preserve ownership and prevent duplicate lead sessions.
5. The lead receives its saved project/handoff and reconciles worker results
   without redispatching completed or uncertain tasks.
6. Ordinary errors and limit phrases in task/repository content do not alter
   cooldown policy, and worker limit handling remains unchanged.
7. Existing CLI arguments, subscription routing and controls are preserved;
   no paid fallback or stronger execution mode is introduced.

Follow with one bounded live restart when allowance and owner-enabled
configuration permit. Keep actual receipts and full quality checks. Browser
v0.5.3 continues first; this plan does not claim lead restart already exists.
