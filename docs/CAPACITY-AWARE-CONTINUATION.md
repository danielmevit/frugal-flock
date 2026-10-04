# Capacity-aware continuation — next-milestone proposal

Recorded 2026-10-04 from the owner's discussion. This is a product design,
not implemented functionality and not an expansion of the frozen M1
contract. Finish M1 verification before starting this work.

## Product promise

Keep a project moving without losing work. Assign a finishable piece that
fits the agent's remaining allowance, reserving capacity for checks and
saving progress. An agent with 30% remaining is not less capable; it needs
a smaller safe workload. Never rush it into skipping validation.

## Capacity readings

Use documented, supported provider signals where available; otherwise
accept a timestamped manual reading or show Unknown. Store the provider,
account/budget-pool identity, applicable model, limit window, remaining
capacity, reset time, observation time, source, and confidence. Do not put
credentials in the readings or browser storage.

Some providers expose usable information. For example, the official
[Claude Code status-line documentation](https://code.claude.com/docs/en/statusline#rate-limit-usage)
describes five-hour and weekly usage/reset fields in supported subscription
contexts. Fields can be absent. This establishes a possible adapter input,
not proof that a Frugal Flock adapter exists or every limit is observable.
Check current provider documentation and installed versions when building.

Do not confuse subscription allowance, context-window space, API request
rate limits, or paid credits. Percentages across plans are not equivalent.
Several workers sharing an account may consume the same allowance: account
for their reservations together without claiming to pool provider quotas.

## Scheduling policy

Use a cheap deterministic local controller to refresh supported telemetry
before dispatch, at task boundaries, and periodically with caching/backoff.
Do not spend AI requests merely asking how much quota remains. Expired or
invalid readings become Unknown, not fully available. A reset timestamp
does not by itself prove that capacity was restored.

Estimate task size, uncertainty, dependencies, model suitability, and the
cost of finishing, checking, and checkpointing. Use conservative ranges
until local history supports better estimates. Reserve allowance for
active tasks, including other workers sharing the same account. Explain
recommendations and let the owner choose allowed providers/concurrency.

Illustrative policy, to be tested rather than hard-coded as a guarantee:

| Capacity state | Behaviour |
|---|---|
| High | Start a substantial but bounded piece with an explicit done/checkpoint point. |
| Around 30% remaining | Finish the current piece or choose a small, well-defined task. |
| Low | Avoid new features; finish checks and prepare a checkpoint. |
| Nearly exhausted | Preserve work, then offer an approved replacement or wait. |
| Unknown/stale | Use conservative small tasks or ask for a manual reading; never invent a percentage. |

Steer running work only through supported safe boundaries or control
interfaces. Not every CLI supports mid-run messages. Prefer short task
steps and explicit stop points over assuming a long process can be
redirected. Do not endlessly switch providers when takeover overhead is
greater than finishing the current step.

## Safe continuation protocol

1. Ask the worker to finish a safe step; settle/stop it and confirm it no
   longer owns the workspace. Never allow overlapping writers.
2. Create a recoverable checkpoint of actual committed and uncommitted
   work, with secret exclusions, exact revisions, manifests, and hashes.
3. Save the task, decisions, completed checks, failures, and next concrete
   step. Distinguish a summary from a backup of file contents.
4. Let the owner choose an allowed, suitable replacement, or follow an
   explicitly preapproved routing policy. No paid fallback by surprise.
5. Verify the checkpoint, grant exclusive workspace ownership, continue,
   rerun checks, and return to human review. No automatic merge.

The M1 manual handoff packet is only context for the SAME checkout. It
does not copy dirty-file contents and must never be presented as this
future recoverable checkpoint/migration feature.

## Delivery and tests

After M1: implement manual capacity input and one supported read-only
adapter; then a dry-run scheduler; then checkpoint/restore and supervised
continuation; only then optional automatic routing. Keep UI simulation
clearly separate from real provider control.

Test stale/missing/out-of-range telemetry, overlapping limit windows,
shared-account workers, sudden limits during edits/tests/checkpoint writes,
authentication failure versus quota exhaustion, reset uncertainty, corrupt
checkpoints, secrets, incompatible replacement tools, lost ownership,
double dispatch, and stop requests. Simulate these cases without provider
calls. Measure accepted work, rework, active human time, and recovery cost.
