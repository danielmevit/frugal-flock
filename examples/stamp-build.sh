#!/usr/bin/env bash
# stamp-build.sh — TESTPLAN Part C, worked end to end.
#
#   bash examples/stamp-build.sh [work-dir]
#
# Builds a REAL, useful tool — `stamp`, a one-line git status printer — through
# the full agentteam loop: freeze a contract, dispatch disjoint parallel tasks,
# verify, merge, sync, then let the saboteur find a genuine bug and close it
# with a fix cycle. The workers are deterministic stand-ins (zero quota) that
# write real, working code; the machinery, the gate, and the resulting tool are
# all real. At the end `stamp` runs on actual repositories and its test suite
# is green — proof the loop produces working software, not just diffs.
set -uo pipefail
export PATH="$HOME/.local/bin:$PATH"
command -v agentteam >/dev/null || { echo "install agentteam first: bash agentteam-install.sh"; exit 1; }

step() { printf '\n\033[1m════ %s ════\033[0m\n' "$*"; }
own()  { printf '  \033[36mYOU:\033[0m %s\n' "$*"; }

WORK="${1:-$(mktemp -d)}"; rm -rf "$WORK"; mkdir -p "$WORK"
CONF="$WORK/conf"; mkdir -p "$CONF/templates"
cp "$HOME/.config/agentteam/templates/"*.md "$CONF/templates/" 2>/dev/null \
  || { echo "run bash agentteam-install.sh first (templates missing)"; exit 1; }
export AGENTTEAM_CONF_DIR="$CONF"

# Stand-in fleet: each worker runs the simulate-block hidden in its task file.
# gamma (the saboteur) and the fixer use the same mechanism.
cat > "$CONF/agents.conf" <<'CONF'
codex=bash -c 'sed -n "/<!-- do/,/do -->/p" "$TASKFILE" | sed "1d;\$d" | bash -s && echo ok'
opencode=bash -c 'sed -n "/<!-- do/,/do -->/p" "$TASKFILE" | sed "1d;\$d" | bash -s && echo ok'
antigravity=bash -c 'sed -n "/<!-- do/,/do -->/p" "$TASKFILE" | sed "1d;\$d" | bash -s && echo ok'
gamma=bash -c 'sed -n "/<!-- do/,/do -->/p" "$TASKFILE" | sed "1d;\$d" | bash -s && echo ok'
CONF

# ---- the project ----------------------------------------------------------
mkdir -p "$WORK/stamp"
git init -q -b dev "$WORK/stamp/repo"
git -C "$WORK/stamp/repo" config user.email you@example.com
git -C "$WORK/stamp/repo" config user.name You
( cd "$WORK/stamp/repo" || exit 1
  printf '# stamp\n\nA one-line git status stamp.\n' > README.md
  printf '__pycache__/\n*.pyc\n' > .gitignore
  git add -A && git commit -q -m "v0: empty stamp project" )
cd "$WORK/stamp/repo" || exit 1

echo "Building the real 'stamp' tool through agentteam in: $WORK"
agentteam init codex opencode antigravity gamma >/dev/null 2>&1

step "PLAN — the owner freezes the contract before any feature work"
own "The output format and module boundaries are the frozen contract."
mkdir -p tests
: > tests/__init__.py
cat > CONTRACT.md <<'EOF'
# stamp contract (frozen)

Output: "<branch> <short-sha> <clean|+dirty>[ ^ahead][ v behind] (<age>)"

Modules (disjoint ownership):
- agefmt.py   : human_age(seconds) -> str
- gitread.py  : is_repo, head, is_dirty, ahead_behind, last_commit_epoch (all take cwd)
- stamp.py    : stamp(cwd) wires the above into the format + a CLI main(argv)
EOF
git add CONTRACT.md tests/__init__.py
git commit -q -m "contract: freeze stamp output format + module boundaries"
own "Contract committed on dev. Sync the workshops onto it before dispatching"
own "(a worker branched before the contract would build against stale code):"
agentteam sync | sed 's/^/    /'

# ---- helper: write a task file with an embedded do-block -----------------
task() { cat > "../coord/tasks/$1.md"; }

step "DISPATCH — S1 (codex) and S2 (opencode), disjoint scopes, in parallel"
task S1-codex <<'EOF'
# Task S1 — worker: codex
## Goal
Implement agefmt.human_age(seconds) per the contract.
## Allowed scope
- agefmt.py
- tests/test_agefmt.py
## Validate
$ python3 -m unittest discover -s tests
## Done means
agefmt.py + its test committed as "S1: agefmt".
## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW
<!-- do
cat > agefmt.py <<'PYEOF'
"""Human-readable durations for stamp."""


def human_age(seconds):
    seconds = int(seconds)
    if seconds < 5:
        return "just now"
    for unit, size in (("y", 31536000), ("mo", 2592000), ("d", 86400),
                       ("h", 3600), ("m", 60)):
        if seconds >= size:
            return f"{seconds // size}{unit} ago"
    return f"{seconds}s ago"
PYEOF
cat > tests/test_agefmt.py <<'PYEOF'
import unittest
from agefmt import human_age


