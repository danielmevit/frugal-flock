# Standalone browser launcher

Frozen 2026-10-09 for `BROWSER-LAUNCHER-1`, the first everyday-launch slice.
This is separate development after the published v0.5.4 recovery release.
No later version is assigned or published by this contract.

`unio browser` starts the existing local dashboard using packaged files,
without a source checkout or a manually assembled Python command. Infer the
enclosing workspace from its repo, worker or subdirectory, or accept an
explicit `--project` from outside. Print the selected project, CLI version,
engine and configuration plus the actual loopback URL.

The invoked CLI's resolved executable is fixed for observation and execution;
the installed launcher does not expose `--engine`. Resolve its configuration
before the observer changes directories. Keep the source server's explicit
engine option for developers. Use one shared server parser/validation path;
packaging does not relax grants or duplicate execution policy.

Default launch is read-only, makes no model calls, writes no project state
and never changes STOP or lead/account policy. Browser opening is opt-in.
Preserve all existing explicit draft/execution/output/files flags and required
startup inputs. Existing loopback, Host, Origin and token checks remain.
No UI redesign, cache optimization, background service or automatic startup.

The standalone installer carries exactly the canonical thirteen browser
modules/assets. A deterministic embed tool and full-gate parity check prevent
source/install drift. No download or extra dependency; Python 3.9+ is required
to launch. Check generated destination types before replacement; refuse
symlinked directories/files and hardlinked payload files. Preserve owner
configuration, bench state, playbooks and unrelated files on reinstall.

Verify installed standalone bytes, actual loopback HTTP/assets/activity,
inferred/explicit project paths containing spaces, explicit manual drafts,
fixed engine/config despite a PATH decoy, startup refusal and preservation.
Reuse existing server checks, personal review and focused native validation
under YOLO. Keep the published recovery tag/assets/evidence unchanged. The
release boundary is now complete; development integration uses the bounded
`BROWSER-LAUNCHER-2` correction and fresh focused checks.

## Managed background dashboard (`DASHBOARD-STARTUP-OPUS-1`)

`unio browser` stays a foreground command with every explicit grant unchanged.
`unio dashboard [ensure|status|stop] [--project PATH] [--open-browser] [--json]`
adds one detached, local, read-only dashboard per project:

```bash
unio dashboard ensure --open-browser   # default action: start or reuse, print the link
unio dashboard status                  # report only; never starts anything
unio dashboard stop                    # end only this project's managed dashboard
```

Ensure starts the packaged read-only server on an unused loopback port chosen
by the operating system, or reuses the same project's healthy managed server,
and prints the actual `http://127.0.0.1:PORT` link. Repeated or concurrent
calls share one server and one link. `--open-browser` asks the desktop to open
only a newly started dashboard; failure still prints the link and keeps the
server. It runs until `dashboard stop`, independent of STOP, usage limits and
the lead session; stop never touches workers. Exit codes: 0 running, started,
reused or stopped (stop with nothing recorded is also 0); 3 not running for
status; 2 invalid usage; 1 refused, unsafe or failed.

Implementation: standalone `tools/runtime/dashboard.py`, installed as
`CONF_DIR/lib/dashboard.py` by deterministic `tools/embed-dashboard.py` and run
with isolated Python imports. The canonical thirteen-file browser payload is
unchanged. The fixed invoked engine, configuration and physical project path
are passed explicitly; there is no shell evaluation, PATH engine lookup or
provider inference. Ensure makes no model call and never changes STOP, lead,
bench, policy, grant, draft, output, authentication or cooldown state.

State lives in `coord/dashboard/` (mode 0700): a strict JSON record of at most
4 KiB, a flock lock and the latest startup output. Every access is relative to
directories opened without following links; symlinks, hardlinks and
non-regular files are refused, and writes are atomic. The record holds the
boot id, the process start time and a random per-launch nonce. That nonce is
handed to the server through an internal environment entry, which the server
removes before any observation child starts. Its read-only `/api/dashboard`
then returns only schema, managed flag, read-only mode, version, project hash
and nonce: no tokens, paths, configuration or raw errors. Foreground and
granted launches have no such metadata and answer 404, so they are never
adopted. Host and Origin checks are unchanged.

Reuse requires the same boot, process start time and nonce in the process's
initial environment, plus matching health metadata. Stop pins the process with
a pidfd, confirms that identity and signals only through the pidfd; a gone or
reused PID is reported stale and never signalled, and no pattern-based process
search exists. Missing, stale, failed, unsafe, corrupt or uncertain state is
reported as such; ensure refuses unsafe or uncertain state instead of starting
a duplicate. The whole command is bounded at 30 seconds (a new launch has 20).
A failed launch kills only its own unreaped child and its new process group,
records the failure and keeps the startup output. The detached server writes to
that private file, never the caller's pipes, so captured calls return promptly.
Linux `/proc` and pidfd support are required.

Checks: `tests/unio-dashboard.py` drives an isolated installed CLI over real
HTTP (start, reuse, concurrent ensure, status without launch, stop and restart,
paths with spaces, stale and reused PIDs, foreign and foreground servers,
corrupt and unsafe state, readiness failure) with zero provider marker calls.
