# The worked example — every feature in one sitting

This is a real, replayable transcript of **every Frugal Flock feature** run
back-to-back against a toy Python project. Nothing here is mocked *in the
machinery* — init, locks, hooks, verify, race, sabotage, the ledger: all
real. The only stand-ins are the AI agents themselves, so the whole tour
costs **zero quota** and about 20 seconds.

Replay it yourself anytime:

```bash
bash examples/demo.sh /tmp/agentteam-demo
```

(Prerequisite: `bash frugal-flock-install.sh` once, and `frugal-flock selftest`
green.)

---

## The trick: a stand-in fleet

Frugal Flock reads agent commands from `coord/agents.conf` — the
**project-scoped override** of the global config. The demo project
carries five stand-ins there, so the global conf with your real
subscription CLIs stays untouched:

```text
# DEMO stand-ins — swap these lines for your real fleet and nothing else changes.
# alpha/beta "do the work" by executing the task file's embedded simulate-block:
alpha=bash -c 'sed -n "/<!-- simulate/,/simulate -->/p" "$TASKFILE" | sed "1d;\$d" | bash -s && echo ok'
beta=...same...
# slow: a long-running agent, for the background/tail/kill drill
slow=bash -c 'echo starting long analysis; sleep 30; echo ok'
# critic: reviewer stand-in for `frugal-flock review`
critic=bash -c '...prints canned findings + VERDICT: APPROVE...'
# gamma: saboteur stand-in — hunts the freshest merge with a failing test
gamma=bash -c '...writes tests/test_sabotage.py, commits it...'
```

`alpha` and `beta` "do the work" by executing a `<!-- simulate … -->`
block hidden at the bottom of each demo task file — the machinery cannot
tell the difference between that and a real AI. Swap these five lines for
your real fleet (`claude`, `codex`, `agy`, `opencode`, `grok` — all
subscription **logins**, never API keys) and the exact same commands run
the real thing.

The project: `greeter`, one `greet.py`, one test file, a CHANGELOG.

---

## Act 1 — init refuses while secrets are tracked

The demo deliberately commits a `.env` with a token, then runs init:

```text
$ frugal-flock init alpha beta gamma slow
  .env
frugal-flock: possible secrets tracked in git (above) — untrack/gitignore them
first, or rerun with AGENTTEAM_ALLOW_SECRETS=1
```

Workers run auto-approved, so tracked secrets would be copied into every
worktree. init refuses until it's fixed (`git rm --cached .env`,
gitignore it). Then:

```text
$ frugal-flock init alpha beta gamma slow
project root : ~/code/greeter
base branch  : dev   (override: edit coord/base)
master       : ~/code/greeter/repo  (open your master CLI here)
workers      : alpha beta gamma slow
guard hooks  : worker worktrees commit only on agent/<w>, never push
```

## Act 2 — roll call and smoke

```text
$ frugal-flock agents
  alpha        OK       on
  beta         OK       on
  slow         OK       on
  critic       OK       on
  gamma        OK       on

$ frugal-flock smoke
  alpha        OK
  beta         OK
  slow         OK
  critic       OK
  gamma        OK
```

Smoke runs each agent once from a **neutral folder** (no repo, no role
cards) and checks the reply actually says "ok" — the 30-second drill
after any CLI update.

## Act 3 — a feature task, the machine-checkable way

`coord/tasks/T1-alpha.md` asks for a polite greeting mode. The two
conventions that make the gate mechanical:

```markdown
## Allowed scope
- greet.py
- tests/test_greet.py

## Validate
$ python3 -m unittest discover -s tests -t . -v
```

Every `- path` line is an enforced scope pattern; every `$ command` line
gets re-run by verify. Dispatch and check:

```text
$ frugal-flock run alpha T1-alpha
[alpha <- alpha] running task 'T1-alpha' (timeout 3600s), log: …/T1-alpha.log
exit=0 duration=0s — report: …/coord/reports/T1-alpha.md
next: frugal-flock verify alpha T1-alpha   then: frugal-flock diff alpha

$ frugal-flock verify alpha T1-alpha
== verify alpha / T1-alpha ==
scope    : OK (2 pattern(s))
validate : 1/1 passed
  PASS  $ python3 -m unittest discover -s tests -t . -v
changes  : commits=1, paths touched=3
verdict  : PASS
```

