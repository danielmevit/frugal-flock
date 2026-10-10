# Perplexity task-fit trials — 2026-10-10

Both owner-selected Perplexity Pro routes worked with Thinking enabled. Neither
was consistently better across this small matched batch. Kimi returned faster;
both supplied usable planner code and incorrect test fixtures. GLM's integration
plan kept workflow slots and allowance evidence clearer. Their security findings
were complementary.

These observations supplement the [model scoreboard](MODEL-SCOREBOARD.md).
They concern requested routes, not independently verified server identities or
a general ranking of AI labs.

## Method

One frozen native Unio Source invocation per route, sequentially on the shared
Perplexity budget; no retries, extra reviewer models, web search or paid API
fallback. Each request contained the same four scenarios and selected source
excerpts. Both adapter receipts record the same 9,192-byte question hash:
`f4c1d7d2175413eadfe77a0cd3d3ae1d5f2bcf9648d203a0d5cd4bdf44462b1a`.

- GLM: `glm_5_3_thinking`, adapter elapsed 367.776 seconds.
- Kimi: `kimik3thinking`, adapter elapsed 90.159 seconds.
- Both: Thinking true, depth Unknown, Source exit 0, complete inline files.

The four scenarios were one combined answer per model, rather than four isolated
conversations. The lead wrote 16 independent planner test methods before seeing
the answers, inspected both complete code proposals, then ran those exact files
without corrections. The archived review failures were reproduced locally.
Initial local test-launcher argument errors were corrected without changing the
model files or frozen checks; those launcher errors are excluded from findings.

## Checked results

| Scenario | GLM 5.3 Thinking | Kimi K3 Thinking |
| --- | --- | --- |
| Debug the current save-cap refusal | Correct: no same-worker eviction candidates, prospective worker count 1/project count 33, misleading pinned/corrupt explanation | Correct same trace and misleading explanation |
| Review archived capacity validation | Found UTC-conversion and window-arithmetic overflows; missed the huge-integer overflow | Found huge-integer and window-arithmetic overflows; missed the UTC-conversion overflow |
| Write a pure ready-task planner | Exact inline implementation passed all 16 independent methods; its 12 proposed test methods contained two faulty fixtures | Exact inline implementation passed all 16 independent methods; its 10 proposed test methods contained two faulty fixtures |
| Plan integration with Unio | Clearer separation of advisory planning, native admission and stale allowance evidence; still a draft | Correctly included lead/shared-account slots, but mixed stale allowance readings with slot occupancy in the waiting-reason proposal |

The security scenario used a real archived candidate preceding the capacity
repairs, not a newly discovered vulnerability in installed v0.5.8. Both models
also identified a reproducible naive-clock `TypeError`; whether untrusted input
can reach that caller-controlled argument is not established by the excerpt.
Each found two of the three pre-reproduced overflow mechanisms. Together they
covered all three, which illustrates why independent findings can be useful;
neither answer alone was exhaustive or an accepted security review.

The generated-test defects were concrete:

- GLM expected a valid empty-dependency task and a valid ASCII label to be
  rejected. Two test methods failed.
- Kimi's test helper converted an intended malformed dependency string into
  a valid list; another fixture contained valid single-letter completed IDs.
  Two subcases failed within one test method.

Both archive suggestions require further design. GLM proposed an archive index;
Kimi proposed an archive tier. Neither is implemented. Scanner accounting,
claim resolution, locking, interruption recovery and storage bounds must be
specified before changing retention. No save, claim or historical worktree was
deleted or archived during these trials.

## Provisional delegation guidance

Use either route for bounded debugging and code proposals with explicit context.
Kimi is a reasonable first choice when a quick small-code draft is useful, based
on this one latency observation. GLM supplied the clearer integration plan here.
Use findings together when reviewing tricky boundaries; keep final acceptance
with a capable implementation agent and the lead. Independently inspect test
fixtures from both routes rather than relying on their self-authored tests.

Workflow slots and provider allowance are separate. The planner's occupied
counts come from native workflows and the lead reservation, grouped by shared
account. Missing or stale allowance does not change those counts. Auth presence
does not establish quota, a passed reset does not prove refill, and advisory
planning cannot override native admission.

Both routes expose Thinking identifiers through the pinned connector, without
high/xhigh controls. Effective model, reasoning depth, token use and remaining
Perplexity allowance stay Unknown. Timing includes transport and is not a
repeatable speed benchmark or a token-cost comparison.

No planner proposal was merged, applied to production or accepted as the
scheduling feature. Original drafts, frozen prompts, checks and receipts remain
private in the workspace. The earlier unequal GLM/Kimi trials remain recorded;
this matched batch supplements their evidence rather than replacing it.

See [Perplexity setup and proposal workflow](../integrations/PERPLEXITY-WEB.md),
[model effort](MODEL-EFFORT.md) and [next functional priorities](continue-with-ai-prompt.md).
