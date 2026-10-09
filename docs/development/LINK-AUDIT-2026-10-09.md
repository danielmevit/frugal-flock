# Local Documentation Link Audit — 2026-10-09

Routine inventory of inline relative Markdown links at frozen main `43332bb55677302fa854ee230c1dec58db746049`.

## Method

- Ran the frozen local inline-link checker once; its command, source and raw JSON are retained in private coordination evidence.
- Ran `bash tools/check-docs.sh` once: **all clean** (68 files ok).

## Counts

| Metric | Value |
| --- | --- |
| Inline relative links checked (outside code) | 405 |
| Skipped by checker scope | 125 |
| Missing targets | 0 |
| Distinct source files | 63 |

All 405 checked targets exist. No missing source/target pairs to report as follow-up.

## Scope limitation

The checker deliberately covers **inline relative targets outside code only**. External/GitHub URLs, in-page anchors, reference-style links, and HTML links are not validated; this report makes no claim that they resolve.

## Active and historical material

The scan covers current guides and dated evidence. Current examples include
`README.md`, `docs/SETUP.md`, `docs/WORK-MODES.md`, the development roadmap,
backlog and model scoreboard. Historical examples include dated session
handoffs, dated findings and `docs/RELEASE-0.5.3.md` through
`docs/RELEASE-0.5.5.md`. A successful target-existence check says nothing about
whether a document's claims are current; this audit does not classify every
tracked guide or validate its content.

## Result

No broken inline relative links found at this commit. No file fixes made; this is an inventory report only.
