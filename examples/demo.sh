#!/usr/bin/env bash
# agentteam worked-example driver — exercises EVERY feature against the real
# installed agentteam, using stand-in agents (zero quota). Output becomes
# docs/EXAMPLE.md.
set -u
export PATH="$HOME/.local/bin:$PATH"

DEMO="${1:?usage: demo.sh <demo-root>}"
rm -rf "$DEMO"; mkdir -p "$DEMO/greeter"
cd "$DEMO/greeter"

step() { echo; echo "════════ $* ════════"; }

# ---------------------------------------------------------------- project
step "ACT 1 — a tiny real project"
git init -q -b dev repo
cd repo
git config user.email daniel@example.com
git config user.name  Daniel

cat > greet.py <<'EOF'
"""greeter — the demo project for the agentteam worked example."""


def greet(name):
    return f"Hello, {name}!"


if __name__ == "__main__":
    import sys
    print(greet(sys.argv[1] if len(sys.argv) > 1 else "world"))
EOF
mkdir -p tests
: > tests/__init__.py
cat > tests/test_greet.py <<'EOF'
import unittest
from greet import greet


class TestGreet(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(greet("Dan"), "Hello, Dan!")


if __name__ == "__main__":
    unittest.main()
EOF
printf '# Changelog\n\n## v0.1.0\n- initial greeter\n' > CHANGELOG.md
printf '__pycache__/\n*.pyc\n' > .gitignore
git add -A && git commit -q -m "v0.1.0: initial greeter"
echo "repo ready:"; git log --oneline

# ------------------------------------------------- stand-in fleet (no quota)
step "ACT 1b — the stand-in fleet (project-scoped coord/agents.conf)"
mkdir -p ../coord
cat > ../coord/agents.conf <<'EOF'
# DEMO stand-ins — swap these lines for your real fleet and nothing else changes.
# alpha/beta "do the work" by executing the task file's embedded simulate-block:
alpha=bash -c 'sed -n "/<!-- simulate/,/simulate -->/p" "$TASKFILE" | sed "1d;\$d" | bash -s && echo ok'
beta=bash -c 'sed -n "/<!-- simulate/,/simulate -->/p" "$TASKFILE" | sed "1d;\$d" | bash -s && echo ok'
# slow: a long-running agent, for the background/tail/kill drill
slow=bash -c 'echo starting long analysis; sleep 30; echo ok'
# critic: reviewer stand-in for `agentteam review`
critic=bash -c 'cat "$TASKFILE" >/dev/null; printf "1. NIT greet.py: docstring could mention the polite flag.\nScope respected; tests exercise the change; no blockers.\nVERDICT: APPROVE\nok\n"'
# gamma: saboteur stand-in — hunts the freshest merge with a failing test
gamma=bash -c 'printf "import unittest\nfrom greet import greet\n\n\nclass TestSabotage(unittest.TestCase):\n    def test_polite_preserves_name_capitalisation(self):\n        self.assertEqual(greet(\"McDonald\", polite=True), \"Good day, McDonald!\")\n\n\nif __name__ == \"__main__\":\n    unittest.main()\n" > tests/test_sabotage.py && git add tests/test_sabotage.py && git commit -q -m "SAB: expose name-mangling in polite mode" && echo "SUMMARY: 1 finding — polite mode rewrites the name"; echo ok'
EOF
echo "coord/agents.conf written (project override — the global conf stays untouched)"

# ------------------------------------------------------- secrets preflight
step "ACT 2 — init refuses while secrets are tracked"
printf 'TOKEN=hunter2\n' > .env
git add .env && git commit -q -m "oops: token in git"
agentteam init alpha beta gamma slow || true
echo "-- fixing it like the handbook says:"
git rm -q --cached .env && printf '.env\n' >> .gitignore
git add .gitignore && git commit -q -m "untrack .env, ignore it"

step "ACT 2b — init, for real this time"
agentteam init alpha beta gamma slow

step "ACT 3 — roll call + smoke (stand-ins answer like any fleet)"
agentteam agents
echo "-- smoke:"
agentteam smoke

# --------------------------------------------------------------- T1 cycle
step "ACT 4 — T1: a feature task, written the machine-checkable way"
cat > ../coord/tasks/T1-alpha.md <<'EOF'
# Task T1 — worker: alpha

## Goal
greet() gains a polite mode: greet(name, polite=True) -> "Good day, <name>!"

## Context
greet.py holds a single greet(name) function returning "Hello, <name>!".
tests/test_greet.py covers the basic form. Keep the default behavior
identical; polite mode is opt-in.

## Allowed scope
- greet.py
- tests/test_greet.py

## Constraints
Standard library only. No new files outside scope (changelog.d/ excepted).

## Validate
$ python3 -m unittest discover -s tests -t . -v

## Done means
Validation passes + changes committed on your branch as "T1: <summary>"
+ changelog fragment changelog.d/T1.md (never CHANGELOG.md itself).

## Report
End with: SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS /
RISKS / NEEDS-REVIEW

<!-- simulate
cat > greet.py <<'EOF_G'
"""greeter — the demo project for the agentteam worked example."""


def greet(name, polite=False):
    if polite:
        return f"Good day, {name.capitalize()}!"
    return f"Hello, {name}!"


if __name__ == "__main__":
    import sys
    print(greet(sys.argv[1] if len(sys.argv) > 1 else "world"))
EOF_G
cat > tests/test_greet.py <<'EOF_T'
import unittest
from greet import greet


class TestGreet(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(greet("Dan"), "Hello, Dan!")

    def test_polite(self):
        self.assertEqual(greet("dan", polite=True), "Good day, Dan!")


if __name__ == "__main__":
    unittest.main()
EOF_T
mkdir -p changelog.d
printf 'T1: greet() gains polite=True mode ("Good day, ...").\n' > changelog.d/T1.md
python3 -m unittest discover -s tests -t . >/dev/null 2>&1
git add greet.py tests/test_greet.py changelog.d/T1.md
git commit -q -m "T1: polite greeting mode"
simulate -->
EOF
echo "task file written; dispatching:"
agentteam run alpha T1-alpha

step "ACT 4b — verify: the mechanical gate"
agentteam verify alpha T1-alpha

step "ACT 4c — the receipts: diff --stat"
agentteam diff alpha --stat

step "ACT 4d — cross-vendor review (critic reviews alpha's work)"
agentteam review alpha T1-alpha critic

step "ACT 4e — the human gate: own test run, then merge, then sync"
python3 -m unittest discover -s tests -t . 2>&1 | tail -2
git merge --no-ff agent/alpha -m "merge T1: polite mode" -q
echo "merged. now every workshop rebuilds on the new base:"
agentteam sync

# ------------------------------------------------------------- guard hooks
step "ACT 5 — the guard hooks say no"
cd ../wt/alpha
git switch -q -c evil-experiment
echo scribble > note.txt
git add note.txt
git commit -m "off-branch commit" || true
git reset -q && rm -f note.txt
git switch -q agent/alpha && git branch -q -D evil-experiment
cd ../../repo
echo "(worker worktrees physically commit only on their own agent/<w> branch)"

# ------------------------------------------------------------ rogue caught
step "ACT 6 — T2: a worker leaves its lane; verify catches it"
cat > ../coord/tasks/T2-beta.md <<'EOF'
# Task T2 — worker: beta

## Goal
Add an edge-case test for the default greeting.

## Context
tests/test_greet.py exists; greet.py is NOT yours to touch.

## Allowed scope
- tests/test_edge.py

## Validate
$ python3 -m unittest discover -s tests -t .

## Done means
Test committed as "T2: <summary>".

## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS /
NEEDS-REVIEW

<!-- simulate
cat > tests/test_edge.py <<'EOF_E'
import unittest
from greet import greet


class TestEdge(unittest.TestCase):
    def test_world_default(self):
        self.assertEqual(greet("world"), "Hello, world!")


if __name__ == "__main__":
    unittest.main()
EOF_E
sed -i 's/the demo project for the agentteam worked example/tidied by beta while passing by/' greet.py
git add tests/test_edge.py greet.py
git commit -q -m "T2: edge test (+ a helpful little refactor)"
simulate -->
EOF
agentteam run beta T2-beta
echo "-- report said done. verify says:"
agentteam verify beta T2-beta || true
echo "-- rejected. owner wipes the branch; foreman will re-brief as T2b:"
git -C ../wt/beta reset -q --hard dev

# ------------------------------------------- background, lock, tail, kill
step "ACT 7 — background runs: -b, status, the lock, tail, kill"
cat > ../coord/tasks/T3-slow.md <<'EOF'
# Task T3 — worker: slow

## Goal
Long analysis (demo of background machinery).

## Context
The slow agent naps; we won't wait for it.

## Allowed scope
- greet.py

## Validate

## Done means
n/a — this run gets killed on purpose.

## Report
SUMMARY
EOF
agentteam run -b slow T3-slow
sleep 2
echo "-- status while it runs (note RUNNING marker + pidfile row):"
agentteam status
echo "-- a second run on the same worker is refused (per-worker lock):"
agentteam run slow T3-slow || true
echo "-- watching the live log for two seconds:"
timeout 2 agentteam tail T3-slow || true
echo "-- enough. kill it:"
agentteam kill T3-slow

# ------------------------------------------------------------------- race
step "ACT 8 — the bake-off: race one task across two workers"
cat > ../coord/tasks/T4.md <<'EOF'
# Task T4 — race task

## Goal
Add farewell(name) -> "Goodbye, <name>." with a test.

## Context
greet.py currently exposes greet() only. Both racers get this same order;
only one branch will be merged.

## Allowed scope
- greet.py
- tests/test_greet.py

## Validate
$ python3 -m unittest discover -s tests -t .

## Done means
farewell() committed as "T4: <summary>" (+ changelog fragment).

## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS /
NEEDS-REVIEW

<!-- simulate
case "$(git rev-parse --abbrev-ref HEAD)" in
  agent/alpha)
    python3 - <<'PY'
import pathlib
p = pathlib.Path("greet.py"); s = p.read_text()
s += '\n\ndef farewell(name):\n    return f"Goodbye, {name}."\n'
p.write_text(s)
PY
    git add greet.py
    git commit -q -m "T4: farewell() — minimal"
    ;;
  agent/beta)
    python3 - <<'PY'
