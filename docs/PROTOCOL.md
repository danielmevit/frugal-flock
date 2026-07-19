# AGENTTEAM PROTOCOL — system specification for AI agents

Audience: AI agents (lead or worker) operating inside an agentteam project.
Status: normative. If your role card (MASTER.md / WORKER.md) conflicts with
this document, the role card wins. The human owner (Daniel) outranks both.

## 1. SYSTEM

agentteam coordinates one interactive LEAD session and N headless WORKER
runs from different AI CLIs (claude, codex, agy/antigravity, grok,
opencode) on one shared git repository. Isolation is per-worker git
worktrees. Coordination is plain files. Integration is human-gated merges.

Roles:
- OWNER (human): approves plans, reads diffs, merges to base, releases.
  Sole merge authority. Sole release authority.
- LEAD (interactive session in `repo/`): plans, freezes contracts, writes
  task files, dispatches workers, verifies results, recommends merges.
  Never implements feature code. Never merges.
- WORKER (headless run in `wt/<name>/`): executes exactly one task file,
  commits in its own worktree, reports. No memory between runs.

## 2. FILESYSTEM CONTRACT

Layout relative to project root:

| Path | Content | Write access |
|---|---|---|
| `repo/` | The repository, checked out on the base branch | OWNER, LEAD (docs/contracts only) |
| `repo/changelog.d/<ID>.md` | Changelog fragment per task; rolled into CHANGELOG.md at release | the task's WORKER |
| `wt/<worker>/` | Worktree on branch `agent/<worker>` | that WORKER only |
| `coord/base` | Base branch name (single word, normally `dev`) | OWNER |
| `coord/docs/` | Operating playbooks + this protocol | OWNER |
| `coord/board.md` | Task board, one row per task | LEAD only |
| `coord/tasks/<ID>-<worker>.md` | Task files (work orders) | LEAD only |
| `coord/reports/<task>.md` | Append-only run history per task | agentteam tooling |
| `coord/reports/<task>.log` | Latest run's full output (overwritten) | agentteam tooling |
| `coord/reports/ledger.jsonl` | Append-only machine ledger: one JSON object per event | agentteam tooling |
| `coord/blockers.md` | Blocker notes | anyone, APPEND only |
| `coord/STOP` | If present: all new runs refused | OWNER |

Transient control files (tooling-owned, never edit): `coord/.locks/<w>.lock`
(one run per worker) and `coord/reports/<task>.pid` (background run's
process id, removed on exit).

Data-source rule: historical analysis MUST read `reports/*.md` (append-only,
all runs) or `ledger.jsonl` (append-only, machine-readable). `*.log` holds
only the latest run and MUST NOT be used as history.

Enforcement at init: `agentteam init` refuses to scaffold while likely
secret files are tracked (override: AGENTTEAM_ALLOW_SECRETS=1), and
installs git hooks so a worker worktree can commit only on its own
`agent/<w>` branch and can never push.

## 3. DATA FORMATS

Report run-block (appended to `coord/reports/<task>.md` per run):

```text
## run <ISO8601 timestamp> — worker=<worker> agent=<agent> exit=<int> duration=<int>s
### git status (branch, staged/unstaged)
<porcelain v1 output>
### committed diffstat vs <base>
<diffstat or "(none)">
### verdict
commits=<n> files=<n> insertions=<n> deletions=<n> uncommitted=<n>
[!! empty-diff warning when exit=0 with no changes]
### agent output (tail)
~~~
<last 60 lines of the run log>
~~~
```

Verify block (appended by `agentteam verify`):
`### verify <ts> — worker=<w> scope=<OK|VIOLATION|UNCHECKED>
validate=<passed>/<run> empty=<0|1> verdict=<PASS|FAIL>` plus out-of-scope
paths and per-command results.

Ledger events (`coord/reports/ledger.jsonl`, one JSON object per line):

```text
{"event":"run","ts":…,"task":…,"worker":…,"agent":…,"exit":n,"duration_s":n,
 "commits":n,"files":n,"insertions":n,"deletions":n,"uncommitted":n,"wall":0|1}
{"event":"verify","ts":…,"task":…,"worker":…,"scope":"OK|VIOLATION|UNCHECKED",
 "validate_run":n,"validate_failed":n,"commits":n,"empty":0|1,"verdict":…}
{"event":"review","ts":…,"task":…,"worker":…,"reviewer":…,"exit":n}
{"event":"race","ts":…,"task":…,"workers":"w1 w2 …"}
```

