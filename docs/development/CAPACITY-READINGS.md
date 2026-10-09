# Manual capacity readings

`bridge/capacity.py` and the standalone `tools/capacity-readings.py` store
and show capacity readings that a person entered by hand. This is a
source-only foundation for a later CLI and browser integration. It is not an
automatic provider meter. It is not installed, routed or shown in the
browser yet. See [provider quota monitoring](../PROVIDER-QUOTA-MONITORING.md)
for the wider plan.

The component uses only the Python standard library. It never makes a
provider, model, network or authentication request. It does not bench or
enable agents, dispatch work, change tier or mode, or retry anything.

## Usage

Run the script directly. It finds its own repository, so it needs no
`PYTHONPATH` and works from any directory.

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

- Manual input only. There is no provider adapter, browser view, installer
  entry or routing use yet.
- Only the latest reading per window is kept. There is no history.
- The lock depends on `flock`. It is suited to local file systems, not to
  network file systems that do not support it.
- Ancestor directories above the project are checked when the store is
  opened, not again on each later access.
- Fixing a mistaken reading needs a newer observed time, or a manual edit
  of the file.
