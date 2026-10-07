# Keep independent work moving

Owner direction recorded 2026-10-07. This is a lead operating policy and a
future scheduler contract. It does not claim an automatic scheduler exists.

## Plan a queue, rather than a blocking batch

Break the approved goal into useful tasks with explicit prerequisites and
file ownership. Start ready, independent tasks on suitable available agents
from different AI labs/accounts. While one runs, advance another ready task,
prepare its contract, inspect an existing result or perform local checks.
Return to each result when it completes; one slow worker need not hold the
whole project. Do not invent chores just to keep every model busy.

Low tier permits one independent workflow per shared budget group, including
the lead. It does not restrict the whole team to one task. For example, a
Codex lead can coordinate one Grok implementation and one Gemini task at the
same time, provided their accounts are independent and their scopes do not
conflict. Another CLI/model name on the same subscription is still the same
budget. A worker's internal helpers follow its own authorized workflow; they
do not justify dispatching a second independent feature on that account.

## Dependencies and integration still matter

Freeze shared schemas or interfaces before dependent implementation. Assign
one owner to a shared file or migration, and give workers separate branches.
A consumer waits for its actual required contract or result. Independent
preparation can proceed without inventing what the unfinished result says.
Never modify a running task's frozen scope, configuration or evidence.

Integration is ordered. Check and personally assess each exact candidate
under the current owner review policy, then merge in dependency order.
Keep a release candidate unchanged during its full gate and source-bound
publication. Another worker can prepare the next milestone in its worktree;
its unfinished changes do not become part of that release. A global runner
upgrade waits until native work using it is idle; active runs keep their
original engine and configuration.

## Revisit the queue at useful boundaries

Track ready, running, awaiting-result, blocked and completed tasks, with their
worker/account, dependency, scope, saved revision and latest actual update.
When a worker finishes or an account resets, consider the next ready task.
Record why an available worker is idle: a prerequisite, scope conflict,
remaining allowance, no suitable approved task or unavailable route.
A blank quota reading stays Unknown; do not repeatedly probe by spending AI
calls. Keep progress reads local, cached and bounded.

Use current capacity and task fit rather than equal utilization. Main feature
owners remain Grok, Gemini/Antigravity, Claude and Codex; free Zen workers are
routine support only. Respect one-call tasks, STOP, account caps, funding
rules and the owner's selected work mode. Quota exhaustion, ordinary timeouts
and quiet output are different observations. Save work before handoff.

## Future automatic scheduler

A local dispatcher should choose only ready tasks within those constraints,
refresh the queue when a result arrives, and expose assignment or idle reasons.
No AI request is needed just to poll completion. Its first delivery should be
a dry-run recommendation view using real task/account state, followed by
owner-enabled dispatch with durable single-attempt claims. It must not replay
unknown outcomes or silently acquire authority to spend, merge or publish.

Offline acceptance should show two independent accounts progressing together,
one shared account refusing a second independent job in low tier, a dependent
task waiting, disjoint next-milestone work surviving a release gate, and STOP
or an unknown attempt preventing another dispatch. Measure accepted work and
lead effort as well as elapsed time; 100% busy is not itself a useful outcome.
