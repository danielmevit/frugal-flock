#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Embed the capacity stores and CLI as byte-identical shell heredocs.

The installed tree mirrors the source layout under $CONF_DIR/lib/capacity,
so the reviewed CLI finds bridge/capacity.py and bridge/provider_capacity.py
without PYTHONPATH.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
FILES = (('bridge', 'capacity.py', 'UNIO_CAPACITY_STORE_PY'),
         ('bridge', 'provider_capacity.py', 'UNIO_CAPACITY_PROVIDER_PY'),
         ('tools', 'capacity-readings.py', 'UNIO_CAPACITY_CLI_PY'))
BEGIN = '# BEGIN EMBEDDED CAPACITY\n'
END = '# END EMBEDDED CAPACITY\n'
DIRS = ('"$CONF_DIR/lib"', '"$CONF_DIR/lib/capacity"',
        '"$CONF_DIR/lib/capacity/bridge"', '"$CONF_DIR/lib/capacity/tools"')


def embedded_block():
    block = BEGIN + '# Check every generated destination before replacing any capacity file.\n'
    block += 'for capacity_dir in ' + ' '.join(DIRS) + '; do\n'
    block += '''  if [ -L "$capacity_dir" ] || { [ -e "$capacity_dir" ] && [ ! -d "$capacity_dir" ]; }; then
    echo "unio: refusing unsafe capacity directory: $capacity_dir" >&2
    exit 1
  fi
done
'''
    block += 'for capacity_name in ' + ' '.join(d + '/' + n for d, n, _ in FILES) + '; do\n'
    block += '''  capacity_file="$CONF_DIR/lib/capacity/$capacity_name"
  if [ -L "$capacity_file" ] || { [ -e "$capacity_file" ] && { [ ! -f "$capacity_file" ] || [ "$(stat -c '%h' -- "$capacity_file")" != 1 ]; }; }; then
    echo "unio: refusing unsafe capacity file: $capacity_file" >&2
    exit 1
  fi
done
mkdir -p "$CONF_DIR/lib/capacity/bridge" "$CONF_DIR/lib/capacity/tools"
'''
    for directory, name, delimiter in FILES:
        source = (ROOT / directory / name).read_bytes().decode('utf-8')
        if not source.endswith('\n') or delimiter in source.splitlines() or '\r' in source:
            raise SystemExit('capacity source must be UTF-8 LF text with a final newline: ' + name)
        block += 'cat > "$CONF_DIR/lib/capacity/' + directory + '/' + name + '" <<\'' + delimiter + "'\n"
        block += source + delimiter + '\n'
    return block + END


def main():
    installer = ROOT / 'unio-install.sh'
    old = installer.read_text()
    block = embedded_block()
    if BEGIN in old:
        left, rest = old.split(BEGIN, 1)
        _, right = rest.split(END, 1)
        updated = left + block + right
    else:
        marker = '# END EMBEDDED BROWSER\n'
        assert marker in old
        updated = old.replace(marker, marker + block, 1)
    if sys.argv[1:] == ['--check']:
        if old != updated:
            raise SystemExit('embedded capacity differs; run python3 -B tools/embed-capacity.py')
        print('embedded capacity: stores and CLI byte-identical')
    elif not sys.argv[1:]:
        installer.write_text(updated)
    else:
        raise SystemExit('usage: embed-capacity.py [--check]')


if __name__ == '__main__':
    main()
