# Unio — The Complete Guidebook

> **Note for document tools / AI converters:** this file is plain, standard
> Markdown. Headings `#`/`##`/`###` map to Word's Title / Heading 1 /
> Heading 2 styles. Fenced code blocks (opened and closed with triple
> backticks) are terminal text — render them in a monospace font. Tables
> are simple pipe tables. There is no HTML and no special syntax anywhere
> in this document.

**Covers Unio 0.5.0 source, including the owner-accepted M1 quality changes · written 2026-07-19, updated 2026-10-05 · for the complete beginner**

The rename is not yet a published release or global installation. This
workspace builds it using the legacy installed Frugal Flock 0.4.0; the
owner must approve switching that global installation separately.

This is the one book that explains everything: what Unio is, how to
install it, how to use every command step by step, how to fix every common
problem, and what every word means. You do not need a programming
background — every technical term is explained the first time it appears
and again in the Glossary (chapter 18). If you only have five minutes,
read chapter 2 and the Cheat Sheet (chapter 19).

---

## 1. How to read this book

- **Never used Unio before?** Read chapters 2–4, then do chapter 5
  with a real terminal open. Chapters 6–9 are your daily life. Come back
  to the rest when you need it.
- **Something is broken?** Go straight to chapter 14 (Troubleshooting).
- **Forgot a command?** Chapter 15 lists every command with an example.
- **Forgot a word?** Chapter 18 is the glossary.

Text that looks `like this` is something you type into the terminal, a
file name, or exact text a program prints. Blocks that look like this:

```text
$ unio status
```

are terminal sessions — the `$` means "you type what follows".

---

## 2. What Unio is — and what it is not

### 2.1 The idea in one paragraph

Unio turns five separate AI coding subscriptions — Claude, Codex
(ChatGPT), Antigravity (Google), Grok Build (X), and OpenCode — into one
coordinated software team on your Ubuntu machine. One AI acts as the
**foreman** (it plans work, writes work orders, inspects results). The
others act as **workers** (each builds its assigned piece in its own
isolated copy of the project). And **you** are the owner — the only one
who can accept work into the real codebase. Unio itself is the
office they all work in: about a thousand lines of scripting that handles
workshops, work orders, reports, receipts checking, and safety switches.
The intelligence is rented from your subscriptions; Unio only
coordinates it.

### 2.2 What it is NOT (important)

- **It is not an AI.** It contains no AI and calls no AI service itself.
- **It uses no API keys — ever.** Every agent is an official command-line
  program (`claude`, `codex`, `agy`, `opencode`, `grok`) running under
  its own subscription **login**, cached on your machine after you sign
  in once. An "API key" would mean paying per request; a login means your
  flat monthly subscription. Unio is built entirely on logins.
- **It does not push, deploy, or release anything.** Only you do those.

### 2.3 The three safety principles

Everything in the design comes from three rules:

1. **Isolation.** Every worker gets its own complete copy of the project
   (a *git worktree* — see Glossary) pinned to its own branch. Two
   workers normally edit separate files. These workshops are coordination
   boundaries, not OS sandboxes: configured commands retain host access
   and can reach other worktrees or files. Review and scope checks judge
   changes; they do not restrict filesystem access.
2. **Receipts over reports.** Every run produces a report (the agent's
   own claim) and a diff (the exact line-by-line truth). Rule one of
   operating this system: **reports can lie, diffs can't.** Since v0.3,
   a machine check (`unio verify`) reads the receipts for you first.
3. **One human gate.** Nothing enters the real codebase without you
   merging it. The foreman recommends; you decide. This is not a
   formality — it is the entire safety model.

### 2.4 The cast

| Role | Who | What they do | What they may never do |
|---|---|---|---|
| **Owner** | You | Approve plans, read diffs, merge, release | — |
| **Foreman** (also called *lead* or *master*) | An interactive AI session in `repo/` | Plan, write task files, dispatch workers, verify results, recommend merges | Write feature code; merge |
| **Worker** | A headless AI run in `wt/<name>/` | Execute exactly one task file, commit in its own worktree, report | Leave its folder, switch branches, push, touch files outside its task's scope |

"Headless" means the AI runs once, non-interactively: it gets the task
text, works, prints its output, and exits. Workers have **zero memory**
between runs — that is why task files must contain everything they need.

### 2.5 The loop — how every piece of work flows

```text
 YOU:     "I want X"  (two sentences, plain English)
   |
 FOREMAN: studies the project, proposes a task breakdown, waits for your "go"
   |          (you read the task files, then say: "go")
 FOREMAN: dispatches workers, in parallel, each in its own workshop
   |
 WORKERS: build, test, commit on their own branch, report
   |
 FOREMAN: machine-checks first (unio verify), reads the diffs, recommends
   |
 YOU:     read the diff yourself -> merge what passes -> reject what doesn't
```

Rejection is normal and healthy. A long streak with zero rejections means
your gate has gone soft — not that the team has become perfect.

---

## 3. What lives on disk

### 3.1 The project layout

`unio init` (or `unio new`) builds this next to any repository
clone:

```text
<project>/
├── repo/            The real project, on the base branch (normally dev).
│   │                YOU and the FOREMAN work here. Nobody else.
│   ├── MASTER.md    The foreman's standing orders — symlinked as
│   │                CLAUDE.md, AGENTS.md, GEMINI.md so any AI brand
│   │                automatically reads its role.
│   └── changelog.d/ Changelog fragments, one small file per task.
│                    Workers never edit CHANGELOG.md itself.
├── wt/              The workshops ("wt" = worktrees).
│   ├── codex/       A full project copy on branch agent/codex, with its
│   ├── antigravity/ own WORKER.md role card. Same pattern per worker.
│   ├── opencode/    Workers never leave their own folder and never
│   └── grok/        touch the base branch.
└── coord/           The office. Deliberately OUTSIDE git.
    ├── base         One word: the integration branch name (dev).
    ├── agents.conf  OPTIONAL project-specific agent commands (overrides
    │                the global config — used e.g. for practice fleets).
    ├── docs/        Your playbooks + the PROTOCOL the AIs must follow.
    ├── board.md     Task board. Only the foreman writes it.
    ├── tasks/       Work orders, one .md file per task (TEMPLATE.md included).
    ├── reports/     Everything the machinery records (see 3.2).
    ├── results/     One JSON result per worker and task (see 3.2).
    ├── handoffs/    Context packets for the next AI (see 7.10).
    ├── blockers.md  "I'm stuck" notes, append-only.
    ├── .locks/      One lock file per worker (machinery-owned; ignore).
    └── STOP         If this file exists, ALL new runs are refused.
```

### 3.2 The data trail

Inside `coord/reports/` you will find, per task:

| File | What it holds | Lifetime |
|---|---|---|
| `<task>.md` | The **report**: one block appended per run (plus verify and review blocks). This is the permanent history. | Append-only, forever |
| `<task>.log` | The full raw output of the **latest** run only. | Overwritten each run |
| `<task>.pid` | Background run's process id. | Removed when the run ends |
| `ledger.jsonl` | The **machine ledger**: one JSON line per event — run, verify, review, race, merge — with durations and change statistics. `unio score` reads this. | Append-only, forever |

Rule: for history, always read the `.md` report or the ledger — never the
`.log`, which only remembers the latest run.

Next to the reports, `coord/results/<worker>/<task>.json` holds the
**current evidence** for one task: the worker process, the validation and
the review, each tied to the exact revision it describes (the commit, the
base, the task file and the files in the workshop). It is rewritten as
the task moves along; `unio result` prints it (section 7.10).
`coord/handoffs/` holds the context packets made by `unio handoff`.

