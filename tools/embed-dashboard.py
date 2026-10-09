#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Embed the managed dashboard helper as a byte-identical shell heredoc.

It installs separately from the canonical browser payload, as
$CONF_DIR/lib/dashboard.py, and runs with isolated Python imports.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'tools' / 'runtime' / 'dashboard.py'
DELIMITER = 'UNIO_DASHBOARD_PY'
BEGIN = '# BEGIN EMBEDDED DASHBOARD\n'
END = '# END EMBEDDED DASHBOARD\n'


def embedded_block():
    source = SOURCE.read_bytes().decode('utf-8')
    if not source.endswith('\n') or DELIMITER in source.splitlines() or '\r' in source:
        raise SystemExit('dashboard source must be UTF-8 LF text with a final newline')
    return (BEGIN + '''# Check the generated destination before replacing the dashboard helper.
if [ -L "$CONF_DIR/lib" ] || { [ -e "$CONF_DIR/lib" ] && [ ! -d "$CONF_DIR/lib" ]; }; then
  echo "unio: refusing unsafe dashboard directory: $CONF_DIR/lib" >&2
  exit 1
fi
dashboard_file="$CONF_DIR/lib/dashboard.py"
if [ -L "$dashboard_file" ] || { [ -e "$dashboard_file" ] && { [ ! -f "$dashboard_file" ] || [ "$(stat -c '%h' -- "$dashboard_file")" != 1 ]; }; }; then
  echo "unio: refusing unsafe dashboard file: $dashboard_file" >&2
  exit 1
fi
mkdir -p "$CONF_DIR/lib"
cat > "$dashboard_file" <<\'''' + DELIMITER + "'\n" + source + DELIMITER + '\n' + END)


def main():
    installer = ROOT / 'unio-install.sh'
    old = installer.read_text()
    block = embedded_block()
    if BEGIN in old:
        left, rest = old.split(BEGIN, 1)
        _, right = rest.split(END, 1)
        updated = left + block + right
    else:
        marker = '# END EMBEDDED CAPACITY\n'
        assert marker in old
        updated = old.replace(marker, marker + block, 1)
    if sys.argv[1:] == ['--check']:
        if old != updated:
            raise SystemExit('embedded dashboard differs; run python3 -B tools/embed-dashboard.py')
        print('embedded dashboard: helper byte-identical')
    elif not sys.argv[1:]:
        installer.write_text(updated)
    else:
        raise SystemExit('usage: embed-dashboard.py [--check]')


if __name__ == '__main__':
    main()
