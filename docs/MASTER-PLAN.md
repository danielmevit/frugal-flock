# The Master Plan — running a team of AI coders on your own computer

This document explains, from zero, the system we built: what it is, why every
piece exists, how to operate it, and a step-by-step roadmap from "nothing is
set up" to "five AI agents building software for me while I supervise."

It is written for someone without a programming background. Every technical
word is explained the first time it appears, and there is a dictionary in
section 2 you can flip back to. Where something is genuinely confusing, it is
marked **THE CONFUSING PART** and explained slowly — those spots are
confusing for professional developers too, so take them at reading speed.

The two companion files are practical, not explanatory: `unio-install.sh`
is the program that sets everything up, and `AGENTTEAM-README.md` is the
short reference card for daily use. This document is the one that makes the
other two make sense.

---

## 1. The big picture

You pay for five AI coding services: Claude, Codex (ChatGPT), Antigravity
(Google), OpenCode, and Grok (X). Each one can write and edit
code. Out of the box, they are five separate chat windows that know nothing
about each other.

The system turns them into a construction company:

```text
        YOU  (the owner — approves plans, signs off on all work)
         │
      MASTER  (one AI, usually Claude — the foreman:
         │     plans the work, writes work orders, inspects results)
         │
   ┌─────┼─────────┬───────────┐
 CODEX ANTIGRAVITY OPENCODE   GROK   (the workers — each gets a work
   │     │         │           │     order, builds in its own workshop,
   └─────┴─────────┴───────────┘     hands back the result)
         │
   YOUR PROJECT  (one shared codebase everything flows back into)
```

The foreman never swings a hammer — it plans, delegates, and inspects. The
workers never talk to each other — they only receive written work orders and
hand back written results. And nothing becomes part of the real project until
**you personally accept it**. That last rule is the safety net for the whole
system: AI agents are fast, confident, and sometimes wrong, so a human
signature stands between their output and your project.

Everything runs inside a virtual machine on your computer (explained below),
using the monthly subscriptions you already pay for. No pay-per-use billing,
no fragile browser tricks — every agent is used exactly the way its maker
intended, just coordinated.

One honest expectation-setting note before the details: this system does not
remove work, it changes your job. Instead of writing code you will be reading
plans, reading results, and making accept/reject decisions. That is a real
job and it takes real attention. What you get in return is that four or five
things can be built at once instead of one.

---

## 2. The dictionary

Read this once now, then come back whenever a word feels slippery.

**Terminal** — a window where you talk to the computer by typing text
commands instead of clicking buttons. You type a command, press Enter, the
computer prints its answer as text. All of this system lives in terminals.

**Command / CLI** — a program you use from the terminal ("CLI" = command
line interface). `unio status` is a command: `unio` is the
program, `status` is what you're asking it to do.

**AI coding agent** — an AI you run in a terminal that can not only chat,
but also open files, edit them, and run programs inside one specific folder.
Claude Code, Codex, Antigravity, OpenCode, and Grok Build are all agents. The
difference from the chat website: the website talks *about* code, the agent
actually *changes files on your machine*.

**Subscription login vs API key** — two ways to pay for AI. A subscription
is a flat monthly fee; you log in once and use it until you hit the included
limit. An API key is a metered pipe: every request costs money, and a busy
agent can burn hundreds of dollars in a day. This system uses **only
subscription logins** — your costs are capped at what you already pay.

**Quota / usage limits** — subscriptions aren't unlimited. Each service
meters you in windows: typically a 5-hour window (use a lot → locked out
until the window resets) and a weekly cap on top. When an agent hits a
limit, it stops answering until the reset. The system has a per-agent
on/off switch exactly for this.

**Virtual machine (VM)** — a complete computer simulated inside your real
one, like a computer in a sealed glass box. Your Ubuntu VM is where
everything runs. Why it matters: the agents run in a mode where they don't
ask permission before editing files or running commands. Inside a sealed
box, the worst case is "wipe the box and restore a snapshot." A **snapshot**
is a save-game of the entire VM — take one before big experiments.

**Git** — a save-game system for a project folder. Every time you (or an
agent) "commit," git stores a snapshot of the project plus a one-line note
about what changed. You can look back at any snapshot or return to one.
Nothing committed is ever silently lost — that is why the whole system is
built on top of it.

