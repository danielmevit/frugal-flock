# Copy this prompt to continue with another AI

Open the repo in your new AI session and paste the Prompt to paste below.
Read the local agent log first; this file gives the current checkpoint.
Earlier checkpoint notes remain in Git history and the append-only local log.

Living checkpoint, updated 2026-10-05 11:51 +0200 by Codex lead
(GPT-6; exact serving variant not exposed). Frozen rename base: 181f13e.
Follow the newest local log and receipts when they supersede this snapshot.

## Current checkpoint

- Source rename tasks A/B/C/D are prepared and dispatched through native
  Frugal Flock with pinned models, timeouts and zero automatic retries.
- A Codex candidate passed 8/8 task checks; GLM's race invocation hit the
  Go cap and was interrupted without source changes. Grok requested two
  changes; the distinct Codex RENAME-A-FIX task is active.
- B Gemini replacement c11935d passed 3/3 checks; independent Codex review
  is active. Lead docs polish corrects a missed alias and current handoff.
- C Google candidate plus explicit lead docs corrections is 4eab8fc.
  Codex's six blocking documentation findings are preserved. A new complete,
  SHA-bound Grok review of the corrected candidate is active.
- D original Kimi run hit the Go cap without edits; the explicitly approved
  Grok replacement is active. The original DeepSeek B failure also remains.
- Merge A, then B, then C, then D. Run the full quality gate after each
  merge and push each only after its gate passes. No rename slice is merged
  at this snapshot; check the newest log for later integration.
- Read [provider capacity](docs/PROVIDER-CAPACITY.md) before assigning models:
  screenshot usage, current documented limits and historical reset estimate
  are preserved there. Actual account meters govern new scheduling.
- The workspace remains the legacy path `_vm/frugal-flock`. Installed build
  tool: Frugal Flock 0.4.0. Source target: Unio 0.5.0, unreleased. No global
  Unio install or release has been authorized.

The owner authorizes available AIs for Unio and milestone tasks, including
cross-company reviews, integration and pushes; do not ask again for ordinary
assignments. Keep every task bounded, preserve rejected/failed receipts and
use GLM high. Global installation, release or new billing changes still
require owner approval. Receipts: `../tmp/rename-unio/receipts/`; task files:
`../coord/tasks/`; original setup: `../tmp/race-limit-wall/`.

## Prompt to paste

```text
Continue Unio in /mnt/d/Vibe Coding/_vm/frugal-flock/repo.
You are the lead. Read ../coord/AGENT-LOG.md FIRST (newest entries), then
continue-with-ai-prompt.md, docs/RENAME-UNIO.md, WORKSPACE-RULES.md,
docs/PROVIDER-CAPACITY.md, and docs/DOGFOOD-WORKFLOW.md. Work in your own lead worktree;
never redo or overwrite other branches.

Next steps, in order:
1. Check the status of the pending A/B/C/D reviews and gates.
2. Review each final candidate across companies, then review it yourself.
3. Merge A, B, C, D in that order; run bash tools/quality-check.sh after
   each merge, then push only after its gate passes.
4. Ensure no current file still says the legacy names except where history requires it.

Rules: use the installed frugal-flock 0.4.0 stop/resume around runs until
Unio installation is separately approved; one invocation per task, no
retries; use date for log timestamps; quote paths (they contain spaces).
Never use pgrep -f or pkill -f with a pattern appearing in your own command.
Ask the owner before installing Unio globally or releasing. After every
checkpoint prepend a dated entry to ../coord/AGENT-LOG.md and update this file.
```

## Checkpoint discipline

Use current main and actual local branch/receipts, not an old NEXT instruction.
Update this file and the local log whenever branch, verification, blocker,
active worker or next task changes. Preserve previous failures and distinguish
process exit, validation, review, human acceptance and integration.
Historical detail is in the dated handoffs and Git history.
