# Lead cooldown recovery

Unio can supervise a Codex lead from outside its AI session. A confirmed
allowance limit creates a durable wait; when the allowance is available, Unio
starts a new lead with the saved goal and instructions to reconcile existing
work. Waiting makes no AI requests. Worker limits and retries are unchanged.

This is **unreleased source for v0.5.4**, with offline acceptance. It is not
in installed v0.5.3. Real subscription-limit recovery still needs a live
acceptance run; do not treat mock-clock evidence as a measured provider reset.
The first adapter requires Linux, Python 3.11+ and **Codex CLI 0.161.0**.
Other CLI versions and AI labs need separately verified adapters.

## Enable it for a goal

Use an owner terminal after the existing Codex lead exits. Unio refuses to
start another lead alongside a detected existing Codex session. Low-tier
account rules still include the registered lead reservation.

From the enclosing project directory containing `coord/`, `wt/` and `repo/`:

```bash
unio lead codex
unio resume
unio lead-cooldown start --model 'gpt-6.1-sol' --effort high \
  --sandbox workspace-write --cd "$PWD" --goal-file "$PWD/coord/lead-goal.md"
unio lead-cooldown status --json
```

Write the goal file first, using only the intended work and its existing
authority. It must be a regular project file, no symlinks, at most 64KiB.
The model must be available on your existing subscription; Unio does not
select a fallback. The goal is frozen at enablement. Keep coordination work
within the selected working directory when using `workspace-write`.

The model, effort, sandbox, working directory, CLI binary, relevant environment
and supported configuration layers are frozen. Changes halt with
`launch_changed`. The first adapter supports the default first-party ChatGPT
route on individual plans. API keys, custom endpoints/providers, default
profiles, managed configuration and managed plans refuse. Unio never changes
authentication, buys credits, uses reset credits or enables a paid fallback.
Existing account billing settings remain outside Unio's control.

## Controls

```bash
unio lead-cooldown status
unio lead-cooldown pause
unio lead-cooldown resume
unio lead-cooldown stop
unio lead-cooldown complete
```

Pause prevents another launch; resume keeps a pending reset time and restarts
an absent supervisor. Stop and complete are terminal for that goal. Start a
new enablement explicitly to change the goal. These controls let a running
lead finish; they do not abruptly kill it. `unio stop` blocks new probes and
launches while the saved clock continues. `unio resume` clears that global
marker; it does not clear a lead-specific pause or terminal decision.

A successful normal turn ends with `turn_ended`; another turn needs explicit
resume unless the lead already marked the goal complete. Ordinary crashes,
authentication/network errors, unknown process exits and unavailable quota
metadata halt for inspection. Resume after a halt authorizes one new lead
launch, preserving the original frozen goal and controls.

## How waiting works

The lead runs through `codex exec --json`. Its output alone cannot establish
quota. A separate bounded `codex app-server` metadata probe reads the current
ChatGPT account and allowance, without starting a thread or model request.
Every launch requires current `ordinaryUsageAllowed: true`. Null or missing
permission stays unavailable; low percentages never establish recovery.

- A confirmed five-hour window without a useful reset waits **18,060 seconds**.
- A usable actual reset waits until that reset plus one minute. A minimum
  five-minute spacing prevents a near/stale reset from causing a launch loop.
- A longer exhausted window keeps its own reset. An unknown longer reset
  stays visibly unresolved and polls metadata no more often than hourly.
- Repeated limits create fresh waits. Seven consecutive limit observations
  halt with `limit_loop` and require inspection before explicit resume.

Waits use wall time, checked locally at least every five seconds. After sleep
or supervisor restart, Unio reconciles saved ownership before launching. A
supervisor crash with a live lead becomes `orphan_wait`; an unknowable exit
remains Unknown. It never fabricates a completed result or retries a worker.
OS login/startup integration is outside this first implementation.

## State and handoffs

Private state, the frozen goal and bounded attempt records live under
`coord/lead-cooldown/`. Atomic writes and kernel locks protect one supervisor
and one managed lead per project. A lead receives no lock/control descriptors.
Each attempt retains its real exit, summarized exec events and capped stderr.
Original worker receipts and saving claims remain unchanged.

The new lead reads the current coordination log, continuation prompt, worker
processes, branches, native receipts and saved work before delegating. Completed
or uncertain jobs cannot be silently redispatched. Restart grants no new
spending, worker retry, review, merge or release authority.

Malformed state refuses locally. `status --json` reports `corrupt`. After
inspection, `unio lead-cooldown stop --force-corrupt` preserves the original
state under a distinct filename and records stopped; inspect any old lead
process separately. Never delete evidence to make a restart appear clean.

These are trusted-host controls, not an OS security boundary: another process
running as the same user can edit state or launch an unmanaged CLI. Detection
is conservative and may also refuse while Codex is active on another project.
The metadata protocol is experimental; changed/unsupported evidence halts.

See the [implementation contract](development/LEAD-COOLDOWN-CONTRACT.md),
[work saving](WORK-SAVING.md) and [work modes](WORK-MODES.md).
