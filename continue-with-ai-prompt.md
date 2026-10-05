# Copy this prompt to continue with another AI

Open the repo in your new AI session and paste the Prompt to paste below.
Read the local agent log first; this file gives the current checkpoint.
Earlier checkpoint notes remain in Git history and the append-only local log.

Living checkpoint, updated 2026-10-05 12:06 +0200 by Codex lead
(GPT-6; exact serving variant not exposed). Current local main: ce33555;
A full gate and push are pending. Read the newest local log and receipts.

## Current checkpoint

- Source rename tasks A/B/C/D were prepared and dispatched through native
  Frugal Flock with pinned models, timeouts and zero automatic retries.
- A Codex candidate passed 8/8 task checks; GLM's race invocation hit the
  Go cap and was interrupted without source changes. Grok requested two
  changes; distinct Codex RENAME-A-FIX completed at 823a01f, passed 5/5
  checks and received Google approval plus lead approval. A merged locally
  at ce33555; its full gate is running, with no push yet at this snapshot.
- B Gemini replacement c11935d passed 3/3 checks. Its Codex review finished
  with changes requested. Lead correction 7eb91b9 addressed seven findings
  and passed 3/3 checks; Grok then requested this checkpoint correction and
  confirmed the rest of the tree matches the contract. Both rejections are
  preserved. The current B branch is agent/antigravity-rename-b; resolve its
  actual HEAD before acting, since this checkpoint is itself a lead update.
  The lead will review the corrected checkpoint and current integration base.
- C Google candidate plus lead docs corrections is 27e2656. Codex's six
  findings and Grok's two follow-up findings are preserved and addressed.
  A focused Grok closing review checks the final correction and the exact D
  API-header counterpart; unchanged file hashes bind the earlier full review.
- D original Kimi run hit the Go cap without edits; approved Grok replacement
  bf2ffb1 passed 9/9 checks, native Google review and all three browser suites.
  The original DeepSeek B failure also remains preserved.
- Merge A, then B, then C, then D. Run the full quality gate after each
  merge and push each only after its gate passes. B/C/D are not merged
  at this snapshot; check the newest log and gate
  receipts for later integration.
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
1. Read the actual A gate receipt, push A only on PASS, and check the
   remaining C closing review. Do not wait on the finished rejected B reviews.
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
