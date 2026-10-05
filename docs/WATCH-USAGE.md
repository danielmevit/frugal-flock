# Read-only activity monitor (unreleased source)

`unio watch` prints local activity when it changes, polling once
per second. Press Ctrl-C to exit. It runs no agent commands, reads no
raw logs or credentials, and changes no project coordination files.
The installed v0.4.0 stays unchanged until a deliberate release/install.

```bash
unio watch
unio watch --once
unio watch --once --json
unio watch --json --interval 0.5
```

JSON mode emits one complete JSON object per line, initially and whenever
the observed state changes. `--once` prints one snapshot and exits.
Intervals must be between 0.1 and 60 seconds. Both compatibility aliases
(`unio`, `unio`) support the same command.

Each snapshot includes STOP, local agent diagnostics and operator retry
times, recorded process/validation/reviewer states, task retry-brake state,
and up to 20 recent ledger events from the last 1 MiB. Start events and
review decisions are recorded by this source version; older history may
lack those fields. Partial final ledger lines wait for the next poll;
malformed lines/results produce warnings instead of invented verdicts.
Ledger replacement/truncation is followed on the next poll.

These are recorded decisions, not fresh revision checks or human approval.
Run `unio result WORKER TASK` to check current readiness. A recorded
running result with a free worker lock shows `completion_unknown`, retaining
the native running state and null exit. Interruption is possible; the free
lock does not establish that no detached process exists. A held lock is
an observation of worker activity, not proof of a particular live provider.
The observer never rewrites process evidence to guess an exit or failure.

Authentication and provider capacity stay unknown. A run's `wall: 1`
becomes `limit_signal: runner_log_pattern`: the runner matched a log pattern,
not a confirmed remaining quota or reset time. An operator's retry reminder
is displayed as such. Symlink or unsupported ledger/lock paths are refused;
unreadable result/retry data are warned about without following symlinks.
Each file is observed independently, not as an atomic project transaction.

Snapshot schema 1: `observed_at`, `stopped`, `agents`, `results`, `retries`,
`recent_events`, `warnings`, and the `evidence` explanation. Result rows
contain worker/task, recorded time, activity, observed worker lock, process
state/exit, validation state/check counts and review state/reviewer. They do
not contain task contents, command strings, raw logs, revision digests, or
`ready_for_human_review`. Treat task/worker IDs as text when rendering them.