### 3.3 The guard hooks (installed automatically)

`unio init` installs three small git guards into the project:

1. **pre-commit** — inside a worker's workshop, commits are only possible
   on that worker's own `agent/<name>` branch. A worker that wanders onto
   another branch is physically stopped.
2. **pre-push** — workers can never push. Only you push, from `repo/`.
3. **post-merge** — every time YOU merge a branch into the base, a
   `merge` event is written into the ledger automatically. This is where
   the scorecard's "merges" column comes from.

If your repository already has its own hooks, Unio leaves them
untouched and tells you so.

---

## 4. Installation — step by step

### 4.1 What you need

- An Ubuntu machine (a real one, a VM, or WSL).
- `git` installed (`sudo apt install git` if missing).
- Python 3 (`python3 --version`; `sudo apt install python3` if missing).
  Only its standard library is used, for the evidence records — nothing is
  downloaded. Without it, run, verify, review, result, handoff, agents and
  smoke stop with "Python 3 is required before run/review/smoke" before
  any AI is called.
- Your AI subscriptions (any subset of the five works — even one).

### 4.2 Install Unio itself

From your clone of [Unio](https://github.com/danielmevit/unio)
(historically named Frugal Flock and `agentteam-docs`):

```text
$ bash unio-install.sh
$ unio version
Unio 0.5.0 (/home/you/.local/bin/unio)
Small plans. Big ideas.
config: /home/you/.config/unio/agents.conf
```

If the second command says "command not found", your `~/.local/bin`
folder is not on the PATH (the list of folders the terminal searches for
programs). Fix it once:

```text
$ echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
```

The installer creates:

| Path | Purpose |
|---|---|
| `~/.local/bin/unio` | The only installed command |
| `~/.config/unio/agents.conf` | The agent config — **the file you edit** (never overwritten by updates) |
| `~/.config/unio/templates/` | Role cards and task templates stamped into every new project |
| `~/.config/unio/playbooks/` | Drop your standard `ai-*.md` playbooks here once; `unio new` copies them into every project |
| `~/.local/share/bash-completion/completions/unio` | Tab-completion for `unio` (open a new terminal to activate) |

Tab-completion means: type `unio ru<TAB>` and the shell finishes the
command; type `unio run <TAB>` and it lists your workers; then
`<TAB>` again lists your task ids.

### 4.3 Install and log in the five AI CLIs (once each)

Headless runs reuse cached credentials, so each login happens exactly
once. On a machine without a browser, most logins print a URL and a code
that you open in the browser of another computer.

| Agent | Install | Log in | Prove it works |
|---|---|---|---|
| Claude Code | `npm i -g @anthropic-ai/claude-code` | run `claude`, follow the sign-in | `claude -p "say ok"` |
| Codex | `curl -fsSL https://chatgpt.com/codex/install.sh \| sh` | run `codex`, sign in with your ChatGPT account | `codex exec "say ok"` |
| Antigravity | per antigravity.google (the `agy` binary) | run `agy`, sign in with Google (prints URL + code) | `agy -p "say ok"` |
| OpenCode | `curl -fsSL https://opencode.ai/install \| bash` | `opencode auth login` | `opencode run "say ok"` |
| Grok Build | `curl -fsSL https://x.ai/cli/install.sh \| bash` | run `grok`, sign in with X | `grok -p "say ok"` |

You do not need all five. Whatever answers its "say ok" test is a usable
seat; everything else can join later.

### 4.4 The config file: `agents.conf` (the lego box)

`~/.config/unio/agents.conf` has one line per agent:

```text
name=shell command that runs that agent headless
```

For example the Claude line:

```text
claude=claude -p "$(cat "$TASKFILE")" --dangerously-skip-permissions
```

Read it as: "to run agent *claude*, call the `claude` program in print
mode, feed it the task file's text, and let it work without asking for
per-action approval." `$TASKFILE` is filled in by Unio at run time.
Auto-approve gives the configured command host-level permissions. Separate
worktrees and the merge gate help coordinate and review changes, but they
do not contain filesystem damage. Use these defaults only on a trusted
host with workloads and permissions the owner has explicitly accepted.

Rules of the lego box:

- Add or remove agents by adding or removing lines. Five lines ship by
  default; you can run with one or with ten.
- A project can carry its own crew: create `<project>/coord/agents.conf`
  and it overrides the global file for that project only.
- Never edit this file to handle quota problems — that is what
  `unio off` is for (chapter 10).

### 4.5 Prove the whole machine works — before spending any quota

```text
$ unio selftest
== unio selftest — sandbox: /tmp/tmp.XXXX ==
  ok    init scaffolds worktrees + coord
  ok    worker-branch guard hooks installed
  ...
selftest: 27 ok, 0 failed
sandbox removed — all green.
```

selftest builds a throwaway project with **mock agents** (tiny scripts
pretending to be AIs) and rehearses the entire loop — init, run, verify,
scope-violation catching, benching, locks, background runs, kill, merge,
sync, review, score. It costs zero quota and about fifteen seconds. Run
it after every Unio update. If it is green, the machinery works and
any problem you hit later is an agent problem, not a Unio problem —
that distinction is half of all troubleshooting.

Then check the real fleet:

```text
$ unio agents      # is each binary installed? benched or on?
$ unio smoke       # one tiny LIVE call per agent: OK / WARN / FAIL
```

And before you dispatch work in a project, `unio doctor` is the
one-command preflight. It checks the base branch exists, every worker's
binary and config line, each worktree's health (on the right branch,
behind the base, uncommitted leftovers), stale background state, the
guard hooks, and disk headroom — then prints `all clear`, a list of
warnings, or errors you should fix first. It catches the quiet
misconfigurations that would otherwise cost you a wasted run.

`smoke` runs from a neutral folder (so no project files are involved) and
checks each agent actually answers "ok". It is the 30-second drill after
any CLI update or after days away.

### 4.6 Practice everything with zero quota

The repository ships a complete replayable demonstration:

```text
$ bash examples/demo.sh /tmp/unio-demo
```

It builds a toy project with a stand-in fleet and performs every feature
in about twenty seconds — the annotated transcript is `docs/EXAMPLE.md`.
Reading that file after this chapter is the fastest way to *see*
everything this book describes.

---

## 5. Starting a project

### 5.1 The one-command way

```text
$ cd ~/code
$ unio new https://github.com/you/yourproject.git myproj
```

`new` does the whole recipe: clones the repository into `myproj/repo`,
switches to (or creates) the `dev` branch, runs `unio init` with the
default workers, and copies every playbook from
`~/.config/unio/playbooks/` into `myproj/coord/docs/`. It ends by
telling you the two follow-ups it deliberately does not do itself:

```text
remote dev  : when ready:  cd myproj/repo && git push -u origin dev
start       : cd myproj/repo && unio agents
```

You can name the workers too: `unio new <url> myproj codex grok`.

### 5.2 The manual way

```text
$ cd ~/code && mkdir myproj && cd myproj
$ git clone <repo-url> repo && cd repo
$ git checkout dev || git checkout -b dev
$ unio init codex antigravity opencode grok
```

`init` is idempotent — running it again is safe, and `unio init
claude` later adds one more workshop without touching the others.

### 5.3 The secrets preflight

Workers run with auto-approval, and worktrees copy every tracked file.
So `init` **refuses to scaffold** while files that look like secrets
(`.env`, key files, `credentials.json`, …) are tracked in git:

```text
  .env
unio: possible secrets tracked in git (above) — untrack/gitignore
them first, or rerun with UNIO_ALLOW_SECRETS=1
```

The fix takes a minute:

```text
$ git rm --cached .env
$ echo '.env' >> .gitignore
$ git commit -m "untrack secrets"
$ unio init ...
```

Only use the override variable if you know exactly why the match is a
false alarm.

### 5.4 Onboarding an EXISTING project (including production)

Established projects have history, users, and things that must not break.
Three differences from a fresh project:

1. **Clone fresh into the layout** (never move your working copy) — the
   `new` command or the manual recipe above, same as always.
2. **First cycle is study-only.** Open the foreman and give it this
   instead of a feature request:

   ```text
   Read MASTER.md and the playbooks in ../coord/docs/. This is an
   EXISTING production project. Do not plan any feature work yet.
   Study the codebase and produce the docs/ai/ set: START_HERE.md
   (purpose, how to run, current state), DECISIONS.md, GOTCHAS.md.
   Commit that to dev, then give me a one-page summary of what this
   project is, its risk areas, and what kinds of tasks are SAFE to
   delegate first. Wait for my go on everything else.
   ```

   This costs one cycle and pays forever: every future worker inherits an
   accurate map instead of guessing.
3. **The gate tightens.** First tasks are small and reversible (a bug
   fix, missing tests, docs). Never "refactor the core" on cycle one. No
   deploy automation — what reaches production stays a purely human act.

---

## 6. Task files — the heart of the system

A task file is a work order: one Markdown file in `coord/tasks/`, named
`<ID>-<worker>.md` (for example `T7-codex.md`). The foreman writes them;
you read them before saying "go". Workers have no memory, so a task file
must be understandable by a total stranger.

### 6.1 The template, section by section

Copy `coord/tasks/TEMPLATE.md` and fill in:

```markdown
# Task T7 — worker: codex

## Goal
One specific, testable outcome. One task = one concern.

## Context
Everything the worker needs: what the code does now, which files matter,
decisions already made, frozen contracts ("types in src/api/types.ts
@ <sha> — do not change them").

## Allowed scope
- src/feature.py
- tests/test_feature.py

## Constraints
Libraries to use or avoid, style rules, no new dependencies.

## Validate
$ dotnet build -c Release
$ python3 -m unittest discover -s tests

## Done means
Validation passes + changes committed on your branch as "T7: <summary>"
+ changelog.d/T7.md if the repo keeps a changelog.

## Report
End with: SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS /
RISKS / NEEDS-REVIEW
```

### 6.2 The two machine conventions (do not skip this)

Two kinds of lines in a task file are not just prose — the machinery
enforces them:

- **Scope lines.** Under `## Allowed scope`, every line starting with
  `- ` is an enforced pattern. `unio verify` compares the worker's
  actual changes against this list and flags anything outside it.
  - A plain path (`- src/feature.py`) allows exactly that file.
  - A trailing slash (`- tests/`) allows the whole folder.
  - Globs work (`- src/*.py`) and match into subfolders.
  - `changelog.d/` is always allowed automatically.
- **Validate lines.** Under `## Validate`, every line starting with
  `$ ` is a command that `unio verify` re-runs itself inside the
  workshop — each must exit successfully. Prose in that section is fine;
  only `$ ` lines are executed.

Write both precisely and the gate becomes largely mechanical.

### 6.3 Changelog fragments

Shared files cause merge conflicts, and a changelog everyone appends to
is the classic offender. So workers never touch `CHANGELOG.md`. Instead
each task writes one tiny file — `changelog.d/T7.md`, one or two lines —
which is always in scope. At release time the foreman rolls all fragments
into `CHANGELOG.md` (that is allowed: the foreman may edit docs).

### 6.4 What good and bad look like

Bad scope: "the relevant files" (nothing is enforceable).
Good scope: three explicit `- ` lines.

Bad validate: "make sure it works".
Good validate: `$ python3 -m unittest discover -s tests` with the
expected outcome stated in prose above it.

> **Python gotcha (learned from a real run):** use
> `discover -s tests` (or `discover tests`), **not**
> `discover -s tests -t .`. On Python 3.11+ the `-t .` form fails with
> "Start directory is not importable" unless `tests/` contains an empty
> `__init__.py` file. A worker told to run the `-t .` form but not allowed
> to create `tests/__init__.py` will correctly report the task as blocked
> rather than pass — so write the Validate line in the form that just works.

Bad goal: "improve error handling everywhere".
Good goal: "requests to /api/save with an empty body return 400 with a
JSON error instead of crashing; test proves it."

---

## 7. Running work — every step explained

### 7.1 A foreground run

```text
$ unio run codex T7-codex
[codex <- codex] running task 'T7-codex' (timeout 3600s), log: .../coord/reports/T7-codex.log
exit=0 duration=214s — report: .../coord/reports/T7-codex.md
next: unio verify codex T7-codex   then: unio diff codex
```

What happened: Unio checked the STOP switch, the agent's bench
status, and the per-worker lock; warned if the worker's branch had fallen
behind the base (stale code wastes runs — set `UNIO_AUTO_SYNC=1` to
fast-forward it first); cleaned any stale git lock from a previously
killed run; then ran the codex CLI inside `wt/codex/` with the task text,
capped at `UNIO_TIMEOUT` seconds (default 3600 = 1 hour).
When it finished, a run block was appended to the report and one `run`
event to the ledger. The task's stored result (section 7.10) was reset at
the start and now records the worker's exit code. If the workshop could
not be fingerprinted afterwards — for example the worker left a special
file such as a FIFO — the real exit code is still recorded, the result is
marked as not ready, and `run` returns nonzero; remove the file and run
again.

### 7.2 Background runs

Long task? Add `-b` and keep working:

```text
$ unio run -b antigravity T8-antigravity
started in background — poll: unio status   live: unio tail T8-antigravity   abort: unio kill T8-antigravity
```

- `unio status` — the briefing: benched agents, open tasks, recent
  reports, each worker's branch state with a **review queue** count
  (commits not yet merged), a `<< RUNNING` marker, and running jobs.
- `unio tail T8-antigravity` — watch the live log; `Ctrl-C` stops
  watching, not the run. `unio tail` with no task follows the
  newest log.
- `unio kill T8-antigravity` — stop it cleanly. The whole session
  is terminated (including the agent under its timeout wrapper); partial
  work stays uncommitted in the workshop; the pidfile is removed.
- **One run per worker.** Dispatching a second task to a busy worker is
  refused: `worker 'antigravity' is already running a task`. Different
  workers run in parallel freely.

### 7.3 Reading the report

Each run appends a block like this to `coord/reports/<task>.md`:

```text
## run 2026-07-19T14:02:11+02:00 — worker=codex agent=codex exit=0 duration=214s

### git status (branch, staged/unstaged)
## agent/codex
### committed diffstat vs dev
 src/feature.py      | 40 ++++++++++
 tests/test_feature.py | 25 +++++++
### verdict
commits=1 files=2 insertions=65 deletions=0 uncommitted=0
### agent output (tail)
~~~
...the last 60 lines the agent printed...
~~~
```

The **verdict** line is the machine's summary of what actually changed.
If a run exits successfully but changed nothing, the block says so
loudly: `!! exit=0 with an empty diff — no-op or overclaim`. Read reports
comfortably with:

```text
$ unio report T7-codex          # last 60 lines
$ unio report T7-codex 200      # more history
```

### 7.4 `verify` — the mechanical gate (run this before reading any diff)

```text
$ unio verify codex T7-codex
== verify codex / T7-codex ==
scope    : OK (2 pattern(s))
validate : 2/2 passed
  PASS  $ dotnet build -c Release
  PASS  $ python3 -m unittest discover -s tests
changes  : commits=1, paths touched=3
verdict  : PASS
```

