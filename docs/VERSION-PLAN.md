# Unio version plan

Owner direction, 2026-10-05: close the rename at 0.5.0, then keep the next
changes in separate versions with their implementation and changelog entries.

| Version | Included work | State |
| --- | --- | --- |
| 0.5.0 | Completed A/B/C/D rename; installer, commands, config, docs and prototypes | [Published 2026-10-06](https://github.com/danielmevit/unio/releases/tag/v0.5.0); source aebe23c; installed with owner approval |
| 0.5.1 | Limit-policy hardening and regression coverage | [Published 2026-10-06](https://github.com/danielmevit/unio/releases/tag/v0.5.1); source af437b1 |
| 0.5.2 | Queue approval, reservation and recovery library | [Published 2026-10-06](https://github.com/danielmevit/unio/releases/tag/v0.5.2); source 1bddeab; latest completed public release |
| 0.5.3 | One real browser-to-worker workflow | Service and large-prompt transport integrated; API, UI and demonstration pending; unpublished |
| 0.5.4 | Checkpoint-based provider continuation | Approved; contract to freeze before dispatch |

Shipping preparation follows these changes. It does not automatically create
a new version or publish a release. The published v0.4.0 title is now
**Unio 0.4.0 — trustworthy results (M1)**; its existing tag and files are kept.
New public release headings use Unio without a former-name suffix.

For each version, its worker updates the installer version and existing
branding assertion as part of the scoped implementation. The lead rolls its
changelog fragment into the matching unreleased section before the full
merged-tree quality gate. Integrate and push only after that gate passes.
Publication requires owner authorization. On 2026-10-06 the owner authorized
completed 0.5.x releases, unattended sequential browser 0.5.3 and checkpoint
0.5.4 work, and installation of the latest verified release on this machine.
The current sequence uses native Unio workers, two independent AI-lab reviews,
a lead overview, full quality gates and exact pushes. It does not authorize
billing changes or publication of unfinished milestones.

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
