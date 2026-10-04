# Frugal Flock Protocol — system specification for AI agents

Audience: AI agents (lead or worker) operating inside a Frugal Flock project.
Status: normative. If your role card (MASTER.md / WORKER.md) conflicts with
this document, the role card wins. The human owner (Daniel) outranks both.

## 1. SYSTEM

Frugal Flock coordinates one interactive LEAD session and N headless WORKER
runs from different AI CLIs (claude, codex, agy/antigravity, grok,
opencode) on one shared git repository. Isolation is per-worker git
worktrees. Coordination is plain files. Integration is human-gated merges.
Execution boundary: `trusted_host`. Configured agent commands run with the
owner's host access; worktrees and temporary directories are coordination
mechanisms, not OS sandboxes.

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
| `coord/reports/<task>.md` | Append-only run history per task | Frugal Flock tooling |
| `coord/reports/<task>.log` | Latest run's full output (overwritten) | Frugal Flock tooling |
| `coord/reports/ledger.jsonl` | Append-only machine ledger: one JSON object per event | Frugal Flock tooling |
| `coord/reports/<task>.review.*/` | Raw reviewer stdout and stderr, one folder per review | Frugal Flock tooling |
| `coord/results/<w>/<task>.json` | Structured result (schema 1), replaced atomically under the worker lock | Frugal Flock tooling |
| `coord/handoffs/<w>/<task>/` | One new context packet per `handoff`; earlier packets are kept | Frugal Flock tooling |
| `coord/blockers.md` | Blocker notes | anyone, APPEND only |
| `coord/STOP` | If present: all new runs refused | OWNER |

Transient control files (tooling-owned, never edit): `coord/.locks/<w>.lock`
(one run per worker) and `coord/reports/<task>.pid` (background run's
process id, removed on exit).

Data-source rule: historical analysis MUST read `reports/*.md` (append-only,
all runs) or `ledger.jsonl` (append-only, machine-readable). `*.log` holds
only the latest run and MUST NOT be used as history.

Timing rule: `duration_s` is measured on a monotonic clock and therefore
excludes time the machine spent asleep; `wall_s` is the wall-clock elapsed
time and `suspended` is 1 when the two diverge by more than a minute. A
suspended run's elapsed time is meaningless — `frugal-flock score` excludes it
from averages, and any other analysis MUST do the same.

Enforcement at init: `frugal-flock init` refuses to scaffold while likely
secret files are tracked (override: AGENTTEAM_ALLOW_SECRETS=1), and
installs git hooks: a worker worktree can commit only on its own
`agent/<w>` branch and can never push, and every merge into the base
branch is recorded as a ledger `merge` event (post-merge hook).

## 3. DATA FORMATS

Report run-block (appended to `coord/reports/<task>.md` per run):

```text
## run <ISO8601 timestamp> — worker=<worker> agent=<agent> exit=<int> duration=<int>s task_sha=<sha256>
[!! post-run snapshot failed — exit=<int> recorded; structured result unbound and not ready]
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

Verify block (appended by `frugal-flock verify`):
`### verify <ts> — worker=<w> scope=<OK|VIOLATION|UNCHECKED>
validate=<passed>/<run> empty=<0|1> verdict=<PASS|FAIL|INCOMPLETE>` plus
out-of-scope paths, individual reasons, and per-command results. PASS exits
0 only with scope and at least one passing Validate command, with existing
safeguards satisfied. Missing scope/checks exits 2 (INCOMPLETE); actual
failures take precedence and exit nonzero, normally 1. No waiver is provided.
Index entries flagged assume-unchanged or skip-worktree make verify exit 2
before any verdict, because Git diff/status would omit their edits.

Ledger events (`coord/reports/ledger.jsonl`, one JSON object per line):

```text
{"event":"run","ts":…,"task":…,"worker":…,"agent":…,"exit":n,"duration_s":n,
 "wall_s":n,"suspended":0|1,"snapshot_failed":0|1,
 "commits":n,"files":n,"insertions":n,"deletions":n,"uncommitted":n,"wall":0|1}
{"event":"verify","ts":…,"task":…,"worker":…,"scope":"OK|VIOLATION|UNCHECKED",
 "validate_run":n,"validate_failed":n,"commits":n,"empty":0|1,"verdict":…}
{"event":"review","ts":…,"task":…,"worker":…,"reviewer":…,"exit":n}
{"event":"race","ts":…,"task":…,"workers":"w1 w2 …"}
{"event":"merge","ts":…,"worker":…,"subject":"<merge commit subject>"}
```

Structured result (`coord/results/<w>/<task>.json`, Python 3 stdlib helper):

```text
schema_version 1, worker, task, updated_at, current_revision
revision    candidate_commit, base_commit, task_sha256, worktree_sha256
            (index + tracked + nonignored untracked contents, not just names)
