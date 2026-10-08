#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only
"""Keep the standalone installer byte-identical to the canonical helper."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
installer = ROOT / 'unio-install.sh'
begin = '# BEGIN EMBEDDED LEAD COOLDOWN\n'
end = '# END EMBEDDED LEAD COOLDOWN\n'
source = (ROOT / 'tools/runtime/lead_cooldown.py').read_text()
block = (begin + 'mkdir -p "$CONF_DIR/lib"\n'
         'cat > "$CONF_DIR/lib/lead_cooldown.py" <<\'LEAD_COOLDOWN_PY\'\n'
         + source + 'LEAD_COOLDOWN_PY\n' + end)
old = installer.read_text()
if begin in old:
    left, rest = old.split(begin, 1)
    _, right = rest.split(end, 1)
    updated = left + block + right
else:
    marker = '# ------------------------------------------------------------- agents.conf\n'
    assert marker in old
    updated = old.replace(marker, block + marker, 1)
if sys.argv[1:] == ['--check']:
    if old != updated:
        raise SystemExit('embedded lead cooldown differs; run tools/embed-lead-cooldown.py')
    print('embedded lead cooldown: byte-identical')
elif not sys.argv[1:]:
    installer.write_text(updated)
else:
    raise SystemExit('usage: embed-lead-cooldown.py [--check]')
