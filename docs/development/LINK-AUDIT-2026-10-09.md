# Local Documentation Link Audit — 2026-10-09

Routine inventory of inline relative Markdown links at frozen main `43332bb55677302fa854ee230c1dec58db746049`.

## Method

- Ran `python3 -B /mnt/d/Vibe Coding/_vm/frugal-flock/tmp/unio-next/audit-local-markdown-links-20261009.py` once; raw JSON kept private in enclosing tmp.
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

## Active vs. historical docs

- **Active docs** (current contracts, all clean): `README.md`, `docs/SETUP.md`, `docs/GUIDEBOOK.md`, `docs/PROTOCOL.md`, `docs/WORK-MODES.md`, `docs/development/ROADMAP.md`, `docs/development/LEAD-ROUTING.md`, `docs/development/MODEL-EFFORT.md`, `docs/development/LEAD-COOLDOWN-*.md`, `docs/development/RECOVERY-ACCEPTANCE-2026-10-08.md`, `docs/development/continue-with-ai-prompt.md`, `docs/development/WORKSPACE-RULES.md`, `docs/ai/START_HERE.md`, `docs/ai/MODEL-ROLES.md`, `docs/ai/LEAD-ESCALATION.md`, `docs/QUALITY-USAGE.md`, `docs/QUALITY-M1-CONTRACT.md`, `docs/M1-STATUS.md`, `docs/M1-ACCEPTANCE-AUDIT.md`, `docs/PROVIDER-CAPACITY.md`, `docs/PROVIDER-QUOTA-MONITORING.md`, `docs/CAPACITY-AWARE-CONTINUATION.md`, `docs/JOB-QUEUE-STORE.md`, `docs/DOGFOOD-WORKFLOW.md`, `docs/BRIDGE-ACTIVITY.md`, `bridge/README.md`, `research/COMPETITIVE-REVIEW.md`, `research/multi-agent-claude-review.md`.
- **Historical examples** (point-in-time snapshots, also clean): `docs/RELEASE-0.5.3.md`, `docs/RELEASE-0.5.4.md`, `docs/RELEASE-0.5.5.md`, `docs/SESSION-HANDOFF-2026-10-04.md`, `docs/SESSION-HANDOFF-2026-10-05.md`, `docs/FINDINGS-2026-10-05.md`, `docs/M1.5-LIVE-CANARY.md`, `docs/M2-DOGFOOD-PLAN.md`, `docs/M2-USER-TEST.md`, `docs/RENAME-UNIO.md`, `docs/PLAN-DRAFTS.md`, `docs/WATCH-USAGE.md`, `docs/TOOLCRAFT-REFERENCE.md`, `docs/UX-DIRECTION.md`, `docs/BRAND.md`, `docs/ENGINE-FINDINGS.md`, `docs/FEATURE-DECISIONS.md`, `docs/FREE-MODELS.md`, `docs/LICENSING.md`, `docs/NEXT-MILESTONE-CONTRACTS.md`, `docs/VERSION-PLAN.md`, `docs/MASTER-PLAN.md`, `docs/TESTPLAN.md`, `docs/EXAMPLE.md`, `docs/HANDBOOK.md`, `docs/HANDOFF.md`, `docs/AI-HANDOFF.md`, `docs/AI-TEAM-WORKFLOWS.md`, `docs/RESEARCH-FINDINGS.md`, `docs/WORK-SAVING.md`, `docs/WORKER-PROGRESS.md`, `docs/WORK-POLICY-STATE-CONTRACT.md`, `docs/BROWSER-*.md`, `docs/development/FUNCTIONALITY-FIRST-PLAN.md`, `docs/development/IMPROVEMENT-BACKLOG.md`, `docs/development/MOBILE-SESSION-COMPANION.md`, `docs/development/LIVE-WORKSPACE-VIEW.md`, `docs/development/MODEL-SCOREBOARD.md`, `docs/development/MODEL-EXPERIENCE.md`, `docs/development/TASK-TIME-BUDGETS.md`, `docs/development/PARALLEL-WORK.md`, `docs/development/README.md`, `changelog.d/IMPROVEMENT-BACKLOG-GEMINI-1.md`.

## Result

No broken inline relative links found at this commit. No file fixes made; this is an inventory report only.
