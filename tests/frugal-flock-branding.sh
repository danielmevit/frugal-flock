#!/usr/bin/env bash
# Frugal Flock rename contract: entirely isolated, no providers or credentials.
set -euo pipefail
REPO_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
BRAND_SANDBOX=$(mktemp -d)
trap 'rm -rf "$BRAND_SANDBOX"' EXIT
fail() { echo "FAIL: $*" >&2; exit 1; }

export AGENTTEAM_BIN_DIR="$BRAND_SANDBOX/bin with spaces"
export AGENTTEAM_CONF_DIR="$BRAND_SANDBOX/conf with spaces"
export AGENTTEAM_COMPLETION_DIR="$BRAND_SANDBOX/completion with spaces"
FLOCK_PATH=$(command -v flock)
FLOCK_HASH=$(sha256sum "$FLOCK_PATH")
FLOCK_INODE=$(stat -Lc '%d:%i' "$FLOCK_PATH")

# Old automation installs the same product. Simulate existing user configuration
# and state before reinstalling through each entrypoint, from a different cwd.
bash "$REPO_DIR/agentteam-install.sh" > "$BRAND_SANDBOX/install.log"
printf '# existing user config\nmock=bash -c "exit 0"\n' > "$AGENTTEAM_CONF_DIR/agents.conf"
cp "$AGENTTEAM_CONF_DIR/agents.conf" "$BRAND_SANDBOX/expected.conf"
mkdir -p "$AGENTTEAM_CONF_DIR/off" "$AGENTTEAM_CONF_DIR/playbooks"
printf 'keep quota state\n' > "$AGENTTEAM_CONF_DIR/off/existing"
printf 'keep playbooks\n' > "$AGENTTEAM_CONF_DIR/playbooks/existing.md"
for installer in frugal-flock-install.sh agentteam-install.sh; do
  (cd "$BRAND_SANDBOX" && bash "$REPO_DIR/$installer") > "$BRAND_SANDBOX/install.log"
  grep -Fq 'Frugal Flock installed. Small plans. Big ideas.' "$BRAND_SANDBOX/install.log"
  cmp "$BRAND_SANDBOX/expected.conf" "$AGENTTEAM_CONF_DIR/agents.conf"
  grep -Fxq 'keep quota state' "$AGENTTEAM_CONF_DIR/off/existing"
  grep -Fxq 'keep playbooks' "$AGENTTEAM_CONF_DIR/playbooks/existing.md"
done
export PATH="$AGENTTEAM_BIN_DIR:$PATH"
frugal-flock help > "$BRAND_SANDBOX/help"
grep -Fq 'Frugal Flock — Small plans. Big ideas.' "$BRAND_SANDBOX/help"
for entry in frugal-flock frgl-flc agentteam; do
  [ -x "$AGENTTEAM_BIN_DIR/$entry" ] || fail "$entry is not executable"
  [ "$AGENTTEAM_BIN_DIR/$entry" -ef "$AGENTTEAM_BIN_DIR/agentteam" ] \
    || fail "$entry does not point to the shared implementation"
  "$entry" help > "$BRAND_SANDBOX/entry-help"
  cmp "$BRAND_SANDBOX/help" "$BRAND_SANDBOX/entry-help"
  "$entry" version > "$BRAND_SANDBOX/version"
  grep -q '^Frugal Flock ' "$BRAND_SANDBOX/version"
  grep -Fxq 'Small plans. Big ideas.' "$BRAND_SANDBOX/version"
  grep -Fxq "config: $AGENTTEAM_CONF_DIR/agents.conf" "$BRAND_SANDBOX/version"
  rc=0
  "$entry" invalid-branding-command > "$BRAND_SANDBOX/error" 2>&1 || rc=$?
  [ "$rc" -eq 1 ] || fail "$entry lost invalid-command status ($rc)"
  grep -Fq "unknown command 'invalid-branding-command'" "$BRAND_SANDBOX/error"

  # A real state operation through every name respects the legacy override.
  "$entry" off mock >/dev/null
  [ -f "$AGENTTEAM_CONF_DIR/off/mock" ] || fail "$entry ignored config override"
  agentteam on mock >/dev/null
  [ ! -f "$AGENTTEAM_CONF_DIR/off/mock" ] || fail "aliases do not share state"

  [ -f "$AGENTTEAM_COMPLETION_DIR/$entry" ] || fail "$entry completion missing"
  # Start fresh for each completion file to also exercise lazy loading by name.
  bash -euo pipefail -s -- "$entry" <<'COMPLETION_TEST'
entry=$1
source "$AGENTTEAM_COMPLETION_DIR/$entry"
registration=$(complete -p "$entry")
function_name=${registration#* -F }
function_name=${function_name%% *}
declare -F "$function_name" >/dev/null
COMP_WORDS=("$entry" '') COMP_CWORD=1
"$function_name"
[ "${#COMPREPLY[@]}" -gt 20 ]
for candidate in "${COMPREPLY[@]}"; do
  # Each offered command must occur in the installed dispatch table.
  grep -Eq "^  ${candidate}(\)|\|)" "$AGENTTEAM_BIN_DIR/agentteam"
done
COMP_WORDS=("$entry" ver) COMP_CWORD=1
"$function_name"
[ "${COMPREPLY[*]}" = 'verify version' ]
COMPLETION_TEST
done

cmp "$REPO_DIR/docs/PROTOCOL.md" "$AGENTTEAM_CONF_DIR/templates/PROTOCOL.md"
[ ! -e "$AGENTTEAM_BIN_DIR/flock" ] && [ ! -L "$AGENTTEAM_BIN_DIR/flock" ]
[ "$(command -v flock)" = "$FLOCK_PATH" ] || fail 'Linux flock was shadowed'
[ "$(sha256sum "$FLOCK_PATH")" = "$FLOCK_HASH" ] || fail 'Linux flock was modified'
[ "$(stat -Lc '%d:%i' "$FLOCK_PATH")" = "$FLOCK_INODE" ] || fail 'Linux flock was replaced'
flock -n "$BRAND_SANDBOX/lock" true

# The canonical installer must propagate failures from the shared installer.
: > "$BRAND_SANDBOX/not-a-directory"
for installer in agentteam-install.sh frugal-flock-install.sh; do
  rc=0
  AGENTTEAM_BIN_DIR="$BRAND_SANDBOX/not-a-directory/bin" \
    bash "$REPO_DIR/$installer" > "$BRAND_SANDBOX/install-error" 2>&1 || rc=$?
  [ "$rc" -eq 1 ] || fail "$installer lost installation failure status ($rc)"
done
echo 'PASS: branding, three shared entrypoints, status propagation, completion, reinstall, protocol and Linux flock'
