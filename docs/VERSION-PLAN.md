# Unio version plan

Owner direction, 2026-10-05: close the rename at 0.5.0, then keep the next
changes in separate versions with their implementation and changelog entries.

| Version | Included work | State |
| --- | --- | --- |
| 0.5.0 | Completed A/B/C/D rename; installer, commands, config, docs and prototypes | Source gated and pushed; installed with owner approval; public release pending |
| 0.5.1 | Limit-policy hardening and regression coverage | Implemented; source integrated, publication pending |
| 0.5.2 | Queue approval, reservation and recovery library | Implemented; source integrated, publication pending |
| 0.5.3 | One real browser-to-worker workflow | Service integrated; API, UI and demonstration pending |
| 0.5.4 | Checkpoint-based provider continuation | Approved; contract to freeze before dispatch |

Shipping preparation follows these changes. It does not automatically create
a new version or publish a release. The published v0.4.0 title is now
**Unio 0.4.0 — trustworthy results (M1)**; its existing tag and files are kept.
New public release headings use Unio without a former-name suffix.

For each version, its worker updates the installer version and existing
branding assertion as part of the scoped implementation. The lead rolls its
changelog fragment into the matching unreleased section before the full
merged-tree quality gate. Integrate and push only after that gate passes.
No tag or public release is created without separate owner approval.

The approved 0.5.0 installation preserved agent settings, left the original
config intact for rollback, and migrated worker markers and shared guards.
Private receipts and rollback live under the enclosing workspace's
`artifacts/migration-unio/` and `tmp/unio-next/receipts/`. Installed authentication
stores and billing settings were not changed. The existing workspace path
remains intact so worktree links and historical receipts continue to resolve.
