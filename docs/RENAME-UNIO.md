# Rename: Frugal Flock becomes Unio

Frozen contract for the rename, written by the lead (Claude Code,
claude-opus-5-5) on 2026-10-05. The owner approved the whole document,
including the lead proposals and the NOTICE draft, on 2026-10-05. Workers follow it
exactly; anything it does not cover goes back to the lead.

## Why Unio

*Unio* is Latin for oneness and union, from *unus*, "one". Classical Latin
also used it for a single, unique pearl. The tool unites AI coding tools
from different companies into one team; the name says that plainly.

## Owner decisions

| Topic | Decision |
|---|---|
| Name | Unio |
| Command | `unio` only. `frugal-flock`, `frgl-flc` and `agentteam` are removed, not kept as aliases. |
| Repository | github.com/danielmevit/unio (renamed 2026-10-05; the old URL redirects). |
| Legal NOTICE | Names only Unio (draft below, exact text needs owner approval). |
| Tagline | "Small plans. Big ideas." stays until a new Unio tagline is chosen. |
| Domain and trademark | unio.io registration and a trademark search for UNIO are the owner's. |

## Lead proposals (approved)

1. **Version.** The rename ships as Unio 0.5.0 (CHANGELOG entry and installer
   version).
2. **Environment variables.** `AGENTTEAM_*` become `UNIO_*` with the same
   suffixes (`UNIO_TIMEOUT`, `UNIO_CONF_DIR`, `UNIO_AUTO_OFF`, and so on).
   No old names are read; nobody else uses the tool.
3. **Config folder.** `~/.config/agentteam` becomes `~/.config/unio`. On
   install, if `~/.config/unio` does not exist and `~/.config/agentteam`
   does, the installer copies it across once and says so; the old folder is
   left in place untouched.
4. **Installer and old commands.** One installer, `unio-install.sh`.
   `agentteam-install.sh` and `frugal-flock-install.sh` are removed. The
   installer deletes `frugal-flock`, `frgl-flc` and `agentteam` from the bin
   folder only when they are Frugal Flock's own installed copies or links
   (checked by content), and reports what it removed.
5. **Project internals.** The worker marker `.agentteam-worker` becomes
   `.unio-worker`; Git guard hooks say "unio guard". `unio init` (and
   `unio doctor`) convert an existing project: rename markers, rewrite
   hooks, update `.git/info/exclude`. Project layout (`repo/`, `wt/`,
   `coord/`), task format, ledger fields and result schema do not change.
6. **File names.** `tests/frugal-flock-*` become `tests/unio-*`;
   `tests/agentteam-probes.sh` becomes `tests/unio-probes.sh`;
   `tools/quality-check.sh` lists the new names.
7. **History stays true.** Dated records keep the names they were written
   with: past CHANGELOG entries, `docs/SESSION-HANDOFF-*`, `docs/M1-*`,
   `research/`, the agent log, reports and receipts. Current documents say
   Unio, and README carries one line: "Unio was called Frugal Flock, and
   agentteam before that."
8. **Workspace folder.** The local workspace stays at
   `_vm/frugal-flock` for now; moving it breaks worktree links. Renaming it
   is a separate, later step. WORKSPACE-RULES says so.
9. **Installed tool.** The global install stays Frugal Flock 0.4.0 while the
   flock builds the rename (build with the installed release). Installing
   Unio 0.5.0 needs a fresh owner go; afterwards the owner's Claude Code
   allow rule changes from `Bash(frugal-flock *)` to `Bash(unio *)`.

## NOTICE change (approved)

Every "Frugal Flock" in NOTICE becomes "Unio", and the project URL becomes
`https://github.com/danielmevit/unio`. The first line reads
"Unio — Small plans. Big ideas." until a new tagline exists. The legal terms
themselves (AGPL-3.0-only, attribution and origin terms under sections 7(b)
and 7(c), the independent-projects clause) are unchanged. Source file
headers change the same way: "Unio — Copyright (C) 2026 Daniel Mitev".

## Execution through the flock

Each slice is one frozen task with its own scope, checks and changelog
fragment, run through the installed tool, reviewed by a different company's
AI and by the lead, then merged on its own. Slices run in this order:

| Slice | Scope | Depends on |
|---|---|---|
| A. Runtime and installer | `agentteam-install.sh` renamed to `unio-install.sh`, removed `frugal-flock-install.sh`, embedded templates, help, completion, hooks, markers, env and config migration, `docs/PROTOCOL.md` (byte-identical with its embedded copy), tests and `tools/quality-check.sh` | — |
| B. README and top-level files | `README.md`, `WORKSPACE-RULES.md`, `TODO.md`, `MASTER.md`, `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `continue-with-ai-prompt.md`, `NOTICE` (approved text) | A |
| C. Guides | Current documents in `docs/` (not the dated history), then regenerate the Word copies | A |
| D. Examples | `examples/` scripts and their references | A |

The full quality gate runs after each merge. When all four are in, the lead
checks that no current file still says Frugal Flock, `frugal-flock`,
`frgl-flc` or `agentteam` except where history requires it, and releases
Unio 0.5.0 only on the owner's go.
