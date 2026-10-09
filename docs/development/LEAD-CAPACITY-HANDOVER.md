# Temporary acting lead and capacity handover

This document describes the planned future capability for temporarily transferring lead coordination when the original lead's allowance runs low or is exhausted.

## Current vs. planned capabilities

**Current native runtime:** The current lead retains full, concise coordination, review, and recovery responsibilities. As its trustworthy allowance falls, it delegates more implementation work to other capable agents to conserve capacity. The current lead does *not* automatically transfer its conversation, attach to a live session of another agent, or automatically switch supervisors. It is suggested to use a 20% delegate-first and 10% prepare-handoff as operating defaults, though these are not native thresholds or guarantees; the owner can override them.

**0.5.6 capability:** Supports manual capacity record/show only. The CLI lead registers a reservation (`unio lead <agent>`), but this does not initiate an automatic session transfer or switch supervisors. Use fresh, observed source/age/windows. "Unknown" capacity does not mean zero or available, and observing a reset passage alone never proves that allowance has been restored.

**Future planned handover:** A future feature will permit an available, capable AI to temporarily take over lead coordination when the original lead's 5-hour allowance is low or exhausted, returning coordination once the original allowance resets.

## Future handover process

The future handover mechanism will ensure a single current coordinator and record the primary lead versus the temporary acting lead.

### Handover record and context packet

A handover will include a bounded context packet containing:
- Reason for handover, last reading, cooldown status, and return condition.
- Explicit goals, owner constraints, and permissions.
- Task and dependency states.
- Scopes, active writers, worktrees, commits, and saves.
- Results, reviews, and receipts.

### Safely staging the transition

- Preserve uncommitted work, early commits, and existing handoffs.
- **Do not** interrupt or discard active writers.
- **Do not** blindly retry, reopen frozen calls, auto-publish, or change authentication.
- Stage the relinquishing and claiming of ownership safely. Competing handovers or partial claims must fail visibly without spawning both leads or silently losing ownership.

### Choosing the acting lead

Choose an available capable main subscription agent (e.g., Claude, Grok, Gemini, Codex) where eligible and where current owner instructions permit.
- **Verified-free OpenCode models remain routine workers ONLY** and must never be the lead or handle final acceptance.
- Check the shared budget group, including the lead reservation. Low tier allows one independent workflow per account budget, not per model alias. No second lead-provider feature/session or slot bypass is permitted.
- Existing worker bench and reroute logic stays unchanged; this feature specifically addresses lead cooldown.

### Returning to the original lead

The acting lead will return coordination after fresh, supported evidence confirms the original allowance is available and an orderly acting-lead checkpoint/handoff is created.
- If the acting lead also hits its limit, it may choose another eligible coordinator only within policy and owner authority; otherwise, it must preserve context and wait with an explicit status.
- Respect the original longer/weekly block rather than assuming a five-hour fallback fixes every limit.
- Prioritize unit/fake capacity, ownership, handoff, and recovery tests for eventual implementation. Do not require waiting hours for genuine quota exhaustion to publish unrelated tested changes.
- **Note:** There is no claim that any simulated or genuine handover has already been observed here.