process     state not_run|running|succeeded|failed, exit_code, revision
            [post_run_snapshot: "failed" — always stale, never ready]
validation  state not_run|passed|failed|incomplete, scope, checks_run,
            checks_failed, reasons, revision
review      state not_run|approved|changes_requested|unknown|failed,
            reviewer, process_exit_code, material_complete, reasons, revision
human       {"state": "pending"}        integration {"state": "not_attempted"}
stale, ready_for_human_review
```

Every section records the revision it was produced at. A new run resets
validation and review; a new verify resets review. `stale` is true when any
evidence revision differs from the current one (commit, base, task file,
index, tracked or nonignored untracked content). `ready_for_human_review`
needs a succeeded process, passed validation and approved review, all at the
current revision and not stale. It is never human acceptance or permission
to integrate. `frugal-flock result` prints this JSON only, recomputed against
the current worktree; a missing or malformed file fails closed (exit 2), and
old report text is never backfilled as structured evidence.

Loop brake: after two failed attempts on a task ID, `run` refuses before
calling a provider (exit 2), shared across workers. Nonzero exits, failed or
incomplete verification and interrupted tracked starts count once per
attempt. Repeated verification does not add failures. Only the owner may
use `frugal-flock allow-retry TASK` to grant one invocation; grants do not
accumulate or erase failures. State is local in `coord/retries/TASK/`,
locked across workers; malformed or symlink state fails closed. Tracking
starts with this source version, without inferring historical outcomes.
Workers must not grant themselves retries. This is trusted-host coordination,
not an access-control boundary or provider-quota approval.

Review gate: `frugal-flock review` needs current passed validation. Its
material is the task file plus the full committed diff against base. It is
refused (exit 2, review recorded `unknown`, `material_complete` false) for
staged, unstaged or untracked work, binary changes, non-UTF-8 data, more than
300000 bytes, or flagged index entries; nothing is ever clipped. The
reviewer's stdout must hold exactly one standalone `VERDICT: APPROVE` or
`VERDICT: REQUEST-CHANGES` line; stderr never counts. Exits: 0 approved;
1 changes requested or reviewer process failure (timeout is 124); 2 unknown
verdict, incomplete material, stale evidence, or a candidate that changed
during the review.

Handoff packet: `coord/handoffs/<w>/<task>/<timestamp>-<id>/` holds
`task.md`, `result.json`, `revision.json`, `changed-files.json` and
`HANDOFF.md`, published by an atomic rename. It is refused while the worker
lock is held, and is not published if the candidate changes meanwhile. It is
context for the same checkout, NOT a backup, restore or provider migration:
uncommitted and untracked contents stay in the source worktree. Credentials,
agents.conf, ignored files and raw logs are never copied; task text may be
sensitive, so review a packet before sharing it.

Availability (`frugal-flock agents --json`, local only, never executes a
configured command or probes sign-in or quota):

```text
{"schema_version":1,"agents":[{"name":…,"binary":{"value":…,
 "present":true|false|null},"bench":{"off":…,"operator_retry_at":…},
 "authentication":"unknown","capacity":"unknown",
 "execution_boundary":"trusted_host"}]}
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

## 4. THE `frugal-flock` COMMANDS (local shell tool)

To be explicit: these are subcommands of the local `frugal-flock` shell
script. No AI-provider API is involved anywhere in this system — every
agent is an official CLI running under its own subscription LOGIN
(cached on the machine), never an API key.