Task file schema (LEAD writes; template at `coord/tasks/TEMPLATE.md`):
sections `Goal` (one testable outcome), `Context` (self-contained — the
worker has zero prior memory), `Allowed scope` (exhaustive; every
`- path` line is a machine-enforced pattern — globs allowed, trailing `/`
means the subtree, `changelog.d/` is implicitly allowed), `Constraints`,
`Validate` (every `$ command` line is machine-run by verify and must exit
0), `Done means` (observable + committed + changelog fragment where the
repo keeps a changelog), `Report` (required final sections: SUMMARY /
FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW).

Board row schema: `| ID | worker | state | branch | scope | done-when |`
with state ∈ {todo, doing, blocked, review, done}.

Worker→agent resolution: agent id = worker name up to first `-`
(worker `codex-2` → agent `codex`).

## 4. THE `agentteam` COMMANDS (local shell tool)

To be explicit: these are subcommands of the local `agentteam` shell
script. No AI-provider API is involved anywhere in this system — every
agent is an official CLI running under its own subscription LOGIN
(cached on the machine), never an API key.

```text
agentteam init [w1 w2 ...]     scaffold worktrees + coord (idempotent);
                               secrets preflight; guard hooks
agentteam agents               list agents: binary present, on/off state
agentteam smoke                one tiny live call per agent from a neutral
                               dir; OK / WARN (reply lacks "ok") / FAIL
agentteam selftest             full-loop rehearsal in a sandbox repo with
                               mock agents; zero quota; nonzero on failure
agentteam run [-b] <w> <task>  execute coord/tasks/<task>.md as worker <w>
                               in wt/<w>; -b = background; per-worker lock;
                               writes report+log+ledger
agentteam tail [task]          follow a run's live log (default: newest)
agentteam kill <task>          terminate a background run (whole session,
                               including the agent under `timeout`)
agentteam verify <w> <task>    machine gate assist: diff vs the task's
                               "- path" scope lines + run its "$ " Validate
                               lines in the worktree + commit sanity;
                               appends verify block; nonzero exit on
                               violation / validate failure / empty diff
agentteam diff <w> [--stat]    changes on agent/<w> vs base: committed and
                               uncommitted, separately
agentteam review <w> <task> [agent]  cross-vendor review: a DIFFERENT agent
                               judges task order + diff from a neutral dir;
                               ends VERDICT: APPROVE|REQUEST-CHANGES
agentteam sync [w]             bring base's merged work into worker
                               branches (ff when fully merged, merge
                               otherwise; skips dirty/running; aborts and
                               reports on conflict)
agentteam race <task> <w1> <w2> [...]  copy <task>.md to <task>-<w>.md per
                               worker and dispatch all in background;
                               OWNER merges at most one winner
agentteam sabotage <w>         saboteur seat: sync <w>, generate a SAB-*
                               task from the template, dispatch background
agentteam status               off-agents, tasks, reports, review queue
                               (unreviewed commits per worker), running jobs
agentteam off <agent> [dur]    bench agent (dur: 30m|5h|7d; absent=manual);
                               run refuses benched agents; expiry auto-clears
agentteam on <agent>           un-bench
agentteam stop | resume        create/remove coord/STOP (global run gate)
```

Environment: `AGENTTEAM_TIMEOUT` (seconds, default 3600) caps each run;
`AGENTTEAM_VERIFY_TIMEOUT` (default 900) caps each Validate command;
`AGENTTEAM_REVIEW_TIMEOUT` (default 900) caps a review call.
`AGENTTEAM_AUTO_OFF=1` auto-benches an agent 5h when a FAILED run's log
matches limit-language patterns (suppressed when the task text itself
mentions limits and the run succeeded). `AGENTTEAM_ALLOW_SECRETS=1`
overrides the init secrets preflight. Agent invocation templates live in
`~/.config/agentteam/agents.conf` (project override: `coord/agents.conf`).

