#!/usr/bin/env python3
# Unio — Copyright (C) 2026 Daniel Mitev
# SPDX-License-Identifier: AGPL-3.0-only; additional terms in NOTICE.
"""Embed the optional subscription adapters as byte-identical shell heredocs.

The canonical adapters install under $CONF_DIR/lib/adapters, separately
from the browser/capacity/dashboard payloads. The installer copies the
exact reviewed bytes: it installs no external dependency and invokes no
model, provider or interpreter for them.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
ADAPTERS = (
    (ROOT / 'tools' / 'vibe-worker.py', 'UNIO_VIBE_WORKER_PY', 'vibe-worker.py'),
    (ROOT / 'tools' / 'perplexity-worker.py', 'UNIO_PERPLEXITY_WORKER_PY', 'perplexity-worker.py'),
    (ROOT / 'tools' / 'copilot-worker.py', 'UNIO_COPILOT_WORKER_PY', 'copilot-worker.py'),
)
BEGIN = '# BEGIN EMBEDDED ADAPTERS\n'
END = '# END EMBEDDED ADAPTERS\n'

PREFLIGHT = '''# Check every generated destination before replacing any adapter: all
# directories and all files are validated first, then all are written.
for adapters_dir in "$CONF_DIR/lib" "$CONF_DIR/lib/adapters"; do
  if [ -L "$adapters_dir" ] || { [ -e "$adapters_dir" ] && [ ! -d "$adapters_dir" ]; }; then
    echo "unio: refusing unsafe adapter directory: $adapters_dir" >&2
    exit 1
  fi
done
for adapters_file in "$CONF_DIR/lib/adapters/vibe-worker.py" "$CONF_DIR/lib/adapters/perplexity-worker.py" "$CONF_DIR/lib/adapters/copilot-worker.py"; do
  if [ -L "$adapters_file" ] || { [ -e "$adapters_file" ] && { [ ! -f "$adapters_file" ] || [ "$(stat -c '%h' -- "$adapters_file")" != 1 ]; }; }; then
    echo "unio: refusing unsafe adapter file: $adapters_file" >&2
    exit 1
  fi
done
mkdir -p "$CONF_DIR/lib/adapters"
'''


def embedded_block():
    parts = [BEGIN, PREFLIGHT]
    for source, delimiter, name in ADAPTERS:
        text = source.read_bytes().decode('utf-8')
        if not text.endswith('\n') or delimiter in text.splitlines() or '\r' in text:
            raise SystemExit(name + ' must be UTF-8 LF text with a final newline')
        head = 'cat > "$CONF_DIR/lib/adapters/' + name + "\" <<'" + delimiter + "'\n"
        parts.append(head + text + delimiter + '\n')
    guide = (ROOT / 'docs' / 'development' / 'AGENT-FLEET.md').read_text()
    delimiter = 'UNIO_AGENT_FLEET_MD'
    if not guide.endswith('\n') or delimiter in guide.splitlines():
        raise SystemExit('fleet guide must end in a newline and not contain its delimiter')
    # Existing operator guide stays intact, including symlinks: no following or replacement.
    parts.append('if [ ! -e "$TPL_DIR/AGENT-FLEET.md" ] && [ ! -L "$TPL_DIR/AGENT-FLEET.md" ]; then\n'
                 + 'cat > "$TPL_DIR/AGENT-FLEET.md" <<\'' + delimiter + "'\n"
                 + guide + delimiter + '\nfi\n')
    parts.append(END)
    return ''.join(parts)


def main():
    installer = ROOT / 'unio-install.sh'
    old = installer.read_text()
    block = embedded_block()
    if BEGIN in old:
        left, rest = old.split(BEGIN, 1)
        _, right = rest.split(END, 1)
        updated = left + block + right
    else:
        marker = '# END EMBEDDED DASHBOARD\n'
        assert marker in old
        updated = old.replace(marker, marker + block, 1)
    if sys.argv[1:] == ['--check']:
        if old != updated:
            raise SystemExit('embedded adapters differ; run python3 -B tools/embed-adapters.py')
        print('embedded adapters: all helpers byte-identical')
    elif not sys.argv[1:]:
        installer.write_text(updated)
    else:
        raise SystemExit('usage: embed-adapters.py [--check]')


if __name__ == '__main__':
    main()
