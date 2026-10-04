#!/usr/bin/env bash
# Frugal Flock — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/frugal-flock
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
# Repeatable checks; no installed user configuration or live providers.
set -euo pipefail
QUALITY_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
QUALITY_CHECK_DIR=$(mktemp -d)
trap 'rm -rf -- "$QUALITY_CHECK_DIR"' EXIT
cd "$QUALITY_REPO"
export AGENTTEAM_AUTO_VERIFY=0 AGENTTEAM_AUTO_OFF=0 AGENTTEAM_AUTO_SYNC=0
for dependency in python3 shellcheck; do
  command -v "$dependency" >/dev/null || { echo "missing dependency: $dependency" >&2; exit 1; }
done
bash -n agentteam-install.sh
bash -n frugal-flock-install.sh
AGENTTEAM_BIN_DIR="$QUALITY_CHECK_DIR/bin" AGENTTEAM_CONF_DIR="$QUALITY_CHECK_DIR/conf" \
  AGENTTEAM_COMPLETION_DIR="$QUALITY_CHECK_DIR/completion" bash frugal-flock-install.sh > "$QUALITY_CHECK_DIR/install.log"
shellcheck -S warning "$QUALITY_CHECK_DIR/bin/agentteam"
AGENTTEAM_CONF_DIR="$QUALITY_CHECK_DIR/conf" "$QUALITY_CHECK_DIR/bin/frugal-flock" selftest
bash tests/frugal-flock-quality.sh
python3 tests/frugal-flock-loop-brake.py
python3 tests/frugal-flock-watch.py
python3 tests/frugal-flock-opencode.py
bash tests/agentteam-probes.sh
bash tests/frugal-flock-branding.sh
bash tools/check-docs.sh
echo 'quality-check: all checks passed'
