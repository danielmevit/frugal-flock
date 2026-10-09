# Provider quota monitoring — roadmap

Owner request recorded 2026-10-05. Unio does not yet have a live remaining
quota indicator. This proposal extends the
[capacity-aware continuation design](CAPACITY-AWARE-CONTINUATION.md).

## Current state, 2026-10-09

| Piece | State |
| --- | --- |
| Manual readings with age, reset and Unknown handling | `unio capacity record` and `show` in 0.5.6. Not included in 0.5.5. See [manual capacity readings](development/CAPACITY-READINGS.md). |
| Automatic provider readings (Codex adapter first) | 0.5.7 candidate, not yet released: explicit `unio capacity refresh codex --group G` performs one read-only Codex metadata read and caches it; `show --provider codex` reads only that cache. See [cached Codex readings](development/CAPACITY-READINGS.md#cached-codex-readings-optional). Other providers remain Unknown. |
| Browser indicators | 0.5.7 candidate, not yet released: the Designated AI agents & limits section shows every recorded window (duration, remaining, reset countdown, age, source) from a cached read-only `/api/limits`; the browser never triggers a refresh. Missing, stale, expired or invalid readings show as Unknown. |
| Lead refresh before dispatch | Planned. The current lead instruction is to delegate more as a fresh reading falls; see [lead capacity handover](development/LEAD-CAPACITY-HANDOVER.md). |
| Scheduling, benching or retry based on readings | Planned. Readings change nothing on their own. |

No release number or delivery date is assigned to the planned pieces.

## What the lead needs

Show the remaining allowance, reset time and age of the reading for every
available limit window before assigning work. The five-hour limit is only
one constraint: weekly or monthly capacity can still block a task. An
allowance is a usage budget, not five hours of guaranteed running time.

Workers can share a provider account and budget pool. Group them using
confirmed pool identifiers, rather than granting each worker a separate
copy of the same allowance. Keep different subscriptions and API billing
separate. Model consumption differs; a percentage is not a reliable count
of finishable tasks.

## Verified inputs, checked 2026-10-05

| Provider or tool | Supported input | Current Unio status |
| --- | --- | --- |
| Codex with ChatGPT authentication | Native `account/rateLimits/read` and update notifications provide usage, window duration and reset timestamps, including multiple limit buckets. | A private read-only feasibility probe succeeded. An optional on-demand adapter is in source, not yet released, and tested only against a fake app-server. |
| Claude Code | Supported status-line input can contain five-hour and weekly usage and reset fields. Availability depends on the subscription/session and fields can be absent. | Candidate adapter input; no live reading was collected in this session. |
| OpenCode Go | Official documentation defines five-hour, weekly and monthly allowances. Account meters are in the console. | No supported automated remaining-quota interface was established by this investigation. Use a timestamped manual meter reading until one is verified. |
| OpenCode CLI statistics | Session token and cost statistics. | Useful for estimating task consumption; insufficient to establish current subscription headroom. |
| Gemini and Grok | Provider-specific inputs still need investigation. | Unknown until a supported read interface or a manual reading is verified. |

Sources: [Codex account interface](https://learn.chatgpt.com/docs/app-server#auth-endpoints),
[Claude status-line limits](https://code.claude.com/docs/en/statusline#rate-limit-usage),
[OpenCode Go allowances](https://opencode.ai/docs/go/), and
[OpenCode CLI statistics](https://opencode.ai/docs/cli/#stats).

The local Codex probe on 2026-10-05 at 14:54:14 +0200 reported 36% used in
a 300-minute window and 61% used in a 10,080-minute window: 64% and 39%
remaining respectively. It made no model call or billing change. This is
historical evidence of feasibility, not a current meter. Its sanitized
receipt is in the private workspace at
`tmp/unio-next/receipts/codex-capacity-probe.json`.

## Delivery sequence

1. Add timestamped manual readings (in 0.5.6) and a
   supported read-only Codex adapter (planned).
   Validate percentages, window lengths, timestamps and provider responses;
   retain all reported limit buckets. Store only the fields needed for
   scheduling, with an opaque local account/pool identifier.
2. Expose a local CLI view and JSON output (manual readings: 0.5.6), then browser indicators showing
   each window, remaining allowance, reset time, source and reading age.
   Distinguish provider readings, manual readings, consumption estimates,
   stale readings and Unknown. Missing data must never look like 100% free.
3. Let the lead refresh cached readings before dispatch, after task/review
   boundaries and periodically while a batch is active. Use bounded reads
   and backoff; checking capacity must not invoke a model. Reserve estimated
   capacity for active workers, independent review, validation and saving
   a checkpoint. Explain conservative task-size recommendations.
4. Connect low-capacity warnings to the approved checkpoint/continuation
   workflow. Finish or stop at a safe boundary, preserve work and follow
   the owner's permitted routing policy. Add other provider adapters only
   after verifying their interfaces.

Keep consumption estimates separate from reported remaining allowance.
Work in another client can spend the same account budget; local receipts
alone cannot reconstruct the account's current balance. A reset countdown
reaching zero also needs a fresh reading before claiming capacity returned.
Telemetry failure must not silently bench a worker, change provider
configuration, restart a task or enable paid fallback.

## Acceptance checks

Use fixtures to cover missing and stale fields, invalid percentages,
multiple windows/buckets, unknown pool identity, concurrent reservations,
other-client usage, provider errors and reset uncertainty. Verify that
monitoring makes zero model calls, does not expose credentials and cannot
perform billing or account-control actions. Test both JSON and browser
views against the same normalized readings and show Unknown on failure.

Until automatic readings ship in a release, the lead should record actual supported
readings or owner-provided meters with `unio capacity record` where the
0.5.6 or newer is installed, otherwise in the private coordination log.
Use bounded tasks and preserve independent review capacity. A manual
reading is what someone saw at one time. Do not claim fleet-wide live
monitoring is active.
