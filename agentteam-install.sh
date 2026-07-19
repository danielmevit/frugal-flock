#!/usr/bin/env bash
# agentteam installer — one-master / many-CLI-workers orchestration for a
# single Ubuntu VM. No API keys, no browser automation: every agent runs its
# own official CLI headless under its own subscription login.
# Installs: ~/.local/bin/agentteam, ~/.config/agentteam/agents.conf (EDIT),
#           ~/.config/agentteam/templates/
# Then:     cd <your repo clone> && agentteam init codex antigravity opencode grok
set -euo pipefail

BIN_DIR="$HOME/.local/bin"
CONF_DIR="$HOME/.config/agentteam"
TPL_DIR="$CONF_DIR/templates"
mkdir -p "$BIN_DIR" "$CONF_DIR" "$TPL_DIR"

# ---------------------------------------------------------------- agentteam
cat > "$BIN_DIR/agentteam" <<'AGENTTEAM_BIN_EOF'
#!/usr/bin/env bash
# agentteam — delegate tasks from a master CLI session to worker CLI agents.
# Layout (created by `agentteam init` next to your repo clone):
#   PROJECT/<clone>/  your repo on the base branch (dev) -> master runs here
#   PROJECT/wt/<w>/   one git worktree per worker, branch agent/<w>
#   PROJECT/coord/    board.md, base, docs/, tasks/, reports/, blockers.md, STOP
set -euo pipefail

CONF_DIR="${AGENTTEAM_CONF_DIR:-$HOME/.config/agentteam}"
CONF_FILE="$CONF_DIR/agents.conf"
TPL_DIR="$CONF_DIR/templates"
OFF_DIR="$CONF_DIR/off"
TIMEOUT="${AGENTTEAM_TIMEOUT:-3600}"

die() { echo "agentteam: $*" >&2; exit 1; }

find_root() {
  local d="$PWD"
  while [ "$d" != "/" ]; do
    if [ -d "$d/coord" ] && [ -d "$d/wt" ]; then echo "$d"; return 0; fi
    d=$(dirname "$d")
  done
  return 1
}

get_base() { cat "$1/coord/base" 2>/dev/null || echo main; }

conf_for_root() {
  local root="$1"
  if [ -f "$root/coord/agents.conf" ]; then echo "$root/coord/agents.conf"
  else echo "$CONF_FILE"; fi
}

agent_cmd() {
  local agent="$1" conf="$2" line
  line=$(grep -E "^${agent}=" "$conf" 2>/dev/null | head -1 || true)
  [ -n "$line" ] || return 1
  printf '%s\n' "${line#*=}"
}

# ---- quota on/off switch ----------------------------------------------
parse_dur() { # 30m / 5h / 7d / plain seconds -> seconds
  local d="$1" n="${1%[mhd]}"
  case "$n" in ''|*[!0-9]*) return 1;; esac
  case "$d" in
    *m) echo $((n*60));; *h) echo $((n*3600));; *d) echo $((n*86400));;
    *) echo "$n";;
  esac
}

is_off() { # true if agent is off; auto-clears expired markers
  local f="$OFF_DIR/$1" exp
  [ -f "$f" ] || return 1
  exp=$(cat "$f" 2>/dev/null || true)
  if [ -n "$exp" ] && [ "$(date +%s)" -ge "$exp" ]; then rm -f "$f"; return 1; fi
  return 0
}

off_desc() {
  local exp; exp=$(cat "$OFF_DIR/$1" 2>/dev/null || true)
  if [ -z "$exp" ]; then echo "manual — re-enable with: agentteam on $1"
  else echo "auto-on in $(( (exp - $(date +%s) + 59) / 60 ))m"; fi
}

cmd_off() {
  local agent="${1:-}"; [ -n "$agent" ] || die "usage: agentteam off <agent> [30m|5h|7d]"
  mkdir -p "$OFF_DIR"
  if [ -n "${2:-}" ]; then
    local secs; secs=$(parse_dur "$2") || die "bad duration '$2' (30m / 5h / 7d)"
    echo $(( $(date +%s) + secs )) > "$OFF_DIR/$agent"
  else
    : > "$OFF_DIR/$agent"
  fi
  echo "agent '$agent' OFF — $(off_desc "$agent")"
}

