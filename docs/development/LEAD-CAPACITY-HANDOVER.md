# Temporary acting lead and capacity handover

This document describes the current lead behavior when allowance runs low and
a planned future capability: temporarily transferring lead coordination while
the original lead's allowance is exhausted. The future part is documentation
only; nothing below is implemented or tested as a runtime feature yet.

## Current vs. planned capabilities

**Current lead instructions (not native automation):** The registered lead
keeps coordination, review and recovery. As its trustworthy allowance falls,
it delegates more implementation to other eligible main workers to conserve
that allowance. The suggested operating defaults are delegate-first below
about 20% remaining and prepare a handover packet below about 10%. They are
lead instructions in [LEAD-ROUTING](LEAD-ROUTING.md), not native runtime
thresholds, and not proof of availability; the owner can override them. Unio
does not automatically transfer a conversation, attach to another agent's live
session or switch supervisors.

**Capacity evidence today:** 0.5.6 provides manual `unio capacity record` and
`show`. The 0.5.7 candidate adds an explicit, read-only `unio capacity refresh
codex` metadata read with cached 5h/weekly windows, and the browser's
Designated AI agents & limits section. Use a fresh observed reading with its
source (Automatic Codex or Manual), age and both the 5h and weekly windows.
Unknown capacity means neither zero nor available, and a passed reset time
alone never proves that allowance has been restored. `unio lead <agent>`
registers a reservation only; it does not transfer a live CLI conversation or
perform acting-lead switching.

**Future planned handover:** When the original lead's 5h or weekly allowance
is low or exhausted, the original lead takes a back seat during its cooldown,
an eligible capable subscription agent temporarily leads, and coordination
returns after a fresh supported reading confirms that the original lead's
allowance is restored.

## Future handover process

The future handover mechanism will keep exactly one current coordinator and
record the primary lead versus the temporary acting lead.

### Handover record and context packet

A handover will include a bounded context packet containing:

- Reason for handover, last reading with source and age, cooldown status and
  return condition.
- Explicit goals, owner constraints, permissions, mode and tier.
- Pending tasks, task and dependency states, and model roles.
- Scopes, active writers, worktrees, commits and saves.
- Results, reviews and exact receipts.
- Shared account budget groups and their limits, including the lead
  reservation.

### Safely staging the transition

- Preserve uncommitted work, early commits and existing handoffs.
- **Do not** interrupt or discard active writers.
- **Do not** blindly retry, reopen frozen calls, auto-publish or change
  authentication.
- Stage the relinquishing and claiming of ownership safely. Competing
  handovers or partial claims must fail visibly without producing two leads or
  silently losing ownership.

### Choosing the acting lead

Choose an available capable main subscription agent (for example Claude,
Grok, Gemini or Codex) where eligible and where current owner instructions
permit.

- **Verified-free OpenCode models remain routine workers ONLY** and must
  never be the lead or handle final acceptance.
- Check the shared budget group, including the lead reservation. Low tier
  allows one independent workflow per account budget, not per model alias.
  Never spawn a duplicate session on the same shared budget, and never bypass
  a slot.
- Existing worker bench and reroute logic stays unchanged; this feature
  specifically addresses lead cooldown.

### Returning to the original lead

The acting lead will return coordination after fresh, supported evidence
confirms the original allowance is available and an orderly acting-lead
checkpoint/handoff is created.

- If the acting lead also hits its limit, it may choose another eligible
  coordinator only within policy and owner authority; otherwise, it must
  preserve context and wait with an explicit status.
- Respect the original longer/weekly block rather than assuming a five-hour
  fallback fixes every limit. Elapsed reset time is not evidence of capacity.

### Testing the future implementation

Prioritize deterministic tests with fake capacity readings and fake handoff
state: ownership claims, competing handovers, stale/Unknown readings,
weekly blocks, return conditions and recovery. Do not require hours of
genuinely exhausted quota to publish unrelated tested changes.

**Note:** No simulated or genuine handover has been observed here, and no
change of lead has been performed by this documentation slice.