import pathlib
p = pathlib.Path("greet.py"); s = p.read_text()
s += '\n\ndef farewell(name):\n    return f"Goodbye, {name}."\n'
p.write_text(s)
t = pathlib.Path("tests/test_greet.py"); ts = t.read_text()
ts = ts.replace("if __name__", 'class TestFarewell(unittest.TestCase):\n    def test_farewell(self):\n        from greet import farewell\n        self.assertEqual(farewell("Dan"), "Goodbye, Dan.")\n\n\nif __name__')
t.write_text(ts)
PY
    mkdir -p changelog.d
    printf 'T4: farewell() function.\n' > changelog.d/T4.md
    git add greet.py tests/test_greet.py changelog.d/T4.md
    git commit -q -m "T4: farewell() + test + fragment"
    ;;
esac
simulate -->
EOF
agentteam race T4 alpha beta
sleep 3
echo "-- both done. the review queue:"
agentteam status | sed -n '/== workers/,/== running/p' | head -8
echo "-- verify both, compare the diffs:"
agentteam verify alpha T4-alpha | tail -3
agentteam verify beta  T4-beta  | tail -3
agentteam diff alpha --stat | sed -n '/committed vs/,/uncommitted/p' | head -5
agentteam diff beta  --stat | sed -n '/committed vs/,/uncommitted/p' | head -6
echo "-- beta wins (same function, plus a real test and the fragment):"
git merge --no-ff agent/beta -m "merge T4: farewell (beta wins the race)" -q
git -C ../wt/alpha reset -q --hard dev   # reject the losing branch
agentteam sync

