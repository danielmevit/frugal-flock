# Copy this prompt to continue with another AI

Open the repo in your new AI session and paste the Prompt to paste below.
Read the local agent log first; this file gives the current checkpoint.
Earlier checkpoint notes remain in Git history and the append-only local log.

Living checkpoint, updated 2026-10-05 10:50 +0200 by Claude Code lead
(claude-opus-5-5), wt/claude-lead on agent/claude-lead, main 9d9f12c.
The lead stopped early because its usage limit was close.

## Current checkpoint

- **The project is being renamed to Unio.** Owner decisions and approved
  lead proposals are frozen in [docs/RENAME-UNIO.md](docs/RENAME-UNIO.md)
  (on main). GitHub repo already renamed: github.com/danielmevit/unio (old
  URL redirects). Only the `unio` command (no old aliases); NOTICE names just
  Unio; tagline stays until a new one is chosen; the local workspace folder
  stays `_vm/frugal-flock`. Owner still to do: register unio.io, trademark
  search for UNIO.
- **LIMIT-WALL is merged (89202b4)** after its full quality gate passed. Five-model race through `frugal-flock race`
  (GLM 5.3 high, Kimi K3 default, Qwen 3.8 Max xhigh, MiniMax M3 thinking,
  DeepSeek V4 Pro high): all exit 0, verify 5/5, every test fails on old code.
  Winner GLM, branch agent/glm-race @ 81c1bfc: lead APPROVE and Codex
  (gpt-6.1-sol xhigh) native review APPROVE. The full quality gate was still
  running at handoff: read the end of
  tmp/race-limit-wall/receipts/quality-check-glm.log (needs "quality-check:
  all checks passed"). Losing race branches are kept, not merged. Details:
  tmp/race-limit-wall/manifest.json and receipts/.
- **Rename slice A task is written:** coord/tasks/RENAME-A.md (race Codex
  gpt-6.1-sol xhigh vs GLM 5.3 high, 2400s). Slices B (README and top-level
  files), C (current docs/ guides; keep dated history such as
  SESSION-HANDOFF-*, M1-*, M1.5-*, QUALITY-M1-CONTRACT, research/,
  changelog.d and past CHANGELOG entries) and D (examples/, bridge/,
  prototype/) still need task files. Plan: A merges first; B, C, D can run
  in parallel because the contract fixes every new name.
- README now has a collapsible FAQ and SETUP section 9 explains lead AI
  permissions. STOP is set; no worker is running.

Owner directions: use all AIs (Codex Sol 6.1 xhigh, OpenCode GLM 5.3 high
plus Kimi K3/Qwen 3.8 Max/DeepSeek V4 Pro/MiniMax M3, Grok high, Antigravity
Gemini 3.1 Pro high) with cross-company reviews; one invocation per task or
review, stated timeout, no automatic retries, every spend logged. Use GLM at
high, not max (max thinks ~2.5x longer for no better result); GLM 5.3 Flash
was unreliable. DeepSeek needs the OpenCode workspace set to Global regions
(done). Owner pushes are authorized; review everything before merging.

## Prompt to paste

```text
Continue Unio (formerly Frugal Flock) in /mnt/d/Vibe Coding/_vm/frugal-flock/repo.
You are the lead. Read ../coord/AGENT-LOG.md FIRST (newest entries), then
continue-with-ai-prompt.md, docs/RENAME-UNIO.md, WORKSPACE-RULES.md and
docs/DOGFOOD-WORKFLOW.md. Work in your own lead worktree ../wt/claude-lead
(branch agent/claude-lead); never redo or overwrite other branches.

Next steps, in order:
1. Read docs/FINDINGS-2026-10-05.md (what the model tests proved).
2. Start the Unio rename through the flock per docs/RENAME-UNIO.md: write
   task files for slices B, C and D (see continue-with-ai-prompt.md for
   scopes), then run slice A (coord/tasks/RENAME-A.md) as a race of Codex
   gpt-6.1-sol xhigh vs GLM 5.3 high, and B/C/D on other vendors, each
   reviewed by a different company and by you. Reuse the pattern in
   ../tmp/race-limit-wall (per-run conf dir with pinned model wrappers,
   review adapter, receipts). Create worker worktrees from main with a
   .agentteam-worker marker so the git guards apply.
3. Merge A first, then B/C/D, full quality gate after each, then check no
   current file still says Frugal Flock or the old commands.

Rules: frugal-flock stop/resume around runs; one invocation per task, no
retries; use `date` for log timestamps; quote paths (they contain spaces);
never `pgrep -f` or `pkill -f` a pattern that appears in your own command.
Ask the owner before installing Unio globally or releasing. After every
checkpoint prepend a dated entry to ../coord/AGENT-LOG.md and update this file.
```

## Checkpoint discipline

Use current main and actual local branch/receipts, not an old NEXT instruction.
Update this file and the local log whenever branch, verification, blocker,
active worker or next task changes. Preserve previous failures and distinguish
process exit, validation, review, human acceptance and integration.
Historical detail is in the dated handoffs and Git history.
