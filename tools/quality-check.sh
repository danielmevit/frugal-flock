#!/usr/bin/env bash
# Unio — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/unio
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
# Repeatable checks; no installed user configuration or live providers.
set -euo pipefail
QUALITY_REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
QUALITY_CHECK_DIR=$(mktemp -d)
trap 'rm -rf -- "$QUALITY_CHECK_DIR"' EXIT
cd "$QUALITY_REPO"
export UNIO_AUTO_VERIFY=0 UNIO_AUTO_OFF=0 UNIO_AUTO_SYNC=0
for dependency in python3 shellcheck; do
  command -v "$dependency" >/dev/null || { echo "missing dependency: $dependency" >&2; exit 1; }
done
bash -n unio-install.sh
UNIO_BIN_DIR="$QUALITY_CHECK_DIR/bin" UNIO_CONF_DIR="$QUALITY_CHECK_DIR/conf" \
  UNIO_COMPLETION_DIR="$QUALITY_CHECK_DIR/completion" bash unio-install.sh > "$QUALITY_CHECK_DIR/install.log"
shellcheck -S warning "$QUALITY_CHECK_DIR/bin/unio"
UNIO_CONF_DIR="$QUALITY_CHECK_DIR/conf" "$QUALITY_CHECK_DIR/bin/unio" selftest
bash tests/unio-quality.sh
python3 tests/unio-loop-brake.py
python3 tests/unio-limit-wall.py
python3 tests/unio-watch.py
python3 tests/unio-opencode.py
python3 -B tests/unio-prompt-transport.py
python3 -B bridge/tests/server_test.py
python3 -B bridge/tests/plan_store_test.py
python3 -B bridge/tests/plan_api_test.py
python3 -B bridge/tests/job_store_test.py
python3 -B bridge/tests/execution_service_test.py
bash tests/unio-probes.sh
bash tests/unio-branding.sh
bash tools/check-docs.sh
echo 'quality-check: all checks passed'