# --------------------------------------------------------------- sabotage
step "ACT 9 — the saboteur seat finds a real bug"
agentteam sabotage gamma
sleep 2
echo "-- the saboteur's report tail:"
tail -n 12 ../coord/reports/SAB-*-gamma.md | head -14
echo "-- its failing test, run against dev:"
git -C ../wt/gamma diff dev...HEAD --stat
cd ../wt/gamma && python3 -m unittest discover -s tests -t . 2>&1 | tail -4; cd ../../repo

# ------------------------------------------------------- bench + red button
step "ACT 10 — quota bench and the red button"
agentteam off alpha 5h
agentteam run alpha T1-alpha || true
agentteam on alpha
agentteam stop
agentteam run alpha T1-alpha || true
agentteam resume

# ------------------------------------------------------------- fix cycle
step "ACT 11 — T5: the fix task closes the loop"
cat > ../coord/tasks/T5-alpha.md <<'EOF'
# Task T5 — worker: alpha

## Goal
Fix the saboteur's finding: polite mode must not rewrite the name.

## Context
greet(name, polite=True) currently returns name.capitalize() — it mangles
"McDonald" to "Mcdonald". The old test_polite asserted the buggy behavior;
correct it. Adopt the saboteur's test as tests/test_sabotage.py.

## Allowed scope
- greet.py
- tests/test_greet.py
- tests/test_sabotage.py

