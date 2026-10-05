# Provider capacity and assignment notes

Recorded 2026-10-05. Future leads must read this file together with the newest
workspace agent-log entries before assigning providers. Refresh public rates
and account meters when making a new assignment; this is a dated observation.

## Owner's usage screenshot

Source: `firefox_4XaNhkBi1x.png`, supplied by the owner from ShareX. The
private workspace copy is `artifacts/provider-usage/2026-10-05/opencode-usage.png`
under the enclosing legacy `frugal-flock` workspace. The selected date range,
subscription tier, remaining allowances and separate thinking-token counts
are not visible. Do not infer these from the table.

| Model | Requests | Input | Cache read | Cache write | Output | Displayed cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GLM 5.3 | 81 | 301.8k | 2.3M | — | 154.9k | $1.72 |
| Kimi K3 | 31 | 132.3k | 669.6k | — | 19.1k | $0.88 |
| Qwen 3.8 Max | 27 | 162 | 821.8k | 76.0k | 15.3k | $0.49 |
| DeepSeek V4 Pro | 35 | 183.6k | 1.0M | — | 20.5k | $0.37 |
| MiniMax M3 | 76 | 85.7k | 3.6M | — | 20.7k | $0.27 |
| GLM 5.3 Flash | 1 | 4.3k | 8.9k | — | 9 | <$0.01 |

Qwen input is literally 162, not 162k. Totals: 251 requests and displayed
cost $3.73 to less than $3.74. These rounded aggregates cover different tasks
and efforts; they are neither completed-task counts nor a quality ranking.
GLM accounts for about 46% of displayed cost. Large cache-read totals show
why repeated context also matters. Avoid reading the entire historical log
into every task; provide the relevant newest entries and a self-contained
scope. Keep complete review material when correctness requires it.

## Public Go limits, checked 2026-10-05

[OpenCode's official Go documentation](https://opencode.ai/docs/go/) defines
five-hour, weekly and monthly allowances as 20%, 50% and 100% respectively.
Model-specific monthly budgets determine allowance consumption. Published
request counts are estimates, not guaranteed request quotas. Consult the
account's actual meters before scheduling a batch.

Prices below are dollars per million tokens; budgets refer to Go, not Go Plus.

| Model | Input | Output | Cache read | Cache write | Monthly budget |
| --- | ---: | ---: | ---: | ---: | ---: |
| GLM 5.3 | 1.40 | 4.40 | 0.26 | — | 15 |
| Kimi K3 | 3.00 | 15.00 | 0.30 | — | 15 |
| Qwen 3.8 Max | 2.00 | 6.00 | 0.25 | 2.50 | 15 |
| DeepSeek V4 Pro, off-peak | 0.66 | 1.98 | 0.022 | — | 15 |
| DeepSeek V4 Pro, peak | 1.32 | 3.96 | 0.044 | — | 15 |
| MiniMax M3 | 0.30 | 1.20 | 0.06 | — | 60 |
| GLM 5.3 Flash | 0.15 | 0.50 | 0.03 | — | 60 |

The screenshot's dollar sum alone does not establish remaining allowance
because these model budgets differ. Use the console rather than predicting
an exact reset or independent capacity for another Go model. Do not enable
paid balance fallback, upgrade a plan or change billing without owner approval.

## Observed availability and standing execution rules

At about 11:06 +0200 on 2026-10-05, the native OpenCode log recorded
`AI_APICallError: Go usage limit exceeded` for GLM, DeepSeek and Kimi in the
rename batch. Their CLIs remained running without completing useful work;
the lead interrupted them and preserved receipts. A running process is not
proof that a provider is making progress. Check both native provider logs
and Unio run receipts when output stalls.

The owner later reported that the Go five-hour window would reset in
1h57m. A receipt created from `date` recorded an approximate reset of
2026-10-05 13:30:02 +0200. This estimate is historical, not a recurring
schedule, proof that weekly/monthly capacity remains, or permission to
retry the original rename tasks.

The owner authorizes use of available AIs for Unio and milestone work;
ordinary provider assignment and cross-company review need no repeated
permission. For this rename cycle, each task gets one invocation, no
automatic retries, a pinned model/effort, a wall-clock budget and preserved
receipts. The owner explicitly granted one Gemini replacement for B and
one Grok replacement for D after their original Go failures. Further work
must have a distinct, concrete task; do not disguise a retry as a new ID.

Keep GLM 5.3 at high effort. The local live findings in
[FINDINGS-2026-10-05.md](FINDINGS-2026-10-05.md) record task results and
effort compatibility; Flash is not a substitute for the approved GLM race.
Use local verified quality and availability alongside cost when choosing
a model. Do not assume an installed CLI has usable quota, or that the same
company reached through another subscription shares the same capacity.

Resume the orchestrator before authorized runs, stop it after launching or
finishing the bounded batch, preserve interrupted work, and record every
checkpoint in the shared log with timestamps from `date`. Independent
review must come from another company, followed by the lead's own review.
Global installation and release publication still require fresh owner approval.

## Latest owner capacity report

On 2026-10-05 the owner reported that the OpenCode Go five-hour limit had
reset and authorized GLM 5.3 at high effort for this milestone run. This is
a dated owner report, not a live probe or evidence of weekly/monthly headroom.
One bounded task invocation and cross-company review remain required; no
automatic retry or paid fallback is enabled.

## Remaining-quota monitoring roadmap

The owner requested a live indicator and proactive lead checks on
2026-10-05. Read [PROVIDER-QUOTA-MONITORING.md](PROVIDER-QUOTA-MONITORING.md)
for verified adapter inputs and the delivery sequence. A read-only Codex
probe succeeded; remaining OpenCode Go capacity is still Unknown without
an actual account-meter reading. Session costs and reset reports do not
establish current remaining allowance. No fleet-wide meter is implemented.

## Additional owner-authorized Anthropic worker

On 2026-10-05 the owner added Claude Opus 5.5 at high effort for milestone
tasks. The private per-run seat pins `claude-opus-5-5` and `--effort high`,
disables model fallback and retains structured model-usage evidence. Local
CLI 2.1.289 is signed in through first-party Claude Pro. That sign-in does
not establish remaining five-hour or weekly allowance. Do not conflate its
subscription with OpenCode Go or assume an automatic quota adapter exists.

Its first assigned task is QUEUE-APPROVAL-FIX-1: a bounded correction of five
reproduced failures in Gemini's queue candidate. An OpenAI worker reviews the
combined Google/Anthropic candidate, followed by the lead. Each invocation
still receives its own receipt and deadline, with no automatic paid retry.
