# Unio version plan

Owner direction, 2026-10-05: close the rename at 0.5.0, then keep the next
changes in separate versions with their implementation and changelog entries.

The [2026-10-08 milestone review](development/FUNCTIONALITY-FIRST-PLAN.md)
separates shipped features from source additions and recommends a functional
delivery order. The approved v0.5.4 recovery scope stays intact; later release
numbers remain unassigned. Finish recovery before further visual expansion.


Validation update, 2026-10-08: see [completed checks, preserved failures and
remaining release work](development/RECOVERY-ACCEPTANCE-2026-10-08.md). Component coverage does
not replace the final versioned release gate.

| Version | Included work | State |
| --- | --- | --- |
| 0.5.0 | Completed A/B/C/D rename; installer, commands, config, docs and prototypes | [Published 2026-10-06](https://github.com/danielmevit/unio/releases/tag/v0.5.0); source aebe23c; installed with owner approval |
| 0.5.1 | Limit-policy hardening and regression coverage | [Published 2026-10-06](https://github.com/danielmevit/unio/releases/tag/v0.5.1); source af437b1 |
| 0.5.2 | Queue approval, reservation and recovery library | [Published 2026-10-06](https://github.com/danielmevit/unio/releases/tag/v0.5.2); source 1bddeab |
| 0.5.3 | One real browser-to-worker workflow alongside browser output/files; owner-approved work modes yolo/medium/safe and subscription tiers low/medium/high with native shared-budget workflow accounting | [Published 2026-10-08](https://github.com/danielmevit/unio/releases/tag/v0.5.3); exact source ae61bf3d11ff; full gate, artifact and upgrade checks passed; installed with owner approval |
| 0.5.4 | Automatic recovery saves, checkpoint continuation and lead CLI cooldown restart; browser themes and live work map | Themes, responsive radial map with zoom/pan, manual save/inspect/restore, automatic native-run saves and one authorized continuation accepted in main; first supported [lead cooldown runtime](LEAD-COOLDOWN.md) implemented and browser observation budget corrected; real subscription-limit restart acceptance and combined release checks pending; not released |

The owner approved the [delivery priorities](development/ROADMAP.md#approved-delivery-priorities)
on 2026-10-06: finish 0.5.3, deliver 0.5.4, then allowance monitoring, agent
connection reliability, smarter delegation, a built-in parallel review
pipeline, reasoning/context efficiency and measured performance. The owner additionally requires
[automatic work saving](WORK-SAVING.md) during runs and on failures in v0.5.4.
On 2026-10-07 the owner added [lead cooldown restart](development/LEAD-COOLDOWN-RESTART.md):
an owner-enabled supervisor waits outside the lead CLI and restarts it from
the saved handoff after its allowance resets. The five-hour fallback is five
hours and one minute. Repeated lead limits create new waits; existing worker
limit handling stays unchanged. Implement work saving before this restart slice.
Later release numbers and dates are not assigned yet. The
[worker progress contract](WORKER-PROGRESS.md) covers browser output and files;
its implementation has passed native checks and the real funded browser journey.
[Task time budgets](development/TASK-TIME-BUDGETS.md) give substantial work
90 minutes or up to two hours, with bounded individual checks and early saves.
The lead configures the native limit, wrapper and supported CLI deadline for each
assignment. This guidance does not automatically change installed defaults.

Shipping preparation follows these changes. It does not automatically create
a new version or publish a release. The published v0.4.0 title is now
**Unio 0.4.0 — trustworthy results (M1)**; its existing tag and files are kept.
New public release headings use Unio without a former-name suffix.

For each version, its worker updates the installer version and existing
branding assertion as part of the scoped implementation. The lead rolls its
changelog fragment into the matching unreleased section before the full
merged-tree quality gate. Focused validation and lead review permit integration
and pushes under the current delivery policy; publication requires that full gate.
Publication requires owner authorization. On 2026-10-06 the owner authorized
completed 0.5.x releases, unattended sequential browser 0.5.3 and checkpoint
0.5.4 work, and installation of the latest verified release on this machine.
The current sequence under the newest owner YOLO+low policy uses one independent
workflow per shared provider/account including lead, focused native validation and
personal lead review without extra model reviewer jobs for this session, with a
full required release gate before publication. This supersedes the earlier
current-session requirement for two AI-lab reviews on every slice. Independent
reviews remain available under other owner-selected policies. Frozen checks and
owner authority remain in force. Exact pushes remain required. It does
not authorize billing changes or publication of unfinished milestones.

The approved 0.5.0 installation preserved agent settings, left the original
config intact for rollback, and migrated worker markers and shared guards.
Private receipts and rollback live under the enclosing workspace's
`artifacts/migration-unio/` and `tmp/unio-next/receipts/`. Installed authentication
stores and billing settings were not changed. The existing workspace path
remains intact so worktree links and historical receipts continue to resolve.

The historical 0.5.0, 0.5.1 and 0.5.2 tags retain their original gated source
snapshots, including their earlier development notes. Each public release
includes an exact-source installer, source archive, legal files, checksums and
provenance. Isolated install, version, help, legal and offline workflow checks
passed, and all six downloaded assets matched their prepared hashes.
