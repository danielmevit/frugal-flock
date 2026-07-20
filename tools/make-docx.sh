#!/usr/bin/env bash
# make-docx.sh — turn an agentteam Markdown document into a formatted .docx.
#
#   ./tools/make-docx.sh                      # docs/GUIDEBOOK.md -> docs/GUIDEBOOK.docx
#   ./tools/make-docx.sh docs/HANDBOOK.md     # any doc; output sits beside it
#
# Uses pandoc for the conversion (a clickable table of contents, real Word
# tables, syntax-highlighted code blocks), then applies the page setup that
# pandoc's default template leaves out: A4, 2 cm margins, and centered page
# numbers in the footer.
#
# Install pandoc if missing — no root required:
#   curl -fsSL -o /tmp/p.tgz https://github.com/jgm/pandoc/releases/download/3.10/pandoc-3.10-linux-amd64.tar.gz
#   tar xzf /tmp/p.tgz -C /tmp && install -m755 /tmp/pandoc-3.10/bin/pandoc ~/.local/bin/pandoc
# (Ubuntu with root: sudo apt install pandoc. On WSL, a Windows install at
#  ~/AppData/Local/Pandoc/pandoc.exe is picked up automatically.)
set -euo pipefail

SRC="${1:-docs/GUIDEBOOK.md}"
OUT="${2:-${SRC%.md}.docx}"
[ -f "$SRC" ] || { echo "make-docx: no such file: $SRC" >&2; exit 1; }

PANDOC=""
if command -v pandoc >/dev/null 2>&1; then
  PANDOC=pandoc
else
  for c in "$HOME/AppData/Local/Pandoc/pandoc.exe" \
           /mnt/c/Users/*/AppData/Local/Pandoc/pandoc.exe \
           "/mnt/c/Program Files/Pandoc/pandoc.exe"; do
    [ -x "$c" ] && { PANDOC="$c"; break; }
  done
fi
[ -n "$PANDOC" ] || { echo "make-docx: pandoc not found — see the install note in this script" >&2; exit 1; }

# A Word .docx cannot be written while Word holds it open.
lock="$(dirname "$OUT")/~\$$(basename "$OUT" | cut -c3-)"
[ -e "$lock" ] && { echo "make-docx: '$OUT' is open in Word — close it first" >&2; exit 1; }

"$PANDOC" "$SRC" -o "$OUT" \
  --toc --toc-depth=2 \
  --syntax-highlighting=tango \
  --wrap=preserve

# Page setup pandoc's default reference document does not provide.
python3 - "$OUT" <<'PY'
import sys
try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm
except ImportError:
    sys.exit(0)          # python-docx absent: the pandoc output is still fine

path = sys.argv[1]
doc = Document(path)
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)      # A4 portrait
for side in ("top", "bottom", "left", "right"):
    setattr(sec, f"{side}_margin", Cm(2))

p = sec.footer.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run()
for tag, attr, text in (
    ("w:fldChar", "begin", None),
    ("w:instrText", None, " PAGE "),
    ("w:fldChar", "separate", None),
    ("w:fldChar", "end", None),
):
    el = OxmlElement(tag)
    if attr:
        el.set(qn("w:fldCharType"), attr)
    if text is not None:
        el.set(qn("xml:space"), "preserve")
        el.text = text
    run._r.append(el)

doc.save(path)
PY

echo "wrote $OUT"
echo "note: open it in Word and allow 'update fields' (or press F9) to fill the table of contents."