**Repository (repo)** — a project folder that git is tracking, including
its entire history of snapshots.

**Commit** — one saved snapshot with its note, e.g. `T3: add PNG export`.
"Committed" work is safely recorded; uncommitted work is just loose changes.

**Branch** — THE CONFUSING PART, #1. A branch is a *parallel timeline* of
snapshots inside the same repo. Imagine the project's history as a chain of
save points. A branch says: "from this save point onward, I'm continuing on
my own chain, without touching yours." Later, the chains can be recombined.
Your projects use two permanent timelines: **`dev`** — the everyday working
timeline where all new work lands, and **`main`** — the polished timeline
that only ever contains released versions. On top of those, this system
creates one temporary timeline per worker (`agent/codex`, `agent/grok`, …)
so each worker's changes stay separated until inspected.

**Merge** — recombining timelines: "take everything the `agent/codex`
timeline did and fold it into `dev`." If two timelines changed the *same
lines* of the same file, git stops and asks a human to decide — that's a
**merge conflict**. The system's rules exist mostly to prevent conflicts
from ever happening (workers aren't allowed to touch the same files).

**Worktree** — THE CONFUSING PART, #2, and the heart of the machine.
Normally one repo = one folder showing one timeline at a time; switching
timelines transforms that folder. A worktree lets one repo appear as
*several folders at once*, each folder pinned to a different timeline. So
`wt/codex/` and `wt/grok/` look like two full copies of your project — but
they're two views into the SAME repo, each locked to its own branch. That's
how five agents edit "the project" simultaneously without stepping on each
other: each is physically working in its own folder, on its own timeline.
The mental model: one book of save-games, several reading rooms, each room
opened to a different chapter.

**Diff** — the receipts. A diff is the exact line-by-line list of what
changed: removed lines start with `-`, added lines start with `+`. When a
worker claims "I added the export button," the diff is where you check what
it *actually* did. Reading diffs is the core skill this system asks of you,
and section 7 teaches it.

**Headless mode** — THE CONFUSING PART, #3. Normally you chat with an agent
back-and-forth. In headless mode you hand it one complete written
instruction; it works silently, prints its result, and shuts down —
**forgetting everything**. Every work order is therefore a message to a
brilliant contractor with total amnesia: if a fact isn't in the work order,
the worker does not know it, no matter how often it was discussed elsewhere.
This is why the system is strict about task files being self-contained.

**Markdown (.md file)** — a plain text file with light formatting (`#` for
headings, `-` for lists). Humans can read it, every AI agent can read it.
All coordination in this system — work orders, reports, the task board —
is just markdown files in folders. No database, no app: files you can open
and read yourself at any moment.

**Symlink** — a shortcut: a fake file that points at a real one. Used here
for one trick: each agent brand looks for its instructions under a
different filename (Claude reads `CLAUDE.md`, Codex reads `AGENTS.md`,
Google's agent reads `GEMINI.md`). We keep ONE real file and symlink
all three names to it — so any agent you launch finds its orders.

**PATH** — the list of folders the terminal searches when you type a
command name. "Put it on your PATH" means "make it findable by name." The
install step handles this; if the terminal ever says
`unio: command not found`, PATH is what broke.

**CodeGraph** — a tool from your own playbook that builds a searchable
index of a codebase, so agents can ask "where is the export function?"
instead of reading every file. The system wires it in automatically where
supported.

**Your playbooks** — your two standards documents
(`ai-project-setup-playbook.md`, `ai-full-build-recipe.md`). They define
how your projects are structured and how work is done (the dev/main model,
the milestone routine, the docs every project keeps). The foreman is
required to read them before planning anything, so the AI team works *your*
way, not a generic way.

---

## 3. The cast

Six seats at the table. Five are AI; the important one is you.

| Seat | Who | Job | Trust level |
|---|---|---|---|
| Owner | **You** | Approve plans. Read diffs. Accept or reject. Merge. Flip agents off when their quota dies. | The only seat that's always right by definition. |
| Foreman (master) | **Claude Code** by default — swappable | Reads your playbooks and the project, proposes a plan, writes work orders, dispatches workers, inspects results, recommends what to merge. Never writes code itself. | High for judgment; still verify — it inspects, you decide. |
| Worker | **Codex** (ChatGPT plan) | The strongest builder. Features, bug fixes, refactoring. First worker to bring online. | Good; still read every diff. |
| Worker | **Antigravity** (`agy`, Google plan) | Huge reading capacity. Best at "read this whole codebase and summarize/mass-edit" jobs. Replaced Gemini CLI (shut down 2026-06-18). | Good at analysis; young tool — verify flags after updates. |
| Worker | **Grok Build** (SuperGrok / X Premium+) | Isolated features and test-writing. The product is a two-month-old beta. | Medium. Review its work extra hard; expect its flags to change. |
| Worker | **OpenCode** (Go plan, $10/mo) | The budget intern. Boring chores only: formatting fixes, boilerplate, documentation, simple tests. Runs cheaper open models. | Lowest. Never give it architecture. |

About **Antigravity**: Google retired the old Gemini CLI on 2026-06-18 and
replaced it with Antigravity CLI — the command is `agy`. It is scriptable
(`agy -p "..."`, plus `--headless --approve all` for unattended runs), so it
holds the Google seat directly. It is a young tool: confirm flags against
`agy --help` after updates, and if background runs behave oddly, read the
task log first — it reacts differently when no human terminal is attached.

**Swapping the foreman:** the foreman is not hardcoded. Whatever agent you
launch inside the project's main folder becomes the foreman, because the
foreman's instruction file sits there under all three filenames the brands
look for. Claude is the default recommendation because planning and
inspection are the highest-judgment jobs in the system, and it's currently
the strongest at them.

---

## 4. The machinery — what's actually on disk

After setup, one project looks like this. Every folder has one job:

```text
myproj/
├── repo/            The real project, on the `dev` timeline.
│   └── MASTER.md    The foreman's standing orders (symlinked as
│                    CLAUDE.md / AGENTS.md / GEMINI.md so any brand
│                    of foreman finds them).
├── wt/              The workshops — one folder per worker.
│   ├── codex/       Full view of the project, pinned to branch agent/codex.
│   │   └── WORKER.md  That worker's standing orders.
│   ├── antigravity/ Same pattern for every worker.
│   ├── opencode/
│   └── grok/
└── coord/           The office. Not part of the project's history —
    │                a shared filing cabinet all sessions can see live.
    ├── base         One word: which timeline is "home" (normally: dev).
    ├── docs/        YOUR playbooks live here. Foreman must read them first.
    ├── board.md     The task board. Only the foreman writes it.
    ├── tasks/       Work orders, one file per task (TEMPLATE.md included).
    ├── reports/     Auto-written result reports + complete work logs.
    ├── blockers.md  "I'm stuck because..." notes. Anyone may append.
    └── STOP         If this file exists, nothing new is allowed to run.
```

Why the office sits OUTSIDE the repo: if work orders lived inside the
project, each worker would see a stale copy of them frozen at the moment
its timeline split off, and their updates would collide when timelines
recombine. Out here, every session reads the same live files. Rule of
thumb baked into the design: **git carries code, plain files carry
conversation.**

And the standing-orders files (MASTER.md / WORKER.md) exist because agents
have short memories: in long sessions, early chat instructions fade, but
these files are re-read automatically. Rules live in files, not in chat.

---

## 5. The controls — every command in plain language

You (or the foreman — it uses the same commands through its terminal
access) drive the system with one program, `unio`:

| Command | In plain language |
|---|---|
| `unio init codex antigravity opencode grok` | "Build the workshops and the office for this project." Run once per project, from inside the repo folder. |
| `unio agents` | "Roll call." Shows each agent: installed? switched on? benched until when? |
| `unio run codex T1-codex` | "Codex — execute work order T1." Runs it in codex's workshop, saves the full log and a result report in the office. |
| `unio run -b grok T2-grok` | Same, but in the background so you can keep issuing commands while grok works. |
| `unio status` | "Morning briefing." Benched agents, open work orders, fresh reports, the state of every workshop, anything still running. |
| `unio diff codex` | "Show me the receipts." The exact changes codex made, compared against the home timeline. The single most important command you own. |
| `unio off antigravity 5h` | "Antigravity is out of quota — bench it for 5 hours." It refuses work and un-benches itself automatically when the time is up. `7d` for a weekly cap; no duration = benched until you say otherwise. |
| `unio on antigravity` | "Back in the game." |
| `unio stop` / `unio resume` | The red button: block ALL new runs project-wide / release it. |

Two safety behaviors run automatically. Every result report ends with the
work log's tail plus a git status — and the log is scanned for phrases like
"usage limit" or "resets at"; if found, it prints the exact `off` command
you should probably run (or benches the agent by itself for 5 hours if you
set `UNIO_AUTO_OFF=1`). And a work order for a benched agent is
refused loudly, never silently queued.

---

## 6. The rules, and what breaks without them

Each rule below is enforced by the standing-orders files. None of them are
etiquette — each one prevents a specific, known disaster.

**Only you merge.** The foreman recommends; you fold work into `dev`.
Without it: an AI resolving a disagreement between two timelines can
produce code that *looks* fine and is subtly broken — the most expensive
class of bug to find.

**Plan first, build after your "go".** Straight from your recipe. Without
it: the team burns a day of quota building the wrong thing confidently.

**Workers never leave their workshop.** Each may edit only files inside
its own folder, and only files listed in its work order. Without it: two
workers edit the same file, and recombining timelines becomes archaeology.

**The diff is the truth; the report is a claim.** Agents sometimes report
success that didn't happen ("tests pass" when they don't). Every
acceptance goes through `unio diff`. Without it: fiction enters your
project with a confident summary attached.

**Work orders are self-contained.** The amnesia principle from the
dictionary: the worker knows nothing except what's written in its task
file. Without it: the worker fills the gaps with guesses, and guesses look
exactly like code.

**Contracts are frozen before parallel work starts.** If codex builds a
data format and antigravity builds the screen that displays it, the format is
written down and committed *first*, and both work orders point at it.
Without it: two halves that each work and don't fit together.

**One dependency owner per cycle.** Exactly one worker per round may touch
the project's shared ingredient lists (dependency files — the lists of
outside libraries the project uses). Without it: the single most common
collision in parallel work.

