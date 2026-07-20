#!/usr/bin/env bash
# check-docs.sh — catch Markdown that converts badly to Word/PDF.
#
#   ./tools/check-docs.sh                 # check every .md in docs/ and the root
#   ./tools/check-docs.sh docs/NEW.md     # check specific files
#
# Run it before converting a document, and after editing one. Exits nonzero
# if anything is wrong, so it can gate a commit.
#
# What it looks for (see docs/DOC-CONVENTIONS.md for the reasoning):
#   1. bare <placeholder> outside code — converters read it as an HTML tag
#      and SILENTLY DELETE it. This has bitten this repo for real.
#   2. unbalanced code fences — everything after them renders as code.
#   3. triple backticks inline in prose — can open a fence by accident.
#   4. unescaped pipes in table cells — split one column into two.
set -uo pipefail

files=("$@")
if [ ${#files[@]} -eq 0 ]; then
  mapfile -t files < <(ls docs/*.md ./*.md 2>/dev/null | grep -vE '(MASTER|WORKER|CLAUDE|AGENTS|GEMINI)\.md')
fi
[ ${#files[@]} -gt 0 ] || { echo "check-docs: no markdown files found"; exit 0; }

python3 - "${files[@]}" <<'PY'
import re, sys


def blank_code_spans(text):
    """Blank out `code spans` (which may wrap across lines) but keep every
    newline, so reported line numbers still match the file."""
    def repl(m):
        return "".join("\n" if ch == "\n" else " " for ch in m.group(0))
    return re.sub(r"`[^`]*`", repl, text)


problems = 0
for path in sys.argv[1:]:
    try:
        raw_text = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"{path}: cannot read ({e})"); problems += 1; continue

    lines = raw_text.split("\n")
    masked = blank_code_spans(raw_text).split("\n")

    infence = False
    found = []
    for n, raw in enumerate(lines, 1):
        if raw.lstrip().startswith("```"):
            infence = not infence
            continue
        if infence:
            continue

        prose = masked[n - 1]                        # code spans already blanked

        for m in re.finditer(r"<[A-Za-z][A-Za-z0-9_.-]*>", prose):
            found.append((n, f"bare {m.group(0)} outside backticks — a converter will delete it"))

        if "```" in prose:
            found.append((n, "triple backticks inside prose — may open a stray code fence"))

        if raw.lstrip().startswith("|"):
            cells = re.split(r"(?<!\\)\|", prose)    # pipes inside code spans are safe
            if any(c.count("|") for c in cells):
                found.append((n, "unescaped | inside a table cell — use \\|"))

    if infence:
        found.append((len(lines), "file ends inside an unclosed code fence"))

    if found:
        problems += len(found)
        print(f"\n{path}:")
        for n, msg in found:
            text = lines[n-1].strip()[:60] if n <= len(lines) else ""
            print(f"  line {n}: {msg}")
            if text:
                print(f"           | {text}")
    else:
        print(f"ok  {path}")

print()
if problems:
    print(f"check-docs: {problems} problem(s) found — see docs/DOC-CONVENTIONS.md")
    sys.exit(1)
print("check-docs: all clean")
PY