class T(unittest.TestCase):
    def test_now(self): self.assertEqual(human_age(0), "just now")
    def test_sec(self): self.assertEqual(human_age(42), "42s ago")
    def test_min(self): self.assertEqual(human_age(180), "3m ago")
    def test_hour(self): self.assertEqual(human_age(7200), "2h ago")
    def test_day(self): self.assertEqual(human_age(172800), "2d ago")
    def test_year(self): self.assertEqual(human_age(63072000), "2y ago")
PYEOF
python3 -m unittest discover -s tests >/dev/null 2>&1
git add agefmt.py tests/test_agefmt.py
git commit -q -m "S1: agefmt"
do -->
EOF

task S2-opencode <<'EOF'
# Task S2 — worker: opencode
## Goal
Implement gitread.py (all git reading) per the contract.
## Allowed scope
- gitread.py
- tests/test_gitread.py
## Validate
$ python3 -m unittest discover -s tests
## Done means
gitread.py + its test committed as "S2: gitread".
## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW
<!-- do
cat > gitread.py <<'PYEOF'
"""Read git repository state for stamp. Standard library only."""
import subprocess


def _git(args, cwd):
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def is_repo(cwd):
    return _git(["rev-parse", "--is-inside-work-tree"], cwd)[0] == 0


def head(cwd):
    _, branch, _ = _git(["rev-parse", "--abbrev-ref", "HEAD"], cwd)
    rc, sha, _ = _git(["rev-parse", "--short", "HEAD"], cwd)
    return branch, (sha if rc == 0 else None)


def is_dirty(cwd):
    return bool(_git(["status", "--porcelain"], cwd)[1])


def ahead_behind(cwd):
    _, up, _ = _git(["rev-parse", "--abbrev-ref", "@{upstream}"], cwd)
    if not up:
        return 0, 0
    _, counts, _ = _git(["rev-list", "--left-right", "--count", "@{upstream}...HEAD"], cwd)
    try:
        behind, ahead = (int(x) for x in counts.split())
        return ahead, behind
    except ValueError:
        return 0, 0


def last_commit_epoch(cwd):
    rc, ts, _ = _git(["log", "-1", "--format=%ct"], cwd)
    return int(ts) if rc == 0 and ts else None
PYEOF
cat > tests/test_gitread.py <<'PYEOF'
import os, subprocess, tempfile, unittest
import gitread


def git(a, d): subprocess.run(["git", *a], cwd=d, capture_output=True)


class T(unittest.TestCase):
    def test_non_repo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(gitread.is_repo(d))

    def test_head_and_clean(self):
        with tempfile.TemporaryDirectory() as d:
            git(["init", "-b", "main"], d); git(["config", "user.email", "a@b"], d)
            git(["config", "user.name", "a"], d)
            open(os.path.join(d, "f"), "w").write("x")
            git(["add", "-A"], d); git(["commit", "-m", "one"], d)
            b, s = gitread.head(d)
            self.assertEqual(b, "main"); self.assertTrue(s)
            self.assertFalse(gitread.is_dirty(d))
PYEOF
python3 -m unittest discover -s tests >/dev/null 2>&1
git add gitread.py tests/test_gitread.py
git commit -q -m "S2: gitread"
do -->
EOF

agentteam run -b codex S1-codex >/dev/null 2>&1
agentteam run -b opencode S2-opencode >/dev/null 2>&1
sleep 3
agentteam status | sed -n '/workers (review queue/,/running/p' | head -7