**The milestone gate.** From your recipe — work is accepted only when the
project builds cleanly (zero warnings where you enforce that), tests pass,
a real run succeeds, and the CHANGELOG (the project's session log) has an
entry. Without it: "done" means "probably done," and probably-done rots.

**Commit hygiene.** Workers save snapshots of only the files they
deliberately changed, never a blanket "everything in the folder." From
your playbook. Without it: accidental junk rides along in history forever.

---

## 7. A full working day, narrated

Concrete example: your vectorizer app needs a "export as PNG" button. Here
is the entire cycle, exactly as it plays out.

**Step 1 — you brief the foreman.** In a terminal, you go to the project's
`repo/` folder, type `claude`, and Claude Code opens as the foreman
(because MASTER.md is sitting there). You type, in plain English:

> Read MASTER.md and the playbooks in ../coord/docs/. I want an "export as
> PNG" button next to the existing SVG export. Propose a task breakdown and
> wait for my go.

**Step 2 — the foreman plans.** It reads your playbooks, studies the
project (using CodeGraph to find the export code instead of reading every
file), and comes back with something like: "Two tasks. T1-codex: add the
PNG rendering function — touches only the export folder. T2-grok: add the
button and wire it up — touches only the UI folder, and uses the function
signature I'll freeze first. Estimated one cycle. Go?"

**Step 3 — you say go.** The foreman commits the frozen "contract" (the
exact name and shape of the new function, so both workers build against
the same thing), writes two work-order files into `coord/tasks/`, updates
the board, and dispatches:

```text
unio run -b codex T1-codex
unio run -b grok  T2-grok
```

Both workers now build simultaneously, each in its own workshop. You can
watch with `unio status`, or walk away.

**Step 4 — results come back.** Each run leaves two things in
`coord/reports/`: the complete raw log, and a report ending with the
worker's own summary (what it changed, what it tested, what it's unsure
about) plus an automatic git status. The foreman reads both reports — and
then does the thing that actually matters:

