# Copy this prompt to continue with another AI

Read the newest workspace agent-log entries before acting. This checkpoint
records the completed rename; earlier decisions and failures remain in Git
history and the append-only local log.

Living checkpoint, updated 2026-10-05 14:24:57 +0200 by Codex lead
(GPT-6; exact serving variant not exposed). Source integration main:
aebe23c. The later handoff-only commit does not alter that source.

## Current checkpoint

Unio 0.5.0 is now installed with owner approval. Original agent configuration
remains intact, migrated settings are byte-identical, and project markers and
Git guards use Unio. Private backup/rollback: `../artifacts/migration-unio/`;
actual receipts: `../tmp/unio-next/receipts/`. No new public release was made.
The existing v0.4.0 release title is now Unio without a former-name suffix.

The owner approved all five next milestones. Version sequence: rename 0.5.0,
limit-policy hardening 0.5.1, queue approval/recovery 0.5.2, real browser flow
0.5.3 and provider continuation 0.5.4. See docs/VERSION-PLAN.md and
docs/NEXT-MILESTONE-CONTRACTS.md. No feature task has been invoked yet.
The owner reports the OpenCode Go 5h limit has reset; use GLM 5.3 high for
the first scoped task, then another company review and the lead review.
This capacity report does not establish weekly/monthly headroom or billing.

The owner-approved rename to Unio is complete in source. A, B, C and D were
merged in that order. Each merge passed the complete
`bash tools/quality-check.sh` before its own push to origin/main.

| Slice | Merge | Full quality gate | Origin/main |
| --- | --- | --- | --- |
| A | ce33555 | PASS | pushed |
| B | c76dd7f | PASS | pushed |
| C | 8a482bc | PASS | pushed |
| D | aebe23c | PASS | pushed |

- A: core tool, installer, configuration, worker markers and tests.
  Codex gpt-6.1-sol xhigh won the race; GLM 5.3 high hit the Go cap without
  a candidate. Grok found two defects. The distinct Codex correction
  823a01f passed verification, Google review and the lead's own review.
- B: README, instructions, changelog, provider guide and ignored local role
  cards. Original DeepSeek hit the Go cap; the owner-approved Gemini
  replacement finished. Codex and Grok findings were corrected. Both
  REQUEST-CHANGES reports remain preserved; final acceptance is the lead's
  material-bound decision, not a claimed final independent approval.
- C: current manuals and regenerated Word document. Gemini implemented;
  Codex and Grok reviewed. All reported findings were corrected. Preserved
  independent REQUEST-CHANGES reports are followed by the lead's final
  adjudication; they are not represented as provider approvals.
- D: examples, bridge and prototype. Original Kimi hit the Go cap; the
  owner-approved Grok replacement bf2ffb1 passed verification, Google's
  native review, the lead's review and all three existing browser suites.
- Oversized or binary material refused by native review was reviewed in
  separate native run tasks using complete, hash-bound packets. These
  review transports and their limitations are recorded in the receipts.
- Frozen histories, previous changelog entries and LICENSE are preserved.
  Embedded LICENSE, NOTICE and protocol match their standalone files.
  The final source audit records permitted historical and migration names.
- Read [provider capacity](docs/PROVIDER-CAPACITY.md) before assigning models.
  It preserves the owner's screenshot, dated public limits and actual Go
  failures. The owner's 1h57m reset estimate was recorded as approximately
  2026-10-05 13:30:02 +0200; it is historical and grants no automatic retry.
- The earlier push security findings were recovered and checked with five
  isolated mock probes. LIMIT-WALL still has known signal-coverage and
  provenance limitations; these were not silently changed by the rename.
  Read `../tmp/rename-unio/receipts/security-review-assessment.md` and
  `security-observations.json` before defining a separate hardening task.
- Current source and installed orchestration: Unio 0.5.0, public release
  pending. Installed migration was approved and completed on 2026-10-05.
  The workspace path remains `_vm/frugal-flock`; worktree links stay intact.
  The orchestrator is stopped between authorized calls. Global doctor
  reports missing profiles for inactive historical DeepSeek/GLM/Qwen workers;
  active milestones use their own pinned per-run configuration.

The owner authorizes available AIs for Unio and milestone tasks, including
cross-company reviews, integration and pushes. Routine assignments do not
need repeated permission. The installed rename is approved and complete;
release publication and new billing changes still require owner approval. All original failures and
rejected reviews remain preserved; no automatic provider retries occurred.

Receipts: `../tmp/rename-unio/receipts/`; final candidates and pinned models:
`../tmp/rename-unio/manifest.json`; task files: `../coord/tasks/`;
original setup: `../tmp/race-limit-wall/`.

## Prompt to paste

```text
Continue Unio in /mnt/d/Vibe Coding/_vm/frugal-flock/repo.
You are the lead. Read ../coord/AGENT-LOG.md FIRST (newest entries), then
continue-with-ai-prompt.md, docs/RENAME-UNIO.md, WORKSPACE-RULES.md,
docs/PROVIDER-CAPACITY.md and docs/DOGFOOD-WORKFLOW.md.
Work in your own lead worktree; preserve other branches and receipts.

The A/B/C/D rename is complete: each merge passed its full gate and was
pushed. Check actual current main and receipts before choosing further work;
do not repeat the completed rename runs or automatically retry the failed
Go calls. Define the next concrete owner-requested milestone task from TODO
and the newest log. Known LIMIT-WALL coverage/provenance limitations need a
separate scoped hardening task if selected.

Use the installed unio 0.5.0 control tool and UNIO_* environment variables.
Resume before authorized native runs and stop after.
Use per-run configs, pinned models, bounded wall-clock budgets and receipts.
One invocation per task, no automatic retries; GLM 5.3 stays at high effort.
Every slice gets another company's review, then your own review. Preserve
rejections and distinguish provider output, verification, lead acceptance,
merge, gate and push. The owner already permits available AI assignments.

Take log timestamps from date. Quote all paths containing spaces.
Never use pgrep -f or pkill -f with a pattern appearing in your own command.
The installed rename is already approved. Ask before release publication or
new billing changes; do not ask again for routine authorized assignments.
After every checkpoint prepend a dated entry to ../coord/AGENT-LOG.md and
update continue-with-ai-prompt.md on your own branch.
```

## Checkpoint discipline

Use actual branches and receipts rather than an old NEXT instruction.
Update this file and the shared log when verification, integration, blocker,
active worker or next task changes. Keep the local log append-only.