Line by line:

- **scope** — every changed path was compared against the task's `- `
  lines. Three possible answers:
  - `OK` — everything inside the lane.
  - `VIOLATION` — lists each out-of-scope path. Reject the branch.
  - `UNCHECKED` — the task had no `- ` lines, so nothing could be
    enforced. Verification is incomplete; correct the task through the
    lead's task process and rerun. Do not treat it as permission to merge.
- **validate** — each `$ ` command was re-run inside the workshop. Fails
  show the exit code and the last lines of output.
- **changes** — commit and file counts; a completely empty result is
  flagged `EMPTY` and fails.
- **verdict** — `PASS` (exit 0) requires scope, at least one Validate
  command, every check passing, and the existing scope/tamper/empty/base
  safeguards satisfied. Missing scope or checks is `INCOMPLETE` (exit 2).
  Actual failures take precedence and return nonzero, normally exit 1.
  If the workshop changed while the checks ran, an otherwise passing
  verdict becomes `INCOMPLETE` too. M1 provides no waiver bypass.

If the changed files cannot be listed reliably — for example a file is
marked with git's assume-unchanged or skip-worktree flag, which hides
edits — verify stops with exit 2 and an error instead of a verdict. The
outcome is also stored in the task's result (section 7.10).

The verdict block is also appended to the report and the ledger. Tip: set
`UNIO_AUTO_VERIFY=1` and every run appends its own verdict
automatically. A successful worker followed by failed or incomplete
verification returns the verification's nonzero exit. A failed worker
keeps its own exit. This is not reviewer approval or human acceptance.

### 7.5 `diff` — the receipts

```text
$ unio diff codex --stat     # just the file list: your scope check
$ unio diff codex            # every changed line: your real review
```

Both show committed changes (vs the base branch) and uncommitted leftovers
separately. An honest, complete run has everything committed and nothing
uncommitted.

### 7.6 `review` — a rival's second opinion

```text
$ unio review codex T7-codex
```

A **different** vendor's agent receives the task order and the full
committed diff in one prompt and returns findings plus a final
`VERDICT: APPROVE` or `VERDICT: REQUEST-CHANGES`. Unio picks the
first available non-author agent, or name one yourself as a third
argument. Model diversity is the point: Claude reviewing Codex catches
different mistakes than Codex reviewing itself. Use it for risky or large
diffs; your gate still decides.

The rules that keep a review honest:

- **Verify first.** Review only starts after a `verify` PASS that still
  matches the current code; otherwise it stops with exit 2.
- **Complete material only.** Everything must be committed, the diff
  must be text (no binary files), valid UTF-8 and at most 300000 bytes.
  Otherwise the reviewer is not called at all — nothing is cut short and
  sent as if it were the whole change.
- **One clear verdict.** Only one line may mention the verdict, it must
  read exactly `VERDICT: APPROVE` or `VERDICT: REQUEST-CHANGES` on its own,
  and it must come from the reviewer's normal output. Anything else is an
  unknown verdict. If the reviewer program itself fails, the review failed,
  whatever it printed.
- **Exit codes:** 0 = approved, 1 = changes requested or reviewer failed,
  2 = unknown verdict, incomplete material, or code that changed meanwhile.

The reviewer works from an empty temporary folder, but like every
configured agent its command still runs with your user's access to the
machine. Its raw output is kept under `coord/reports/`, and the decision
goes into the task's result. An approval is evidence for you — not your
acceptance.

### 7.7 The human gate — merging

Only after verify passed and you read the diff, from `repo/`:

```text
$ git merge --no-ff agent/codex -m "merge T7: <what it was>"
```