**Step 5 — inspection.** `unio diff codex`. Removed lines start with
`-`, added lines with `+`. You don't need to understand every line to
review usefully. You're checking: Are the changed files the ones the work
order allowed? Is the size sane (a button shouldn't be 2,000 lines)? Do the
`+` lines mention the things the task was about? Did tests get added or
changed? The foreman does the deep code-quality read and reports; you do
the sanity read and decide.

**Step 6 — the gate.** Accepted only if: build clean, tests green, smoke
run works, CHANGELOG entry present. Say grok's diff shows it also
"improved" a file outside its scope — that's a rejection. The foreman
writes a sharper work order (T2b), re-dispatches, and the second diff
comes back clean.

**Step 7 — you merge.** In `repo/`:

```text
git merge --no-ff agent/codex
git merge --no-ff agent/grok
```

The two timelines fold into `dev`. The feature exists. `main` remains
untouched — it only moves when you explicitly release a version, per your
own git model.

Total human effort: one brief, one "go", two sanity reads, two merge
commands. Total elapsed time: however long the slowest worker took —
they ran in parallel.

---

## 8. THE ROADMAP

Do the phases in order. Each has a goal, steps, a realistic time cost, a
"you are done when" test, and the failure you're most likely to hit. Do
not skip Phase 1 — it's where diff-reading stops being scary, and
everything after depends on that.

### Phase 0 — Build the garage *(one evening)*

Goal: a VM where every agent answers when called.

1. On the Ubuntu VM, run the installer: `bash unio-install.sh`.
2. Install each agent CLI and log in once each (the exact commands are in
   AGENTTEAM-README §2 — each login opens a web page where you sign in
   with that service's account; the terminal remembers it afterwards).
3. Roll call: `unio agents` — every configured row should say OK.
4. Prove each one is alive with the one-liners: `claude -p "say ok"`,
   `codex exec "say ok"`, `agy -p "say ok"`, `opencode run "say ok"`,
   `grok -p "say ok"`.
5. Install CodeGraph and wire it to the agents (one command, playbook §3).
6. Take a VM snapshot. Label it "clean garage."

**Done when** all five one-liners answer. **Likely failure:** a login that
didn't stick or a command not found — fix logins by rerunning the agent
interactively once; fix "not found" by checking PATH (dictionary, §2).

### Phase 1 — One worker, no foreman, toy project *(one evening)*

Goal: feel the whole loop with your own hands before trusting anyone
else's, on a project that cannot matter.

1. Make a scratch project (any tiny folder with a git history — even a
   folder with one text file).
2. `unio init codex` — one workshop.
3. Copy `coord/tasks/TEMPLATE.md` to `T1-codex.md` and write a trivial
   work order YOURSELF: "create a file called hello.txt containing the
   word hello; that file is your entire allowed scope."
4. `unio run codex T1-codex`. Read the report in `coord/reports/`.
5. `unio diff codex` — read your first diff. It will be three lines.
6. Merge it: `git merge --no-ff agent/codex` inside the repo folder.
7. Practice the switches: `unio off codex 5h`, watch a run get
   refused, `unio on codex`. Touch the red button: `unio stop`,
   `unio resume`.

**Done when** you have personally written a work order, read a diff, and
merged a branch — even a toy one. **Likely failure:** running commands
from the wrong folder ("not inside a Unio project" — go into the
repo or any project subfolder first).

### Phase 2 — Foreman + one worker, real but small *(a weekend)*

Goal: hand the steering wheel to the foreman and learn to supervise
instead of operate.

1. Pick a real but low-stakes project. Set it up per your own playbook
   (AGENTS.md router, docs/ai/, dev branch). `unio init codex`.
2. Copy your two playbooks into `coord/docs/`.
3. Open `claude` in `repo/` and give it the briefing prompt (README §4).
4. Let the foreman write the work orders this time. Read them before
   saying go — you're checking they're self-contained (would a total
   stranger know what to do?) and small (one concern each).
5. Run the cycle to a merge. Then run two more cycles.

**Done when** three foreman-written tasks have crossed your gate and been
merged, and at least one got rejected once and redone (if none did, your
gate is too soft — look harder). **Likely failure:** vague work orders
producing garbage diffs. The fix is always the same: sharper task file,
never "hope it does better this time."

### Phase 3 — Grow the crew, learn quota juggling *(a normal week of use)*

Goal: parallel work, and limits handled as routine instead of crisis.

1. Add workers one at a time, in this order: antigravity (`unio init
   antigravity`), then grok, then opencode. Give each a first task suited to
   its strength (§3's table) and judge its diffs for a day before adding
   the next.
2. First time two workers run simultaneously, make sure their work orders
   share zero files — check the "Allowed scope" lines against each other.
3. When any service whines about limits mid-run, the report will flag it
   and print the bench command. Bench it (`off <agent> 5h` or `7d`), tell
   the foreman to reroute per its fallback policy, keep working.
4. Keep score for the week, per agent: tasks given / diffs accepted
   first try / diffs rejected. This is your real quality data.

**Done when** you've survived one full quota outage without the day
stopping, and you can say from your scorecard which agent earns its seat.
**Likely failure:** giving the weak agents interesting work because the
strong ones are benched. Boring work goes to the bench-warmers; the
interesting work *waits* for codex/claude to come back.

### Phase 4 — Full operation *(ongoing)*

Goal: this is just how you build software now.

1. Standard cycle: brief → plan → go → parallel build → inspect → merge.
   Background runs (`-b`) as default; `unio status` as your morning
   briefing.
2. Board discipline: the foreman keeps `coord/board.md` current; you can
   glance at one file and know the state of everything.
3. Cut the losers: any agent below roughly half of codex's acceptance
   rate on your scorecard gets only chores, or gets dropped. Its
   subscription money moves to a bigger plan on a winner.
4. Releases stay yours and manual, per your model: merge `dev` into
   `main` and tag, only when you decide it's a release.

**Done when** a feature you didn't write any code for ships in a release
you did sign off on.

### Phase 5 — Later, when it earns it *(optional)*

Only touch these when a real pain shows up. Two workshops for the same
engine when one is your bottleneck (`unio init codex-2`). A
project-specific crew via `coord/agents.conf`. Automatic testing on
GitHub (every push gets tested in the cloud, so "tests green" stops
depending on anyone's honesty — this is the "CI" developers talk about).
Bigger subscription tiers when the scorecard proves an agent is earning
more than its quota allows. A fifth seat is the same recipe:
one line in `agents.conf`, one `unio init <name>`.

---

## 9. When things go wrong

| What you see | What it means | What to do |
|---|---|---|
| `unio: command not found` | The terminal can't find the program (PATH). | `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc` |
| `not inside a Unio project` | You're in a folder with no `coord/` + `wt/` above it. | `cd` into the project's repo folder first. |
| A worker "hangs" forever | It's waiting on a question its auto-approve mode didn't cover, or its login expired. | Open `coord/reports/<task>.log` and read the end; re-login that agent interactively; rerun. |
| Run fails instantly, log nearly empty | Agent not logged in, or its command flag changed (Grok beta especially). | `unio agents`, then the Phase-0 one-liner for that agent; fix the line in `agents.conf` if the flag moved. |
| Report says success, diff looks wrong | The agent is overclaiming — this is normal, not an emergency. | Reject. Foreman writes a sharper work order. This is the system working. |
| "usage limit / resets at" in a log | Quota window burned. | `unio off <agent> 5h` (weekly: `7d`), reroute, carry on. |
| Two workers changed the same file | A work order broke the disjoint-scope rule. | Accept one, reject the other, fix the scopes; tighten the foreman's task-writing with feedback. |
| Everything is on fire | — | `unio stop`, breathe, read `status` and the last reports, `resume` when you understand what happened. Worst case: restore the VM snapshot; committed work survives in the repo. |

**Known honest limits of the system.** The quota detector matches common
error phrasings; it will miss unusual ones — the manual `off` switch is
the primary tool, the detector is a helper. Grok Build is beta software;
budget patience. Antigravity is a passenger until Google documents it.
And no rule file makes an agent obedient with certainty — the workshops,
receipts, and your gate are the actual guarantees, which is why none of
them are optional.

---

## 10. Where each piece of paper lives

- **This file (MASTER-PLAN.md)** — the explanation and the roadmap. Read
  once fully; revisit the dictionary and troubleshooting as needed.
- **AGENTTEAM-README.md** — the daily reference card: exact install
  commands, per-agent login table, command list, tuning.
- **unio-install.sh** — the installer. You run it once per VM; you
  never need to read it.
- **multi-agent-claude-review.md** — the background research: why this
  architecture, what the services' terms allow, what alternatives exist,
  with sources. Useful when you wonder "why was it built this way?"
- **Your playbooks** (`ai-project-setup-playbook.md`,
  `ai-full-build-recipe.md`) — your standards. They outrank everything
  above about *how projects are built*; this system is the delivery
  mechanism that makes a team of AIs follow them.
