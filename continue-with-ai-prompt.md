# Copy this prompt to continue with another AI

Open the repo in your new AI session and paste the Prompt to paste below.
Read the local agent log first; this file gives the current checkpoint.
Earlier checkpoint notes remain in Git history and the append-only local log.

Living checkpoint, updated 2026-10-05 10:50 +0200 by Claude Code lead
(claude-opus-5-5), wt/claude-lead on agent/claude-lead, main 9d9f12c.
The lead stopped early because its usage limit was close.

## Current checkpoint

- **Unio Rename:** The rename cycle is in progress from frozen base `181f13e`.
- Slice A (Runtime and installer) and Slice C (Guides) are currently in cross-company independent reviews.
- Slice B (README and top-level files) and Slice D (Examples) had their original runs interrupted due to usage limits. Replacement runs were authorized and launched.
- **Provider Capacity:** A new guide is available at `docs/PROVIDER-CAPACITY.md` detailing provider capacity and limits.
- **Legacy Path:** The local workspace path `_vm/frugal-flock` stays intact as a legacy local path. The globally installed build tool remains Frugal Flock 0.4.0 (legacy build tool) until owner approval, while source targets Unio 0.5.0.

Owner directions: cross-company review follows for A/B/C/D, then integration under explicit owner authorization.

## Prompt to paste

```text
Continue Unio in /mnt/d/Vibe Coding/_vm/frugal-flock/repo.
You are the lead. Read ../coord/AGENT-LOG.md FIRST (newest entries), then
continue-with-ai-prompt.md, docs/RENAME-UNIO.md, WORKSPACE-RULES.md,
docs/PROVIDER-CAPACITY.md, and docs/DOGFOOD-WORKFLOW.md. Work in your own lead worktree;
never redo or overwrite other branches.

Next steps, in order:
1. Check the status of the pending A/B/C/D reviews and gates.
2. Integrate slices only after their full gate passes and is pushed, with cross-company review and lead review.
3. Ensure no current file still says the legacy names except where history requires it.

Rules: unio stop/resume around runs; one invocation per task, no
retries; use `date` for log timestamps; quote paths (they contain spaces).
Ask the owner before installing Unio globally or releasing. After every
checkpoint prepend a dated entry to ../coord/AGENT-LOG.md and update this file.
```

## Checkpoint discipline

Use current main and actual local branch/receipts, not an old NEXT instruction.
Update this file and the local log whenever branch, verification, blocker,
active worker or next task changes. Preserve previous failures and distinguish
process exit, validation, review, human acceptance and integration.
Historical detail is in the dated handoffs and Git history.
