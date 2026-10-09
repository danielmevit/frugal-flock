# Capacity Readings

This component provides a bounded, standard-library-only implementation to track remaining capacity limits from LLM providers or manual entries. The current slice provides a foundation with manual inputs; it does not benchmark agents, invoke models, or auto-retry tasks.

## Usage

You can use the standalone `tools/capacity-readings.py` script to record and view capacity data for groups (i.e. shared budgets).

### Recording a Reading

```bash
python3 tools/capacity-readings.py --project . record \
    --group my-shared-budget \
    --window 5m \
    --window-minutes 5 \
    --remaining-percent 55.5 \
    --observed-at 2026-10-09T14:00:00+00:00 \
    [--reset-at 2026-10-09T14:05:00+00:00]
```

- `--group`: Opaque label identifying the shared budget.
- `--window`: Opaque label for this specific rate-limit window.
- `--window-minutes`: Duration of the window in minutes (positive integer).
- `--remaining-percent`: Remaining usage allowance, from 0 to 100.
- `--observed-at`: Timezone-aware ISO8601 timestamp of when the capacity was read.
- `--reset-at` (optional): Timezone-aware ISO8601 timestamp of when this bucket resets.

Source is always `"manual"` for this initial release; callers cannot pretend an input is from an automated provider.

### Showing Readings

```bash
python3 tools/capacity-readings.py --project . show [--group my-shared-budget] [--json] [--max-age-seconds 900]
```

Displays window, source, observation time/age, and its fresh/stale/expired/invalid status.
If the data is stale or expired, the usage percent is tracked under a separate non-usable field (`last_remaining_percent`) and does not count as positive available allowance.

## Schema Details

Data is stored as a strict bounded JSON in `<project>/coord/capacity/readings.json`. It will never overwrite malformed data.

### Example JSON output

```json
{
  "schema_version": 1,
  "groups": {
    "my-shared-budget": {
      "5m": {
        "source": "manual",
        "window_minutes": 5,
        "observed_at": "2026-10-09T14:00:00+00:00",
        "reset_at": "2026-10-09T14:05:00+00:00",
        "remaining_percent": 55.5
      }
    }
  }
}
```

## Limitations
- This CLI does not call APIs, benchmark models, or guess any missing remaining budget. Missing or invalid capacity readings are represented as `Unknown` and do not manufacture fake availability.
- No historical data logging of account usage; the tool merely holds the latest snapshot per window.
- Does not expose credentials, logs, or account identifiers.
- A reset countdown hitting zero only flags the value as expired. A new reading must be recorded before usage can continue.