cmd_on() {
  local a="${1:-}"; [ -n "$a" ] || die "usage: agentteam on <agent>"
  rm -f "$OFF_DIR/$a"; echo "agent '$a' ON"
}

# ------------------------------------------------------------------ init
cmd_init() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || die "run 'agentteam init' from inside your repo clone"
  local main_dir root base
  main_dir=$(git rev-parse --show-toplevel)
  root=$(dirname "$main_dir")
  local workers=("$@")
  [ ${#workers[@]} -gt 0 ] || workers=(codex antigravity opencode grok)

  mkdir -p "$root/wt" "$root/coord/tasks" "$root/coord/reports" "$root/coord/docs"
  [ -f "$root/coord/board.md" ]          || cp "$TPL_DIR/board.md" "$root/coord/board.md"
  [ -f "$root/coord/tasks/TEMPLATE.md" ] || cp "$TPL_DIR/TASK.md" "$root/coord/tasks/TEMPLATE.md"
  [ -f "$root/coord/blockers.md" ]       || printf '# Blockers (append-only)\n' > "$root/coord/blockers.md"
  [ -f "$root/coord/docs/PROTOCOL.md" ]  || cp "$TPL_DIR/PROTOCOL.md" "$root/coord/docs/PROTOCOL.md" 2>/dev/null || true

  # base branch: Daniel's model = dev (main is releases only); fallback = HEAD
  if [ ! -f "$root/coord/base" ]; then
    if git -C "$main_dir" rev-parse -q --verify dev >/dev/null; then base=dev
    else base=$(git -C "$main_dir" symbolic-ref --short HEAD); fi
    echo "$base" > "$root/coord/base"
  fi
  base=$(get_base "$root")

  # keep role cards + codegraph index out of git (repo .gitignore untouched)
  local excl
  excl="$(cd "$main_dir" && git rev-parse --path-format=absolute --git-common-dir)/info/exclude"
  local f
  for f in MASTER.md WORKER.md CLAUDE.md AGENTS.md GEMINI.md .codegraph/; do
    grep -qxF "$f" "$excl" 2>/dev/null || echo "$f" >> "$excl"
  done

  # master role card — readable by any master CLI via symlinked names
  [ -f "$main_dir/MASTER.md" ] || cp "$TPL_DIR/MASTER.md" "$main_dir/MASTER.md"
  local name
  for name in CLAUDE.md AGENTS.md GEMINI.md; do
    if [ -e "$main_dir/$name" ] && [ ! -L "$main_dir/$name" ]; then
      echo "note: $main_dir/$name exists (your repo router) — add one line to it: 'Also read and follow MASTER.md.'" >&2
    else
      ln -sfn MASTER.md "$main_dir/$name"
    fi
  done

  # worker worktrees + role cards (+ CodeGraph index per worktree if present)
  local w agent conf
  conf=$(conf_for_root "$root")
  for w in "${workers[@]}"; do
    if [ ! -d "$root/wt/$w" ]; then
      git -C "$main_dir" worktree add "$root/wt/$w" -b "agent/$w" "$base" >/dev/null 2>&1 \
        || git -C "$main_dir" worktree add "$root/wt/$w" "agent/$w" >/dev/null
    fi
    sed "s/{{WORKER}}/$w/g" "$TPL_DIR/WORKER.md" > "$root/wt/$w/WORKER.md"
    for name in CLAUDE.md AGENTS.md GEMINI.md; do
      if [ -e "$root/wt/$w/$name" ] && [ ! -L "$root/wt/$w/$name" ]; then
        echo "note: $root/wt/$w/$name exists — add 'Also read and follow WORKER.md.' to it" >&2
      else
        ln -sfn WORKER.md "$root/wt/$w/$name"
      fi
    done
    if command -v codegraph >/dev/null 2>&1; then
      (cd "$root/wt/$w" && codegraph init >/dev/null 2>&1) || true
    fi
    agent="${w%%-*}"
    agent_cmd "$agent" "$conf" >/dev/null \
      || echo "warn: no agents.conf entry for agent '$agent' (worker '$w') — edit $conf" >&2
  done

  echo "project root : $root"
  echo "base branch  : $base   (override: edit coord/base)"
  echo "master       : $main_dir  (open your master CLI here)"
  echo "workers      : ${workers[*]}"
  echo "playbooks    : drop your operational .md files into $root/coord/docs/"
  echo "next         : agentteam agents"
}

# ------------------------------------------------------------------- run
cmd_run() {
  local bg=0
  if [ "${1:-}" = "-b" ]; then bg=1; shift; fi
  local worker="${1:-}" task="${2:-}"
  [ -n "$worker" ] && [ -n "$task" ] || die "usage: agentteam run [-b] <worker> <task-id>"
  local root; root=$(find_root) || die "not inside an agentteam project"
  [ -f "$root/coord/STOP" ] && die "STOP is active (agentteam resume to clear)"
  task="${task%.md}"
  local tf="$root/coord/tasks/$task.md"
  [ -f "$tf" ] || die "no task file: $tf"
  local wt="$root/wt/$worker"
  [ -d "$wt" ] || die "no worktree for '$worker' — run: agentteam init $worker"
  local agent="${worker%%-*}" conf cmdline base
  is_off "$agent" && die "agent '$agent' is OFF ($(off_desc "$agent")) — reassign the task or: agentteam on $agent"
  conf=$(conf_for_root "$root")
  cmdline=$(agent_cmd "$agent" "$conf") || die "no agents.conf entry for '$agent' in $conf"
  base=$(get_base "$root")

  local report="$root/coord/reports/$task.md"
  local log="$root/coord/reports/$task.log"

  if [ "$bg" = 1 ]; then
    nohup "$0" run "$worker" "$task" >/dev/null 2>&1 &
    echo "started in background (pid $!) — poll with: agentteam status"
    return 0
  fi

  echo "[$worker <- $agent] running task '$task' (timeout ${TIMEOUT}s), log: $log"
  export TASKFILE="$tf"
  local rc=0
  ( cd "$wt" && timeout "$TIMEOUT" bash -c "$cmdline" ) > "$log" 2>&1 || rc=$?

  {
    echo
    echo "## run $(date -Is) — worker=$worker agent=$agent exit=$rc"
    echo
    echo "### git status (branch, staged/unstaged)"
    git -C "$wt" status --porcelain=v1 -b
    echo
    echo "### committed diffstat vs $base"
    git -C "$wt" diff --stat "$base...HEAD" 2>/dev/null || echo "(none)"
    echo
    echo "### agent output (tail)"
    echo '~~~'
    tail -n 60 "$log"
    echo '~~~'
  } >> "$report"

  if grep -qiE 'rate.?limit|usage limit|limit (reached|exceeded)|quota|too many requests|resets (at|in)' "$log"; then
    echo "!! output mentions usage limits — if '$agent' hit its 5h/weekly cap:  agentteam off $agent 5h   (weekly: 7d)" >&2
    if [ "${AGENTTEAM_AUTO_OFF:-0}" = "1" ]; then cmd_off "$agent" 5h >&2; fi
  fi

  echo "exit=$rc — report: $report"
  return "$rc"
}

cmd_diff() {
  local worker="${1:-}"; [ -n "$worker" ] || die "usage: agentteam diff <worker> [--stat]"
  local root; root=$(find_root) || die "not inside an agentteam project"
  local wt="$root/wt/$worker"; [ -d "$wt" ] || die "no worktree: $wt"
  local mode="${2:-}" base; base=$(get_base "$root")
  echo "== branch/status =="
  git -C "$wt" status -sb
  echo; echo "== committed vs $base =="
  if [ "$mode" = "--stat" ]; then git -C "$wt" diff --stat "$base...HEAD" || true
  else git -C "$wt" diff "$base...HEAD" || true; fi
  echo; echo "== uncommitted =="
  if [ "$mode" = "--stat" ]; then git -C "$wt" diff --stat HEAD || true
  else git -C "$wt" diff HEAD || true; fi
}

cmd_status() {
  local root; root=$(find_root) || die "not inside an agentteam project"
  [ -f "$root/coord/STOP" ] && echo "!! STOP is active — runs are blocked" && echo
  echo "== agents off (quota) =="
  local f a found=0
  for f in "$OFF_DIR"/*; do
    [ -e "$f" ] || continue
    a=$(basename "$f")
    if is_off "$a"; then echo "  $a — $(off_desc "$a")"; found=1; fi
  done
  [ "$found" = 1 ] || echo "  (none — all agents on)"
  echo; echo "== tasks (coord/tasks) =="
  ls -1 "$root/coord/tasks" 2>/dev/null | grep -v '^TEMPLATE\.md$' || echo "(none)"
  echo; echo "== recent reports (coord/reports) =="
  ls -lt "$root/coord/reports" 2>/dev/null | head -12 || true
  echo; echo "== workers =="
  local wt
  for wt in "$root"/wt/*/; do
    [ -d "$wt" ] || continue
    echo "-- $(basename "$wt")"
    git -C "$wt" status -sb | head -4
  done
  echo; echo "== running =="
  pgrep -af "bin/agentteam run" 2>/dev/null | grep -v "^$$ " || echo "(none)"
}

cmd_agents() {
  local root conf; root=$(find_root 2>/dev/null || true)
  if [ -n "${root:-}" ]; then conf=$(conf_for_root "$root"); else conf="$CONF_FILE"; fi
  echo "config: $conf"
  local line name cmd bin state
  while IFS= read -r line; do
    case "$line" in ''|'#'*) continue;; esac
    name="${line%%=*}"; cmd="${line#*=}"; bin="${cmd%% *}"
    if is_off "$name"; then state="OFF ($(off_desc "$name"))"
    else state="on"; fi
    if command -v "$bin" >/dev/null 2>&1; then
      printf '  %-12s OK       %-4s %s\n' "$name" "$state" ""
    else
      printf '  %-12s MISSING  %-4s binary "%s" not on PATH\n' "$name" "$state" "$bin"
    fi
  done < "$conf"
}