```text
frugal-flock init [w1 w2 ...]     scaffold worktrees + coord (idempotent);
                               secrets preflight; guard hooks
frugal-flock agents [--json]      list agents: binary present, on/off state;
                               --json = schema 1, local only (see §3)
frugal-flock smoke                one tiny live call per agent from a neutral
                               dir (still trusted_host); OK / WARN (reply
                               lacks "ok") / FAIL
frugal-flock selftest             full-loop rehearsal in a sandbox repo with
                               mock agents; zero quota; nonzero on failure
frugal-flock run [-b] <w> <task>  execute coord/tasks/<task>.md as worker <w>
                               in wt/<w>; -b = background; per-worker lock;
                               writes report+log+ledger+structured result;
                               a failed worker's own exit code wins
frugal-flock tail [task]          follow a run's live log (default: newest)
frugal-flock kill <task>          terminate a background run (whole session,
                               including the agent under `timeout`)
frugal-flock report <task> [n]    print the last n (default 60) lines of a
                               task's append-only report
frugal-flock version              installed tool version + config path
frugal-flock verify <w> <task>    machine gate assist: diff vs the task's
                               "- path" scope lines + run its "$ " Validate
                               lines in the worktree + commit sanity;
                               appends verify block and records validation;
                               exit 0 PASS, 1 FAIL (violation, failed check,
                               empty diff, tampered task), 2 INCOMPLETE (no
                               scope or no Validate lines) or unsupported
                               worktree state
frugal-flock diff <w> [--stat]    changes on agent/<w> vs base: committed and
                               uncommitted, separately
frugal-flock review <w> <task> [agent]  cross-vendor review: a DIFFERENT agent
                               judges task order + committed diff from a
                               neutral dir; gated and parsed as in §3;
                               exit 0 approved, 1 changes/failure, 2 unknown
frugal-flock result <w> <task>    structured result JSON on stdout only; no
                               provider call; exit 2 if missing, malformed or
                               the worktree state is unsupported
frugal-flock handoff <w> <task>   new same-checkout context packet under
                               coord/handoffs (see §3); not a backup
frugal-flock sync [w]             bring base's merged work into worker
                               branches (ff when fully merged, merge
                               otherwise; skips dirty/running; aborts and
                               reports on conflict)
frugal-flock race <task> <w1> <w2> [...]  copy <task>.md to <task>-<w>.md per
                               worker and dispatch all in background;
                               OWNER merges at most one winner
frugal-flock sabotage <w>         saboteur seat: sync <w>, generate a SAB-*
                               task from the template, dispatch background
frugal-flock score [root]         per-worker scorecard from ledger.jsonl:
                               runs, ok/fail, walls, verify rate, merges,
                               avg duration
frugal-flock doctor               preflight the project: base branch present,
                               agent binaries, python3, worktree health,
                               stale pidfiles, disk headroom; nonzero on error
frugal-flock new <url> [name] [w...]  bootstrap a project: clone -> dev branch
                               -> init -> copy $CONF/playbooks/*.md into
                               coord/docs/
frugal-flock status               off-agents, tasks, reports, review queue
                               (unreviewed commits per worker), running jobs
frugal-flock off <agent> [dur]    bench agent (dur: 30m|5h|7d; absent=manual);
                               run refuses benched agents; expiry auto-clears
frugal-flock on <agent>           un-bench
frugal-flock stop | resume        create/remove coord/STOP (global run gate)
```

Environment: `AGENTTEAM_TIMEOUT` (seconds, default 3600) caps each run;
`AGENTTEAM_VERIFY_TIMEOUT` (default 900) caps each Validate command;
`AGENTTEAM_REVIEW_TIMEOUT` (default 900) caps a review call.
`AGENTTEAM_AUTO_OFF=1` auto-benches an agent 5h when a FAILED run's log
matches limit-language patterns (suppressed when the task text itself
mentions limits and the run succeeded). `AGENTTEAM_AUTO_VERIFY=1` makes
every run append its own verify verdict after finishing. If the worker
succeeds but verification fails or is incomplete, run returns the
verification's nonzero exit; a failed worker retains its own exit code.
`AGENTTEAM_AUTO_SYNC=1` fast-forwards a worker onto the base branch
before a run when the worktree is clean, so it never builds against
stale code (otherwise `run` warns and leaves it to the operator).
`AGENTTEAM_ALLOW_SECRETS=1` overrides the init secrets preflight. Python 3
(standard library only, nothing downloaded) is required by run, verify,
review, smoke, agents, result and handoff. Unsupported worktree states fail
closed with exit 2: assume-unchanged or skip-worktree index flags (verify,
review, handoff); FIFOs, devices, sockets, nested repositories and submodules
(run, verify, review, result, handoff). Agent
invocation templates live in `~/.config/agentteam/agents.conf` (project
override: `coord/agents.conf`).

