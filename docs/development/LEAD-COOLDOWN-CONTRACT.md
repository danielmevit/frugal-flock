# Lead cooldown supervisor contract

**Specification only.** No supervisor, command, adapter or release exists yet.
Runtime implementation, offline acceptance and one live restart are pending.
This freezes the first slice of the [cooldown milestone](LEAD-COOLDOWN-RESTART.md),
which stays the plan of record. It builds on
[work saving](WORK-SAVING-CONTRACT.md) and the [work modes](../WORK-MODES.md).

The supervisor is one Python standard-library helper embedded in the standalone
installer, like the save helper. No service, package, daemon manager, UI or
OS startup integration. Linux with `/proc` only; other platforms refuse `start`.

## Adapter evidence (Codex CLI 0.161.0, recorded 2026-10-08)

Local, no model call: `codex --version` printed `codex-cli 0.161.0`; binary is the
standalone `0.161.0-x86_64-unknown-linux-musl` release. `codex exec --help` and
`codex app-server --help` were read. `codex app-server generate-json-schema
--out` (stable surface, no `--experimental`) produced the v2 bundle; SHA256
prefixes: `GetAccountRateLimitsResponse.json` cb9655e68130,
`ErrorNotification.json` eb702b074f6f, `ClientRequest.json` 1535135c00a6.

Official pages read (the developers.openai.com paths redirect to learn.chatgpt.com):

- https://learn.chatgpt.com/docs/non-interactive-mode — `codex exec --json` emits
  JSONL `thread.started`, `turn.started`, `turn.completed`, `turn.failed`,
  `item.*` and `error`. No classified error code or reset field is documented.
- https://learn.chatgpt.com/docs/app-server — turn failures carry
  `codexErrorInfo` (including `UsageLimitExceeded`); `account/rateLimits/read`
  returns windows with `usedPercent`, `windowDurationMins`, `resetsAt` (Unix
  seconds) and `rateLimitReachedType`. The page calls app-server experimental.
- https://learn.chatgpt.com/docs/developer-commands — `codex exec` Stable,
  `codex app-server` Experimental.
- https://learn.chatgpt.com/docs/config-file/config-reference —
  `model_reasoning_effort`, `approval_policy` (`never` for non-interactive).
- https://learn.chatgpt.com/docs/pricing — five-hour windows apply to Plus and
  Business; "Pro plans currently have no five-hour limit"; weekly limits may
  apply; after a limit, users may buy credits or use an API key.

