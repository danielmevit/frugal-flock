# Manual capacity readings

`bridge/capacity.py` and `tools/capacity-readings.py` store and show
capacity readings that a person entered by hand. Unio 0.5.6
installs them as `unio capacity`. This is not an automatic provider meter,
and it is not routed or shown in the browser yet. See
[provider quota monitoring](../PROVIDER-QUOTA-MONITORING.md) for the wider
plan.

The component uses only the Python standard library. `record` and `show`
never make a provider, model, network or authentication request. The one
exception is the separate, explicit `refresh codex` command described in
[cached Codex readings](#cached-codex-readings-optional), which is in
source and not yet released. Nothing here benches or enables agents,
dispatches work, changes tier or mode, or retries anything.

## Usage

The installed command takes the same arguments as the source script:

```bash
unio capacity --project PATH record --group codex --window five-hour \
    --window-minutes 300 --remaining-percent 42 \
    --observed-at 2026-10-09T14:00:00+02:00
unio capacity show --group codex --json   # inside an initialized workspace
unio capacity --help                      # works anywhere
```

Inside an initialized workspace (a directory with `coord/` and `wt/`), an
omitted `--project` selects that workspace root, resolved without symlinks,
just as the other native commands find it. Outside one, `--project` is
required and its absence is refused before anything is written. Arguments
are passed to Python as data and never evaluated by a shell. Abbreviated
options are refused. The installer writes the store and CLI byte for byte
under `~/.config/unio/lib/capacity/` and runs them in isolated Python
(`-I -S`), so neither `PYTHONPATH`, site packages nor the source tree is
used. Installation never writes or changes readings.

From the source tree, run the script directly. It finds its own repository,
so it needs no `PYTHONPATH` and works from any directory.

```bash
python3 tools/capacity-readings.py --project PATH record \
    --group codex --window five-hour --window-minutes 300 \
    --remaining-percent 42 --observed-at 2026-10-09T14:00:00+02:00 \
    --reset-at 2026-10-09T17:30:00+02:00

python3 tools/capacity-readings.py --project PATH show
python3 tools/capacity-readings.py --project PATH show --group codex --json --max-age-seconds 900
```

`record` options:

| Option | Meaning |
| --- | --- |
| `--group` | Opaque shared-budget label, required. |
| `--window` | Opaque window label, required, for example `five-hour` or `weekly`. |
| `--window-minutes` | Window length, an integer from 1 through 527040. |
| `--remaining-percent` | Remaining allowance seen, a finite number from 0 through 100. |
| `--observed-at` | When it was seen, ISO 8601 with a timezone offset. |
| `--reset-at` | Optional reset time, ISO 8601 with a timezone offset. |

`show` options:

| Option | Meaning |
| --- | --- |
| `--group` | Show only this group. A group with no reading shows as Unknown. |
| `--json` | Print the normalized view as JSON. |
| `--max-age-seconds` | Fresh/stale boundary, 1 through 31622400 seconds, default 900. |

A group label stands for one shared budget. Every worker that draws on the
same account uses the same label. Workers do not get separate copies.

Labels are 1 to 64 ASCII letters, digits, `.`, `_` or `-`, and must start
with a letter or digit. Do not put credentials, account names, e-mail
addresses or other account identifiers in labels.

Exit codes: 0 on success. 1 when a reading or path is refused, or when
`show` finds invalid state. 2 when the arguments are malformed.

## Input rules

`record` refuses the reading, and leaves existing state unchanged, when:

- a label is invalid;
- a number is a boolean, NaN, infinite or out of range, or the window
  length is not a whole number;
- a time has no timezone offset, is longer than 64 characters, or is not
  valid ISO 8601;
- the observed time is more than 300 seconds in the future;
- the reset time is before the observed time, or more than one window
  length (plus 300 seconds) after it;
- the window already has a reading with the same or a later observed time,
  which covers duplicates and out-of-order readings;
- the reading would add a 33rd group or a 9th window to a group, or make
  the file larger than 65536 bytes.

The source is always `manual`. No option or function argument can label a
reading as provider data.

## Status and usable allowance

Each window in `show` has these fields: `source`, `window_minutes`,
`observed_at`, `age_seconds`, `reset_at` (or null), `status`,
`last_reading_remaining_percent` and `usable_remaining_percent`. Statuses
are checked in this order:

| Status | When |
| --- | --- |
| `unknown` | The observed time is more than 300 seconds ahead of the current clock. |
| `expired` | The reset time has passed, or a whole window length has passed since the reading. |
| `stale` | The reading is older than `--max-age-seconds`. |
| `fresh` | None of the above. |

`last_reading_remaining_percent` is always the value that was recorded.
`usable_remaining_percent` equals that value only when the status is
`fresh`. In every other case it is null. Missing, invalid, stale and
expired readings never become usable allowance or 100 percent.

A reset time that has passed does not prove the allowance was refilled.
Record a new reading first. Use in other clients can spend the same budget,
so even a fresh reading is only what was seen at that time.

The top level of the view also has `checked_at`, `max_age_seconds`,
`groups` and `state`. `state` is `ok`, `missing` (no state file yet) or
`invalid`. When the state is invalid, `error` gives the reason and every
requested group is Unknown.

## Stored schema

State lives only at `PROJECT/coord/capacity/readings.json`. `record`
creates `coord` and `coord/capacity` with mode 0700 when they are absent.
`show` creates nothing.

```json
{
  "groups": {
    "codex": {
      "five-hour": {
        "observed_at": "2026-10-09T12:00:00+00:00",
        "remaining_percent": 42.0,
        "reset_at": "2026-10-09T15:30:00+00:00",
        "source": "manual",
        "window_minutes": 300
      }
    }
  },
  "schema_version": 1
}
```

Times are stored in UTC. A loaded file is used only when the whole file is
valid:

- it must be strict UTF-8 JSON of at most 65536 bytes;
- it must have no duplicate keys and no NaN or Infinity;
- it must contain exactly `schema_version` (the integer 1) and `groups`;
- it may hold at most 32 groups, and each group 1 to 8 windows;
- each reading must have exactly the fields above (`reset_at` is optional)
  and pass the same checks as new input.

If any part is wrong, `show` reports `invalid` and Unknown, and `record`
refuses without changing the file's bytes. Fix or move the file by hand.

## Storage safety

- The project path must be an existing directory with no symlink in it.
- `coord`, `capacity`, the state file and the lock file are opened
  relative to directory descriptors with `O_NOFOLLOW`, so a symlink at any
  of those steps is refused rather than followed outside the project.
- The state file and the lock file must be regular files. Reads stop at
  the byte limit.
- Writers take an exclusive `flock` on `coord/capacity/.readings.lock`.
  They re-read and validate the state under that lock and merge the one
  window into it. They then write a uniquely named temporary file with
  `O_EXCL | O_NOFOLLOW`, fsync it and atomically rename it over the state
  file. Concurrent writers keep every other group and window.

## Limitations

- Manual readings are typed in by hand. The only automatic source is the
  optional Codex refresh below. There is no browser view or routing use
  yet.
- Only the latest reading per window is kept. There is no history.
- The lock depends on `flock`. It is suited to local file systems, not to
  network file systems that do not support it.
- Ancestor directories above the project are checked when the store is
  opened, not again on each later access.
- Fixing a mistaken reading needs a newer observed time, or a manual edit
  of the file.

## Cached Codex readings (optional)

In source, not yet released. `bridge/provider_capacity.py` adds one
optional automatic source: the Codex account's own rate-limit metadata.
It is stored apart from the manual readings, in
`PROJECT/coord/capacity/providers.json`, and never changes
`readings.json`. Manual `record` and `show` without `--provider` behave
and print exactly as before and never load the provider module.

```bash
unio capacity --project PATH refresh codex --group codex [--json]
unio capacity --project PATH show --provider codex [--group codex] [--json]
```

`refresh` runs only when you call it; nothing polls. It starts the
installed `codex app-server --listen stdio://` once, as its own process
group, in the empty project-owned directory
`coord/capacity/codex-cwd/`, with no model, profile or configuration
option. It sends exactly these requests and no others:

1. `initialize`, then the `initialized` notification;
2. `account/read` with `refreshToken: false`;
3. `account/rateLimits/read` with `excludeResetCreditDetails: true`, only
   when the account is a signed-in ChatGPT account.

It never starts a thread or turn, calls a model, logs in or out, refreshes
a token or uses reset credits. Server-initiated requests are refused, not
answered. Unio does not read the Codex auth store. Only the account kind
(`chatgpt`) and the normalized windows are kept: no e-mail address, plan,
token, credits, raw output, standard error or raw provider response is
stored or printed. The whole read has a 30-second deadline and a 1 MiB
output limit. On every exit path the owned process group is sent SIGTERM,
then SIGKILL, before the process is reaped; no process is ever killed by
name.

`show --provider codex` only reads `providers.json`. It never starts a
process or opens a network connection. Other provider names show as
Unknown, and `refresh` refuses them; only Codex is supported.

### Normalization

- When the response has `rateLimitsByLimitId`, every bucket in it is kept,
  keyed by its limit ID, and the single `rateLimits` is ignored so nothing
  is counted twice. The single `rateLimits` is used only when the map is
  absent or null. An explicit `null` map is deliberately treated like an
  absent key, for compatibility with app-servers that send the field before
  they support per-limit buckets. Any non-null map that is malformed (not an
  object, empty, more than 16 buckets, or a bad limit ID) makes the whole
  read Unknown; it never falls back.
- A bucket keeps its `primary` and `secondary` windows. A null window is a
  legitimate absence and stays null. A bucket that is not an object is kept
  by ID as Unknown with no values.
- A window is valid only when `usedPercent` is a finite number from 0
  through 100 (not a boolean), `windowDurationMins` is an integer from 1
  through 527040, and `resetsAt` is null or whole Unix seconds between
  2001 and 2100. A reset more than one window length plus 300 seconds after
  the read is `implausible_reset`. Any other defect is `invalid_window`.
  Remaining percent is 100 minus `usedPercent`.
- Duplicate JSON keys, NaN or Infinity, integers longer than 20 digits,
  over-deep nesting, oversized messages and malformed protocol messages
  make the whole read Unknown.

### Failures and freshness

Every attempt is recorded. A failed attempt sets the group's `state` to
`unknown` with one bounded `reason`, for example `binary_missing`,
`start_failed`, `timeout`, `exited`, `output_limit`, `invalid_message`,
`unexpected_request`, `request_failed`, `not_signed_in`,
`unsupported_account`, `invalid_account`, `invalid_rate_limits` or
`no_valid_window`. It removes the current windows, so an earlier read is
never shown as current. The most recent successful read stays under
`last_good`, marked `historical: true`, with every
`usable_remaining_percent` null.

For a current successful read, each window gets a status by the same rules
as manual readings: `unknown` when the read is more than 300 seconds in
the future, `expired` once its reset has passed or a whole window length
has gone by, `stale` after `--max-age-seconds` (default 900), otherwise
`fresh`. Only a `fresh` window has a `usable_remaining_percent`. A passed
reset never counts as refilled allowance; refresh again. A reading is an
observation only. It is never permission to run, bench or retry, and other
clients can spend the same budget at any time.

Stored `providers.json` is validated as strictly as a fresh read. Each
`used_percent` and `remaining_percent` must be a finite number from 0
through 100 on its own, not only consistent with the other. Every stored
attempt, observation and reset time must be a plausible time (2001 through
2100), so an extreme value such as year 9999 makes the file invalid instead
of crashing. A stored reset more than one window length plus 300 seconds
after its observation is refused, so a forged far-future reset never becomes
usable. An invalid file shows as `invalid`, is never overwritten by a refresh
and keeps its exact bytes.

Exit codes: `refresh` returns 0 when the read succeeded and 1 when it
recorded Unknown or was refused. `show --provider` returns 1 only when
`providers.json` is invalid.

### Stored state

`providers.json` has the same protections as `readings.json`:
descriptor-relative `O_NOFOLLOW` opens, a single-link regular file of at
most 262144 bytes, strict JSON, at most 32 groups and 16 buckets, its own
`flock` lock (`.providers.lock`) and an atomic fsynced replace. Any defect
makes the whole file invalid. `refresh` then refuses before starting Codex
and leaves the bytes unchanged.

### Testing

`UNIO_CAPACITY_TEST_CODEX` is a test-only injection. When set, it must be
an absolute path to an executable that stands in for `codex`. The focused
tests use a fake metadata executable this way:

```bash
python3 -B bridge/tests/provider_capacity_test.py
python3 -B tests/unio-provider-capacity.py
```

Neither test calls a live provider. A live read is a manual, separate
step.