The receipts, then a **rival vendor's opinion** (`critic` reviews
`alpha`'s diff — it gets the task order + diff in one prompt, no file
access):

```text
$ frugal-flock diff alpha --stat
== committed vs dev ==
 changelog.d/T1.md   | 1 +
 greet.py            | 4 +++-
 tests/test_greet.py | 3 +++

$ frugal-flock review alpha T1-alpha critic
1. NIT greet.py: docstring could mention the polite flag.
Scope respected; tests exercise the change; no blockers.
VERDICT: APPROVE
```

Note `changelog.d/T1.md`: workers write **changelog fragments**, never
CHANGELOG.md itself — the one shared file that used to guarantee merge
conflicts. The human gate closes the act: run the tests yourself, merge,
then re-base every workshop:

```text
$ git merge --no-ff agent/alpha -m "merge T1: polite mode"
$ frugal-flock sync
  alpha          fast-forwarded to dev
  beta           fast-forwarded to dev
  gamma          fast-forwarded to dev
  slow           fast-forwarded to dev
```

## Act 4 — the guard hooks say no

Inside a worker worktree, a commit on any branch but its own is
physically rejected:

```text
$ git switch -c evil-experiment && git commit -m "off-branch commit"
agentteam guard: worker 'alpha' must commit on agent/alpha (currently on: evil-experiment)
```

(A matching pre-push hook stops workers pushing at all.)

## Act 5 — a worker leaves its lane; verify catches it

T2 allows `tests/test_edge.py` only. The worker adds the test — and
"helpfully" edits `greet.py` on the way through. The report claims
success; the machine disagrees:

```text
$ frugal-flock verify beta T2-beta
== verify beta / T2-beta ==
scope    : VIOLATION — out-of-scope changes:
             greet.py
validate : 1/1 passed
changes  : commits=1, paths touched=2
verdict  : FAIL
```

Rejected. The owner wipes the branch (`git -C ../wt/beta reset --hard
dev`); the foreman re-briefs as T2b. **This is the system working** — a
lying report died at the gate without anyone reading a diff.

## Act 6 — background runs: the lock, tail, kill

```text
$ frugal-flock run -b slow T3-slow
started in background — poll: frugal-flock status   live: frugal-flock tail T3-slow   abort: frugal-flock kill T3-slow

$ frugal-flock status
== workers (review queue vs dev) ==
  alpha          [agent/alpha]  unreviewed commits: 0   uncommitted files: 0
  slow           [agent/slow]   unreviewed commits: 0   uncommitted files: 0     << RUNNING
== running ==
  T3-slow (background, pid 21656) — tail: frugal-flock tail T3-slow   abort: frugal-flock kill T3-slow

$ frugal-flock run slow T3-slow
frugal-flock: worker 'slow' is already running a task (frugal-flock status)

$ frugal-flock tail T3-slow
starting long analysis

$ frugal-flock kill T3-slow
killed 'T3-slow' (session 21656) — partial work may sit uncommitted in the worktree
```

One run per worker (the lock), live logs, and a kill that takes the
whole session — including the agent under `timeout`.

## Act 7 — the bake-off

Same task, two workers, in parallel; isolation makes it free:

```text
$ frugal-flock race T4 alpha beta
race on. compare: frugal-flock verify/diff per worker — merge exactly one winner, reject the rest.

$ frugal-flock status        # the review queue fills
  alpha          [agent/alpha]  unreviewed commits: 1
  beta           [agent/beta]   unreviewed commits: 1

$ frugal-flock diff alpha --stat          $ frugal-flock diff beta --stat
 greet.py | 4 ++++                      changelog.d/T4.md   | 1 +
                                        greet.py            | 4 ++++
                                        tests/test_greet.py | 6 ++++++
```

Both verify PASS; beta shipped the same function **plus a real test and
the fragment** — beta wins. Merge one, reset the other, sync. The race
lands in the ledger as head-to-head data for the scorecard.

## Act 8 — the saboteur seat finds a real bug

T1's polite mode hid a genuine defect: it returns
`name.capitalize()`, which mangles "McDonald" into "Mcdonald". Every
existing test passed anyway — they only used lowercase names. Spare
quota goes hunting:

