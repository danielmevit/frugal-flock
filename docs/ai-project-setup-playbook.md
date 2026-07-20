# AI Project Setup Playbook

A reusable standard for every project: how to structure the AI-memory `.md` files and
wire up CodeGraph. Point any agent (Claude, Codex, opencode, antigravity) at this file
when starting or onboarding a project.

> **Core philosophy — two layers, no overlap:**
> - **CodeGraph owns _structure_** (where things are, symbols, call paths, blast radius).
>   Machine-generated, refreshed automatically or on demand — never hand-maintained.
> - **`docs/ai/` owns _intent_** (why it's built this way, how to work in it, the traps).
>   Human/agent-curated, because a tool can't infer it.
>
> Never hand-maintain a file map in Markdown — that's CodeGraph's job, and it drifts.

---

## 0. New-project bootstrap (checklist)

```
[ ] 1. Create AGENTS.md (router)              → §2, §3
[ ] 2. Create docs/ai/ core files             → §2, §4
[ ] 3. Add .codegraph/ to .gitignore
[ ] 4. codegraph init   (build the index)     → §5
[ ] 5. (optional) codegraph.json to exclude dead/generated dirs → §5
[ ] 6. git config core.filemode false   (only on WSL /mnt drives) → §6
[ ] 7. First CHANGELOG entry + commit
```
One-liner for an agent: *"Set up this project per `_refs/ai-project-setup-playbook.md`."*

---

## 1. Folder structure

```
<project>/
  AGENTS.md            ← router: rules + map + CodeGraph pointer (KEEP SHORT)
  README.md            ← human overview (optional)
  CHANGELOG.md         ← what shipped, timestamped (the session log)
  ROADMAP.md           ← priorities / plan (optional)
  TODO.md              ← manual tasks / next steps (optional)
  SOUL.md              ← agent identity & standards (optional)
  codegraph.json       ← CodeGraph excludes (optional)
  .gitignore           ← must include .codegraph/
  docs/ai/
    START_HERE.md      ← orientation, current priority, how to run
    DESIGN_SYSTEM.md   ← (UI projects) tokens, layout laws, theming
    CONTENT_MODEL.md   ← (data-driven projects) data schemas, media conventions
    DECISIONS.md       ← durable "why" choices (NOT the changelog)
    GOTCHAS.md         ← operational traps: build, run, deploy, known bugs
  .codegraph/          ← CodeGraph index (GITIGNORED — local, per-machine)
```

### What each file owns

| File | Owns | Rule |
|------|------|------|
| `AGENTS.md` | Operating rules + a map to everything else | Keep it a router. No deep detail. |
| `docs/ai/START_HERE.md` | First read: purpose, current task, run commands, nav | The single entry point. |
| `docs/ai/DESIGN_SYSTEM.md` | Design tokens, layout rules, theming, CSS gotchas | UI projects only. |
| `docs/ai/CONTENT_MODEL.md` | Data schemas, content shapes, asset/media conventions | Data-driven projects only. |
| `docs/ai/DECISIONS.md` | *Why* X over Y — reasoning that shouldn't be re-litigated | Never duplicate the changelog. |
| `docs/ai/GOTCHAS.md` | Traps: build/run/deploy quirks, env issues, known bugs | Saves the most time. |
| `CHANGELOG.md` | *What* shipped, dated | The session log. Don't make a second one. |
| `ROADMAP.md` / `TODO.md` | Priorities & manual tasks | Point START_HERE at these. |

### Match the file set to the project

- **Small / content site** → `START_HERE` + `DESIGN_SYSTEM` + `CONTENT_MODEL` + `DECISIONS` + `GOTCHAS`.
- **Systems / app (large, stateful)** → add a real `DECISIONS`, a `GLOSSARY.md` (domain terms),
  and an interop/architecture note. Skip `CONTENT_MODEL`.
- **Algorithm / library** → add an `ALGORITHM_INDEX.md` (name → family → params → line anchor),
  a `GLOSSARY.md`, and a short pipeline note. This is the highest-value file for that shape.

> Rule: a memory file is only worth having if it's kept current. Stale docs are worse than none.
> Don't create empty "Needs confirmation" scaffolding — write a file only when it has real content.

---

## 2. `AGENTS.md` template (the router)

```md
# Agent rules — <project>

## Reading ritual (start of every session)
1. SOUL.md (if present) — identity & standards
2. AGENTS.md — this file
3. docs/ai/START_HERE.md — orientation; follow its links as the task needs

## Navigation — find code without crawling files
- Structure / "where is X?", callers, call paths → CodeGraph (`codegraph_explore` or
  `codegraph explore "..."`). Trust it; don't grep-loop.
- Intent / why / gotchas → the right file in docs/ai/ (map below).
- Do NOT hand-maintain a file map — CodeGraph owns structure.
- After editing code, run `codegraph sync` if the index doesn't auto-refresh here (see GOTCHAS).

## docs/ai/ map
| File | Owns |
|------|------|
| START_HERE.md | Orientation, current priority, how to run |
| DESIGN_SYSTEM.md | Design tokens, layout, theming |
| CONTENT_MODEL.md | Data schemas, media conventions |
| DECISIONS.md | Durable "why" choices |
| GOTCHAS.md | Build/run/deploy traps, known bugs |

## Workflow
- Plan → implement → run → summarize in one go. Milestone-sized steps.
- Each change: verify (build) + a CHANGELOG.md entry.

## Commit & push
- <your commit format + co-author line>
- <push command for this environment>

## Documentation upkeep
- CHANGELOG.md = what shipped (the session log; don't make a second one).
- Update DECISIONS.md on a durable choice; CONTENT_MODEL.md on a schema change.
- Keep START_HERE's "current priority" in sync with ROADMAP/TODO.
```

---

## 3. CodeGraph — the setup model

CodeGraph is **three independent, one-time layers**. None are per-session.

| Layer | Scope | Command |
|-------|-------|---------|
| 1. CLI (the binary) | Once per **machine/OS** | install (see below) |
| 2. Agent wiring (MCP) | Once per **agent** | `codegraph install -t <agent>` |
| 3. Project index | Once per **project** | `codegraph init` |

Key facts:
- The **index (`.codegraph/`) is shared** — it's a file in the project. All agents on that
  machine query the same one. Paths are repo-relative, so it's portable across environments.
- Wiring is **per environment**: WSL configs and Windows configs are separate. A native
  Windows app won't see a CLI/wiring you did in WSL, and vice-versa. Do each environment once.

### Install the CLI

```bash
# macOS / Linux / WSL
curl -fsSL https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.sh | sh
# or: npm i -g @colbymchenry/codegraph
```
```powershell
# Windows (PowerShell) — then restart the terminal so PATH updates
irm https://raw.githubusercontent.com/colbymchenry/codegraph/main/install.ps1 | iex
```

### Wire agents (once per agent, per environment)

```
codegraph install -t all            # wire every detected supported agent
codegraph install -t codex,opencode # wire specific ones
```
Supported target ids: `claude, cursor, codex, opencode, hermes, gemini, antigravity, kiro`.
(**Not supported:** Grok — use the shell `codegraph explore "..."` from it instead.)
➡️ **Restart the agent** afterwards so it loads the MCP server.

### Index a project (once per project)

```
cd <project>
codegraph init          # builds .codegraph/
codegraph index         # full rebuild from scratch (use after changing codegraph.json)
codegraph status        # show freshness / stats
codegraph explore "..." # query from the shell (works in any terminal/agent)
```

### `.gitignore` and `codegraph.json`

- **Always gitignore `.codegraph/`** — it's a local, per-machine build artifact.
- Optional `codegraph.json` (committed) to exclude dead/generated dirs from the graph:
  ```json
  { "exclude": ["**/_archive/**", "**/vendor/**"] }
  ```
  (`node_modules`, `dist`, `.venv`, gitignored files, and >1 MB files are auto-excluded.)
- Privacy: `codegraph telemetry off` (or `CODEGRAPH_TELEMETRY=0`) — per machine.

### Keeping the index fresh

- **Native paths (Mac / Windows / Linux-native):** live file-watching works → auto-sync.
- **WSL accessing a Windows drive (`/mnt/...`):** live-watching is unreliable → **run
  `codegraph sync` after edits** (make it a rule in GOTCHAS.md, like restarting a dev server).
- Git-hook option exists but skip it if you commit from a different OS than the CLI is on.

---

## 4. Environment gotchas (WSL vs native)

Docs written for a WSL setup often don't apply when you switch to a native OS. Watch for:

| Concern | WSL on `/mnt` (Windows drive) | Native (Windows/Mac/Linux) |
|---------|-------------------------------|----------------------------|
| CodeGraph auto-sync | ❌ manual `codegraph sync` | ✅ auto |
| Dev-server HMR | often broken → restart after edits | usually works |
| Git push creds | may need `cmd.exe /c "git push"` | plain `git push` |
| Phantom file-mode diffs | `git config core.filemode false` | not needed |

When you move a project between environments, update `docs/ai/GOTCHAS.md` to match.

---

## 5. Commit hygiene

- Stage **only your own changes** — don't sweep in pre-existing CRLF/line-ending or file-mode
  churn (`git add <specific paths>`, not blind `git add -A`).
- Every meaningful change gets a `CHANGELOG.md` entry.
- Keep the working tree clean before handing off.

---

## 6. Handoff / kickoff prompt (fill in the blanks)

> You're taking over **`<project>`** at `<path>`. Everything you need is in the repo.
> **Onboard:** read `AGENTS.md`, then `docs/ai/START_HERE.md` and follow its links; recent
> work is in `CHANGELOG.md`, your task is in `TODO.md`. **Find code** with CodeGraph
> (`codegraph_explore` / `codegraph explore "..."`) instead of grepping — run `codegraph sync`
> after edits if the index doesn't auto-refresh here. **Run:** `<run command>`.
> Work in steps: plan → implement → run → update `CHANGELOG.md` → summarize.

---

*This playbook supersedes the earlier `ai-project-memory-setup.md`. Keep it in `_refs/` and
update it as the standard evolves.*