## Validate
$ python3 -m unittest discover -s tests -t . -v

## Done means
All tests green (including the adopted sabotage test), committed as
"T5: <summary>" + changelog.d/T5.md.

## Report
SUMMARY / FILES CHANGED / TESTS RUN + RESULTS / ASSUMPTIONS / RISKS /
NEEDS-REVIEW

<!-- simulate
python3 - <<'PY'
import pathlib
p = pathlib.Path("greet.py"); s = p.read_text()
s = s.replace('f"Good day, {name.capitalize()}!"', 'f"Good day, {name}!"')
p.write_text(s)
t = pathlib.Path("tests/test_greet.py"); ts = t.read_text()
ts = ts.replace('greet("dan", polite=True), "Good day, Dan!"',
                'greet("dan", polite=True), "Good day, dan!"')
t.write_text(ts)
PY
cat > tests/test_sabotage.py <<'EOF_S'
import unittest
from greet import greet


class TestSabotage(unittest.TestCase):
    def test_polite_preserves_name_capitalisation(self):
        self.assertEqual(greet("McDonald", polite=True), "Good day, McDonald!")


if __name__ == "__main__":
    unittest.main()
EOF_S
printf 'T5: polite mode no longer rewrites the name (saboteur finding).\n' > changelog.d/T5.md
python3 -m unittest discover -s tests -t . >/dev/null 2>&1
git add greet.py tests/test_greet.py tests/test_sabotage.py changelog.d/T5.md
git commit -q -m "T5: stop mangling names in polite mode"
simulate -->
EOF
agentteam run alpha T5-alpha
agentteam verify alpha T5-alpha
git merge --no-ff agent/alpha -m "merge T5: saboteur finding fixed" -q
git -C ../wt/gamma reset -q --hard dev   # SAB branch superseded by T5
agentteam sync

# ----------------------------------------------------------------- ledger
step "ACT 12 — the ledger remembers everything"
tail -n 9 ../coord/reports/ledger.jsonl
echo "-- fragments waiting for release roll-up:"
ls changelog.d/
echo "-- final history:"
git log --oneline | head -8
python3 -m unittest discover -s tests -t . 2>&1 | tail -2

step "DONE"