cmd_smoke() { # one tiny live call per configured agent — the post-update ritual
  local root conf; root=$(find_root 2>/dev/null || true)
  if [ -n "${root:-}" ]; then conf=$(conf_for_root "$root"); else conf="$CONF_FILE"; fi
  local tf; tf=$(mktemp); printf 'Reply with exactly: ok\n' > "$tf"
  local line name cmd rc out
  while IFS= read -r line; do
    case "$line" in ''|'#'*) continue;; esac
    name="${line%%=*}"; cmd="${line#*=}"
    if is_off "$name"; then printf '  %-12s SKIP (benched)\n' "$name"; continue; fi
    if ! command -v "${cmd%% *}" >/dev/null 2>&1; then printf '  %-12s MISSING binary\n' "$name"; continue; fi
    rc=0; out=$(TASKFILE="$tf" timeout 180 bash -c "$cmd" 2>&1) || rc=$?
    if [ "$rc" -eq 0 ]; then printf '  %-12s OK\n' "$name"
    else printf '  %-12s FAIL exit=%s — %s\n' "$name" "$rc" "$(printf '%s' "$out" | tail -1 | cut -c1-70)"; fi
  done < "$conf"
  rm -f "$tf"
}

cmd_stop()   { local root; root=$(find_root) || die "not in a project"; touch "$root/coord/STOP"; echo "STOP set — new runs blocked (running tasks finish or hit timeout)"; }
cmd_resume() { local root; root=$(find_root) || die "not in a project"; rm -f "$root/coord/STOP"; echo "STOP cleared"; }

