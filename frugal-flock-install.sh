#!/usr/bin/env bash
# Frugal Flock — Small plans. Big ideas.
# Canonical installer entrypoint. Keep this beside agentteam-install.sh,
# which embeds the shared implementation for compatibility with old automation.
set -euo pipefail
INSTALLER_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec bash "$INSTALLER_DIR/agentteam-install.sh" "$@"
