#!/usr/bin/env bash
# agentteam installer — one-master / many-CLI-workers orchestration for a
# single Ubuntu VM. No API keys, no browser automation: every agent runs its
# own official CLI headless under its own subscription login.
# Installs: ~/.local/bin/agentteam, ~/.config/agentteam/agents.conf (EDIT),
#           ~/.config/agentteam/templates/
# Then:     agentteam selftest   (mock-agent rehearsal, zero quota)
#           cd <your repo clone> && agentteam init codex antigravity opencode grok
set -euo pipefail

BIN_DIR="${AGENTTEAM_BIN_DIR:-$HOME/.local/bin}"
CONF_DIR="${AGENTTEAM_CONF_DIR:-$HOME/.config/agentteam}"
TPL_DIR="$CONF_DIR/templates"
mkdir -p "$BIN_DIR" "$CONF_DIR" "$TPL_DIR" "$CONF_DIR/playbooks"

# ---------------------------------------------------------------- agentteam
cat > "$BIN_DIR/agentteam" <<'AGENTTEAM_BIN_EOF'
#!/usr/bin/env bash
# agentteam — delegate tasks from a master CLI session to worker CLI agents.
# Layout (created by `agentteam init` next to your repo clone):
#   PROJECT/<clone>/  your repo on the base branch (dev) -> master runs here
#   PROJECT/wt/<w>/   one git worktree per worker, branch agent/<w>
#   PROJECT/coord/    board.md, base, docs/, tasks/, reports/, blockers.md, STOP
set -euo pipefail

AGENTTEAM_VERSION="0.3.1"
CONF_DIR="${AGENTTEAM_CONF_DIR:-$HOME/.config/agentteam}"
CONF_FILE="$CONF_DIR/agents.conf"
TPL_DIR="$CONF_DIR/templates"
OFF_DIR="$CONF_DIR/off"
TIMEOUT="${AGENTTEAM_TIMEOUT:-3600}"
LIMIT_RE='rate.?limit|usage limit|limit (reached|exceeded)|quota|too many requests|resets (at|in)'

die() { echo "agentteam: $*" >&2; exit 1; }

