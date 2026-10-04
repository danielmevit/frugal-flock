#!/usr/bin/env bash
# Mock-only quality regressions. Installs and runs entirely under mktemp.
set -euo pipefail
QUALITY_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
QUALITY_SB=$(mktemp -d)
trap 'rm -rf -- "$QUALITY_SB"' EXIT
export AGENTTEAM_BIN_DIR="$QUALITY_SB/bin"
export AGENTTEAM_CONF_DIR="$QUALITY_SB/conf"
export AGENTTEAM_COMPLETION_DIR="$QUALITY_SB/completion"
export GIT_AUTHOR_NAME=quality-test GIT_AUTHOR_EMAIL=quality@test.invalid
export GIT_COMMITTER_NAME=quality-test GIT_COMMITTER_EMAIL=quality@test.invalid
export AGENTTEAM_TIMEOUT=30 AGENTTEAM_VERIFY_TIMEOUT=15
export AGENTTEAM_AUTO_VERIFY=0 AGENTTEAM_AUTO_OFF=0 AGENTTEAM_AUTO_SYNC=0
bash "$QUALITY_REPO/frugal-flock-install.sh" > "$QUALITY_SB/install.log"
QUALITY_AT="$AGENTTEAM_BIN_DIR/frugal-flock"
git init -q -b dev "$QUALITY_SB/project/repo"
cd "$QUALITY_SB/project/repo"
git commit -qm initial --allow-empty
"$QUALITY_AT" init mock noop > "$QUALITY_SB/init.log" 2>&1
printf '%s\n' "mock=bash -c 'set -e; echo work >> hello.txt; git add hello.txt; git commit -qm quality; exit \"\${MOCK_EXIT:-0}\"'" \
  "noop=bash -c 'exit 0'" > "$AGENTTEAM_CONF_DIR/agents.conf"
QUALITY_OK=0
task() {
  printf '# Task %s\n## Goal\nquality\n## Allowed scope\n%s\n## Validate\n%s\n' \
    "$1" "$2" "$3" > "../coord/tasks/$1.md"
}
expect() {
  local want="$1" label="$2" rc=0; shift 2
  "$@" > "$QUALITY_SB/output" 2>&1 || rc=$?
  if [ "$rc" != "$want" ]; then
    printf 'FAIL %s: expected %s, got %s\n' "$label" "$want" "$rc" >&2
    tail -n 12 "$QUALITY_SB/output" >&2; exit 1
  fi
  QUALITY_OK=$((QUALITY_OK+1))
}
for id in missing-scope missing-checks missing-both; do
  scope="- hello.txt"; checks='$ true'
  [ "$id" != missing-scope ] && [ "$id" != missing-both ] || scope=""
  [ "$id" != missing-checks ] && [ "$id" != missing-both ] || checks=""
  task "$id" "$scope" "$checks"
  expect 0 "$id worker" "$QUALITY_AT" run mock "$id"
  expect 2 "$id incomplete" "$QUALITY_AT" verify mock "$id"
  grep -q 'verdict  : INCOMPLETE' "$QUALITY_SB/output"
done
task pass '- hello.txt' '$ test -s hello.txt'
expect 0 'ordinary worker' "$QUALITY_AT" run mock pass
expect 0 'complete validation' "$QUALITY_AT" verify mock pass
task failed-check '- hello.txt' '$ false'
expect 1 'real check failure' "$QUALITY_AT" verify mock failed-check
task wrong-scope '- other.txt' '$ true'
expect 1 'real scope violation' "$QUALITY_AT" verify mock wrong-scope
task empty '- hello.txt' '$ true'
expect 0 'empty worker process' "$QUALITY_AT" run noop empty
expect 1 'empty candidate failure' "$QUALITY_AT" verify noop empty
task auto-fail '- hello.txt' '$ false'
expect 1 'auto-verify failure propagates' env AGENTTEAM_AUTO_VERIFY=1 "$QUALITY_AT" run mock auto-fail
task auto-incomplete '- hello.txt' ''
expect 2 'auto-verify incomplete propagates' env AGENTTEAM_AUTO_VERIFY=1 "$QUALITY_AT" run mock auto-incomplete
task auto-pass '- hello.txt' '$ test -s hello.txt'
expect 0 'automatic success' env AGENTTEAM_AUTO_VERIFY=1 "$QUALITY_AT" run mock auto-pass
task process-fail '- hello.txt' '$ true'
expect 7 'worker failure preserved' env MOCK_EXIT=7 AGENTTEAM_AUTO_VERIFY=1 "$QUALITY_AT" run mock process-fail
echo "quality regressions: $QUALITY_OK passed"
python3 "$QUALITY_REPO/tests/frugal-flock-quality-cases.py"
python3 "$QUALITY_REPO/tests/frugal-flock-quality-coverage.py"
