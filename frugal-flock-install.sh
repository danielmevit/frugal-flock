#!/usr/bin/env bash
# Frugal Flock — Copyright (C) 2026 Daniel Mitev
# Public attribution: Daniel Mevit (@danielmevit)
# Original project: https://github.com/danielmevit/frugal-flock
# SPDX-License-Identifier: AGPL-3.0-only
# Additional attribution/origin terms: NOTICE (AGPLv3 sections 7(b), 7(c)).
# See LICENSE and NOTICE; distributed without warranty.
# Frugal Flock — Small plans. Big ideas.
# Canonical installer entrypoint. Keep this beside agentteam-install.sh,
# which embeds the shared implementation for compatibility with old automation.
set -euo pipefail
INSTALLER_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec bash "$INSTALLER_DIR/agentteam-install.sh" "$@"