step "GATE — verify each, then the owner merges, then sync"
for wt in codex:S1-codex opencode:S2-opencode; do
  w=${wt%%:*}; t=${wt#*:}
  agentteam verify "$w" "$t" | grep -E 'scope|validate|verdict'
  own "reading the diff, then merging $t"
  git merge --no-ff -q "agent/$w" -m "merge $t" 2>/dev/null
done
agentteam sync >/dev/null

step "DISPATCH — S3 (antigravity) wires the tool, after S1+S2 are in"
task S3-antigravity <<'EOF'
# Task S3 — worker: antigravity
## Goal
Implement stamp.stamp(cwd) + CLI, wiring agefmt and gitread per the contract.
## Allowed scope
- stamp.py
- tests/test_stamp.py
## Validate
$ python3 -m unittest discover -s tests
## Done means
stamp.py + its test committed as "S3: stamp cli".
## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW
<!-- do
cat > stamp.py <<'PYEOF'
#!/usr/bin/env python3
"""stamp — one-line git status stamp."""
import sys
import time

import gitread
from agefmt import human_age


def stamp(cwd="."):
    if not gitread.is_repo(cwd):
        return "not a git repository"
    branch, sha = gitread.head(cwd)
    if sha is None:
        return f"{branch or 'HEAD'} (no commits yet)"
    state = "+dirty" if gitread.is_dirty(cwd) else "clean"
    ahead, behind = gitread.ahead_behind(cwd)
    track = "".join([f" ^{ahead}" if ahead else "", f" v{behind}" if behind else ""])
    ts = gitread.last_commit_epoch(cwd)
    age = f" ({human_age(time.time() - ts)})" if ts else ""
    return f"{branch} {sha} {state}{track}{age}"


def main(argv):
    if "--help" in argv or "-h" in argv:
        print("usage: stamp [PATH]\n\nPrint a one-line git status stamp.")
        return 0
    print(stamp(argv[1] if len(argv) > 1 else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
PYEOF
cat > tests/test_stamp.py <<'PYEOF'
import os, subprocess, tempfile, unittest
import stamp


def git(a, d): subprocess.run(["git", *a], cwd=d, capture_output=True)


class T(unittest.TestCase):
    def test_non_repo(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(stamp.stamp(d), "not a git repository")

    def test_clean(self):
        with tempfile.TemporaryDirectory() as d:
            git(["init", "-b", "main"], d); git(["config", "user.email", "a@b"], d)
            git(["config", "user.name", "a"], d)
            open(os.path.join(d, "f"), "w").write("x")
            git(["add", "-A"], d); git(["commit", "-m", "one"], d)
            out = stamp.stamp(d)
            self.assertIn("main", out); self.assertIn("clean", out)
PYEOF
python3 -m unittest discover -s tests >/dev/null 2>&1
git add stamp.py tests/test_stamp.py
git commit -q -m "S3: stamp cli"
do -->
EOF
agentteam run antigravity S3-antigravity >/dev/null 2>&1
agentteam verify antigravity S3-antigravity | grep -E 'scope|validate|verdict'
own "merging S3 and syncing"
git merge --no-ff -q agent/antigravity -m "merge S3: stamp cli" 2>/dev/null
agentteam sync >/dev/null

step "PROVE IT LIKE A USER — run the real tool on real repositories"
python3 -m unittest discover -s tests 2>&1 | tail -1
own "stamp on this very project:      $(python3 stamp.py .)"
own "stamp on the agentteam-docs repo: $(python3 stamp.py '/mnt/d/Vibe Coding/_vm/agentteam-docs' 2>/dev/null || echo '(not present)')"

step "SABOTAGE — spare quota hunts the fresh code for a real bug"
task SAB-gamma <<'EOF'
# Task SAB-gamma — worker: gamma (saboteur seat)
## Goal
Find a real crash in stamp by attacking untested paths.
## Allowed scope
- tests/test_sabotage.py
## Validate
## Done means
A failing test committed as "SAB: crash on missing path".
## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW
<!-- do
cat > tests/test_sabotage.py <<'PYEOF'
import unittest
import stamp


class TestSabotage(unittest.TestCase):
    def test_missing_path_does_not_crash(self):
        # stamp on a path that does not exist must not raise
        self.assertEqual(stamp.stamp("/no/such/path/here"), "not a git repository")
PYEOF
git add tests/test_sabotage.py
git commit -q -m "SAB: crash on missing path"
echo "FINDING: stamp('/no/such/path') raises FileNotFoundError (subprocess cwd)"
do -->
EOF
agentteam run gamma SAB-gamma >/dev/null 2>&1
own "the saboteur's finding:"
agentteam report SAB-gamma 20 | grep -i finding || true
own "confirming the finding fails against dev:"
git merge --no-ff -q agent/gamma -m "merge SAB: adopt failing test" 2>/dev/null
python3 -m unittest discover -s tests 2>&1 | tail -3 | head -1

step "FIX — one task closes the saboteur's finding"
agentteam sync >/dev/null
task F1-codex <<'EOF'
# Task F1 — worker: codex
## Goal
Fix the saboteur's finding: a missing path must not crash.
## Allowed scope
- gitread.py
## Validate
$ python3 -m unittest discover -s tests
## Done means
All tests green (incl. the sabotage test), committed "F1: guard missing path".
## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS / NEEDS-REVIEW
<!-- do
python3 - <<'PYEOF'
import pathlib, re
p = pathlib.Path("gitread.py"); s = p.read_text()
s = s.replace(
    'def _git(args, cwd):\n    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)\n    return r.returncode, r.stdout.strip(), r.stderr.strip()',
    'def _git(args, cwd):\n    import os\n    if not os.path.isdir(cwd):\n        return 1, "", "no such path"\n    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)\n    return r.returncode, r.stdout.strip(), r.stderr.strip()')
p.write_text(s)
PYEOF
python3 -m unittest discover -s tests >/dev/null 2>&1
git add gitread.py
git commit -q -m "F1: guard missing path"
do -->
EOF
agentteam run codex F1-codex >/dev/null 2>&1
agentteam verify codex F1-codex | grep -E 'validate|verdict'
own "merging the fix"
git merge --no-ff -q agent/codex -m "merge F1: guard missing path" 2>/dev/null

step "DONE — green suite, the bug is closed, the tool is real"
python3 -m unittest discover -s tests 2>&1 | tail -1
own "stamp on a missing path now:  $(python3 stamp.py /no/such/path)"
own "final history:"
git log --oneline | sed 's/^/    /'
step "SCORECARD"
agentteam score 2>/dev/null | head -8

if [ "${KEEP:-0}" = "1" ]; then
  echo; echo "kept the built tool at: $WORK/stamp/repo"
else
  cd /; rm -rf "$WORK"
fi