Fleet intelligence: `frugal-flock score` (ledger-based, always available)
and the companion tool `myapp <project-root>` (full scorecard incl.
pre-ledger history from reports/*.md). LEAD SHOULD consult one of them
when assigning tasks.

## 5. LIFECYCLE

1. OWNER states intent to LEAD.
2. LEAD reads coord/docs/*, repo docs (AGENTS.md router, docs/ai/), and
   `frugal-flock agents`; produces a task breakdown; WAITS for OWNER "go".
3. LEAD freezes shared contracts (types/schemas/fixtures) as commits on
   the base branch BEFORE dispatching dependent tasks; task files cite
   contract paths @ sha.
4. LEAD dispatches via `frugal-flock run`; parallel tasks MUST have disjoint
   Allowed-scope sets (changelog.d/ exempt — one file per task); at most
   one task per cycle may modify dependency manifests (package files,
   lockfiles, migrations). Race tasks are the sanctioned exception to
   disjointness: several workers, same scope, at most one merge.
5. WORKER executes its task file exactly: modifies only Allowed-scope
   paths, runs Validate, writes its changelog fragment, commits only files
   it changed (never blanket staging), ends output with the Report
   sections.
6. LEAD verifies, machine first: `frugal-flock verify` (scope + Validate +
   commit sanity), then reads the report and `frugal-flock diff`; for risky
   diffs also `frugal-flock review`. `frugal-flock result` shows whether that
   evidence is still current. Reports are claims; diffs, verify verdicts and
   logs are ground truth.
7. OWNER merges accepted branches into base (`git merge --no-ff`).
   Acceptance gate: verify PASS, clean build, tests green, smoke run,
   changelog fragment where the repo keeps a changelog. After the merge
   cycle, LEAD runs `frugal-flock sync` so all workshops rebuild on the new
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
      backing it is treated as unverified. `frugal-flock verify` is the
      mechanical floor of that evidence, not its ceiling.
- I11 Workers never edit CHANGELOG.md; changelog entries are per-task
      fragments in changelog.d/, rolled up at release by LEAD/OWNER.
- I12 A run that claims success with an empty diff (no commits, no
      uncommitted changes) is treated as FAILED.
- I13 `ready_for_human_review` is never human acceptance or permission to
      merge; only OWNER accepts and integrates.
- I14 Evidence is bound to a revision. After any change to commit, base,
      task file or worktree content, earlier verify/review results are
      stale: verify again, then review again.
- I15 A handoff packet is context for the same checkout, not a backup,
      restore or provider migration.
- I16 Worktrees are not sandboxes. The execution boundary is the trusted
      host.

## 7. FAILURE PROTOCOL

| Condition | Required behavior |
|---|---|
| Auth/token error in output | Report it verbatim; OWNER re-logins the CLI; task is rerunnable. |
| Limit language in output (rate/usage limit, quota, resets at) | LEAD suggests `frugal-flock off <agent> 5h` (weekly: 7d) and reroutes. |
| Validate commands fail | Do not claim success. Report failure + hypothesis. |
| `frugal-flock verify` reports SCOPE VIOLATION | Reject the branch; LEAD re-briefs with corrected scope; a violating diff is never merged as-is. |
| `frugal-flock verify` reports INCOMPLETE (exit 2) | The task has no scope or no Validate lines: LEAD adds them. There is no waiver. |
| Unsupported worktree state (flagged index entries, FIFO, device, socket, nested repository, submodule) | Clear it (`git update-index --no-assume-unchanged --no-skip-worktree`, `git sparse-checkout disable`, or remove the file), then rerun the command. |
| Run reports "post-run snapshot failed" | The worker's real exit is recorded but the result stays stale. Fix the worktree, then run the task again. |
| `frugal-flock result` shows stale evidence | Verify again, then review again. Never reuse old evidence. |
| Review refused as incomplete material | Commit all work. Binary, non-UTF-8 or oversized changes need manual inspection. |
| Worker lock busy ("already running a task") | Wait or `frugal-flock status`; abort a stray background run with `frugal-flock kill <task>`. |
| Stale index.lock after a killed run | Cleared automatically at the next `frugal-flock run`; if git still complains, remove `<gitdir>/index.lock` by hand. |
| Blocked on missing contract/file | I2/I6: flag, don't fix; wait. |
| Task file ambiguous | LEAD: rewrite it. WORKER: state the ambiguity and the interpretation chosen; prefer the narrower reading. |
| Merge conflict on integration | OWNER decision; LEAD proposes resolution order; nobody force-merges. Routine prevention: `frugal-flock sync` after every merge cycle. |

## 8. REFERENCES

- Role cards: `MASTER.md` (lead), `WORKER.md` (worker) — override this doc.
- Owner playbooks: `coord/docs/ai-project-setup-playbook.md`,
  `coord/docs/ai-full-build-recipe.md` — define working style (dev/main
  model, verified milestones, evaluation-first, docs upkeep).
- Human documentation: docs/HANDBOOK.md, docs/MASTER-PLAN.md,
  docs/SETUP.md in the Frugal Flock docs repository.