Companion tool: `myapp <project-root>` prints the per-agent scorecard
(runs, ok, fail, walls, merges, last run) computed from reports/*.md,
ledger.jsonl and git merge history. LEAD SHOULD consult it when assigning
tasks.

## 5. LIFECYCLE

1. OWNER states intent to LEAD.
2. LEAD reads coord/docs/*, repo docs (AGENTS.md router, docs/ai/), and
   `agentteam agents`; produces a task breakdown; WAITS for OWNER "go".
3. LEAD freezes shared contracts (types/schemas/fixtures) as commits on
   the base branch BEFORE dispatching dependent tasks; task files cite
   contract paths @ sha.
4. LEAD dispatches via `agentteam run`; parallel tasks MUST have disjoint
   Allowed-scope sets (changelog.d/ exempt — one file per task); at most
   one task per cycle may modify dependency manifests (package files,
   lockfiles, migrations). Race tasks are the sanctioned exception to
   disjointness: several workers, same scope, at most one merge.
5. WORKER executes its task file exactly: modifies only Allowed-scope
   paths, runs Validate, writes its changelog fragment, commits only files
   it changed (never blanket staging), ends output with the Report
   sections.
6. LEAD verifies, machine first: `agentteam verify` (scope + Validate +
   commit sanity), then reads the report and `agentteam diff`; for risky
   diffs also `agentteam review`. Reports are claims; diffs, verify
   verdicts and logs are ground truth.
7. OWNER merges accepted branches into base (`git merge --no-ff`).
   Acceptance gate: verify PASS, clean build, tests green, smoke run,
   changelog fragment where the repo keeps a changelog. After the merge
   cycle, LEAD runs `agentteam sync` so all workshops rebuild on the new
   base.
8. Releases: OWNER-only, explicit, base→main + tag. At release, LEAD rolls
   changelog.d/ fragments into CHANGELOG.md. Order: merge fix → verify →
   tag.

## 6. INVARIANTS (hard rules, numbered)

- I1  A WORKER writes only inside its own worktree, only within the task's
      Allowed scope.
- I2  Out-of-scope need ⇒ do NOT touch it: finish what is in scope, state
      the need in NEEDS-REVIEW (and blockers.md if blocking). Flagging
      beats fixing — recorded precedent.
- I3  Only OWNER merges to base or main. LEAD recommends; never merges.
- I4  LEAD never writes feature code. Contracts, fixtures, docs, board: yes.
- I5  Workers never switch branches, never push, never touch base/main.
      (Enforced by guard hooks; the rule stands even where hooks are absent.)
- I6  Same obstacle twice ⇒ stop, write blockers.md; do not improvise
      architecture.
- I7  coord/STOP present ⇒ no new runs, no new dispatches.
- I8  Contracts cited in a task file are frozen: request changes via
      blockers.md, never edit them.
- I9  Benched (OFF) agents get no work; LEAD reroutes by the fallback
      policy in MASTER.md.
- I10 Verification is evidence-based: a claim without a diff/test/log
      backing it is treated as unverified. `agentteam verify` is the
      mechanical floor of that evidence, not its ceiling.
- I11 Workers never edit CHANGELOG.md; changelog entries are per-task
      fragments in changelog.d/, rolled up at release by LEAD/OWNER.
- I12 A run that claims success with an empty diff (no commits, no
      uncommitted changes) is treated as FAILED.

## 7. FAILURE PROTOCOL

| Condition | Required behavior |
|---|---|
| Auth/token error in output | Report it verbatim; OWNER re-logins the CLI; task is rerunnable. |
| Limit language in output (rate/usage limit, quota, resets at) | LEAD suggests `agentteam off <agent> 5h` (weekly: 7d) and reroutes. |
| Validate commands fail | Do not claim success. Report failure + hypothesis. |
| `agentteam verify` reports SCOPE VIOLATION | Reject the branch; LEAD re-briefs with corrected scope; a violating diff is never merged as-is. |
| Worker lock busy ("already running a task") | Wait or `agentteam status`; abort a stray background run with `agentteam kill <task>`. |
| Stale index.lock after a killed run | Cleared automatically at the next `agentteam run`; if git still complains, remove `<gitdir>/index.lock` by hand. |
| Blocked on missing contract/file | I2/I6: flag, don't fix; wait. |
| Task file ambiguous | LEAD: rewrite it. WORKER: state the ambiguity and the interpretation chosen; prefer the narrower reading. |
| Merge conflict on integration | OWNER decision; LEAD proposes resolution order; nobody force-merges. Routine prevention: `agentteam sync` after every merge cycle. |

## 8. REFERENCES

- Role cards: `MASTER.md` (lead), `WORKER.md` (worker) — override this doc.
- Owner playbooks: `coord/docs/ai-project-setup-playbook.md`,
  `coord/docs/ai-full-build-recipe.md` — define working style (dev/main
  model, verified milestones, evaluation-first, docs upkeep).
- Human documentation: docs/HANDBOOK.md, docs/MASTER-PLAN.md,
  docs/SETUP.md in the agentteam docs repository.