```text
$ frugal-flock sabotage gamma
syncing 'gamma' so the saboteur sees the latest merged work:
  gamma          fast-forwarded to dev
saboteur dispatched: SAB-20260719-221927-gamma

# its report:
### committed diffstat vs dev
 tests/test_sabotage.py | 11 +++++++++++
SUMMARY: 1 finding — polite mode rewrites the name

# the failing test, run against dev:
Ran 4 tests in 0.001s
FAILED (failures=1)
```

A bug the whole green test suite missed, exposed by one failing test —
the launcher-bug lesson, institutionalized.

## Act 9 — bench and the red button

```text
$ frugal-flock off alpha 5h
agent 'alpha' OFF — auto-on in 300m
$ frugal-flock run alpha T5-alpha
frugal-flock: agent 'alpha' is OFF (auto-on in 300m) — reassign the task or: frugal-flock on alpha
$ frugal-flock on alpha

$ frugal-flock stop
STOP set — new runs blocked (running tasks finish or hit timeout)
$ frugal-flock run alpha T5-alpha
frugal-flock: STOP is active (frugal-flock resume to clear)
$ frugal-flock resume
```

## Act 10 — the fix task closes the loop

T5 fixes the saboteur's finding, corrects the old test that had encoded
the bug as truth, and adopts the sabotage test into the suite:

```text
$ frugal-flock run alpha T5-alpha && frugal-flock verify alpha T5-alpha
scope    : OK (3 pattern(s))
validate : 1/1 passed
verdict  : PASS
$ git merge --no-ff agent/alpha -m "merge T5: saboteur finding fixed"
$ frugal-flock sync
```

## Act 11 — the ledger remembers everything

`coord/reports/ledger.jsonl`, one JSON event per line — the machine twin
of the human reports, ready for the scorecard:

```text
{"event":"verify","ts":"…","task":"T2-beta","worker":"beta","scope":"VIOLATION",…,"verdict":"FAIL"}
{"event":"race","ts":"…","task":"T4","workers":"alpha beta"}
{"event":"run","ts":"…","task":"T4-beta","worker":"beta","exit":0,"duration_s":0,"commits":1,"files":3,…}
{"event":"run","ts":"…","task":"SAB-20260719-221927-gamma","worker":"gamma",…}
{"event":"verify","ts":"…","task":"T5-alpha","worker":"alpha","scope":"OK",…,"verdict":"PASS"}
```

And the final state of the project tells the whole story on its own:

```text
$ git log --oneline
0b5fd80 merge T5: saboteur finding fixed
3d07a7f T5: stop mangling names in polite mode
94b812f merge T4: farewell (beta wins the race)
a19f10f T4: farewell() + test + fragment
ce4baf4 merge T1: polite mode
2d9864f T1: polite greeting mode
78696c5 untrack .env, ignore it
79e572b oops: token in git

$ ls changelog.d/        # fragments waiting for the release roll-up
T1.md  T4.md  T5.md

$ python3 -m unittest discover -s tests -t .
OK
```

---

## The scoreboard of this sitting

| Feature | Where it showed up |
|---|---|
| Secrets preflight | init refused the tracked `.env` |
| Project-scoped agents.conf | the whole stand-in fleet |
| init + worktrees + role cards | Act 1 |
| Guard hooks (branch / no-push) | the rejected `evil-experiment` commit |
| agents / smoke | Act 2 |
| Machine-checkable task files | `- path` scope, `$ ` Validate lines |
| run + duration + verdict + report | T1 |
| verify PASS / VIOLATION / empty-diff | T1 pass, T2 caught |
| diff (receipts) | T1, T4 |
| Cross-vendor review | critic on T1: VERDICT: APPROVE |
| Changelog fragments | changelog.d/T1,T4,T5 |
| Human gate + merge + sync | after T1, T4, T5 |
| Background -b, status queue, lock, tail, kill | T3 |
| race (bake-off) | T4: beta wins |
| sabotage (saboteur seat) | SAB-* finds the capitalize bug |
| off/on bench, STOP/resume | Act 9 |
| ledger.jsonl | Act 11 |
| selftest | run before the demo (18 checks, green) |

Swap five conf lines for your real fleet, and this exact choreography is
your working day.