cmd_help() {
  cat <<'HELP'
agentteam — one master CLI session delegating to worker CLI agents

  agentteam init [workers...]      scaffold wt/ + coord/ next to your clone
                                   (default: codex antigravity opencode grok)
  agentteam agents                 list agents: binary found? on/off?
  agentteam run [-b] <w> <task>    run coord/tasks/<task>.md with worker <w>
                                   in its worktree; -b = background
  agentteam diff <w> [--stat]      review a worker's changes vs base branch
  agentteam status                 off-agents, tasks, reports, branches, jobs
  agentteam off <agent> [30m|5h|7d]  quota switch: disable an agent
                                   (5h window: off 5h; weekly cap: off 7d;
                                    no duration = until 'agentteam on')
  agentteam on <agent>             re-enable an agent
  agentteam smoke                  one tiny live call per agent — run after
                                   every CLI update to catch renamed flags
  agentteam stop | resume          project kill switch for ALL runs

Worker -> agent: prefix before first "-" ("codex-2" uses agent "codex").
Agent commands: ~/.config/agentteam/agents.conf (project override:
coord/agents.conf). Base branch: coord/base. AGENTTEAM_TIMEOUT (3600s);
AGENTTEAM_AUTO_OFF=1 auto-disables an agent 5h when its output mentions
usage limits.
HELP
}