# Worker and task ids address files under wt/ and coord/; keep them simple
# names so they cannot escape those directories.
check_id() { # $1=value $2=what it is
  case "$1" in
    ''|.|..)      die "empty or invalid $2 name";;
    */*|*\\*)     die "$2 name must not contain a path separator: '$1'";;
    -*)           die "$2 name must not start with '-': '$1'";;
    *..*)         die "$2 name must not contain '..': '$1'";;
  esac
}

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

ledger_add() { # $1=root  $2=one JSON object — the machine twin of reports/*.md
  mkdir -p "$1/coord/reports"
  printf '%s\n' "$2" >> "$1/coord/reports/ledger.jsonl"
}

lock_probe() { # $1=root $2=worker; 0 = worker is free
  local lf="$1/coord/.locks/$2.lock"
  [ -e "$lf" ] || return 0
  ( exec 9>>"$lf"; flock -n 9 ) 2>/dev/null
}

task_section() { # $1=task file  $2=section title (text after "## ")
  awk -v s="$2" '/^## /{f=(substr($0,4)==s); next} f' "$1"
}

scope_allowed() { # $1=changed path, rest=patterns; changelog.d/ always in scope
  local f="$1"; shift
  local p
  for p in "$@" "changelog.d/*"; do
    p="${p%/}"
    case "$f" in $p|$p/*) return 0;; esac
  done
  return 1
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
  # worktrees branch from a commit; an unborn HEAD gives a cryptic git error
  git rev-parse -q --verify HEAD >/dev/null 2>&1 \
    || die "this repo has no commits yet — make one first, e.g.:
       git commit --allow-empty -m 'initial commit'"
  local w
  for w in "$@"; do check_id "$w" worker; done
  local main_dir root base
  main_dir=$(git rev-parse --show-toplevel)
  root=$(dirname "$main_dir")
  local workers=("$@")
  [ ${#workers[@]} -gt 0 ] || workers=(codex antigravity opencode grok)

  # preflight: workers run auto-approved — refuse while secrets are tracked
  local leaks
  leaks=$(git -C "$main_dir" ls-files \
    | grep -E '(^|/)\.env(\.|$)|(^|/)id_(rsa|ed25519|ecdsa)($|\.)|\.(pem|p12|pfx)$|(^|/)(credentials|secrets?)\.(json|ya?ml|toml|txt)$' \
    || true)
  if [ -n "$leaks" ] && [ "${AGENTTEAM_ALLOW_SECRETS:-0}" != "1" ]; then
    echo "$leaks" | sed 's/^/  /' >&2
    die "possible secrets tracked in git (above) — untrack/gitignore them first, or rerun with AGENTTEAM_ALLOW_SECRETS=1"
  fi

  mkdir -p "$root/wt" "$root/coord/tasks" "$root/coord/reports" "$root/coord/docs" "$root/coord/.locks"
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

  # guard hooks: a worker worktree commits only on its own branch, never pushes
  local hooks
  hooks="$(cd "$main_dir" && git rev-parse --path-format=absolute --git-common-dir)/hooks"
  mkdir -p "$hooks"
  if [ -f "$hooks/pre-commit" ] && ! grep -q 'agentteam guard' "$hooks/pre-commit"; then
    echo "note: existing pre-commit hook left untouched — worker-branch guard NOT installed" >&2
  else
    cat > "$hooks/pre-commit" <<'HOOK_COMMIT_EOF'
#!/bin/sh
# agentteam guard — inside a worker worktree, commit only on agent/<worker>
gd=$(git rev-parse --git-dir 2>/dev/null) || exit 0
case "$gd" in
  */worktrees/*)
    w=${gd##*/worktrees/}; w=${w%%/*}
    b=$(git rev-parse --abbrev-ref HEAD)
    if [ "$b" != "agent/$w" ]; then
      echo "agentteam guard: worker '$w' must commit on agent/$w (currently on: $b)" >&2
      exit 1
    fi;;
esac
HOOK_COMMIT_EOF
    chmod +x "$hooks/pre-commit"
  fi
  if [ -f "$hooks/pre-push" ] && ! grep -q 'agentteam guard' "$hooks/pre-push"; then
    echo "note: existing pre-push hook left untouched — worker no-push guard NOT installed" >&2
  else
    cat > "$hooks/pre-push" <<'HOOK_PUSH_EOF'
#!/bin/sh
# agentteam guard — workers never push; the owner pushes from repo/
gd=$(git rev-parse --git-dir 2>/dev/null) || exit 0
case "$gd" in
  */worktrees/*)
    echo "agentteam guard: workers do not push (owner pushes from repo/)" >&2
    exit 1;;
esac
HOOK_PUSH_EOF
    chmod +x "$hooks/pre-push"
  fi
  if [ -f "$hooks/post-merge" ] && ! grep -q 'agentteam guard' "$hooks/post-merge"; then
    echo "note: existing post-merge hook left untouched — merges will not be ledger-logged" >&2
  else
    cat > "$hooks/post-merge" <<'HOOK_MERGE_EOF'
#!/bin/sh
# agentteam guard — record every merge into the base branch as a ledger event
gd=$(git rev-parse --git-dir 2>/dev/null) || exit 0
case "$gd" in */worktrees/*) exit 0;; esac
root=$(dirname "$(git rev-parse --show-toplevel)")
[ -d "$root/coord/reports" ] || exit 0
p2=$(git rev-parse -q --verify HEAD^2 2>/dev/null) || exit 0
w=$(git for-each-ref 'refs/heads/agent/*' --points-at "$p2" --format='%(refname:short)' 2>/dev/null | head -1)
w=${w#agent/}
s=$(git log -1 --format=%s | tr '"' "'")
printf '{"event":"merge","ts":"%s","worker":"%s","subject":"%s"}\n' \
  "$(date -Is)" "$w" "$s" >> "$root/coord/reports/ledger.jsonl"
HOOK_MERGE_EOF
    chmod +x "$hooks/post-merge"
  fi

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
  echo "guard hooks  : worker worktrees commit only on agent/<w>, never push"
  echo "playbooks    : drop your operational .md files into $root/coord/docs/"
  echo "next         : agentteam agents"
}

# ------------------------------------------------------------------- run
cmd_run() {
  local bg=0
  if [ "${1:-}" = "-b" ]; then bg=1; shift; fi
  local worker="${1:-}" task="${2:-}"
  [ -n "$worker" ] && [ -n "$task" ] || die "usage: agentteam run [-b] <worker> <task-id>"
  check_id "$worker" worker; check_id "$task" task
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

  mkdir -p "$root/coord/.locks"
  local report="$root/coord/reports/$task.md"
  local log="$root/coord/reports/$task.log"

  if [ "$bg" = 1 ]; then
    lock_probe "$root" "$worker" || die "worker '$worker' is already running a task (agentteam status)"
    if command -v setsid >/dev/null 2>&1; then
      AGENTTEAM_BG=1 nohup setsid -f "$0" run "$worker" "$task" >/dev/null 2>&1
    else
      AGENTTEAM_BG=1 nohup "$0" run "$worker" "$task" >/dev/null 2>&1 &
    fi
    echo "started in background — poll: agentteam status   live: agentteam tail $task   abort: agentteam kill $task"
    return 0
  fi

  # one run per worker: hold the lock for the whole run (freed on exit)
  exec 9>>"$root/coord/.locks/$worker.lock"
  flock -n 9 || die "worker '$worker' is already running a task (agentteam status)"

  local pidfile=""
  if [ "${AGENTTEAM_BG:-0}" = "1" ]; then
    pidfile="$root/coord/reports/$task.pid"
    echo "$$" > "$pidfile"
    trap '[ -n "$pidfile" ] && rm -f "$pidfile"' EXIT
    trap 'exit 143' TERM
    trap 'exit 130' INT
  fi

  # a run killed mid-commit can leave git's index.lock behind — clear it
  local gd
  gd=$(git -C "$wt" rev-parse --path-format=absolute --git-dir 2>/dev/null || true)
  if [ -n "$gd" ] && [ -f "$gd/index.lock" ]; then
    rm -f "$gd/index.lock"
    echo "note: removed stale $gd/index.lock (a previous run died mid-commit)" >&2
  fi

  # efficiency guard: a worker branch behind the base builds against stale
  # code and usually wastes the whole run. Warn, or auto-sync if asked.
  local behind
  behind=$(git -C "$wt" rev-list --count "HEAD..$base" 2>/dev/null || echo 0)
  if [ "${behind:-0}" -gt 0 ]; then
    if [ "${AGENTTEAM_AUTO_SYNC:-0}" = "1" ] && [ -z "$(git -C "$wt" status --porcelain=v1 2>/dev/null)" ]; then
      if git -C "$wt" merge --no-edit "$base" >/dev/null 2>&1; then
        echo "note: '$worker' was $behind commit(s) behind $base — auto-synced before running"
      else
        git -C "$wt" merge --abort >/dev/null 2>&1 || true
        echo "!! '$worker' is $behind behind $base and auto-sync hit a conflict — resolve in wt/$worker" >&2
      fi
    else
      echo "!! '$worker' is $behind commit(s) behind $base — it may build against stale code." >&2
      echo "   run 'agentteam sync $worker' first, or set AGENTTEAM_AUTO_SYNC=1." >&2
    fi
  fi

  echo "[$worker <- $agent] running task '$task' (timeout ${TIMEOUT}s), log: $log"
  export TASKFILE="$tf"
  local rc=0 t0 dur
  t0=$(date +%s)
  ( cd "$wt" && timeout "$TIMEOUT" bash -c "$cmdline" ) > "$log" 2>&1 || rc=$?
  dur=$(( $(date +%s) - t0 ))

  # receipts for the verdict line + ledger
  local commits files ins dels unc
  commits=$(git -C "$wt" rev-list --count "$base..HEAD" 2>/dev/null || echo 0)
  read -r files ins dels < <(git -C "$wt" diff --shortstat "$base...HEAD" 2>/dev/null \
    | awk '{f=0;i=0;d=0;for(n=1;n<NF;n++){if($(n+1)~/^file/)f=$n;if($(n+1)~/^insertion/)i=$n;if($(n+1)~/^deletion/)d=$n}print f+0,i+0,d+0}') || true
  files=${files:-0}; ins=${ins:-0}; dels=${dels:-0}
  unc=$(git -C "$wt" status --porcelain=v1 2>/dev/null | wc -l)

  {
    echo
    echo "## run $(date -Is) — worker=$worker agent=$agent exit=$rc duration=${dur}s"
    echo
    echo "### git status (branch, staged/unstaged)"
    git -C "$wt" status --porcelain=v1 -b
    echo
    echo "### committed diffstat vs $base"
    git -C "$wt" diff --stat "$base...HEAD" 2>/dev/null || echo "(none)"
    echo
    echo "### verdict"
    echo "commits=$commits files=$files insertions=$ins deletions=$dels uncommitted=$unc"
    if [ "$rc" -eq 0 ] && [ "$commits" -eq 0 ] && [ "$unc" -eq 0 ]; then
      echo "!! exit=0 with an empty diff — no-op or overclaim; treat as FAILED (I10/I12)"
    fi
    echo
    echo "### agent output (tail)"
    echo '~~~'
    tail -n 60 "$log"
    echo '~~~'
  } >> "$report"

  # limit detection is a helper only: a task whose own text mentions limits
  # must not bench a healthy agent, and AUTO_OFF fires only on a FAILED run
  local wall=0
  if tail -n 40 "$log" | grep -qiE "$LIMIT_RE"; then
    if grep -qiE "$LIMIT_RE" "$tf" && [ "$rc" -eq 0 ]; then
      : # the task itself is about limits and the run succeeded — noise
    else
      wall=1
      echo "!! output mentions usage limits — if '$agent' hit its 5h/weekly cap:  agentteam off $agent 5h   (weekly: 7d)" >&2
      if [ "${AGENTTEAM_AUTO_OFF:-0}" = "1" ] && [ "$rc" -ne 0 ]; then cmd_off "$agent" 5h >&2; fi
    fi
  fi

  ledger_add "$root" "$(printf '{"event":"run","ts":"%s","task":"%s","worker":"%s","agent":"%s","exit":%d,"duration_s":%d,"commits":%d,"files":%d,"insertions":%d,"deletions":%d,"uncommitted":%d,"wall":%d}' \
    "$(date -Is)" "$task" "$worker" "$agent" "$rc" "$dur" "$commits" "$files" "$ins" "$dels" "$unc" "$wall")"

  echo "exit=$rc duration=${dur}s — report: $report"
  if [ "${AGENTTEAM_AUTO_VERIFY:-0}" = "1" ]; then
    exec 9>&-   # release the worker lock so verify can probe it
    cmd_verify "$worker" "$task" || true
    echo "next: agentteam diff $worker"
  else
    echo "next: agentteam verify $worker $task   then: agentteam diff $worker"
  fi
  return "$rc"
}

# ---------------------------------------------------------------- verify
cmd_verify() {
  local worker="${1:-}" task="${2:-}"
  [ -n "$worker" ] && [ -n "$task" ] || die "usage: agentteam verify <worker> <task-id>"
  check_id "$worker" worker; check_id "$task" task
  local root; root=$(find_root) || die "not inside an agentteam project"
  task="${task%.md}"
  local tf="$root/coord/tasks/$task.md"; [ -f "$tf" ] || die "no task file: $tf"
  local wt="$root/wt/$worker";           [ -d "$wt" ] || die "no worktree: $wt"
  lock_probe "$root" "$worker" || die "worker '$worker' is mid-run — verify when it finishes"
  local base; base=$(get_base "$root")

  local changed commits
  changed=$( { git -C "$wt" diff --name-only "$base...HEAD" 2>/dev/null || true;
               git -C "$wt" status --porcelain=v1 2>/dev/null | cut -c4- | sed 's/.* -> //; s:/$::'; } | sort -u )
  commits=$(git -C "$wt" rev-list --count "$base..HEAD" 2>/dev/null || echo 0)

  # scope: every "- path" line under "## Allowed scope" is an enforced pattern
  local pats=() line
  while IFS= read -r line; do
    case "$line" in '- '*) pats+=("${line#- }");; esac
  done < <(task_section "$tf" "Allowed scope")

  local scope="OK" viol=""
  if [ ${#pats[@]} -eq 0 ]; then
    scope="UNCHECKED"
  else
    while IFS= read -r line; do
      [ -n "$line" ] || continue
      scope_allowed "$line" "${pats[@]}" || viol="$viol$line"$'\n'
    done <<< "$changed"
    [ -z "$viol" ] || scope="VIOLATION"
  fi

  # validate: every "$ cmd" line under "## Validate" must exit 0, run in wt
  local vrun=0 vfail=0 vout="" cmd out rc
  while IFS= read -r line; do
    case "$line" in '$ '*) ;; *) continue;; esac
    cmd="${line#\$ }"
    vrun=$((vrun+1))
    rc=0
    out=$( cd "$wt" && timeout "${AGENTTEAM_VERIFY_TIMEOUT:-900}" bash -c "$cmd" 2>&1 ) || rc=$?
    if [ "$rc" -eq 0 ]; then
      vout="${vout}  PASS  \$ $cmd"$'\n'
    else
      vfail=$((vfail+1))
      vout="${vout}  FAIL  \$ $cmd   (exit=$rc)"$'\n'"$(printf '%s\n' "$out" | tail -n 8 | sed 's/^/        | /')"$'\n'
    fi
  done < <(task_section "$tf" "Validate")

  local empty=0
  [ "$commits" -eq 0 ] && [ -z "$changed" ] && empty=1

  local verdict="PASS" ret=0
  if [ "$scope" = "VIOLATION" ] || [ "$vfail" -gt 0 ] || [ "$empty" = 1 ]; then verdict="FAIL"; ret=1; fi

  local pcount; pcount=$(printf '%s\n' "$changed" | grep -c .) || true
  echo "== verify $worker / $task =="
  case "$scope" in
    OK)        echo "scope    : OK (${#pats[@]} pattern(s))";;
    UNCHECKED) echo "scope    : UNCHECKED — no '- path' lines under '## Allowed scope'";;
    VIOLATION) echo "scope    : VIOLATION — out-of-scope changes:"; printf '%s' "$viol" | sed 's/^/             /';;
  esac
  if [ "$vrun" -eq 0 ]; then echo "validate : none — no '\$ ' command lines under '## Validate'"
  else echo "validate : $((vrun-vfail))/$vrun passed"; printf '%s' "$vout"; fi
  echo "changes  : commits=$commits, paths touched=$pcount"
  [ "$empty" = 1 ] && echo "!! EMPTY — no commits and no uncommitted changes: no-op or overclaim"
  echo "verdict  : $verdict"

  {
    echo
    echo "### verify $(date -Is) — worker=$worker scope=$scope validate=$((vrun-vfail))/$vrun empty=$empty verdict=$verdict"
    [ -n "$viol" ] && { echo "out-of-scope:"; printf '%s' "$viol" | sed 's/^/  /'; }
    [ -n "$vout" ] && printf '%s' "$vout"
  } >> "$root/coord/reports/$task.md"

  ledger_add "$root" "$(printf '{"event":"verify","ts":"%s","task":"%s","worker":"%s","scope":"%s","validate_run":%d,"validate_failed":%d,"commits":%d,"empty":%d,"verdict":"%s"}' \
    "$(date -Is)" "$task" "$worker" "$scope" "$vrun" "$vfail" "$commits" "$empty" "$verdict")"

  return "$ret"
}

cmd_diff() {
  local worker="${1:-}"; [ -n "$worker" ] || die "usage: agentteam diff <worker> [--stat]"
  check_id "$worker" worker
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

# ------------------------------------------------------------------ sync
cmd_sync() { # after merges: bring base's new work into worker branches
  local root; root=$(find_root) || die "not inside an agentteam project"
  local base; base=$(get_base "$root")
  local list=("$@") wt w
  for w in "$@"; do check_id "$w" worker; done
  if [ ${#list[@]} -eq 0 ]; then
    for wt in "$root"/wt/*/; do [ -d "$wt" ] && list+=("$(basename "$wt")"); done
  fi
  [ ${#list[@]} -gt 0 ] || die "no worktrees found"
  for w in "${list[@]}"; do
    wt="$root/wt/$w"
    if [ ! -d "$wt" ]; then printf '  %-14s no worktree\n' "$w"; continue; fi
    if ! lock_probe "$root" "$w"; then printf '  %-14s SKIP — running a task\n' "$w"; continue; fi
    if [ -n "$(git -C "$wt" status --porcelain=v1 2>/dev/null)" ]; then
      printf '  %-14s SKIP — uncommitted changes (commit or clean first)\n' "$w"; continue
    fi
    if git -C "$wt" merge-base --is-ancestor HEAD "$base" 2>/dev/null; then
      if git -C "$wt" merge --ff-only "$base" >/dev/null 2>&1; then
        printf '  %-14s fast-forwarded to %s\n' "$w" "$base"
      else
        printf '  %-14s could not fast-forward — check manually\n' "$w"
      fi
    else
      if git -C "$wt" merge --no-edit "$base" >/dev/null 2>&1; then
        printf '  %-14s merged %s in (own unmerged commits kept)\n' "$w" "$base"
      else
        git -C "$wt" merge --abort >/dev/null 2>&1 || true
        printf '  %-14s CONFLICT with %s — resolve manually in wt/%s\n' "$w" "$base" "$w"
      fi
    fi
  done
}

cmd_status() {
  local root; root=$(find_root) || die "not inside an agentteam project"
  local base; base=$(get_base "$root")
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
  ls -lt "$root/coord/reports" 2>/dev/null | grep -v '^total' | head -12 || true
  echo; echo "== workers (review queue vs $base) =="
  local wt w br ahead unc run
  for wt in "$root"/wt/*/; do
    [ -d "$wt" ] || continue
    w=$(basename "$wt")
    br=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')
    ahead=$(git -C "$wt" rev-list --count "$base..HEAD" 2>/dev/null || echo '?')
    unc=$(git -C "$wt" status --porcelain=v1 2>/dev/null | wc -l)
    run=""
    lock_probe "$root" "$w" || run="   << RUNNING"
    printf '  %-14s [%s]  unreviewed commits: %-3s uncommitted files: %-3s%s\n' \
      "$w" "$br" "$ahead" "$unc" "$run"
  done
  echo; echo "== running =="
  local pf pid t any=0
  for pf in "$root"/coord/reports/*.pid; do
    [ -e "$pf" ] || continue
    t=$(basename "$pf" .pid)
    pid=$(cat "$pf" 2>/dev/null || true)
    if [ -n "$pid" ] && { pgrep -s "$pid" >/dev/null 2>&1 || kill -0 -- "-$pid" 2>/dev/null || kill -0 "$pid" 2>/dev/null; }; then
      echo "  $t (background, pid $pid) — tail: agentteam tail $t   abort: agentteam kill $t"; any=1
    else
      rm -f "$pf"
    fi
  done
  local pg; pg=$(pgrep -af "bin/agentteam run" 2>/dev/null | grep -v "^$$ " || true)
  if [ -n "$pg" ]; then printf '%s\n' "$pg" | sed 's/^/  /'; any=1; fi
  [ "$any" = 1 ] || echo "  (none)"
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
  local tf nd; tf=$(mktemp); printf 'Reply with exactly: ok\n' > "$tf"
  nd=$(mktemp -d)   # neutral dir: no repo, no role cards, nothing to touch
  local line name cmd rc out
  while IFS= read -r line; do
    case "$line" in ''|'#'*) continue;; esac
    name="${line%%=*}"; cmd="${line#*=}"
    if is_off "$name"; then printf '  %-12s SKIP (benched)\n' "$name"; continue; fi
    if ! command -v "${cmd%% *}" >/dev/null 2>&1; then printf '  %-12s MISSING binary\n' "$name"; continue; fi
    rc=0; out=$( cd "$nd" && TASKFILE="$tf" timeout 180 bash -c "$cmd" 2>&1 ) || rc=$?
    if [ "$rc" -ne 0 ]; then
      printf '  %-12s FAIL exit=%s — %s\n' "$name" "$rc" "$(printf '%s' "$out" | tail -1 | cut -c1-70)"
    elif printf '%s' "$out" | grep -qiw ok; then
      printf '  %-12s OK\n' "$name"
    else
      printf '  %-12s WARN — replied, but not "ok": %s\n' "$name" "$(printf '%s' "$out" | tail -1 | cut -c1-60)"
    fi
  done < "$conf"
  rm -rf "$tf" "$nd"
}

# ---------------------------------------------------------------- review
cmd_review() { # a DIFFERENT vendor judges the task order + the diff
  local worker="${1:-}" task="${2:-}" reviewer="${3:-}"
  [ -n "$worker" ] && [ -n "$task" ] || die "usage: agentteam review <worker> <task-id> [reviewer-agent]"
  check_id "$worker" worker; check_id "$task" task
  local root; root=$(find_root) || die "not inside an agentteam project"
  task="${task%.md}"
  local tf="$root/coord/tasks/$task.md"; [ -f "$tf" ] || die "no task file: $tf"
  local wt="$root/wt/$worker";           [ -d "$wt" ] || die "no worktree: $wt"
  local base; base=$(get_base "$root")
  local author="${worker%%-*}" conf; conf=$(conf_for_root "$root")

  if [ -z "$reviewer" ]; then
    local line name cmdw
    while IFS= read -r line; do
      case "$line" in ''|'#'*) continue;; esac
      name="${line%%=*}"; cmdw="${line#*=}"
      [ "$name" = "$author" ] && continue
      is_off "$name" && continue
      command -v "${cmdw%% *}" >/dev/null 2>&1 || continue
      reviewer="$name"; break
    done < "$conf"
  fi
  [ -n "$reviewer" ] || die "no available reviewer (all benched or missing) — name one: agentteam review $worker $task <agent>"
  [ "$reviewer" != "$author" ] || die "reviewer must be a different vendor than the author agent '$author'"
  local rcmd; rcmd=$(agent_cmd "$reviewer" "$conf") || die "no agents.conf entry for reviewer '$reviewer'"

  local pf; pf=$(mktemp)
  {
    if [ -f "$TPL_DIR/REVIEW.md" ]; then cat "$TPL_DIR/REVIEW.md"
    else printf 'You are an independent code reviewer from a different AI vendor. Judge only the material below. End with "VERDICT: APPROVE" or "VERDICT: REQUEST-CHANGES".\n'; fi
    printf '\n===== TASK ORDER (%s) =====\n' "$task"
    cat "$tf"
    printf '\n===== DIFF committed vs %s =====\n' "$base"
    git -C "$wt" diff "$base...HEAD" 2>/dev/null | head -c 200000 || true
    printf '\n===== UNCOMMITTED =====\n'
    git -C "$wt" diff HEAD 2>/dev/null | head -c 100000 || true
    printf '\n===== END OF MATERIAL =====\nRemember: end with exactly one line "VERDICT: APPROVE" or "VERDICT: REQUEST-CHANGES".\n'
  } > "$pf"

  local nd out rc=0
  nd=$(mktemp -d)   # reviewer works blind from the prompt — no repo access
  echo "[review] $reviewer reviewing $worker's '$task' (timeout ${AGENTTEAM_REVIEW_TIMEOUT:-900}s)"
  out=$( cd "$nd" && TASKFILE="$pf" timeout "${AGENTTEAM_REVIEW_TIMEOUT:-900}" bash -c "$rcmd" 2>&1 ) || rc=$?
  printf '%s\n' "$out"

  {
    echo
    echo "### review $(date -Is) — reviewer=$reviewer author=$worker exit=$rc"
    echo '~~~'
    printf '%s\n' "$out" | tail -n 80
    echo '~~~'
  } >> "$root/coord/reports/$task.md"
  ledger_add "$root" "$(printf '{"event":"review","ts":"%s","task":"%s","worker":"%s","reviewer":"%s","exit":%d}' \
    "$(date -Is)" "$task" "$worker" "$reviewer" "$rc")"
  rm -rf "$nd" "$pf"
  return "$rc"
}

# ------------------------------------------------------------------ race
cmd_race() { # same task to several workers in parallel; merge ONE winner
  local task="${1:-}"; shift || true
  [ -n "$task" ] && [ $# -ge 2 ] || die "usage: agentteam race <task-id> <worker> <worker> [...]"
  check_id "$task" task
  local root; root=$(find_root) || die "not inside an agentteam project"
  task="${task%.md}"
  local tf="$root/coord/tasks/$task.md"; [ -f "$tf" ] || die "no task file: $tf"
  local w
  for w in "$@"; do
    check_id "$w" worker
    [ -d "$root/wt/$w" ] || die "no worktree for '$w' — run: agentteam init $w"
    is_off "${w%%-*}" && die "agent '${w%%-*}' is OFF — bench-aware racing: pick another worker"
    lock_probe "$root" "$w" || die "worker '$w' is busy (agentteam status)"
  done
  local ct
  for w in "$@"; do
    ct="$root/coord/tasks/$task-$w.md"
    if [ ! -f "$ct" ]; then
      cp "$tf" "$ct"
      printf '\n> race copy of %s for worker %s — several workers race this task; only ONE winning branch gets merged.\n' "$task" "$w" >> "$ct"
    fi
    "$0" run -b "$w" "$task-$w"
  done
  ledger_add "$root" "$(printf '{"event":"race","ts":"%s","task":"%s","workers":"%s"}' "$(date -Is)" "$task" "$*")"
  echo "race on. compare: agentteam verify/diff per worker — merge exactly one winner, reject the rest."
}

# -------------------------------------------------------------- sabotage
cmd_sabotage() { # the saboteur seat: attack fresh merges with failing tests
  local worker="${1:-}"; [ -n "$worker" ] || die "usage: agentteam sabotage <worker>"
  check_id "$worker" worker
  local root; root=$(find_root) || die "not inside an agentteam project"
  local wt="$root/wt/$worker"; [ -d "$wt" ] || die "no worktree for '$worker' — run: agentteam init $worker"
  is_off "${worker%%-*}" && die "agent '${worker%%-*}' is OFF"
  lock_probe "$root" "$worker" || die "worker '$worker' is busy (agentteam status)"
  [ -f "$TPL_DIR/SABOTEUR.md" ] || die "SABOTEUR.md template missing — rerun the installer"
  echo "syncing '$worker' so the saboteur sees the latest merged work:"
  cmd_sync "$worker"
  local id; id="SAB-$(date +%Y%m%d-%H%M%S)"
  sed "s/{{WORKER}}/$worker/g; s/{{ID}}/$id/g" "$TPL_DIR/SABOTEUR.md" > "$root/coord/tasks/$id-$worker.md"
  "$0" run -b "$worker" "$id-$worker"
  echo "saboteur dispatched: $id-$worker — findings land in coord/reports/$id-$worker.md"
}

# ------------------------------------------------------------- tail/kill
cmd_tail() {
  local root; root=$(find_root) || die "not inside an agentteam project"
  local task="${1:-}" f
  if [ -n "$task" ]; then
    task="${task%.md}"; f="$root/coord/reports/$task.log"
  else
    f=$(ls -t "$root"/coord/reports/*.log 2>/dev/null | head -1 || true)
  fi
  [ -n "$f" ] && [ -f "$f" ] || die "no log found (agentteam tail <task-id>)"
  echo ">> $f"
  exec tail -n 40 -f "$f"
}

cmd_kill() {
  local task="${1:-}"; [ -n "$task" ] || die "usage: agentteam kill <task-id>"
  check_id "${task%.md}" task
  local root; root=$(find_root) || die "not inside an agentteam project"
  task="${task%.md}"
  local pf="$root/coord/reports/$task.pid"
  [ -f "$pf" ] || die "no background run recorded for '$task' (foreground runs: Ctrl-C)"
  local pid; pid=$(cat "$pf" 2>/dev/null || true)
  if [ -z "$pid" ]; then rm -f "$pf"; die "empty pidfile removed — nothing to kill"; fi
  # background runs are session leaders (setsid); kill the SESSION — a plain
  # group-kill misses the agent because `timeout` runs it in its own group
  if pgrep -s "$pid" >/dev/null 2>&1; then
    pkill -TERM -s "$pid" 2>/dev/null || true
    sleep 1
    if pgrep -s "$pid" >/dev/null 2>&1; then pkill -KILL -s "$pid" 2>/dev/null || true; fi
    echo "killed '$task' (session $pid) — partial work may sit uncommitted in the worktree"
  elif kill -0 -- "-$pid" 2>/dev/null || kill -0 "$pid" 2>/dev/null; then
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    sleep 1
    if kill -0 -- "-$pid" 2>/dev/null || kill -0 "$pid" 2>/dev/null; then
      kill -KILL -- "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    fi
    echo "killed '$task' (pid $pid) — partial work may sit uncommitted in the worktree"
  else
    echo "'$task' already finished — cleaning up its pidfile"
  fi
  rm -f "$pf"
}

# ---------------------------------------------------------- report/version
cmd_report() { # read a task's report without typing coord/reports paths
  local task="${1:-}"; [ -n "$task" ] || die "usage: agentteam report <task-id> [lines]"
  check_id "${task%.md}" task
  local root; root=$(find_root) || die "not inside an agentteam project"
  task="${task%.md}"
  local f="$root/coord/reports/$task.md"
  [ -f "$f" ] || die "no report yet for '$task' (run it first; live output: agentteam tail $task)"
  local n="${2:-60}"
  echo ">> $f (last $n lines — full history is append-only above)"
  tail -n "$n" "$f"
}

cmd_version() {
  echo "agentteam $AGENTTEAM_VERSION ($0)"
  echo "config: $CONF_FILE"
}

# ------------------------------------------------------------------ score
cmd_score() { # fleet scorecard straight from the ledger; myapp = full view
  local root="${1:-}"
  if [ -n "$root" ]; then [ -d "$root/coord" ] || die "no coord/ under: $root"
  else root=$(find_root) || die "not inside an agentteam project (or: agentteam score <project-root>)"; fi
  local lg="$root/coord/reports/ledger.jsonl"
  [ -f "$lg" ] || die "no ledger yet: $lg (it appears after the first run)"
  printf '  %-14s %5s %4s %5s %6s %8s %7s %8s\n' worker runs ok fail walls verify merges avg-dur
  awk '
    function get(s, k,   v) {
      if (match(s, "\"" k "\":\"[^\"]*\"")) { v=substr(s,RSTART,RLENGTH); sub(/^[^:]*:"/,"",v); sub(/"$/,"",v); return v }
      if (match(s, "\"" k "\":-?[0-9]+"))   { v=substr(s,RSTART,RLENGTH); sub(/^[^:]*:/,"",v); return v }
      return ""
    }
    { e=get($0,"event"); w=get($0,"worker"); if (w=="") next; seen[w]=1 }
    e=="run"    { runs[w]++; if (get($0,"exit")=="0") ok[w]++; else fail[w]++
                  if (get($0,"wall")=="1") walls[w]++; dur[w]+=get($0,"duration_s") }
    e=="verify" { if (get($0,"verdict")=="PASS") vp[w]++; else vf[w]++ }
    e=="merge"  { merges[w]++ }
    END {
      for (w in seen) {
        vd = sprintf("%d/%d", vp[w], vp[w]+vf[w])
        ad = (runs[w] ? int(dur[w]/runs[w]) : 0)
        printf "%d\t  %-14s %5d %4d %5d %6d %8s %7d %7ds\n", \
               merges[w], w, runs[w], ok[w], fail[w], walls[w], vd, merges[w], ad
      }
    }' "$lg" | sort -rn | cut -f2-
  echo "  (source: ledger.jsonl — merges are ledger-logged by the post-merge hook;"
  echo "   full scorecard incl. pre-ledger history: myapp $root)"
}

# ----------------------------------------------------------------- doctor
cmd_doctor() { # preflight: catch what would otherwise waste a run or quota
  local root; root=$(find_root) || die "not inside an agentteam project"
  local base conf warn=0 bad=0
  base=$(get_base "$root"); conf=$(conf_for_root "$root")
  local main_dir="$root/repo"
  [ -d "$main_dir" ] || main_dir=$(dirname "$(git -C "$root"/wt/* rev-parse --git-common-dir 2>/dev/null | head -1)" 2>/dev/null)
  ok()   { printf '  ok    %s\n' "$1"; }
  warn() { printf '  WARN  %s\n' "$1"; warn=$((warn+1)); }
  err()  { printf '  ERR   %s\n' "$1"; bad=$((bad+1)); }

  echo "== agentteam doctor =="
  echo "project: $root"
  echo "base:    $base"

  # STOP / config
  [ -f "$root/coord/STOP" ] && warn "STOP is active — all runs are blocked (agentteam resume)" \
                            || ok "no STOP file (runs allowed)"
  [ -f "$conf" ] && ok "agents.conf found: $conf" \
                 || err "no agents.conf at $conf — every run will fail"

  # base branch exists where the main repo can see it
  if [ -d "$main_dir/.git" ] || [ -f "$main_dir/.git" ]; then
    git -C "$main_dir" rev-parse -q --verify "$base" >/dev/null 2>&1 \
      && ok "base branch '$base' exists" \
      || err "base branch '$base' does not exist in the repo — sync/merge/diff will misbehave"
  fi

  # each worker: worktree healthy, on its own branch, conf line present
  local wt w br agent behind dirty
  for wt in "$root"/wt/*/; do
    [ -d "$wt" ] || continue
    w=$(basename "$wt"); agent="${w%%-*}"
    if ! git -C "$wt" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      err "worker '$w': worktree is broken (git cannot read it)"; continue
    fi
    br=$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null)
    [ "$br" = "agent/$w" ] || warn "worker '$w' is on branch '$br', expected 'agent/$w'"
    behind=$(git -C "$wt" rev-list --count "HEAD..$base" 2>/dev/null || echo 0)
    [ "${behind:-0}" -gt 0 ] && warn "worker '$w' is $behind commit(s) behind $base (agentteam sync $w)"
    dirty=$(git -C "$wt" status --porcelain=v1 2>/dev/null | wc -l)
    [ "$dirty" -gt 0 ] && warn "worker '$w' has $dirty uncommitted file(s) in its worktree"
    if ! agent_cmd "$agent" "$conf" >/dev/null 2>&1; then
      err "worker '$w': no agents.conf line for agent '$agent' — its runs will fail"
    elif ! command -v "$(agent_cmd "$agent" "$conf" | awk '{print $1}')" >/dev/null 2>&1; then
      warn "worker '$w': agent '$agent' binary not on PATH (benched-equivalent)"
    fi
  done

  # guard hooks present in the shared git dir
  local hooks
  hooks=$(git -C "$main_dir" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)/hooks
  if [ -d "$hooks" ]; then
    grep -q 'agentteam guard' "$hooks/pre-commit" 2>/dev/null \
      && ok "guard hooks installed (worker-branch + no-push + merge-ledger)" \
      || warn "guard hooks missing — re-run 'agentteam init <worker>' to install them"
  fi

  # stale control files
  local pf stale=0 t pid
  for pf in "$root"/coord/reports/*.pid; do
    [ -e "$pf" ] || continue
    pid=$(cat "$pf" 2>/dev/null); t=$(basename "$pf" .pid)
    if [ -n "$pid" ] && { pgrep -s "$pid" >/dev/null 2>&1 || kill -0 "$pid" 2>/dev/null; }; then
      ok "background run live: $t (pid $pid)"
    else
      warn "stale pidfile for '$t' (dead process) — 'agentteam status' clears it"; stale=1
    fi
  done

  # disk headroom (worktrees each copy the whole repo)
  local avail
  avail=$(df -Pm "$root" 2>/dev/null | awk 'NR==2{print $4}')
  if [ -n "$avail" ]; then
    [ "$avail" -lt 500 ] && warn "only ${avail}MB free under the project — worktrees need room" \
                         || ok "disk headroom: ${avail}MB free"
  fi

  echo
  if [ "$bad" -gt 0 ]; then
    echo "doctor: $bad error(s), $warn warning(s) — fix the errors before dispatching."
    return 1
  elif [ "$warn" -gt 0 ]; then
    echo "doctor: 0 errors, $warn warning(s) — runnable, but look at the warnings."
    return 0
  fi
  echo "doctor: all clear."
}

# -------------------------------------------------------------------- new
cmd_new() { # bootstrap: clone -> dev branch -> init -> playbooks, one command
  local url="${1:-}"; [ -n "$url" ] || die "usage: agentteam new <repo-url> [name] [workers...]"
  local name="${2:-}"
  [ -n "$name" ] || name=$(basename "$url" .git)
  shift; [ $# -gt 0 ] && shift || true
  local workers=("$@")
  [ -e "$name" ] && die "'$name' already exists here — pick another name or cd elsewhere"
  mkdir -p "$name"
  if ! git clone "$url" "$name/repo"; then rm -rf "$name"; die "clone failed: $url"; fi
  ( cd "$name/repo"
    git checkout dev 2>/dev/null || git checkout -q -b dev
    "$0" init ${workers[@]+"${workers[@]}"}
  )
  mkdir -p "$CONF_DIR/playbooks"
  local pb copied=0
  for pb in "$CONF_DIR/playbooks/"*.md; do
    [ -e "$pb" ] || continue
    cp "$pb" "$name/coord/docs/" && copied=$((copied+1))
  done
  echo
  echo "project '$name' ready."
  if [ "$copied" -gt 0 ]; then
    echo "playbooks   : $copied copied from $CONF_DIR/playbooks/ into coord/docs/"
  else
    echo "playbooks   : none in $CONF_DIR/playbooks/ — drop your ai-*.md there once; every 'agentteam new' copies them in"
  fi
  echo "remote dev  : when ready:  cd $name/repo && git push -u origin dev"
  echo "start       : cd $name/repo && agentteam agents"
}

# -------------------------------------------------------------- selftest
ST_OK=0; ST_FAIL=0
st_chk() { # <description> <command...> — count and print one check
  local d="$1"; shift
  if "$@" >/dev/null 2>&1; then ST_OK=$((ST_OK+1)); printf '  ok    %s\n' "$d"
  else ST_FAIL=$((ST_FAIL+1)); printf '  FAIL  %s\n' "$d"; fi
}

cmd_selftest() { # the whole loop, rehearsed with mock agents — zero quota
  local b missing=""
  for b in git flock awk timeout; do
    command -v "$b" >/dev/null 2>&1 || missing="$missing $b"
  done
  [ -z "$missing" ] || die "selftest needs:$missing"
  [ -f "$TPL_DIR/TASK.md" ] || die "templates missing at $TPL_DIR — rerun the installer"

  local ST; ST=$(mktemp -d)
  echo "== agentteam selftest — sandbox: $ST =="
  mkdir -p "$ST/conf/templates"
  cp "$TPL_DIR"/*.md "$ST/conf/templates/"

  cat > "$ST/conf/agents.conf" <<'ST_CONF_EOF'
mock=bash -c 'cat "$TASKFILE" >/dev/null; echo working; echo line >> hello.txt; git add hello.txt; git commit -q -m "selftest: mock"; echo ok'
rogue=bash -c 'echo rogue; echo x > forbidden.txt; git add forbidden.txt; git commit -q -m "selftest: rogue"; echo ok'
slow=bash -c 'echo napping; sleep 30; echo ok'
rev=bash -c 'cat "$TASKFILE" >/dev/null; echo reviewed; echo "VERDICT: APPROVE"'
noop=bash -c 'echo did nothing at all; echo ok'
ST_CONF_EOF

  local repo="$ST/proj/repo"
  mkdir -p "$ST/proj"
  git init -q -b dev "$repo"
  git -C "$repo" config user.email selftest@agentteam.local
  git -C "$repo" config user.name  agentteam-selftest
  git -C "$repo" commit -q --allow-empty -m "init"

  export AGENTTEAM_CONF_DIR="$ST/conf"
  cd "$repo"

  st_chk "init scaffolds worktrees + coord" \
    bash -c '"$0" init mock rogue slow noop >/dev/null 2>&1 && [ -d ../wt/mock ] && [ -d ../wt/slow ] && [ -f ../coord/board.md ] && [ -f ../coord/tasks/TEMPLATE.md ]' "$0"
  st_chk "worker-branch guard hooks installed" \
    bash -c 'grep -q "agentteam guard" .git/hooks/pre-commit && grep -q "agentteam guard" .git/hooks/pre-push'

  cat > ../coord/tasks/T1-mock.md <<'ST_T1_EOF'
# Task T1 — worker: mock
## Goal
Create hello.txt containing the word line.
## Context
agentteam selftest task.
## Allowed scope
- hello.txt
## Constraints
none
## Validate
$ test -f hello.txt
$ grep -q line hello.txt
## Done means
hello.txt committed on your branch.
## Report
SUMMARY
ST_T1_EOF

  st_chk "run executes a mock worker (exit 0)" \
    bash -c '"$0" run mock T1-mock >/dev/null 2>&1' "$0"
  st_chk "worker committed on its own branch" \
    bash -c '[ "$(git -C ../wt/mock rev-list --count dev..HEAD)" -ge 1 ]'
  st_chk "run block appended to the report" \
    bash -c 'grep -q "worker=mock" ../coord/reports/T1-mock.md'
  st_chk "run event in ledger.jsonl" \
    bash -c 'grep -q "\"event\":\"run\"" ../coord/reports/ledger.jsonl'
  st_chk "verify passes an in-scope task" \
    bash -c '"$0" verify mock T1-mock >/dev/null 2>&1' "$0"

  cat > ../coord/tasks/T2-rogue.md <<'ST_T2_EOF'
# Task T2 — worker: rogue
## Goal
Touch only hello.txt (the rogue agent will not).
## Context
agentteam selftest — this worker intentionally leaves its scope.
## Allowed scope
- hello.txt
## Validate
## Done means
n/a
## Report
SUMMARY
ST_T2_EOF

  bash -c '"$0" run rogue T2-rogue >/dev/null 2>&1' "$0" || true
  st_chk "verify catches an out-of-scope diff" \
    bash -c 'out=$("$0" verify rogue T2-rogue 2>&1); rc=$?; [ "$rc" -ne 0 ] && printf "%s" "$out" | grep -q VIOLATION' "$0"
  st_chk "verify event in ledger.jsonl" \
    bash -c 'grep -q "\"event\":\"verify\"" ../coord/reports/ledger.jsonl'

  "$0" off mock 30m >/dev/null
  st_chk "benched agent is refused work" \
    bash -c '! "$0" run mock T1-mock >/dev/null 2>&1' "$0"
  "$0" on mock >/dev/null
  "$0" stop >/dev/null
  st_chk "STOP refuses all new runs" \
    bash -c '! "$0" run mock T1-mock >/dev/null 2>&1' "$0"
  "$0" resume >/dev/null
  st_chk "run works again after on + resume" \
    bash -c '"$0" run mock T1-mock >/dev/null 2>&1' "$0"

  mkdir -p ../coord/.locks
  ( exec 9>>../coord/.locks/mock.lock; flock 9; sleep 4 ) &
  local holder=$!
  sleep 1
  st_chk "busy worker is refused (per-worker lock)" \
    bash -c '! "$0" run mock T1-mock >/dev/null 2>&1' "$0"
  wait "$holder" 2>/dev/null || true

  cat > ../coord/tasks/T3-slow.md <<'ST_T3_EOF'
# Task T3 — worker: slow
## Goal
Sleep (background-run fodder for the selftest).
## Context
agentteam selftest.
## Allowed scope
- hello.txt
## Validate
## Done means
n/a
## Report
SUMMARY
ST_T3_EOF

  "$0" run -b slow T3-slow >/dev/null
  sleep 2
  st_chk "background run writes a pidfile" \
    bash -c '[ -f ../coord/reports/T3-slow.pid ]'
  st_chk "kill terminates the background run" \
    bash -c '"$0" kill T3-slow >/dev/null 2>&1 && [ ! -f ../coord/reports/T3-slow.pid ]' "$0"

  git merge --no-ff -q agent/mock -m "merge T1" >/dev/null 2>&1 || true
  st_chk "post-merge hook records a merge event in the ledger" \
    bash -c 'grep "\"event\":\"merge\"" ../coord/reports/ledger.jsonl | grep -q "\"worker\":\"mock\""'
  st_chk "sync fast-forwards a merged worker to base" \
    bash -c '"$0" sync mock >/dev/null 2>&1 && [ "$(git rev-parse agent/mock)" = "$(git rev-parse dev)" ]' "$0"
  st_chk "score prints the fleet table" \
    bash -c '"$0" score 2>/dev/null | grep -q "  mock"' "$0"
  st_chk "AUTO_VERIFY appends the verdict on its own" \
    bash -c 'AGENTTEAM_AUTO_VERIFY=1 "$0" run mock T1-mock >/dev/null 2>&1; [ "$(grep -c "### verify" ../coord/reports/T1-mock.md)" -ge 2 ]' "$0"
  st_chk "new bootstraps a project from a repo url" \
    bash -c 'cd ../.. && "$0" new proj/repo freshcopy >/dev/null 2>&1 && [ -d freshcopy/wt/codex ] && [ -f freshcopy/coord/board.md ]' "$0"

  st_chk "cross-agent review returns a verdict" \
    bash -c 'out=$("$0" review mock T1-mock rev 2>&1); printf "%s" "$out" | grep -q "VERDICT: APPROVE"' "$0"

  cat > ../coord/tasks/T4-mock.md <<'ST_T4_EOF'
# Task T4 — worker: mock
## Goal
No machine-run Validate lines here (prose only).
## Context
agentteam selftest.
## Allowed scope
- hello.txt
## Validate
Prose only: run the suite yourself.
## Done means
n/a
## Report
SUMMARY
ST_T4_EOF
  bash -c '"$0" run mock T4-mock >/dev/null 2>&1' "$0" || true
  st_chk "verify exits 0 on a no-Validate task" \
    bash -c '"$0" verify mock T4-mock >/dev/null 2>&1' "$0"

  cat > ../coord/tasks/T5-noop.md <<'ST_T5_EOF'
# Task T5 — worker: noop
## Goal
The agent will do nothing; the machinery must notice.
## Context
agentteam selftest.
## Allowed scope
- hello.txt
## Validate
## Done means
n/a
## Report
SUMMARY
ST_T5_EOF
  bash -c '"$0" run noop T5-noop >/dev/null 2>&1' "$0" || true
  st_chk "empty exit-0 run is flagged in the report" \
    bash -c 'grep -q "empty diff" ../coord/reports/T5-noop.md'
  st_chk "verify FAILs an empty run" \
    bash -c 'out=$("$0" verify noop T5-noop 2>&1); rc=$?; [ "$rc" -ne 0 ] && printf "%s" "$out" | grep -q EMPTY' "$0"
  st_chk "report command prints a task's history" \
    bash -c '"$0" report T1-mock 200 2>/dev/null | grep -q "worker=mock"' "$0"
  st_chk "version prints" \
    bash -c '"$0" version | grep -q "^agentteam "' "$0"
  st_chk "task ids cannot escape coord/tasks" \
    bash -c '! "$0" run mock ../reports/T1-mock >/dev/null 2>&1' "$0"
  st_chk "worker ids cannot escape wt/" \
    bash -c '! "$0" run mock-../../repo T1-mock >/dev/null 2>&1 && ! "$0" diff ../repo >/dev/null 2>&1' "$0"
  st_chk "init refuses a repo with no commits" \
    bash -c 'd=$(mktemp -d); git init -q -b dev "$d/r"; cd "$d/r";
             out=$("$0" init mock 2>&1); rc=$?; cd /; rm -rf "$d";
             [ "$rc" -ne 0 ] && printf "%s" "$out" | grep -qi "no commits"' "$0"
  st_chk "doctor runs and prints a verdict" \
    bash -c '"$0" doctor 2>/dev/null | grep -q "^doctor:"' "$0"
  st_chk "run warns when a worker is behind base (noop lagged the T1 merge)" \
    bash -c 'out=$("$0" run noop T5-noop 2>&1); printf "%s" "$out" | grep -qi "behind"' "$0"
  st_chk "AUTO_SYNC clears the stale-branch warning" \
    bash -c 'out=$(AGENTTEAM_AUTO_SYNC=1 "$0" run noop T5-noop 2>&1); printf "%s" "$out" | grep -qi "auto-synced"' "$0"

  "$0" off slow >/dev/null   # keep smoke from sitting through slow's nap
  st_chk "smoke prints one row per agent" \
    bash -c '[ "$("$0" smoke 2>/dev/null | wc -l)" -ge 5 ]' "$0"

  echo
  echo "selftest: $ST_OK ok, $ST_FAIL failed"
  cd /
  if [ "$ST_FAIL" -eq 0 ]; then
    rm -rf "$ST"
    echo "sandbox removed — all green."
  else
    echo "sandbox kept for inspection: $ST"
    return 1
  fi
}

cmd_stop()   { local root; root=$(find_root) || die "not in a project"; touch "$root/coord/STOP"; echo "STOP set — new runs blocked (running tasks finish or hit timeout)"; }
cmd_resume() { local root; root=$(find_root) || die "not in a project"; rm -f "$root/coord/STOP"; echo "STOP cleared"; }

cmd_help() {
  cat <<'HELP'
agentteam — one master CLI session delegating to worker CLI agents

setup / health
  agentteam new <repo-url> [name] [workers...]
                                     bootstrap a whole project: clone ->
                                     dev branch -> init -> playbooks copied
                                     from ~/.config/agentteam/playbooks/
  agentteam init [workers...]        scaffold wt/ + coord/ next to your clone
                                     (default: codex antigravity opencode grok)
                                     refuses while secret-looking files are
                                     tracked; installs worker-branch guard hooks
  agentteam agents                   list agents: binary found? on/off?
  agentteam smoke                    one tiny live call per agent, from a
                                     neutral dir — run after every CLI update
  agentteam selftest                 rehearse the whole loop with mock agents
                                     in a throwaway sandbox — zero quota
  agentteam doctor                   preflight a project: base branch, agent
                                     binaries, worktree health, stale state,
                                     disk — catch what would waste a run

work
  agentteam run [-b] <w> <task>      run coord/tasks/<task>.md in w's worktree
                                     (-b = background; one run per worker)
  agentteam tail [task]              follow a run's live log (default: newest)
  agentteam kill <task>              stop a background run (whole session)
  agentteam report <task> [lines]    read a task's report (default: last 60)
  agentteam verify <w> <task>        machine gate: diff vs the task's "- path"
                                     scope lines + run its "$ " Validate lines
                                     + commit sanity; verdict into the report
  agentteam diff <w> [--stat]        review a worker's changes vs base branch
  agentteam review <w> <task> [agent]  a DIFFERENT vendor reviews the task
                                     order + diff; VERDICT line + report block
  agentteam sync [w]                 after merges: bring base into worker
                                     branches (ff/merge; skips dirty/running)

fleet plays
  agentteam race <task> <w1> <w2> [...]  same task to several workers in
                                     parallel — merge exactly one winner
  agentteam sabotage <w>             saboteur seat: sync, then hunt fresh
                                     merges with failing tests (SAB-* task)
  agentteam score [project-root]     fleet scorecard from the ledger: runs,
                                     ok/fail, walls, verify rate, merges,
                                     avg duration — per worker

switches
  agentteam status                   off-agents, tasks, reports, review queue,
                                     running jobs
  agentteam off <agent> [30m|5h|7d]  quota switch: disable an agent
                                     (no duration = until 'agentteam on')
  agentteam on <agent>               re-enable an agent
  agentteam stop | resume            project kill switch for ALL new runs
  agentteam version                  installed version + config path

Worker -> agent: prefix before first "-" ("codex-2" uses agent "codex").
Config: ~/.config/agentteam/agents.conf (project override: coord/agents.conf).
Base branch: coord/base. Machine history: coord/reports/ledger.jsonl.
Env: AGENTTEAM_TIMEOUT (3600s)  AGENTTEAM_VERIFY_TIMEOUT (900s)
     AGENTTEAM_REVIEW_TIMEOUT (900s)  AGENTTEAM_ALLOW_SECRETS=1 (init override)
     AGENTTEAM_AUTO_OFF=1 (bench 5h when a FAILED run mentions usage limits)
     AGENTTEAM_AUTO_VERIFY=1 (every run appends its verify verdict itself)
     AGENTTEAM_AUTO_SYNC=1 (fast-forward a stale worker onto base before a run)
HELP
}

case "${1:-help}" in
  init)     shift; cmd_init "$@";;
  run)      shift; cmd_run "$@";;
  verify)   shift; cmd_verify "$@";;
  diff)     shift; cmd_diff "$@";;
  sync)     shift; cmd_sync "$@";;
  report)   shift; cmd_report "$@";;
  score)    shift; cmd_score "$@";;
  doctor)   shift; cmd_doctor "$@";;
  new)      shift; cmd_new "$@";;
  version|-V|--version) cmd_version;;
  status)   shift; cmd_status "$@";;
  agents)   shift; cmd_agents "$@";;
  off)      shift; cmd_off "$@";;
  on)       shift; cmd_on "$@";;
  smoke)    shift; cmd_smoke "$@";;
  review)   shift; cmd_review "$@";;
  race)     shift; cmd_race "$@";;
  sabotage) shift; cmd_sabotage "$@";;
  tail)     shift; cmd_tail "$@";;
  kill)     shift; cmd_kill "$@";;
  selftest) shift; cmd_selftest "$@";;
  stop)     shift; cmd_stop "$@";;
  resume)   shift; cmd_resume "$@";;
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
   ZERO memory of this chat — task files must be self-contained. The
   "- path" lines under Allowed scope and the "$ " lines under Validate
   are machine-enforced by `agentteam verify` — write them precisely.
3. `agentteam run <worker> <ID>-<worker>` (long: add -b, poll with status,
   watch live with `agentteam tail`).
4. Machine check FIRST: `agentteam verify <worker> <ID>-<worker>` — scope
   compliance, Validate commands re-run, commit sanity; the verdict lands
   in the report. Then read ../coord/reports/<ID>-<worker>.md and the REAL
   diff: `agentteam diff <worker>`. Never trust a report without both.
   For risky or large diffs, get a rival's opinion too:
   `agentteam review <worker> <ID>-<worker>` (a different vendor judges it).
5. Accept only if the milestone gate passes: verify PASS + clean build
   (0 warnings where the repo enforces it) + tests green + smoke run +
   changelog fragment changelog.d/<ID>.md (if the repo keeps a CHANGELOG —
   workers never edit CHANGELOG.md itself). Then tell Daniel the branch is
   ready to merge into the base branch. Reject -> sharper task file (<ID>b),
   rerun. Two failed attempts -> escalate to Daniel.
6. After Daniel merges: `agentteam sync` — every workshop rebuilds on the
   new base instead of drifting stale. At release time, roll the
   changelog.d/ fragments into CHANGELOG.md (you may edit docs).

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
  per cycle. changelog.d/ is the one shared dir — safe, one file per task.
- You alone write ../coord/board.md (one row per task); read blockers.md
  every cycle; if ../coord/STOP exists, stop delegating immediately.

## Fleet intelligence
- `agentteam score` — the always-available scorecard from the ledger:
  runs, ok/fail, walls, verify pass-rate, merges (auto-logged by the
  post-merge hook), avg duration, per worker. Consult it when assigning
  tasks — favor workers that earn merges; flag chronic wall-hitters.
- `myapp <project-root>` — the full scorecard product, including
  pre-ledger history parsed from reports/*.md.
- ../coord/reports/ledger.jsonl is the machine history: one JSON line per
  run/verify/review/race/merge with durations and diffstats. Cite it,
  not vibes.
- Head-to-head data when vendors disagree: `agentteam race <task> w1 w2`
  runs one task on several vendors in parallel; exactly one winner merges.
- Spare quota after merge days -> `agentteam sabotage <worker>`: the
  saboteur seat attacks freshly merged work with failing tests. Real bugs
  found there are cheaper than bugs found by users.
MASTER_TPL_EOF

cat > "$TPL_DIR/WORKER.md" <<'WORKER_TPL_EOF'
# Role: worker "{{WORKER}}"

You are one worker in a multi-agent team. Your entire assignment is the
task prompt you were given. Follow it exactly.

- Onboard first if present: this repo's AGENTS.md and docs/ai/START_HERE.md
  (reading ritual). The rules HERE override them on branches, scope, commits.
- Work ONLY in this directory — a git worktree on branch agent/{{WORKER}}.
  Never switch branches, never push, never touch the base branch (dev/main).
  Git hooks enforce this; do not fight them.
- Modify only files in the task's "Allowed scope". The "- path" lines there
  are machine-checked after your run (`agentteam verify`) — out-of-scope
  edits get the whole branch rejected. Need something outside it? Do NOT
  touch it — finish what you can, state the need in your report.
- No architecture changes, no new dependencies, unless the task grants them.
- Find code with CodeGraph (`codegraph explore "..."`) when available; run
  `codegraph sync` after edits if the index seems stale.
- Run the task's Validate commands before finishing — the "$ " lines will
  be re-run mechanically; claiming success with failing Validate commands
  is detected.
- If the repo keeps a CHANGELOG: never edit CHANGELOG.md itself (shared
  file = merge conflicts). Write your entry to changelog.d/<ID>.md instead
  — one or two lines; that path is always in scope.
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
One "- path" line per allowed file or directory — ENFORCED by `agentteam
verify` (globs ok; a trailing / means the whole directory; changelog.d/
is always allowed):
- src/feature.py
- tests/test_feature.py

## Constraints
Libraries to use/avoid, style, frozen interfaces, no new deps.

## Validate
Prose is fine here, but every line starting with "$ " is machine-run by
`agentteam verify` inside the worktree and must exit 0:
$ dotnet build -c Release
$ python3 -m unittest discover tests -v

## Done means
Validation passes + changes committed on your branch — only the files you
touched — as "<ID>: <summary>". If the repo keeps a CHANGELOG, add
changelog.d/<ID>.md (one or two lines); never edit CHANGELOG.md itself.

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

cat > "$TPL_DIR/REVIEW.md" <<'REVIEW_TPL_EOF'
# Role: independent reviewer (a different vendor than the author)

You are reviewing another AI's work. Below: the task order it was given,
then its diff (committed vs base, then uncommitted). You have no file
access — judge only what is in this prompt.

Check, in order:
1. SCOPE — does the diff touch only the task's Allowed scope?
2. CORRECTNESS — does the change do what the Goal says? Logic errors,
   missed edge cases, broken callers.
3. TESTS — do the tests actually exercise the change, or merely pass?
4. SMELLS — dead code, needless complexity, style breaks with context.

Be adversarial: your job is to find what the author missed, not to be
agreeable. Cite concrete lines from the diff for every claim. If the
material is truncated, say so and judge what you can see.

Output: at most ~20 lines. Numbered findings, each tagged BLOCKER /
MINOR / NIT, then exactly one final line:
VERDICT: APPROVE            (nothing blocking)
VERDICT: REQUEST-CHANGES    (one or more blockers)
REVIEW_TPL_EOF

cat > "$TPL_DIR/SABOTEUR.md" <<'SABOTEUR_TPL_EOF'
# Task {{ID}} — worker: {{WORKER}} (the saboteur seat)

## Goal
Find real defects in recently merged work by writing tests that FAIL
against the current base branch. Bugs exposed — not code fixed — is the
deliverable.

## Context
You are the saboteur: one agent per cycle attacks what the team just
merged. Read CHANGELOG.md / changelog.d/ and `git log --oneline -15` to
see what changed recently, then hunt: edge cases, error paths, boundary
values, wrong-directory launches, concurrency, off-by-ones — the paths
the existing tests never visit. Passing tests only check what was
predicted; you look for what wasn't.

## Allowed scope
- tests/
- test/
- changelog.d/

## Constraints
- Do NOT fix any bug you find — expose it. Fixes are separate tasks.
- Do NOT modify existing tests; add new ones, clearly marked (file or
  test names containing "sabotage" or the repo's equivalent convention).
- Genuine defects only: a test asserting behavior nobody promised is
  noise, not a finding.

## Validate
Your new failing tests ARE the product, so no "$ " auto-commands here.
Run the repo's test suite yourself: existing tests must still pass;
only your new sabotage tests may fail.

## Done means
New tests committed on your branch as "{{ID}}: sabotage findings".
If a real hunt finds nothing, commit nothing and say so — an empty
sabotage report is a valid (good!) result.

## Report
End with: SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS /
RISKS / NEEDS-REVIEW — and per finding: WHERE (file:line), REPRO (the
failing test name), EXPECTED vs ACTUAL, SEVERITY.
SABOTEUR_TPL_EOF

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
installs git hooks: a worker worktree can commit only on its own
`agent/<w>` branch and can never push, and every merge into the base
branch is recorded as a ledger `merge` event (post-merge hook).

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
{"event":"merge","ts":…,"worker":…,"subject":"<merge commit subject>"}
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
agentteam report <task> [n]    print the last n (default 60) lines of a
                               task's append-only report
agentteam version              installed tool version + config path
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
agentteam score [root]         per-worker scorecard from ledger.jsonl:
                               runs, ok/fail, walls, verify rate, merges,
                               avg duration
agentteam doctor               preflight the project: base branch present,
                               agent binaries, worktree health, stale
                               pidfiles, disk headroom; nonzero on error
agentteam new <url> [name] [w...]  bootstrap a project: clone -> dev branch
                               -> init -> copy $CONF/playbooks/*.md into
                               coord/docs/
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
mentions limits and the run succeeded). `AGENTTEAM_AUTO_VERIFY=1` makes
every run append its own verify verdict after finishing.
`AGENTTEAM_AUTO_SYNC=1` fast-forwards a worker onto the base branch
before a run when the worktree is clean, so it never builds against
stale code (otherwise `run` warns and leaves it to the operator).
`AGENTTEAM_ALLOW_SECRETS=1` overrides the init secrets preflight. Agent
invocation templates live in `~/.config/agentteam/agents.conf` (project
override: `coord/agents.conf`).

Fleet intelligence: `agentteam score` (ledger-based, always available)
and the companion tool `myapp <project-root>` (full scorecard incl.
pre-ledger history from reports/*.md). LEAD SHOULD consult one of them
when assigning tasks.

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
PROTOCOL_TPL_EOF

# --------------------------------------------------------------- completion
COMP_DIR="${AGENTTEAM_COMPLETION_DIR:-$HOME/.local/share/bash-completion/completions}"
mkdir -p "$COMP_DIR"
cat > "$COMP_DIR/agentteam" <<'COMPLETION_EOF'
# bash completion for agentteam — commands, then workers/tasks/agents in context
_agentteam() {
  local cur cmd root d cmds
  cur="${COMP_WORDS[COMP_CWORD]}"
  cmds="new init run verify diff sync review race sabotage score doctor tail kill report status agents off on smoke selftest stop resume version help"
  if [ "$COMP_CWORD" -eq 1 ]; then
    COMPREPLY=( $(compgen -W "$cmds" -- "$cur") ); return
  fi
  cmd="${COMP_WORDS[1]}"
  d="$PWD"; root=""
  while [ "$d" != "/" ]; do
    if [ -d "$d/coord" ] && [ -d "$d/wt" ]; then root="$d"; break; fi
    d=$(dirname "$d")
  done
  local workers="" tasks="" agents=""
  [ -n "$root" ] && workers=$(ls "$root/wt" 2>/dev/null)
  [ -n "$root" ] && tasks=$(ls "$root/coord/tasks" 2>/dev/null | sed 's/\.md$//' | grep -v '^TEMPLATE$')
  agents=$(sed -n 's/^\([a-zA-Z0-9_-]*\)=.*/\1/p' \
    "${AGENTTEAM_CONF_DIR:-$HOME/.config/agentteam}/agents.conf" 2>/dev/null)
  case "$cmd" in
    run)
      if [ "$COMP_CWORD" -eq 2 ]; then COMPREPLY=( $(compgen -W "-b $workers" -- "$cur") )
      elif [ "${COMP_WORDS[2]}" = "-b" ] && [ "$COMP_CWORD" -eq 3 ]; then COMPREPLY=( $(compgen -W "$workers" -- "$cur") )
      else COMPREPLY=( $(compgen -W "$tasks" -- "$cur") ); fi;;
    verify|review)
      if [ "$COMP_CWORD" -eq 2 ]; then COMPREPLY=( $(compgen -W "$workers" -- "$cur") )
      elif [ "$COMP_CWORD" -eq 3 ]; then COMPREPLY=( $(compgen -W "$tasks" -- "$cur") )
      else COMPREPLY=( $(compgen -W "$agents" -- "$cur") ); fi;;
    diff|sync|sabotage) COMPREPLY=( $(compgen -W "$workers" -- "$cur") );;
    race)
      if [ "$COMP_CWORD" -eq 2 ]; then COMPREPLY=( $(compgen -W "$tasks" -- "$cur") )
      else COMPREPLY=( $(compgen -W "$workers" -- "$cur") ); fi;;
    tail|kill|report) COMPREPLY=( $(compgen -W "$tasks" -- "$cur") );;
    off|on) COMPREPLY=( $(compgen -W "$agents" -- "$cur") );;
  esac
}
complete -F _agentteam agentteam
COMPLETION_EOF

echo
echo "agentteam installed."
echo "  command   : $BIN_DIR/agentteam   (ensure that dir is on PATH)"
echo "  config    : $CONF_DIR/agents.conf   <- EDIT: enable/tune your agents"
echo "  quota     : agentteam off <agent> 5h|7d   /   agentteam on <agent>"
echo
echo "Next: agentteam selftest        (mock-agent rehearsal, zero quota)"
echo "Then: cd <your repo clone> && agentteam init codex antigravity opencode grok"
