# Give tasks enough time to finish

Choose a deadline for the work, rather than imposing the same short limit on
every worker. A core implementation can reasonably need 90 minutes or up to
two hours. Repeatedly cutting it off and reconstructing its context can waste
more allowance than one properly planned run.

These are lead planning defaults, adopted on 2026-10-07. They do not change
the installed CLI's timeout automatically or extend a run already started.

| Work | Usual allocation |
| --- | --- |
| Routine docs, formatting or a predefined check | 15–30 minutes |
| A focused repair with a reproduction and a narrow scope | 30–60 minutes |
| A substantial feature, core refactor or interacting failure paths | 90 minutes; up to 120 minutes when justified |

Estimate from the actual scope, relevant context, model and recent receipts.
Record the chosen limit in the task and per-run configuration. A short task
does not need the full allocation. A larger allocation is permission to
finish the assigned work, not permission to expand it.

## Give cumulative token budgets room for implementation

Owner update, 2026-10-09: loosen the initial trial caps. For a Vibe implementation
task, use **2,000,000 cumulative tokens** ordinarily, or **4,000,000** for substantial
work with a justified scope. Use estimated per-task price ceilings of **$5** and
**$10** respectively, within the owner's existing included monthly subscription.
These are planning defaults for new authorized runs, not permission for overage,
paid fallback or expanding scope. A smaller research or routine task can use less.
If a CLI does not expose a cumulative token control, record that limitation;
do not invent a flag. The Vibe adapter must expose its selected bounds explicitly.

Cumulative input includes context sent again on subsequent steps. It is different
from the model's per-request context window, per-response output limit, reasoning
effort and remaining subscription allowance. Pin actual model prices when using
Vibe's estimated max-price control; a zero-price default can make it ineffective.
A call can overshoot a cumulative/price check by its final response. An estimate
does not prove remaining included funds or prevent subscription overage by itself.
Never interpret a local token, price or time stop as provider exhaustion.

The first GLM trial reached 201,286 tokens under a 200,000-token cap, mainly
198,950 input tokens. The Medium 3.5 trial reached 601,926 under a 600,000-token
cap. Both original exit-3 results and their work are preserved. Those local stops
do not establish a model-quality ranking. New budget defaults do not authorize
replaying those frozen tasks; honor the invocation and correction policy.

Reduce avoidable context: read the newest coordination entries, then targeted
source and receipts; do not send the entire historical log on every step. Ask for
early commits, keep progress summaries compact and preserve raw evidence privately.
Use high by default and xhigh only where supported and justified. Max and ultra
effort are forbidden by the current owner policy. Larger task budgets do not
increase reasoning effort or change the low-tier one-workflow-per-budget rule.

## Keep the timeout layers consistent

Unio's `UNIO_TIMEOUT`, an outer wrapper such as `timeout`, and the selected
CLI's own deadline can all stop a Source invocation. The earliest one wins.
A 90-minute Unio limit cannot help if its wrapper or CLI still stops after
29 minutes. Set each supported layer deliberately and allow a small margin
for shutdown and recording the result.

For example, the native Source limit can be selected per invocation:

```bash
UNIO_TIMEOUT=5400 unio run WORKER TASK
```

The lead must also configure that task's pinned wrapper and any supported
CLI deadline; this environment setting alone does not adjust them. Check
each CLI's actual controls rather than inventing a flag. Preserve the
frozen task/configuration and the one-invocation policy. If existing timers
cannot be changed safely, record the limitation and use the new budget for
the next authorized assignment; do not silently replay an unchanged task.

## Bound checks and save useful progress

A long implementation allowance should not make a stuck test wait for two
hours. Bound individual subprocesses and barrier waits, clean up their exact
owned children, and return the actual failure. Quiet model output alone
does not prove that a call is stuck.

Ask for an early coherent commit and progress checkpoints about every
10–15 minutes during longer work. Record the current finding, saved revision
and next step. Use the native verifier for the frozen Validate list; avoid
having the worker and lead repeatedly run the same unchanged suite. Focused
debugging checks remain appropriate when they resolve a demonstrated defect.
Run the full required project gate at the selected delivery boundary.

Wall time, subscription allowance and model effort are separate controls.
Two hours of elapsed time does not establish two hours of billed usage or a
known amount of quota. Use supported dated readings when available; missing
capacity remains Unknown. A task deadline is not a provider usage limit and
must not automatically bench the provider or start a quota cooldown.

Workers save useful changes before final checks. Keep failed exits, partial
work and truthful handoffs. [Automatic work saving](../WORK-SAVING.md) is a
separate planned safeguard; a longer deadline does not replace it.