case "${1:-help}" in
  init)    shift; cmd_init "$@";;
  run)     shift; cmd_run "$@";;
  diff)    shift; cmd_diff "$@";;
  status)  shift; cmd_status "$@";;
  agents)  shift; cmd_agents "$@";;
  off)     shift; cmd_off "$@";;
  on)      shift; cmd_on "$@";;
  smoke)   shift; cmd_smoke "$@";;
  stop)    shift; cmd_stop "$@";;
  resume)  shift; cmd_resume "$@";;
  help|-h|--help) cmd_help;;
  *) die "unknown command '${1}' (agentteam help)";;
esac
AGENTTEAM_BIN_EOF
chmod +x "$BIN_DIR/agentteam"
# ------------------------------------------------------------- agents.conf
if [ -f "$CONF_DIR/agents.conf" ]; then
  echo "keeping existing $CONF_DIR/agents.conf"
else
cat > "$CONF_DIR/agents.conf" <<'AGENTS_CONF_EOF'
# agentteam agents.conf — one line per agent:  name=shell command
# $TASKFILE = task file path. Commands run INSIDE the worker's worktree.
# Lego rules: add/remove lines freely; disable a quota-dead agent with
# `agentteam off <name> 5h` (or 7d for weekly caps) — no editing needed.
# Syntax verified against official docs 2026-07-10; recheck with --help.

# Claude Code (Anthropic sub). Unattended => skip-permissions; VM-only setting.
claude=claude -p "$(cat "$TASKFILE")" --dangerously-skip-permissions

# Codex CLI (ChatGPT plan). exec = non-interactive. danger-full-access is
# required: workspace-write keeps .git read-only and a worktree's git
# metadata lives in the main repo's .git/worktrees/ — commits fail otherwise.
# Same trust level as the other agents' auto-approve modes; VM-only setup.
codex=codex exec --sandbox danger-full-access "$(cat "$TASKFILE")"

# Antigravity CLI "agy" (Google account) — replaced Gemini CLI, which Google
# shut down 2026-06-18. Flags verified on a live install 2026-07-17:
# -p = non-interactive print mode; --dangerously-skip-permissions =
# auto-approve; print timeout defaults to only 5m, so raise it. VM-only.
antigravity=agy -p "$(cat "$TASKFILE")" --dangerously-skip-permissions --print-timeout 55m

# OpenCode (Go plan or Copilot login). Verified on a live install
# 2026-07-17: --dangerously-skip-permissions replaced the older --auto.
# NOTE: for `opencode run`, -p means password, NOT prompt — task text is
# passed as a plain argument. Model if needed: opencode models, then -m.
opencode=opencode run --dangerously-skip-permissions "$(cat "$TASKFILE")"

# Grok Build (SuperGrok / X Premium+; early beta — flags may change).
# Note: CodeGraph has no Grok wiring — Grok uses `codegraph explore` via shell.
grok=grok -p "$(cat "$TASKFILE")" --always-approve

AGENTS_CONF_EOF
fi

# ---------------------------------------------------------------- templates
cat > "$TPL_DIR/MASTER.md" <<'MASTER_TPL_EOF'
# Role: Team lead (plan, delegate, review, integrate — do NOT implement)

You are the master session of a multi-agent CLI team. Daniel is the human
owner: he approves plans and he merges. You never merge, never write code.