Generated schema facts: `GetAccountRateLimitsResponse` has `ordinaryUsageAllowed`
(null = unavailable; "clients must not infer recovery from percentages or reset
times"), `rateLimits` and `rateLimitsByLimitId`. Params include
`supportsLunaReserve` ("automatic Luna Reserve fallback") and
`excludeResetCreditDetails`. `account/rateLimitResetCredit/consume`,
`account/login/*`, `account/logout` and `account/sendAddCreditsNudgeEmail` mutate.

**Chosen adapter `codex-exec-0.161.0`.** The lead runs under stable
`codex exec --json`. Its stream is only a *trigger*. Quota is confirmed solely by
one short no-model probe of `codex app-server` over stdio, after the lead is
reaped and before each launch. Running the lead itself under app-server would
make the supervisor answer approval requests, a larger privileged surface.
The probe is the only structured quota source; it is experimental, so a protocol
or version change disables classification (refusal or halt), never a guess.

Unverified live behavior: what 0.161.0 `exec --json` prints on a real limit;
whether `ordinaryUsageAllowed`/`rateLimitReachedType` are populated for the
owner's plan; whether `rateLimits/read` refreshes OAuth tokens. The first live
restart records these. Until then a limit without probe evidence halts.

## Commands

| Command | Effect |
| --- | --- |
| `unio lead-cooldown start --model M --effort E --sandbox S --cd DIR --goal-file F` | Owner enables; freeze launch; spawn supervisor |
| `unio lead-cooldown status [--json]` | Read-only state, reason, wake time and evidence age |
| `unio lead-cooldown pause` | Persist paused; no launch or probe until resume |
| `unio lead-cooldown resume` | Clear pause or halt; respawn supervisor if absent; never shortens a wait |
| `unio lead-cooldown stop [--force-corrupt]` | Persist stopped; drop wait; terminal for this enablement |
| `unio lead-cooldown complete` | Persist completed goal; terminal for this enablement |

Exits: 0 success; 1 refusal (wrong mode, STOP, unsupported adapter); 2 bad
arguments, busy lock or unknown partial mutation. JSON is one bounded object.
`start`/`resume` refuse when `UNIO_LEAD_SUPERVISED` is set (a supervised lead
cannot re-enable itself); `pause`/`stop`/`complete` only reduce calls and are
accepted from anyone. That variable is a guard, not a security boundary.

`start` validation: model matches `[A-Za-z0-9._-]{1,64}`; effort is exactly one
of low, medium, high, xhigh, max; sandbox exactly `read-only` or
`workspace-write`. No full access, bypass, `--add-dir`, profile, `--oss` or
extra `-c`. DIR resolves without symlink escape to an existing directory inside
the project. F is a regular, no-follow, project file of at most 64KiB. Refuse if
`unio lead` is not `codex`, a non-terminal enablement exists, or
`CODEX_API_KEY`/`OPENAI_API_KEY` is set. Refuse if `codex` is not exactly
0.161.0, or the start probe shows a non-`chatgpt` account. Only type and plan
are stored, never email.

Frozen argv, built once and stored verbatim; prompt arrives on stdin:
`CODEX exec --json --strict-config -m M -c model_reasoning_effort="E"
-c approval_policy="never" -s S -C DIR -` (CODEX is the absolute resolved
path). User config is loaded, so its route applies: the SHA256 of
`$CODEX_HOME/config.toml` (default `~/.codex`) is frozen. A changed binary path,
version or config hash halts with `launch_changed`; Unio never edits Codex config,
auth, credits or sandbox. Changing `unio lead` while the enablement is active
or paused refuses (small hook in the policy setter).

## Durable state

`coord/lead-cooldown/` is 0700; files 0600, owner-only, no symlinks. Files:
`state.json`, `supervisor.lock`, `goal.md` (frozen copy), `attempts/ID/` with
`prompt.md`, capped `stderr.log` and `exec-events.json`. Writes go to a temp
file in the same directory, then fsync, `os.replace` and parent fsync. Readers
reject duplicate/unknown keys, wrong types and unknown schema versions. A
corrupt or unreadable state refuses every command except `status`, which
reports `corrupt`; never reset silently. Only `stop --force-corrupt` may move
it aside to `state.corrupt-TIMESTAMP` and write `stopped`.

`state.json` schema 1, all keys required:

| Key | Meaning |
| --- | --- |
| `schema_version`, `revision` | 1; integer incremented per write |
| `enablement_id` | 32 lowercase hex, new per `start` |
| `mode` | `active`, `paused`, `stopped`, `completed` |
| `phase` | `idle`, `launching`, `running`, `orphan_wait`, `cooldown`, `unresolved`, `halted` |
| `halt_reason` | null or a fixed code below |
| `frozen` | adapter, codex path/version, model, effort, sandbox, cwd, config and goal SHA256, argv |
| `lead` | null or attempt ID, pid, start ticks, session ID, boot ID, launch time |
| `cooldown` | null or the wait object below |
| `consecutive_limits`, `attempts_total` | Integers |
| `attempts` | Last 32 attempt records; older ones append to capped `archive.jsonl` |
| `created_at`, `updated_at` | Integer Unix seconds UTC |

Attempt record: `attempt_id`, `seq`, `launched_at`, `ended_at`, `exit_code`,
`signal`, `saw_turn_failed`, `saw_turn_completed`, `probe` (`limit`, `no_limit`,
`unavailable`, `not_run`) and `outcome` (`turn_completed`, `limit`, `failed`,
`interrupted`, `unknown`). Wait object: `kind` (`five_hour`,
`weekly_or_longer`, `unknown_longer`), `detected_at`, `wake_at` (null only when
unresolved), `source` (`reset`, `fallback_18060`, `unresolved`), `reset_at`,
`limit_id`, `window_mins`, `probe_at`, `evidence_sha256`. Halt codes:
`turn_ended`, `failed`, `interrupted`, `outcome_unknown`, `probe_unavailable`,
`limit_loop`, `launch_changed`, `stray_processes`, `history_full`.
The archive cap is 8MiB; reaching it halts with `history_full`. Nothing is evicted.

## Ownership, processes and signals

One supervisor per project: `fcntl.flock(LOCK_EX|LOCK_NB)` on
`supervisor.lock` (no-follow, regular, owned), held for its whole life. The
kernel releases it on crash. A second launcher exits 2. The supervisor runs
detached (`start_new_session`), stdio to `/dev/null` plus its own capped log.

One live lead: spawned with `start_new_session=True`, `close_fds=True`, no
`pass_fds`, so it inherits neither lock nor control descriptors. Its env is the
supervisor's, plus `UNIO_LEAD_SUPERVISED=1` and `UNIO_LEAD_ATTEMPT=ID`.
Identity is pid, `/proc/PID/stat` start ticks, session ID and `/proc` boot ID;
a different boot ID means it is gone. Live-lead discovery scans own-UID `/proc`
entries whose session equals the recorded lead session (or, while `launching`,
which are session leaders) and whose bounded 64KiB environ holds the exact
token. Background `unio run` uses `setsid`, so its workers are in other sessions
and are never counted or signalled.

Launch order: confirm the active mode, absent STOP, unchanged frozen launch and
a passing pre-launch probe. Durably write `launching` with a new attempt ID and
null pid, then spawn. Write the prompt, close stdin and durably record
`running` with identity. On restart, `launching`/`running` never launch.
Discovery finds the lead (`orphan_wait`, poll 5s) or finds nothing. Since the
exit code of a non-child is unknowable, the outcome is `unknown`; a probe then
decides cooldown or `halted:outcome_unknown`. No duplicate launch is possible
from either window.

The supervisor reads stdout as bounded JSONL: lines over 1MiB are dropped and
counted. It records only event types and the presence of `turn.failed`/
`turn.completed`, never agent text. After `waitpid`, it sends SIGTERM to the
remaining lead process group, waits 10s, then SIGKILL. Remaining
token-and-session matches give `halted:stray_processes`. SIGTERM, SIGINT or
SIGHUP to the supervisor forwards SIGTERM to the lead group, waits 30s, then
SIGKILL. It reaps, records `interrupted`, halts with mode unchanged, and exits.
Losing the supervisor also closes the lead's stdout pipe; that lead
then likely exits and is reconciled as `unknown`.

STOP coexists unchanged: it blocks launches and probes; waits keep counting.
At wake with STOP present, the phase stays put until STOP is cleared. STOP never
kills a running lead. `pause`/`stop`/`complete` likewise never signal a live
lead: they prevent the next launch, record the reaped exit, then the supervisor
exits. The registered lead reservation is the lead's only slot in the codex
group. The supervisor never runs a worker, so no second Codex workflow starts.

## Probe and wait rules

Probe argv: `CODEX app-server --strict-config --listen stdio://`, same env,
30s deadline, 1MiB read cap. It sends exactly `initialize` (`clientInfo`
only, no capabilities), `initialized`, `account/read {refreshToken:false}`
and `account/rateLimits/read {excludeResetCreditDetails:true}`. It never sends
`supportsLunaReserve`, consume, login, logout, nudge, `thread/*` or `turn/*`.
Bucket: `rateLimitsByLimitId.codex`, else `rateLimits`. Store its canonical
JSON SHA256, never the email. Missing or invalid responses mean `unavailable`.

Confirmed limit: `ordinaryUsageAllowed` is false, or the bucket's
`rateLimitReachedType` is non-null. Exec text, worker/repository/tool output,
lead messages or any agent-written file never classify quota. The probe runs
after any lead exit except `turn_completed` with exit 0, and before every
launch. Exhausted windows are those with `usedPercent` of 100 or more; the
longest `windowDurationMins` names the kind. 300 is `five_hour`, at least 10080
is `weekly_or_longer`, and other or null values are `unknown_longer`. With
`D` = detection time and `R` = the latest `resetsAt` among exhausted windows:

1. No exhausted window: `unknown_longer`, handled as rule 4.
2. `R` known and within (D+60, D+691200]: wake at R+60 (`reset`).
3. Else `five_hour`: wake at D+18060 (`fallback_18060`).
4. Else `unresolved`: no `wake_at`. Probe at most hourly; leave when
   `ordinaryUsageAllowed` is true. Never use the five-hour fallback.

Every wake, including a stale or repeated reset, is a fresh wait from new
evidence and at least D+300. A confirmed pre-launch limit also starts a new
wait. Each limit increments `consecutive_limits`; a `turn.completed` resets it.
The seventh consecutive limit halts with `limit_loop`. The supervisor sleeps in
wall-clock steps of at most 300s. Each step re-reads state, STOP, mode and
`time.time()`, so suspend and clock jumps are reconciled, not counted.

Non-limit outcomes never enter cooldown or relaunch: a crash, nonzero exit,
auth or network error, or timeout halts `failed`. An unavailable probe halts
`probe_unavailable`. A normal turn end halts `turn_ended`. `resume` permits
exactly one new launch after a halt. `start` probes first; a confirmed limit
begins a cooldown without launching. A paused wait keeps its absolute wake time.
The supervisor exits when it owns no live lead and the mode is not active or
the phase is `halted`; `resume` respawns it to continue the persisted state.

## Handoff and authority

Each launch writes `attempts/ID/prompt.md`: fixed template, the frozen goal,
and the project root, worker cwd, enablement, attempt and limit history. It tells
the lead to read `coord/AGENT-LOG.md`, `unio policy`, `unio status`, native
receipts and `unio save inspect --worker` evidence before delegating. Unresolved
tasks and no-replay claims stay pending. Completed or unknown jobs are never
redispatched; unknown needs reconciliation. The lead must not use `unio save
continue` without a separate, explicitly authorized task. It runs
`unio lead-cooldown complete` only when the frozen goal is met.

A lead restart is a new lead session, not `exec resume` or worker continuation.
It grants no worker retry, review, merge, release or spending authority. Owner
enablement authorizes only bounded launches of the frozen argv.
Trusted-host limits: same-user processes can edit state, kill the supervisor,
clear env or launch an unmanaged Codex outside Unio. The supervisor detects only
its own sessions. Codex may draw purchased credits under the owner's
existing account settings; Unio never buys, consumes reset credits or opts in.

## Mock-clock acceptance matrix

Inject `now()`, `sleep()`, spawn, probe and `/proc` readers. Mock CLIs are
short scripts and no real AI or network is used. Each row asserts launches and
probes made, final state and file modes.

| # | Plan category / scenario | Expected |
| --- | --- | --- |
| 1 | Five-hour confirmed, `resetsAt` null | Wake D+18060; 0 launches before; 1 after |
| 2a | Reset D+7200 | Wake D+7260 |
| 2b | Weekly exhausted, reset null | `unresolved`; no 18060 wake; launch only after allowed=true |
| 3a | Stale reset D-10, five-hour | Fresh D+18060; no rapid relaunch |
| 3b | Seven consecutive limits | `halted:limit_loop` at the seventh; no further probe or launch |
| 4a | Stop, pause, complete, then restart supervisor | Persist; 0 launches |
| 4b | Second `start` or `resume` with live lock | Exit 2; 1 supervisor |
| 4c | Crash in `launching`, token lead alive | `orphan_wait`; 0 new launches until gone |
| 4d | Crash in `running`, lead gone, no probe limit | `halted:outcome_unknown` |
| 4e | Clock jumps 6h (sleep) and STOP at wake | No launch until STOP cleared |
| 5 | Prompt contents | Goal, log/receipt/save rules, no-redispatch text |
| 6a | Limit phrase in repo, exec text or sidecar; probe `no_limit` | `halted:failed` |
| 6b | Auth, network, timeout or crash exit | Halt, no cooldown; worker limits untouched |
| 7 | Argv, config hash, version, API-key env, probe messages | Exact argv; change halts; key refuses start; exactly four probe messages, no fallback/consume |
| 8 | Corrupt, unknown-key or symlinked state | Refuse; `status` reports corrupt |
| 9 | Probe timeout, bad JSON or oversized output | `probe_unavailable`; never cooldown |

Then one owner-enabled live restart records the real limit stream, probe
evidence and timing. Run focused checks per slice and the full gate at release.