The post-merge hook records the merge in the ledger automatically (that
is the scorecard's "merges" column). The acceptance bar, per your own
recipe: verify PASS + clean build + tests green + smoke run + changelog
fragment.

### 7.8 `sync` — after your merges

```text
$ unio sync
  codex          fast-forwarded to dev
  antigravity    fast-forwarded to dev
  ...
```

Worker branches were created from an older base; after merges they lag
reality. `sync` brings the base branch into every workshop — instant
fast-forward when the branch is fully merged, a real merge when the
worker has unmerged commits, skip when the workshop is dirty or running,
and a clean abort with a `CONFLICT` note when the two genuinely clash.
Run it after every merge session; it prevents next week's conflicts.

### 7.9 Rejecting work

Rejection is one command plus one instruction:

```text
$ git -C ../wt/codex reset --hard dev        # wipe the branch
```

Then tell the foreman: "T7 rejected because `<reason>`. Write a sharper
T7b." Sharper task file — never "hope it does better this time". Two
failed attempts on the same task = the foreman must escalate to you.

### 7.10 `result` and `handoff` — the evidence, and the next-AI packet

```text
$ unio result codex T7-codex       # JSON on screen; changes nothing
$ unio handoff codex T7-codex      # writes a packet, prints its folder
```

`result` prints the task's stored evidence: the worker process
(succeeded or failed, with its exit code), the validation (passed, failed
or incomplete, with reasons) and the review (approved, changes requested,
unknown or failed). Each piece remembers the exact revision it was made
for. Change anything — a commit, the base branch, the task file, any
file in the workshop that git does not ignore — and the old evidence is
marked `stale`.
`ready_for_human_review` is true only when the process succeeded,
validation passed and the review approved, all for the code as it is
right now. Even then the human decision stays yours: the result always
shows your acceptance as `pending`.

`handoff` writes a new folder under `coord/handoffs/` for another AI that
will continue in the same workshop: the task text, the current result,
the revision, the list of changed files, and a HANDOFF.md with what was
checked, what is open and the next safe steps. It is **context, not a
backup**: uncommitted work stays only in the workshop, and no credentials,
`agents.conf`, raw logs or ignored files are copied. Read the packet before
you share it — task text can be sensitive. It refuses to run while the
worker is busy.

The full field list and every exit code are in `docs/QUALITY-USAGE.md`.

---

## 8. See one complete cycle

The file `docs/EXAMPLE.md` adapts a historical Frugal Flock transcript to
current Unio commands. Its retained run IDs and output describe the older
run, not newly measured Unio output. It illustrates chapter 7: a feature
built, verified, reviewed, merged, and synced; a
rogue worker caught by verify; background runs, a race, the saboteur
finding a genuine bug; and the fix cycle that closes the loop. Replay it
on your machine anytime:

```text
$ bash examples/demo.sh /tmp/unio-demo
```

Zero quota — the fleet is stood-in by scripts, the machinery is real.

When you want to *stress-test* rather than tour — deliberately try to
break each guarantee — run `bash examples/breakit.sh` and follow
`docs/TESTPLAN.md`, which takes you from that automated attack kit through
real-fleet checks to building your first genuine project.

---

## 9. The daily rhythm

The single most important fact for continuity: **the project's memory
lives in files, not in any chat.** Worker branches, reports, the board,
the ledger, git history — all survive every shutdown automatically. You
could fire the foreman every night and hire a fresh one every morning
without losing anything that matters.

### 9.1 Starting a session (2 minutes)

```text
$ cd ~/code/<project>/repo
$ unio status          # where did I leave off? benched agents? queue?
$ unio doctor          # anything that would waste a run? (base, agents, stale)
$ unio smoke           # after CLI updates or days away
$ claude                    # hire the foreman (or resume: claude -c)
```

Returning the same day: `claude -c` resumes the previous conversation.
After days away, prefer a FRESH session with this prompt (old chats
degrade; files don't):

```text
Read MASTER.md, ../coord/docs/*, ../coord/board.md, and CHANGELOG.md.
We are resuming. Summarize current state — merged, in flight, blocked —
then propose the next step. Wait for my go.
```

### 9.2 Working efficiently

- Dispatch long tasks with `-b`; review results in batches — two or three
  diffs in one sitting beats context-switching per task.
- `verify` before you read any diff; `review` for the risky ones;
  `result` to see whether all the evidence still matches the code.
- After your merges: `sync`.
- Two terminals: foreman in one, YOUR gate commands in the other. Never
  gate inside the foreman's window.
- Reject early. A sharp re-brief costs minutes; polishing a wrong diff
  costs an evening.
- Hard tasks early in your 5-hour quota windows; chores late. Bench dead
  agents immediately (chapter 10).
- One cycle at a time: your review is the bottleneck — protect it.

### 9.3 Ending a session (3 minutes — the save ritual)

```text
$ unio status      # 1. "running: (none)" — never leave -b runs going
                        #    (stragglers: unio kill <task>)
```

This one is worth taking literally: a background run left open while the
machine slept overnight came back ten hours later having errored out. The
run block and the ledger now flag that case (`suspended`), and `unio
score` keeps such runs out of its averages — but the wasted night is not
recoverable. Close the books before you close the lid.

Tell the foreman to close the books:

```text
End of session. Update ../coord/board.md to the exact current state, add
a CHANGELOG entry for anything merged today that lacks one, and write a
short "NEXT SESSION" note at the top of the board. Then stop.
```

```text
$ git push               # 2. the actual save button — code leaves the machine
$ exit                   # 3. everything durable is on disk
```

### 9.4 What survives what

| Thing | Survives shutdown? |
|---|---|
| Worker branches, commits, reports, ledger, board | Yes, automatically |
| Foreman chat | Yes via `claude -c`, but degrades — files are canonical |
| Running `-b` tasks | NO — finish or kill before leaving |
| Un-pushed commits | Only on this machine until `git push` |
| Bench timers | Yes (global, in `~/.config/unio/off/`) |

---

## 10. Quota management (the bench)

Subscriptions have 5-hour windows and weekly caps. Unio treats that
as routine, not crisis.

```text
$ unio off codex 5h     # window burned: benched, auto-returns in 5h
$ unio off grok 7d      # weekly cap: benched for a week
$ unio off opencode     # benched until you say otherwise
$ unio on codex         # manual return anytime
$ unio agents           # installed? on/OFF, with your chosen retry time
$ unio agents --json    # the same, machine-readable
```

Facts worth knowing:

- The bench is **global across all your projects** — correct, because the
  quota belongs to the subscription, not to a project.
- A benched agent is refused work everywhere (`run`, `race`, `sabotage`),
  and the foreman is instructed to reroute per its fallback table.
- **Limit observations:** a failed run's normalized final 60 log lines
  can trigger a warning and a suggested bench command. Failure for this
  helper means a nonzero actual exit or no commits and no uncommitted
  files. The warning and ledger `wall=1` mean suspected limit language;
  printed file text can also match. The raw log keeps the evidence.
  Worker output never benches an agent. `UNIO_AUTO_OFF` is retained for
  compatibility with no effect; use `unio off` explicitly after checking
  the provider's actual state. Successful work stays `wall=0` regardless
  of printed limit phrases, and receipts retain the real exit.
- Boring work goes to the bench-warmers; interesting work *waits* for the
  strong agents to come back.
- `agents` is a local check only: it never runs an agent and never asks a
  provider about login or quota, so authentication and capacity always
  show as unknown. A bench time is the retry time you chose, not a
  provider-confirmed reset. Conf lines that use shell syntax (the shipped
  ones pass the task with `"$(cat "$TASKFILE")"`) show `installed=unknown`;
  `unio doctor` checks that each worker's program exists.

---

## 11. Fleet intelligence — who earns their seat

### 11.1 `unio score`

```text
$ unio score
  worker          runs   ok  fail  walls   verify  merges  avg-dur
  codex             14   13     1      1     12/13       6     311s
  antigravity        6    5     1      0       4/5       2     540s
  grok               5    3     2      1       2/4       0     220s
```

Column by column: **runs** (effort), **ok/fail** (exit results), **walls**
(runs that hit quota/auth walls), **verify** (verify verdicts passed /
total — the honesty rate), **merges** (branches you accepted — the only
column that is money), **avg-dur** (average run duration). Sorted by
merges: earners on top. Everything comes from `ledger.jsonl`; merges are
logged automatically by the post-merge hook.

Use it weekly: an agent far below the leaders' acceptance rate gets only
chores — or loses its seat, and its subscription money moves to a bigger
plan on a winner.

The companion product `myapp <project-root>` remains the full scorecard,
including history from before the ledger existed.

### 11.2 The ledger, for the curious

One JSON object per line in `coord/reports/ledger.jsonl`:

```text
{"event":"run", "ts":..., "task":..., "worker":..., "agent":..., "exit":0,
 "duration_s":214, "wall_s":214, "suspended":0, "snapshot_failed":0,
 "commits":1, "files":2, "insertions":65, "deletions":0, "uncommitted":0,
 "wall":0}
{"event":"verify", ..., "scope":"OK", "validate_run":2, "validate_failed":0,
 "commits":1, "empty":0, "verdict":"PASS"}
{"event":"review", ..., "reviewer":"claude", "exit":0}
{"event":"race",   ..., "workers":"codex grok"}
{"event":"merge",  ..., "worker":"codex", "subject":"merge T7: ..."}
```

Append-only, machine-readable, and the raw feed for any future tooling.
`snapshot_failed` is 1 when the workshop could not be fingerprinted after
the run (section 7.1); the review event's `exit` is the reviewer
program's exit code, not its verdict.

---

## 12. Advanced plays

### 12.1 `race` — the bake-off

When you want head-to-head data (or just the best version of something
important), give the same task to several vendors at once:

```text
$ unio race T9 codex grok
```

Unio copies `coord/tasks/T9.md` into `T9-codex.md` and `T9-grok.md`
and dispatches both in the background (isolation makes this free). Then:

```text
$ unio verify codex T9-codex     $ unio verify grok T9-grok
$ unio diff codex                $ unio diff grok
```

Merge exactly **one** winner; reset the losers (`git -C ../wt/grok reset
--hard dev`); `sync`. The race lands in the ledger — over time your
scorecard becomes controlled-experiment data, not anecdotes. Racers
deliberately share scope; that is the one sanctioned exception to the
disjoint-scope rule, because only one branch survives.

### 12.2 `sabotage` — the saboteur seat

Spare quota after a merge day? Convert it into a standing red team:

```text
$ unio sabotage opencode
```

This syncs the worker (so it sees the latest merged work), generates a
`SAB-<timestamp>` task from the saboteur template, and dispatches it in
the background. The saboteur's job: find REAL defects in recently merged
work by writing tests that FAIL against the current base — edge cases,
boundary values, the paths existing tests never visit. It must not fix
anything; bugs exposed are the deliverable, each documented with WHERE /
REPRO / EXPECTED vs ACTUAL / SEVERITY. An honest "found nothing" with no
commits is a valid, good result. When it does find something, the fix is
a normal task on the next cycle — and the failing test joins the suite.

### 12.3 Doubling a strong seat

Worker names resolve to agents by the part before the first dash:
`unio init codex-2` creates a second workshop that runs the same
codex CLI — two codex tasks in parallel when codex is your bottleneck.

---

## 13. Maintenance

### 13.1 Updating the AI CLIs

Unio bundles no AI — it calls whatever binaries are on your PATH, so
updating a CLI updates the fleet instantly:

```text
$ claude update
$ curl -fsSL https://chatgpt.com/codex/install.sh | sh
$ agy update
$ opencode upgrade
$ curl -fsSL https://x.ai/cli/install.sh | bash
```

**The post-update ritual (do not skip):** flags get renamed between
versions — it has already happened three times in this system's life.

```text
$ unio smoke
```

If a row FAILs with a usage/flag dump: run `<binary> --help`, find the
renamed flag, fix that one line in `agents.conf`. Two minutes.

### 13.2 Updating Unio itself

Open a terminal inside your existing clone. Its local folder may still be
called `frugal-flock` or the historical `agentteam-docs`; it does not need
to be renamed. The legacy local workspace path
`/mnt/d/Vibe Coding/_vm/frugal-flock` stays intact to preserve worktree links.

```text
$ git remote set-url origin https://github.com/danielmevit/unio.git
$ git pull --ff-only
$ bash unio-install.sh     # never touches your agents.conf
$ unio selftest            # mock-agent checks, zero quota
$ unio version             # confirm what you now run
```

If Git reports a conflict or diverged history, stop and resolve it before
reinstalling; do not discard local work to force the update.

Existing projects keep their old role cards; re-running
`unio init <worker>` inside a project refreshes that worker's card.
Big MASTER.md template changes: paste them into important projects by
hand if you want them.

### 13.3 Backups, standing policy

Code: `git push` at session end — that is everything that matters.
Config: `tar czf unio-conf.tgz -C ~ .config/unio` after conf
changes. Full machine snapshots are optional; the rebuild path (installer
+ five logins) is under an hour.

---

## 14. Troubleshooting

### 14.1 The universal 4-step diagnosis

Almost every problem yields to the same sequence:

1. `unio status` — is STOP set? someone benched? something RUNNING?
2. `unio agents` — is the binary there? is the agent benched?
3. Read the END of the log: `unio tail <task>` (or open
   `coord/reports/<task>.log`). The last ten lines almost always name
   the real problem: a login expired, a flag renamed, a question waiting.
4. Read the report verdict: `unio report <task>`. Empty diff?
   Uncommitted work? Wall language?

And remember the great divider: **`unio selftest` green means the
machinery is fine** — the problem is an agent, a login, or a task file.

### 14.2 Install and setup problems

| Symptom | Cause and fix |
|---|---|
| `unio: command not found` | `~/.local/bin` not on PATH. `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc` |
| `not inside a Unio project` | You are in a folder with no `coord/` + `wt/` above it. `cd` into the project's `repo/` (any subfolder works). |
| Tab-completion doesn't work | Open a NEW terminal (completion loads per shell). Ubuntu needs the `bash-completion` package, normally preinstalled. |
| "Python 3 is required before run/review/smoke" | Install it: `sudo apt install python3`. Only the standard library is used; nothing else is downloaded. |
| init: "possible secrets tracked in git" | Working as intended — see section 5.3. Untrack the file, gitignore it, run init again. |
| init warns "no agents.conf entry for agent X" | You initialized a worker whose agent has no line in `agents.conf`. Add the line or ignore the seat. |
| init: "this repo has no commits yet" | A worktree branches from a commit, so an empty repo cannot be scaffolded. Make one commit first (`git commit --allow-empty -m "initial commit"`), then init. |
| "worker/task name must not contain a path separator / `..` / start with `-`" | A safety guard: these names build paths under `wt/` and `coord/tasks/`, so they must be plain names. You typed a slash, a `..`, or a leading dash — use the bare id (`T7-codex`, not a path). |

### 14.3 Agent problems

| Symptom | Cause and fix |
|---|---|
| Worker fails instantly; log shows a usage/flag dump | The CLI updated and renamed a flag. `<binary> --help`, fix the line in `agents.conf`, rerun. `unio smoke` catches this class early. |
| Log says token/login expired | `<cli> logout && <cli> login` (interactive, once), rerun the task. |
| Worker "hangs" forever | It is waiting on a question its auto-approve flags didn't cover, or an internal print-timeout (Antigravity defaults to 5 minutes — the shipped conf raises it to 55m). Read the log end; if truly stuck: `unio kill <task>`. |
| Log mentions rate/usage limit | The window is burned. `unio off <agent> 5h` (weekly cap: `7d`), tell the foreman to reroute, keep working. |
| smoke says WARN — "replied, but not ok" | The agent answered something else. Usually harmless chatter; if persistent, run the one-liner (`claude -p "say ok"` etc.) and look at the reply. |
| smoke says MISSING binary | The CLI is not installed or not on PATH for this shell. |

### 14.4 Run problems

| Symptom | Cause and fix |
|---|---|
| `worker 'x' is already running a task` | The per-worker lock: one run per workshop. `unio status` shows what; a stray background run dies with `unio kill <task>`. |
| `STOP is active` | Someone (you) pressed the red button. `unio resume` when you understand why it was pressed. |
| `agent 'x' is OFF (auto-on in 137m)` | Benched. Wait, reroute, or `unio on x`. |
| `no task file: .../T7.md` | Task name typo, or the file is in the wrong folder. Task files live in `coord/tasks/`, and you pass the name without `.md`. |
| Background run seems gone but no report block | It was killed (or the machine slept). The log holds whatever it printed. Rerun — tasks are rerunnable by design. |
| git complains about `index.lock` | A killed run died mid-commit. The next `unio run` on that worker clears it automatically; manually: delete the named lock file. |
| run: "post-run snapshot failed" | The worker left a FIFO, socket, device, nested repository or submodule in its workshop. The real exit code is recorded, but the result stays not ready. Remove the file and run again. |

### 14.5 Gate problems (verify / diff / merge)

| Symptom | Cause and fix |
|---|---|
| verify: `scope : VIOLATION` | The worker left its lane. Preserve the branch for inspection and ask the foreman for a scoped repair task. Never merge a violating diff as-is. |
| verify: `scope : UNCHECKED` | The task had no scope lines: INCOMPLETE, exit 2 unless another failure takes precedence. Correct the task through the lead and rerun; it is not PASS. |
| verify: no Validate commands | INCOMPLETE, exit 2 unless another failure takes precedence. Define the required check explicitly and rerun; no waiver bypass exists. |
| verify: `EMPTY — no commits and no uncommitted changes` | The agent claimed success and did nothing. Treat as failed; re-brief sharper. |
| verify FAIL but the report claims success | Working as designed: the report lied, the machine caught it. Trust verify. |
| verify: `INCOMPLETE` with `candidate_changed_during_validation` | Something changed the workshop while the checks ran. Make sure nothing else writes there, then rerun verify. |
| "unsupported assume-unchanged/skip-worktree index flags" | Those git flags hide edits from scope checks and review. Clear them (`git update-index --no-assume-unchanged --no-skip-worktree` on the named paths, or `git sparse-checkout disable`) and rerun. |
| review: "requires current passed validation" | Run verify first. Any commit, file change or task edit since the last PASS makes that PASS stale. |
| review: "incomplete review material" | Commit all staged, unstaged and untracked work. Binary or oversized diffs cannot be reviewed this way — inspect them yourself. |
| review exit 2, verdict unknown | The reviewer did not end with exactly one `VERDICT: APPROVE` or `VERDICT: REQUEST-CHANGES` line. Rerun or ask another reviewer. |
| Report says done; diff shows uncommitted work | The worker forgot to commit. Commit it yourself in `wt/<w>` or rerun with a sharper "Done means". |
| Report says done; diff looks wrong | Normal. Reject; the foreman re-briefs. The system working. |
| Two workers changed the same file | A scope overlap slipped through. Accept one, reject the other, fix disjointness. (Exception: a deliberate `race`.) |
| Merge conflict when you merge | Rare with disjoint scopes + regular `sync`. Resolve by hand or abort (`git merge --abort`) and re-order the merges; nobody force-merges. |

### 14.6 Emergency

Everything on fire: `unio stop` (all new runs refused), breathe,
read `unio status` and the last reports, `unio resume` when you
understand what happened. Worst case, restore your machine snapshot —
everything committed and pushed survives in the repository.

Known honest limits: the quota detector matches common phrasings and will
miss unusual ones (the manual bench is the primary tool). Grok Build is
beta software; budget patience. And no rule file makes an AI perfectly
obedient — the workshops, the hooks, the receipts, and your gate are the
actual guarantees, which is why none of them are optional.

---

## 15. Command reference (all commands)

Setup and health:

| Command | What it does |
|---|---|
| `unio new <repo-url> [name] [workers...]` | Bootstrap a whole project: clone → dev branch → init → playbooks copied from `~/.config/unio/playbooks/`. |
| `unio init [w1 w2 ...]` | Scaffold workshops + office next to your clone (default workers: codex antigravity opencode grok). Idempotent; secrets preflight; installs guard hooks. |
| `unio agents [--json]` | Roll call: each agent — program installed (yes / no / unknown)? on or benched? Local only; no login or quota check. `--json` = machine-readable. |
| `unio smoke` | One tiny live call per agent from a neutral folder; OK / WARN / FAIL per row. Run after every CLI update. |
| `unio selftest` | Rehearse the entire loop with mock agents in a throwaway sandbox — zero quota. |
| `unio doctor` | Preflight a project: base branch, agent binaries and config lines, worktree health, stale state, disk. Catches what would waste a run. Exits nonzero on an error. |
| `unio version` | Installed version + config path. |

Work:

| Command | What it does |
|---|---|
| `unio run <w> <task>` | Execute `coord/tasks/<task>.md` with worker `<w>` in its workshop; blocks until done. |
| `unio run -b <w> <task>` | Same, in the background. |
| `unio tail [task]` | Follow a run's live log (default: newest). |
| `unio kill <task>` | Stop a background run — the whole session, agent included. |
| `unio report <task> [lines]` | Read a task's report (default: last 60 lines). |
| `unio verify <w> <task>` | The mechanical gate: scope check + Validate re-run + commit sanity; verdict into report, ledger and result. Exit 0 PASS, 1 FAIL, 2 INCOMPLETE. |
| `unio diff <w> [--stat]` | The receipts: committed and uncommitted changes vs the base branch. |
| `unio review <w> <task> [agent]` | After a current verify PASS, a DIFFERENT vendor reviews the task order + committed diff; ends `VERDICT: APPROVE` or `REQUEST-CHANGES`. Exit 0 approved, 1 changes or reviewer failed, 2 unknown or incomplete. |
| `unio result <w> <task>` | Print the task's stored evidence as JSON (read-only, no AI call). |
| `unio handoff <w> <task>` | Write a context packet for the next AI under `coord/handoffs/`; not a backup. |
| `unio sync [w]` | Bring the base branch into worker branches after merges (fast-forward / merge / skip dirty / abort on conflict). |

Fleet plays:

| Command | What it does |
|---|---|
| `unio race <task> <w1> <w2> [...]` | Same task to several workers in parallel; merge exactly one winner. |
| `unio sabotage [worker]` | The saboteur seat: syncs the worker, then sends it hunting for real bugs in freshly merged work by writing failing tests. Name a worker, or name none and the seat rotates round-robin through your fleet so routine work keeps getting fresh eyes. |
| `unio sabotage --all` | Runs every available vendor as saboteur in turn, one after another (never in parallel — same code, and it keeps quota manageable). Use it when a feature or release is finished: each model finds different defects, and one that two models independently find is almost certainly real. |
| `unio score [project-root]` | Per-worker scorecard from the ledger: runs, ok/fail, walls, verify rate, merges, avg duration. |

Switches:

| Command | What it does |
|---|---|
| `unio status` | The briefing: benched agents, tasks, reports, review queue, running jobs. |
| `unio off <agent> [30m\|5h\|7d]` | Bench an agent (no duration = until `on`). Global across projects. |
| `unio on <agent>` | Un-bench immediately. |
| `unio stop` / `unio resume` | Project-wide red button: refuse / allow all new runs. |
| `unio help` | The built-in summary of all of the above. |

Your commands (the human gate — plain git, from `repo/`):

| Command | When |
|---|---|
| `git merge --no-ff agent/<w> -m "merge T7: ..."` | Accept a branch — only after verify + reading the diff. Ledger-logged automatically. |
| `git -C ../wt/<w> reset --hard dev` | Reject a branch. |
| `git push` | End of every session. This IS your backup. |

---

## 16. Settings reference (environment variables)

Set these in front of a command (`UNIO_TIMEOUT=7200 unio run …`)
or export them in `~/.bashrc` to make them permanent.

| Variable | Default | Meaning |
|---|---|---|
| `UNIO_TIMEOUT` | 3600 | Per-run time limit, seconds. |
| `UNIO_VERIFY_TIMEOUT` | 900 | Time limit per Validate command in `verify`. |
| `UNIO_REVIEW_TIMEOUT` | 900 | Time limit for a `review` call. |
| `UNIO_AUTO_OFF` | ignored | Accepted for compatibility; worker output never changes availability. Use explicit `unio off` / `unio on`. |
| `UNIO_AUTO_VERIFY` | off | `1` = append verify verdict; a successful worker plus failed/incomplete checks returns nonzero. |
| `UNIO_AUTO_SYNC` | off | `1` = fast-forward a stale worker onto the base before a run (clean worktree only). Otherwise `run` just warns. |
| `UNIO_ALLOW_SECRETS` | off | `1` = override init's tracked-secrets refusal. Know why. |

Files that act as settings: `coord/base` (the integration branch name),
`coord/agents.conf` (project-specific crew), `coord/STOP` (the red
button, managed by `stop`/`resume`).

---

## 17. The rules the AIs live under, in plain language

The normative version is `docs/PROTOCOL.md` (installed into every
project's `coord/docs/`); these are the twelve invariants translated:

1. A worker writes only inside its own workshop, only within its task's
   allowed scope.
2. Needs something outside its scope? It must NOT touch it — finish what
   it can and flag the need in its report. Flagging beats fixing.
3. Only you merge. The foreman recommends; it never merges.
4. The foreman never writes feature code — contracts, fixtures, docs,
   and the board only.
5. Workers never switch branches, never push, never touch dev or main
   (the hooks enforce this physically).
6. Hitting the same obstacle twice means stop and write a blocker note —
   never improvise architecture.
7. If the STOP file exists, nothing new starts.
8. Contracts cited in a task are frozen — change requests go through
   blockers, never silent edits.
9. Benched agents get no work; the foreman reroutes.
10. Verification is evidence-based: a claim without a diff, test, or log
    behind it counts as unverified. `verify` is the mechanical floor of
    that evidence, not its ceiling.
11. Workers never edit CHANGELOG.md — one fragment per task in
    `changelog.d/`, rolled up at release.
12. A run that claims success with an empty diff is treated as failed.

---

## 18. Glossary

| Term | Meaning |
|---|---|
| **agent** | One AI vendor's command-line program, configured by one line in `agents.conf` (claude, codex, antigravity, opencode, grok). |
| **base branch** | The integration branch every worker measures against — normally `dev`. Stored in `coord/base`. `main` is releases only. |
| **bench / off** | Temporarily disabling an agent (usually for quota). Global across projects; auto-expires if given a duration. |
| **branch** | A named line of development in git. Workers each own `agent/<name>`. |
| **CLI** | Command-line interface — a program you run in the terminal. |
| **commit** | A saved snapshot of changes in git, with a message. |
| **diff** | The exact line-by-line difference between two states of the code. The receipts. |
| **foreman / lead / master** | The interactive AI session that plans and delegates. Never codes, never merges. |
| **fragment** | A one-file changelog entry in `changelog.d/`, merged into CHANGELOG.md at release. |
| **gate** | Your review-and-merge decision. The only way code enters the base branch. |
| **handoff packet** | A folder written by `unio handoff` so another AI can continue in the same workshop: task, result, revision, changed files, next steps. Context, not a backup. |
| **headless** | Running non-interactively: one prompt in, work happens, output comes back, the program exits. |
| **hook** | A small script git runs automatically around actions (commit, push, merge). Unio installs three guards. |
| **ledger** | `coord/reports/ledger.jsonl` — machine-readable history: one JSON line per run/verify/review/race/merge. Run timings are suspend-aware: `duration_s` counts only real working time, `wall_s` is clock time, and `suspended` marks a run the machine slept through. |
| **lock** | The per-worker "one run at a time" guarantee (`coord/.locks/`). |
| **merge** | Bringing one branch's commits into another. Yours alone. |
| **PATH** | The list of folders your terminal searches for programs. |
| **quota window** | A subscription's usage allowance period (commonly 5 hours, plus weekly caps). |
| **repo / repository** | A project folder tracked by git, including its full history. |
| **result** | `coord/results/<worker>/<task>.json` — the task's current evidence (process, validation, review), each tied to an exact revision. Printed by `unio result`. |
| **scope** | The exhaustive list of files a task may touch — machine-enforced via the task's `- ` lines. |
| **smoke test** | The cheapest possible "is it alive?" check — one tiny call per agent. |
| **task file** | A self-contained work order in `coord/tasks/`, one per task. |
| **verify** | The mechanical gate assist: scope + Validate + commit sanity. PASS, FAIL, or INCOMPLETE when evidence is missing. |
| **wall** | A run that died against an auth or quota barrier rather than failing on the work itself. |
| **worktree / workshop** | A full additional checkout of the same repository in its own folder, pinned to its own branch (`wt/<name>`). The isolation mechanism. |

---

## 19. Cheat sheet — one page

```text
SETUP (once)          bash unio-install.sh ; unio selftest
                      log in each CLI once ; unio agents ; unio smoke
NEW PROJECT           cd ~/code && unio new <repo-url> myproj
SESSION START         unio status ; unio doctor ; claude
HEALTH CHECK          unio doctor    (before dispatching: catches waste)
DISPATCH              unio run -b <worker> <task>
WATCH                 unio status | tail <task> | kill <task>
JUDGE                 unio verify <w> <task> ; unio diff <w>
                      second opinion: unio review <w> <task>
                      evidence: unio result <w> <task>
HANDOFF               unio handoff <w> <task>   (context for the next AI)
ACCEPT                git merge --no-ff agent/<w> -m "merge T7: ..." ; unio sync
REJECT                git -C ../wt/<w> reset --hard dev  + re-brief the foreman
QUOTA                 unio off <agent> 5h|7d ; unio on <agent>
PANIC                 unio stop  ...  unio resume
SCOREBOARD            unio score
EXTRA PLAYS           unio race <task> w1 w2 ; unio sabotage <w>
SESSION END           status (nothing running) -> foreman updates board -> git push
AFTER ANY UPDATE      unio smoke ; after unio updates: selftest + version
```

---

## Appendix A — turning this book into a Word document

This file is deliberately written in plain, portable Markdown so that any
converter or AI assistant can produce a clean `.docx` from it.

**Option 1 — the repo's own script (recommended).** A ready-made Word
copy lives at `docs/GUIDEBOOK.docx`. To regenerate it after any edit:

```text
./tools/make-docx.sh                    # docs/GUIDEBOOK.md -> docs/GUIDEBOOK.docx
./tools/make-docx.sh docs/HANDBOOK.md   # or any other document
```

The script runs pandoc for the conversion (clickable table of contents,
real Word tables, syntax-highlighted code blocks), then applies the page
setup pandoc leaves out: A4, 2 cm margins, and centered page numbers in
the footer. It refuses to run while the file is open in Word, and finds
pandoc automatically — native Linux install, or a Windows install when
you are on WSL.

Installing pandoc needs no root:

```text
curl -fsSL -o /tmp/p.tgz https://github.com/jgm/pandoc/releases/download/3.10/pandoc-3.10-linux-amd64.tar.gz
tar xzf /tmp/p.tgz -C /tmp && install -m755 /tmp/pandoc-3.10/bin/pandoc ~/.local/bin/pandoc
```

(With root, `sudo apt install pandoc` works too.) When you open the
result, Word asks to update fields — say yes, or press F9, to fill in the
table of contents.

**Option 2 — plain pandoc**, if you prefer to drive it yourself:

```text
pandoc docs/GUIDEBOOK.md -o unio-guidebook.docx --toc --toc-depth=2
```

**Option 3 — hand it to an AI assistant.** Upload or paste this file and
use a prompt like the following:

```text
Convert the attached Markdown file into a well-formatted Word document.

- Use the document's H1 as the Word Title style; "## N. ..." headings as
  Heading 1; "### N.N ..." headings as Heading 2.
- Insert a table of contents after the title page, built from Heading 1
  and Heading 2.
- Render every fenced code block in a monospace font (Consolas 10pt) with
  light grey shading, and do not spell-check or auto-correct inside them —
  they are terminal commands and must stay exact.
- Render Markdown tables as real Word tables with a header row, banded
  rows, and borders; keep them within page width (landscape or reduced
  font for the wide ones is fine).
- Keep inline `code spans` in monospace.
- Page size A4, 2 cm margins, page numbers in the footer.
- Do not reword, summarize, or add content — reproduce the text exactly.
```

**Note on the folder diagram** in chapter 3.1: it uses box-drawing
characters (├── └──). They display correctly in any standard monospace
font (Consolas, Courier New). If your converter mangles them, ask it to
render that block as a plain indented list instead.

**If you edit this book or write another one**, read
`docs/DOC-CONVENTIONS.md` first and run `./tools/check-docs.sh` before
converting. The rule that matters most: never leave a bare
`<placeholder>` outside backticks — every converter reads it as an HTML
tag and silently deletes it, which already cost this book a sentence
once.

---

## Appendix B — where everything is documented

| Document | What it is |
|---|---|
| `docs/GUIDEBOOK.md` | This book — the complete beginner-to-daily-use manual. |
| `docs/HANDOFF.md` | For whoever takes the project over: what to edit, the change loop, the classes of bug found so far, accounts and quota. |
| `docs/HANDBOOK.md` | The operator's condensed handbook (same facts, terser). |
| `docs/EXAMPLE.md` | Historical transcript adapted to current Unio commands; retained output is from the older run. Replay with `examples/demo.sh`. |
| `docs/SETUP.md` | The compact install/setup reference. |
| `docs/PROTOCOL.md` | The normative spec the AIs follow (auto-installed into every project). |
| `docs/MASTER-PLAN.md` | The original deep explanation + the phased roadmap + dictionary. |
| `docs/TESTPLAN.md` | The break-it campaign: attack every guarantee (`examples/breakit.sh`), then real-fleet checks, then your first real build. |
| `unio-install.sh` | The installer. Run it; don't read it. |
| `research/multi-agent-claude-review.md` | The original architecture research and terms-of-service analysis. |
