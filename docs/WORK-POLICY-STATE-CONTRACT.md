# Work-policy state contract

Frozen shared interface for the smaller implementation slices, 2026-10-07.
The broad MiMo WORK-POLICY-1 trial timed out with zero code; it is preserved
as failed evidence and is not retried unchanged. Deliver the existing
[work-mode contract](WORK-MODES.md) in two bounded concerns: command/state
visibility, then native workflow accounting and per-run prompt snapshots.

## Persistent schema

The workspace file `coord/work-policy.json` uses exactly these fields:

```json
{
  "schema_version": 1,
  "mode": "medium",
  "tier": "low",
  "lead_agent": null,
  "accounts": {}
}
```

An optional `updated_at` ISO timestamp with timezone may be added by a setter.
Missing file means these defaults. Reject duplicate/unknown keys, unknown
schema, wrong types, invalid enum or labels, symlink/nonregular/hardlinked or
oversized state without resetting it. Maximum state size is 64 KiB. Account
keys and group values use the existing validated agent label syntax. Labels
are logical budget identifiers, never authentication or credential values.

Mode/tier setters preserve all other fields. Lead setter takes an agent or
`none`; account setter takes an agent and group. Writers serialize under
`coord/.locks/work-policy.lock`, validate before mutation and replace state
atomically. Commands reject invalid and surplus arguments before writing.
Queries never dispatch, authenticate, probe quota or alter agents.conf.

## Incremental delivery must stay truthful

The command/state slice implements mode, tier, policy, lead and account,
first-contact instructions and a readable installed guide. Policy JSON
reports schema_version, selected state, derived account workflow limit
(low1/medium2/high4), and `capacity: "unknown"`. It also explicitly reports
`workflow_enforcement: "advisory"` until the next guard slice is delivered.
Human output and README explain that distinction. Settings guide the lead
but do not pretend to constrain unmanaged CLI sessions.

The guard slice changes workflow_enforcement to a native active-workflow
value only after it actually reserves/counts slots for foreground/background
Source and independent review, including a registered lead. It supplies a
snapshot/policy header through existing safe prompt transport and preserves
original task hashing. Existing state schema and commands remain stable.
Tier reduction counts all existing group slots. Regrouping an occupied agent
or the registered lead's agent refuses. Internal helpers on one assignment
are not automatically counted as additional independent workflows.

Neither slice skips frozen Validate commands, changes owner permissions,
alters billing/effort settings or claims a live subscription meter. Public
release status remains separate from development source functionality.
