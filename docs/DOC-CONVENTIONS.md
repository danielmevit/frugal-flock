# Writing docs in this repo

Rules for every Markdown file here. They exist because these documents get
converted to Word and PDF, and a converter is not a Markdown reader: it
throws away anything that looks like markup it recognizes. Each rule below
comes from something that actually broke.

Check any document before converting or committing it:

```text
./tools/check-docs.sh                 # every doc in the repo
./tools/check-docs.sh docs/NEW.md     # just one
./tools/check-docs.sh --selftest      # prove the checker still catches bugs
```

It exits nonzero when something is wrong, so it can gate a commit. The
`--selftest` run plants each kind of bug in a throwaway file and confirms
it is caught — worth running after editing the checker itself, because a
lint that silently stops catching things is worse than no lint at all.

---

## Rule 1 — never leave a bare `<placeholder>` outside backticks

**This is the important one.** Text like `<task>`, `<worker>`, `<reason>`
or `<project>` looks like an HTML tag. Markdown allows inline HTML, so
every converter — pandoc included — treats it as a tag, and since no such
tag exists, it **silently deletes it**. No warning, no error: the word
just vanishes from the Word file.

It happened in this repo. GUIDEBOOK chapter 7.9 read:

```text
Then tell the foreman: "T7 rejected because <reason>. Write a sharper T7b."
```

and the generated Word document read:

```text
Then tell the foreman: "T7 rejected because . Write a sharper T7b."
```

Write it in backticks instead — always:

```text
wrong:   commit it yourself in wt/<w>
right:   commit it yourself in `wt/<w>`

wrong:   You're taking over **<project>**
right:   You're taking over **`<project>`**
```

Inside fenced code blocks nothing is interpreted, so placeholders there
need no backticks. The rule is only about prose, table cells, headings,
and list items.

One deliberate exception: `<details>` and `<summary>`, the tags behind
GitHub's collapsible FAQ entries. The checker allows exactly these two,
and only in README.md, which is read on GitHub and never converted. In a
document converted to Word they stay flagged: a converter would delete the
question lines and leave the answers behind.

## Rule 2 — keep code fences balanced, and never write triple backticks in prose

An unclosed fence turns the entire rest of the document into a code block.
Writing the fence characters inline in a sentence can open one by accident;
say "triple backticks" in words instead, or use a code span.

## Rule 2b — never leave a single backtick unclosed

One stray backtick pairs with the next real one, so a stretch of prose
between them silently becomes "code" — in the Word file *and* in this
repo's own linter, which would then stop seeing bare placeholders inside
that stretch. The checker therefore reports any file with an odd number
of backticks before it reports anything else.

A code span that wraps across two lines is fine — Markdown joins the
lines with a space, and pandoc reproduces it correctly (several docs here
rely on it):

```text
Re-run `frugal-flock init
<worker>` to refresh that worker's card.
```

Just make sure it is closed.

## Rule 3 — escape pipes inside table cells

A `|` inside a table cell splits it into two columns. Write `\|`:

```text
| `frugal-flock off <agent> [30m\|5h\|7d]` | Bench an agent. |
```

Pipes inside code spans are safe, but escaping is harmless and clearer.
The checker catches this by comparing each row's cell count against the
header's, so a split cell shows up as "3 cells but the header has 2".

## Rule 4 — one heading level per structural level

`#` for the document title, `##` for chapters, `###` for sections. The
converter maps these to Word's Title / Heading 1 / Heading 2 styles and
builds the table of contents from them, so skipping a level produces a
broken TOC.

## Rule 5 — code blocks are exact

Everything inside a fence is reproduced verbatim in the Word file, with
spell-check disabled. Paste real terminal output rather than retyping it,
and never let an editor "fix" quotes or dashes inside a fence.

---

## Producing the Word file

```text
./tools/make-docx.sh                     # docs/GUIDEBOOK.md -> docs/GUIDEBOOK.docx
./tools/make-docx.sh docs/HANDBOOK.md    # any document
```

Close the file in Word first — the script refuses to overwrite an open
document. When you open the result, allow Word to update fields (or press
F9) so the table of contents fills in. GUIDEBOOK Appendix A has the full
detail, including a prompt for converting by AI instead.

## When PROTOCOL.md changes

`docs/PROTOCOL.md` is duplicated inside `agentteam-install.sh` as the
template that gets installed into every project's `coord/docs/`. The two
copies must stay byte-identical. After editing either one:

```text
bash frugal-flock-install.sh                                  # rewrite templates
cp ~/.config/agentteam/templates/PROTOCOL.md docs/PROTOCOL.md
diff ~/.config/agentteam/templates/PROTOCOL.md docs/PROTOCOL.md   # must be empty
```
