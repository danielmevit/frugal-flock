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

# --selftest: prove the checks actually fire, on planted bugs (see the
# agentteam selftest philosophy — a checker nobody checks is worth little).
if [ "${1:-}" = "--selftest" ]; then
  t=$(mktemp -d); ok=0; fail=0
  probe() { # <name> <expect: bad|good> <content>
    printf '%b' "$3" > "$t/$1.md"
    "$0" "$t/$1.md" >/dev/null 2>&1; rc=$?
    if { [ "$2" = bad ] && [ $rc -ne 0 ]; } || { [ "$2" = good ] && [ $rc -eq 0 ]; }; then
      ok=$((ok+1)); printf '  ok    %s\n' "$1"
    else
      fail=$((fail+1)); printf '  FAIL  %s (expected %s, exit=%s)\n' "$1" "$2" "$rc"
    fi
  }
  probe bare-placeholder bad  '# T\n\nrejected because <reason>. Fix it.\n'
  probe stray-backtick   bad  '# T\n\nA stray ` tick.\n\nA bare <thing> here.\n\nAnd `code`.\n'
  probe unclosed-fence   bad  '# T\n\n```text\nunclosed\n'
  probe table-pipe       bad  '# T\n\n| a | b |\n|---|---|\n| x | 30m|5h |\n'
  probe inline-fence     bad  '# T\n\nFences (```) are code.\n'
  probe clean-doc        good '# T\n\nUse `wt/<w>` here.\n\n| a | b |\n|---|---|\n| `[30m\\|5h]` | y |\n'
  probe wrapped-span     good '# T\n\nRe-run `agentteam init\n<worker>` to refresh it.\n'
  rm -rf "$t"
  echo
  echo "check-docs selftest: $ok ok, $fail failed"
  [ "$fail" -eq 0 ] || exit 1
  exit 0
fi

files=("$@")
if [ ${#files[@]} -eq 0 ]; then
  mapfile -t files < <(
    for f in docs/*.md ./*.md; do
      [ -e "$f" ] || continue
      case "$(basename "$f")" in MASTER.md|WORKER.md|CLAUDE.md|AGENTS.md|GEMINI.md) continue;; esac
      printf '%s\n' "$f"
    done)
fi
[ ${#files[@]} -gt 0 ] || { echo "check-docs: no markdown files found"; exit 0; }

python3 - "${files[@]}" <<'PY'
import re, sys


def strip_fences(text):
    """Blank fenced code blocks, keeping line numbering intact."""
    out, infence, unclosed = [], False, False
    for ln in text.split("\n"):
        if ln.lstrip().startswith("```"):
            infence = not infence
            out.append("")
            continue
        out.append("" if infence else ln)
    return "\n".join(out), infence


def blank_code_spans(text):
    """Blank out `code spans` (which may wrap across lines) but keep every
    newline, so reported line numbers still match the file."""
    def repl(m):
        return "".join("\n" if ch == "\n" else " " for ch in m.group(0))
    return re.sub(r"`[^`]*`", repl, text)


def cells_of(row):
    """Split a table row on unescaped pipes, ignoring the outer borders."""
    r = row.strip()
    if r.startswith("|"):
        r = r[1:]
    if r.endswith("|") and not r.endswith("\\|"):
        r = r[:-1]
    return re.split(r"(?<!\\)\|", r)


problems = 0
for path in sys.argv[1:]:
    try:
        raw_text = open(path, encoding="utf-8").read()
    except OSError as e:
        print(f"{path}: cannot read ({e})"); problems += 1; continue

    lines = raw_text.split("\n")
    defenced, unclosed_fence = strip_fences(raw_text)
    found = []

    # A stray backtick makes every code span after it pair up wrongly, which
    # would hide real problems from the checks below — so catch it first.
    stray = defenced.count("`") % 2
    if stray:
        n = next((i for i, l in enumerate(defenced.split("\n"), 1) if "`" in l), 1)
        found.append((n, "odd number of backticks in this file — a code span is unclosed "
                         "(later checks are unreliable until this is fixed)"))

    masked = blank_code_spans(defenced).split("\n")

    infence = False
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

    # Tables: every row must have the same number of cells as its header.
    # A row with more cells means an unescaped | split one cell in two.
    n = 0
    while n < len(masked):
        if masked[n].lstrip().startswith("|"):
            start, block = n, []
            while n < len(masked) and masked[n].lstrip().startswith("|"):
                block.append(masked[n])
                n += 1
            width = len(cells_of(block[0]))
            for k, row in enumerate(block[1:], 1):
                got = len(cells_of(row))
                if got != width:
                    found.append((start + k + 1,
                                  f"table row has {got} cells but the header has {width} — "
                                  "an unescaped | splits a cell (write \\|)"))
            continue
        n += 1

    if unclosed_fence:
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
