# Unio Improvement Backlog

This backlog consolidates pending, accepted, and shipped functional improvements for Unio, organized by priority. It acts as a detailed inventory supporting the [ROADMAP.md](ROADMAP.md) without assigning fixed deadlines or version numbers for unreleased work.

## Current Delivery States

- **Shipped**: Released globally and installed (e.g., v0.5.4).
- **Accepted Development**: Merged in `main`, passes focused checks and personal review, waiting for a release.
- **Partially Implemented**: Working pieces exist in `main`, but the full milestone is incomplete.
- **Pending**: A prepared task or candidate awaiting completion or acceptance. Distinguish an active run from a queued task or a failed attempt.
- **Planned**: Approved by the owner but not yet started.
- **Unknown Evidence**: Claims lacking measured verification or runtime support.

## Functional Priorities

### 1. Allowance, Reset, and Worker Readiness

- **Shipped**: Native shared-budget workflow admission, including the lead in low tier.
- **Added in 0.5.6**: Manual readings with `unio capacity record`/`show`, grouped by shared budget, with observation age, optional reset time, and fresh/stale/expired/Unknown handling. This packages the reviewed store independently of the browser. See [capacity readings](CAPACITY-READINGS.md).
- **Implementation evidence**: Gemini's first candidate passed 3 native checks but had four reproduced defects. Opus corrected those and packaged the command; the lead then corrected two inherited extreme-input crashes before the release gate. The scoreboard preserves each result rather than treating process success as acceptance.
- **Planned**: Automatic provider readings, browser reset/age indicators and their integration with worker readiness and scheduling. No extra per-token spending or promotion of free workers to lead. There is no live meter.
- **Evidence**: [PROVIDER-QUOTA-MONITORING.md](../PROVIDER-QUOTA-MONITORING.md), [TASK-TIME-BUDGETS.md](TASK-TIME-BUDGETS.md)

### 2. Ready-Task Scheduling and Parallel Execution

- **Next Slice**: Automated dependency handling, conflict ownership, and ready-task dispatch.
- **Available now**: The lead can run independent tasks concurrently through native workflows on separate budgets.
- **Planned**: Automatic ready-queue scheduling and explainable idle/dependency decisions.
- **Evidence**: [PARALLEL-WORK.md](PARALLEL-WORK.md)

### 3. Connection, Auth, and Transport Reliability

- **Documented now**: A [help-only readiness inventory](AUTH-READINESS-INVENTORY.md), with local sign-in, remote authentication, allowance and workflow readiness kept distinct. Claude JSON status is the smallest documented first adapter; actual exit and safe-field behavior still need checking.
- **Planned**: Implement supported read-only adapters and improve prompt/connection reliability without blind retries.

### 4. Review Aggregation and Security

- **Planned**: Independent multi-lab review aggregation and security improvements. Native independent reviews are a product goal; however, the current owner delivery policy is personal lead review without spawning additional reviewer jobs.

### 5. Context Efficiency and Measurement

- **Planned**: Measured scan performance optimizations, including automatic-save scan overhead on mounted file systems, and context/token efficiency improvements. Do not invent missing benchmark scores or claim a requested tool was actually used without evidence.

### 6. Work Saving and Recoverable Handoffs

- **Shipped**: Manual and automatic native-run saves and separately authorized restored-worker continuation shipped in 0.5.4.
- **Available now**: Early commits are worker policy and context handoffs already exist. Snapshots are not commits or off-device backups.
- **Planned**: Better enforcement of early checkpoints and clearer recovery/handoff status.
- **Evidence**: [WORK-SAVING-CONTRACT.md](WORK-SAVING-CONTRACT.md)

### 7. Lead Cooldown and Identity Controls

- **Shipped**: Lead cooldown shipped experimentally, opt-in in 0.5.4; genuine limit restart is still unobserved.
- **Planned**: Extended supported adapters/identity and [temporary lead capacity handover](LEAD-CAPACITY-HANDOVER.md) remain future work.
- **Evidence**: [LEAD-COOLDOWN-CONTRACT.md](LEAD-COOLDOWN-CONTRACT.md), [LEAD-COOLDOWN-RESTART.md](LEAD-COOLDOWN-RESTART.md), [LEAD-CAPACITY-HANDOVER.md](LEAD-CAPACITY-HANDOVER.md)

### 8. Work Modes and Model Roles

- **Shipped**: CLI mode/tier switches and shared-budget workflow admission shipped in 0.5.3.
- **Documented now**: Supported model effort controls, main implementation roles, free routine-only workers and a curated task-fit scoreboard.
- **Planned**: Browser policy selectors, automatic task-fit recommendations and richer model/outcome measurements. See [model experience](MODEL-EXPERIENCE.md).
- **Evidence**: [MODEL-EFFORT.md](MODEL-EFFORT.md), [MODEL-EXPERIENCE.md](MODEL-EXPERIENCE.md)

### 9. Browser Appearance and Live Overview

- **Shipped**: Worker updates/output/tracked worktree files shipped in 0.5.3. Themes/basic map shipped in 0.5.4.
- **Shipped in 0.5.5**: Installed launcher, left-to-right layout and task-logo cards with muted outcome strips. Early commits are policy; snapshots do not guarantee a commit or off-device backup.
- **Planned**: Live lead messages and phone pairing are different, planned capabilities. UI polish comes after functional work.
- **Evidence**: [LIVE-WORKSPACE-VIEW.md](LIVE-WORKSPACE-VIEW.md)

### 10. Mobile Session Companion

- **Planned**: Scoped mobile session pairing, revocable QR invitations, and live lead messaging within an active session. Not a general remote desktop.
- **Evidence**: [MOBILE-SESSION-COMPANION.md](MOBILE-SESSION-COMPANION.md)

### 11. Essential Settings and Front-Facing Org

- **Shipped**: AGPL-3.0-only license, lawful attribution, and contribution records. Current README/tagline, repo organization, release/install/provenance and effort/role guides already exist.
- **Planned**: Essential settings/access controls UI.

## Parallel Work

- **Opus**: The initial release-preparation attempt failed OAuth without edits on 2026-10-09. After sign-in, the owner-authorized capacity correction was approved by the lead at `528e214`. Because Grok is unavailable, the owner then authorized further Opus feature work: Opus packaged the native capacity command for 0.5.6; the lead made bounded extreme-input corrections before release validation.
- **Grok**: Capacity Source ended 402 without edits on 2026-10-09; no active Grok run is claimed.
- **Gemini**: Completed the bounded help-only readiness inventory; lead editorial correction tightened three evidence claims. No credentials or model probes were run by the inventory.
- **Verified-free LongCat**: Ran the predefined local link audit: 405 targets checked, 125 skipped, 0 missing. The lead corrected document classification wording. This was routine support, not implementation or security acceptance.