Layout: this dir = the base branch (see ../coord/base — normally `dev`;
`main` is releases only, per Daniel's git model). Workers = ../wt/<name>,
git worktrees on branch agent/<name>, each a different AI CLI.
Coordination = ../coord.

## Reading ritual (before any planning)
1. ../coord/docs/*.md — Daniel's operational playbooks (project setup
   standard + full-build recipe). They define the working style: plan from
   the reference, verified milestones, evaluation-first, docs upkeep.
2. This repo's own AGENTS.md router and docs/ai/START_HERE.md, if present.
3. Navigate code with CodeGraph (`codegraph explore "..."`) — no grep-loops.
Plan first: present the breakdown to Daniel; delegate only after his "go".

## How to delegate
1. `agentteam agents` — who is ON. OFF = quota-exhausted (5h/weekly cap).
   Reroute per the policy below; never queue work on an OFF agent. If a
   worker's output hits a limit mid-cycle, tell Daniel and suggest
   `agentteam off <agent> 5h` (weekly: 7d).
2. Write ../coord/tasks/<ID>-<worker>.md from TEMPLATE.md. Workers have
   ZERO memory of this chat — task files must be self-contained.
3. `agentteam run <worker> <ID>-<worker>` (long: add -b, poll with status).
4. Read ../coord/reports/<ID>-<worker>.md, then verify the REAL diff:
   `agentteam diff <worker>`. Never trust a report without the diff.
5. Accept only if the milestone gate passes: clean build (0 warnings where
   the repo enforces it) + tests green + smoke run + CHANGELOG.md entry (if
   the repo keeps one). Then tell Daniel the branch is ready to merge into
   the base branch. Reject -> sharper task file (<ID>b), rerun. Two failed
   attempts -> escalate to Daniel.

## Delegation policy (strength -> fallback when OFF)
- codex     implementation, refactors, debugging      -> claude-w, grok
- antigravity  huge-context analysis, mechanical bulk -> codex
- grok      isolated features, tests (BETA: review hard) -> codex
- opencode  chores: boilerplate, lint, docs           -> any idle agent
- claude-w  (optional Claude worker) genuinely hard work
- you       contracts, architecture, task design, all review, integration

## Rules
- Freeze shared contracts (types/schemas/fixtures) on the base branch
  BEFORE delegating dependent tasks; cite them (path @ sha) in task files.
- Disjoint scopes; exactly one dependency owner (lockfiles, migrations)
  per cycle.
- You alone write ../coord/board.md (one row per task); read blockers.md
  every cycle; if ../coord/STOP exists, stop delegating immediately.

## Fleet intelligence
- `myapp <project-root>` prints the per-agent scorecard (runs, fails,
  walls, merges) for any agentteam project. Consult it when assigning
  tasks — favor agents that earn merges; flag chronic wall-hitters.
MASTER_TPL_EOF

cat > "$TPL_DIR/WORKER.md" <<'WORKER_TPL_EOF'
# Role: worker "{{WORKER}}"

You are one worker in a multi-agent team. Your entire assignment is the
task prompt you were given. Follow it exactly.

- Onboard first if present: this repo's AGENTS.md and docs/ai/START_HERE.md
  (reading ritual). The rules HERE override them on branches, scope, commits.
- Work ONLY in this directory — a git worktree on branch agent/{{WORKER}}.
  Never switch branches, never push, never touch the base branch (dev/main).
- Modify only files in the task's "Allowed scope". Need something outside
  it? Do NOT touch it — finish what you can, state the need in your report.
- No architecture changes, no new dependencies, unless the task grants them.
- Find code with CodeGraph (`codegraph explore "..."`) when available; run
  `codegraph sync` after edits if the index seems stale.
- Run the task's Validate commands before finishing. Add a CHANGELOG.md
  entry if the repo keeps one.
- Commit ONLY the files you changed — `git add <specific paths>`, never a
  blind `git add -A` (no sweeping in line-ending or file-mode churn).
  Message: "<ID>: <summary>".
- System spec (read-only, if rules seem ambiguous):
  ../../coord/docs/PROTOCOL.md
- End your output with exactly: SUMMARY / FILES CHANGED / TESTS RUN +
  RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW
WORKER_TPL_EOF

cat > "$TPL_DIR/TASK.md" <<'TASK_TPL_EOF'
# Task <ID> — worker: <name>

## Goal
One specific, testable outcome. One task = one concern.

## Context
Everything the worker needs (it has NO memory of prior discussion): what
the code does now, relevant files and roles, decisions already made, frozen
contracts ("types in src/api/types.ts @ <sha> — do not change them").

## Allowed scope
Exact files/dirs it may create or modify. Everything else is off-limits.

## Constraints
Libraries to use/avoid, style, frozen interfaces, no new deps.

## Validate
Exact commands + expected outcome, e.g.:
  dotnet build   (0 warnings, 0 errors)   /   npm test -- --run auth
Include the smoke command if the repo has one (e.g. app --smoke).

## Done means
Validation passes + CHANGELOG.md entry (if repo keeps one) + changes
committed on your branch — only the files you touched — as "<ID>: <summary>".

## Report
End with: SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS /
RISKS / NEEDS-REVIEW
TASK_TPL_EOF

cat > "$TPL_DIR/board.md" <<'BOARD_TPL_EOF'
# Board — master-owned. One row per task.

Contracts frozen this cycle: (none yet)

| ID | worker | state | branch | scope | done-when |
|----|--------|-------|--------|-------|-----------|
BOARD_TPL_EOF

cat > "$TPL_DIR/PROTOCOL.md" <<'PROTOCOL_TPL_EOF'
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
| `wt/<worker>/` | Worktree on branch `agent/<worker>` | that WORKER only |
| `coord/base` | Base branch name (single word, normally `dev`) | OWNER |
| `coord/docs/` | Operating playbooks + this protocol | OWNER |
| `coord/board.md` | Task board, one row per task | LEAD only |
| `coord/tasks/<ID>-<worker>.md` | Task files (work orders) | LEAD only |
| `coord/reports/<task>.md` | Append-only run history per task | agentteam tooling |
| `coord/reports/<task>.log` | Latest run's full output (overwritten) | agentteam tooling |
| `coord/blockers.md` | Blocker notes | anyone, APPEND only |
| `coord/STOP` | If present: all new runs refused | OWNER |

Data-source rule: historical analysis MUST read `reports/*.md` (append-only,
all runs). `*.log` holds only the latest run and MUST NOT be used as history.

## 3. DATA FORMATS

Report run-block (appended to `coord/reports/<task>.md` per run):

```text
## run <ISO8601 timestamp> — worker=<worker> agent=<agent> exit=<int>
### git status (branch, staged/unstaged)
<porcelain v1 output>
### committed diffstat vs <base>
<diffstat or "(none)">
### agent output (tail)
~~~
<last 60 lines of the run log>
~~~
```

Task file schema (LEAD writes; template at `coord/tasks/TEMPLATE.md`):
sections `Goal` (one testable outcome), `Context` (self-contained — the
worker has zero prior memory), `Allowed scope` (exhaustive path list),
`Constraints`, `Validate` (exact commands), `Done means` (observable +
committed), `Report` (required final sections: SUMMARY / FILES CHANGED /
TESTS RUN + RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW).

Board row schema: `| ID | worker | state | branch | scope | done-when |`
with state ∈ {todo, doing, blocked, review, done}.

Worker→agent resolution: agent id = worker name up to first `-`
(worker `codex-2` → agent `codex`).

## 4. COMMAND API (`agentteam`)

```text
agentteam init [w1 w2 ...]     scaffold worktrees + coord (idempotent)
agentteam agents               list agents: binary present, on/off state
agentteam run [-b] <w> <task>  execute coord/tasks/<task>.md as worker <w>
                               in wt/<w>; -b = background; writes report+log
agentteam diff <w> [--stat]    changes on agent/<w> vs base: committed and
                               uncommitted, separately
agentteam status               off-agents, tasks, reports, worktree states,
                               running jobs
agentteam off <agent> [dur]    bench agent (dur: 30m|5h|7d; absent=manual);
                               run refuses benched agents; expiry auto-clears
agentteam on <agent>           un-bench
agentteam stop | resume        create/remove coord/STOP (global run gate)
```

Environment: `AGENTTEAM_TIMEOUT` (seconds, default 3600) caps each run.
`AGENTTEAM_AUTO_OFF=1` auto-benches an agent 5h when its log matches
limit-language patterns. Agent invocation templates live in
`~/.config/agentteam/agents.conf` (project override: `coord/agents.conf`).

Companion tool: `myapp <project-root>` prints the per-agent scorecard
(runs, ok, fail, walls, merges, last run) computed from reports/*.md and
git merge history. LEAD SHOULD consult it when assigning tasks.

## 5. LIFECYCLE

1. OWNER states intent to LEAD.
2. LEAD reads coord/docs/*, repo docs (AGENTS.md router, docs/ai/), and
   `agentteam agents`; produces a task breakdown; WAITS for OWNER "go".
3. LEAD freezes shared contracts (types/schemas/fixtures) as commits on
   the base branch BEFORE dispatching dependent tasks; task files cite
   contract paths @ sha.
4. LEAD dispatches via `agentteam run`; parallel tasks MUST have disjoint
   Allowed-scope sets; at most one task per cycle may modify dependency
   manifests (package files, lockfiles, migrations).
5. WORKER executes its task file exactly: modifies only Allowed-scope
   paths, runs Validate, commits only files it changed (never blanket
   staging), ends output with the Report sections.
6. LEAD verifies: reads report, reads `agentteam diff`, re-runs tests.
   Reports are claims; diffs are ground truth.
7. OWNER merges accepted branches into base (`git merge --no-ff`).
   Acceptance gate: clean build, tests green, smoke run, CHANGELOG entry
   where the repo keeps one.
8. Releases: OWNER-only, explicit, base→main + tag. Order: merge fix →
   verify → tag.

## 6. INVARIANTS (hard rules, numbered)

- I1  A WORKER writes only inside its own worktree, only within the task's
      Allowed scope.
- I2  Out-of-scope need ⇒ do NOT touch it: finish what is in scope, state
      the need in NEEDS-REVIEW (and blockers.md if blocking). Flagging
      beats fixing — recorded precedent.
- I3  Only OWNER merges to base or main. LEAD recommends; never merges.
- I4  LEAD never writes feature code. Contracts, fixtures, docs, board: yes.
- I5  Workers never switch branches, never push, never touch base/main.
- I6  Same obstacle twice ⇒ stop, write blockers.md; do not improvise
      architecture.
- I7  coord/STOP present ⇒ no new runs, no new dispatches.
- I8  Contracts cited in a task file are frozen: request changes via
      blockers.md, never edit them.
- I9  Benched (OFF) agents get no work; LEAD reroutes by the fallback
      policy in MASTER.md.
- I10 Verification is evidence-based: a claim without a diff/test/log
      backing it is treated as unverified.

## 7. FAILURE PROTOCOL

| Condition | Required behavior |
|---|---|
| Auth/token error in output | Report it verbatim; OWNER re-logins the CLI; task is rerunnable. |
| Limit language in output (rate/usage limit, quota, resets at) | LEAD suggests `agentteam off <agent> 5h` (weekly: 7d) and reroutes. |
| Validate commands fail | Do not claim success. Report failure + hypothesis. |
| Blocked on missing contract/file | I2/I6: flag, don't fix; wait. |
| Task file ambiguous | LEAD: rewrite it. WORKER: state the ambiguity and the interpretation chosen; prefer the narrower reading. |
| Merge conflict on integration | OWNER decision; LEAD proposes resolution order; nobody force-merges. |

## 8. REFERENCES

- Role cards: `MASTER.md` (lead), `WORKER.md` (worker) — override this doc.
- Owner playbooks: `coord/docs/ai-project-setup-playbook.md`,
  `coord/docs/ai-full-build-recipe.md` — define working style (dev/main
  model, verified milestones, evaluation-first, docs upkeep).
- Human documentation: AGENTTEAM-HANDBOOK.md, MASTER-PLAN.md,
  AGENTTEAM-README.md in the agentteam docs repository.
PROTOCOL_TPL_EOF

echo
echo "agentteam installed."
echo "  command   : $BIN_DIR/agentteam   (ensure ~/.local/bin is on PATH)"
echo "  config    : $CONF_DIR/agents.conf   <- EDIT: enable/tune your agents"
echo "  quota     : agentteam off <agent> 5h|7d   /   agentteam on <agent>"
echo
echo "Next: cd <your repo clone> && agentteam init codex antigravity opencode grok"
