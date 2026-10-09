#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Installed CLI entry: reuse server options with a fixed native engine."""
from pathlib import Path
import sys

if sys.version_info < (3, 9):
    raise SystemExit('unio browser: Python 3.9 or newer is required')

from server import main

if __name__ == '__main__':
    main(sys.argv[4:], engine_override=Path(sys.argv[1]),
         project_default=Path(sys.argv[2]) if sys.argv[2] else None,
         installed_version=sys.argv[3])
