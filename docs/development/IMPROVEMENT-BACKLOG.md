# Unio Improvement Backlog

This backlog consolidates pending, accepted, and shipped functional improvements for Unio, organized by priority. It acts as a detailed inventory supporting the [ROADMAP.md](ROADMAP.md) without assigning fixed deadlines or version numbers for unreleased work.

## Current Delivery States

- **Shipped**: Released globally and installed (e.g., v0.5.4).
- **Accepted Development**: Merged in `main`, passes focused checks and personal review, waiting for a release.
- **Partially Implemented**: Working pieces exist in `main`, but the full milestone is incomplete.
- **Pending**: Being actively worked on in parallel branches (e.g., pending 0.5.5 candidate, manual allowance component).
- **Planned**: Approved by the owner but not yet started.
- **Unknown Evidence**: Claims lacking measured verification or runtime support.

## Functional Priorities

### 1. Allowance, Reset, and Worker Readiness

- **Next Slice**: Implement manual capacity readings and age tracking, treating missing/stale capacity as `Unknown`.
- **Planned**: Shared-budget accounting and integration with live fleet quotas. One workflow per shared budget in low tier includes lead. No extra per-token spending/free-model promotion.
- **Dependencies**: Wait for Grok's pending source-only manual allowance component.
- **Evidence**: [PROVIDER-QUOTA-MONITORING.md](../PROVIDER-QUOTA-MONITORING.md), [TASK-TIME-BUDGETS.md](TASK-TIME-BUDGETS.md)

### 2. Ready-Task Scheduling and Parallel Execution

- **Next Slice**: Automated dependency handling, conflict ownership, and ready-task dispatch.
- **Planned**: Parallel execution using independent accounts.
- **Evidence**: [PARALLEL-WORK.md](PARALLEL-WORK.md)

### 3. Connection, Auth, and Transport Reliability

- **Planned**: Explicit authentication checks, prompt transport reliability, and avoiding blind retries on known connection issues.

### 4. Review Aggregation and Security

- **Planned**: Independent multi-lab review aggregation and security improvements. Native independent reviews are a product goal; however, the current owner delivery policy is personal lead review without spawning additional reviewer jobs.

### 5. Context Efficiency and Measurement

- **Planned**: Measured scan performance optimizations, context/token efficiency improvements. Do not invent missing benchmark scores or claim a requested tool was actually used without evidence.

### 6. Work Saving and Recoverable Handoffs

- **Shipped**: Manual and automatic native-run saves and separately authorized restored-worker continuation shipped in 0.5.4.
- **Planned**: Broader work-saving features, early commits, and handoffs. Note: Snapshots are not commits or off-device backups.
- **Evidence**: [WORK-SAVING-CONTRACT.md](WORK-SAVING-CONTRACT.md)

### 7. Lead Cooldown and Identity Controls

- **Shipped**: Lead cooldown shipped experimentally, opt-in in 0.5.4; genuine limit restart is still unobserved.
- **Planned**: Extended supported adapters/identity remain future work.
- **Evidence**: [LEAD-COOLDOWN-CONTRACT.md](LEAD-COOLDOWN-CONTRACT.md), [LEAD-COOLDOWN-RESTART.md](LEAD-COOLDOWN-RESTART.md)

### 8. Work Modes and Model Roles

- **Shipped**: CLI mode/tier switches and shared-budget workflow admission shipped in 0.5.3.
- **Planned**: Live allowance readings/automatic readiness and browser selectors, fine-grained model effort controls/roles, leveraging free routine-only workers, and task-fit evidence.
- **Evidence**: [MODEL-EFFORT.md](MODEL-EFFORT.md), [MODEL-EXPERIENCE.md](MODEL-EXPERIENCE.md)

### 9. Browser Appearance and Live Overview

- **Shipped**: Worker updates/output/tracked worktree files shipped in 0.5.3. Themes/basic map shipped in 0.5.4.
- **Accepted Development**: Launcher/left-to-right/task-logo cards are accepted development pending 0.5.5 publication. Early commits are policy; snapshots do not guarantee a commit or off-device backup.
- **Planned**: Live lead messages and phone pairing are different, planned capabilities. UI polish comes after functional work.
- **Evidence**: [LIVE-WORKSPACE-VIEW.md](LIVE-WORKSPACE-VIEW.md)

### 10. Mobile Session Companion

- **Planned**: Scoped mobile session pairing, revocable QR invitations, and live lead messaging within an active session. Not a general remote desktop.
- **Evidence**: [MOBILE-SESSION-COMPANION.md](MOBILE-SESSION-COMPANION.md)

### 11. Essential Settings and Front-Facing Org

- **Shipped**: AGPL-3.0-only license, lawful attribution, and contribution records. Current README/tagline, repo organization, release/install/provenance and effort/role guides already exist.
- **Planned**: Essential settings/access controls UI.

## Parallel Work

- **Opus**: Failed OAuth with no edits on 2026-10-09, not preparing a candidate.
- **Grok**: Capacity Source ended 402 with no edits on 2026-10-09 and is queued, not currently working.
