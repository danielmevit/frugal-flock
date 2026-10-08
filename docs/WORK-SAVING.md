# Work saving — manual commands in source, automatic saving planned for v0.5.4

Owner requirement recorded 2026-10-06 after a worker reached its allowance
limit with useful edits but no final commit. See the
[version plan](VERSION-PLAN.md), the frozen
[implementation contract](development/WORK-SAVING-CONTRACT.md) and the
[roadmap](development/ROADMAP.md#approved-delivery-priorities).

## Status

| Part | State |
| --- | --- |
| Manual `unio save create`, `inspect` and `restore` | Implemented in source (slice 1); not in any public release yet |
| Automatic baseline, periodic and final saves during runs | Planned for v0.5.4 (slice 2) |
| One authorized continuation from a save (`unio save continue`) | Planned for v0.5.4 (slice 2); not available |
| Lead cooldown supervisor | Later slice under its own contract |

The current public release is v0.5.3. It contains none of these commands.
The source version stays at 0.5.3 until the combined v0.5.4 delivery has
passed its full release gate.

## Manual saving (slice 1, in source)

```text
unio save create WORKER TASK
unio save inspect SAVE_ID [--json]
unio save inspect --worker WORKER [--json]
unio save restore SAVE_ID DESTINATION
```

These commands make no provider call and work while STOP is set. Exit 0
means success, 1 a known refusal or failure, 2 bad arguments, a busy lock
or an Unknown restore outcome.

`create` holds the source worker's native lock and observes the worktree
twice. It saves only when both observations match: committed history after
the base (as a verified Git bundle carrying HEAD over the base), the full
index and the working files, each with its own bytes and modes. Staged,
unstaged, untracked, deleted, binary, empty and executable content is kept
exactly. Ignored caches and the native ignored role cards are omitted before
any of their bytes are read. The base is the frozen task base that `unio run`
recorded, otherwise the commit named by `coord/base`.

A save is refused, not partially written, for changing bytes, secret-looking
names (including ignored `.env` files and secrets in carried commits, even
when later deleted), symbolic links, hard links, FIFOs, nested repositories,
unmerged, sparse, assume-unchanged, skip-worktree or intent-to-add index
states, an operation in progress, unsafe or case-colliding path names and
anything over the bounds: 4000 paths, 100 commits, 4 MiB per file, 32 MiB
stored, 1 MiB task text, 30 seconds. The source HEAD, index and files are
never written.

Saves live under the private `coord/saves/` directory: one directory per
save with `manifest.json`, the literal task text, a content pool named by
SHA-256 and the optional bundle. A save becomes visible only after it is
complete and verified; an interrupted save leaves the previous good save in
place. Each worker keeps its latest five unclaimed saves; restore claims pin
the saves they used. A separate latest-attempt record per worker shows a
newer refused or failed attempt without hiding the last good save.

`inspect` validates every stored byte and reports the save, or a worker's
last good save, latest attempt and live state. Live state is Unknown while
the worker is busy or cannot be observed.

`restore` writes into a different worker that is idle, clean and at the
saved base in the same repository. Everything is validated first: manifest,
content, task text, bundle (in a private quarantine), paths and collisions
with ignored destination files. It then records a claim, fast-forwards only
the destination branch, rebuilds the exact index and working files, and
compares the result with the saved fingerprint. On failure it restores the
destination's exact earlier state, or records the outcome as Unknown and
never restores into that destination again automatically. It never commits,
resets the source, cleans ignored files or moves another branch.

## Automatic saving (planned for v0.5.4)

Unio should save recoverable checkpoints throughout a run, preserving
unfinished work when an AI stops unexpectedly. The native supervisor saves
local file state at the start, periodically when edits change, and after a
provider failure or timeout. Saving needs no AI request. Each save records
its worker, task, run, revisions, file hashes and actual observation time.

Workers receive guidance to commit coherent, scoped changes regularly. A
finish reserve leaves time to validate and commit before the run deadline
or a known allowance boundary. Use supported readings and timestamped manual
input where available; missing quota information remains Unknown. This
cannot predict every provider cutoff, so saving works independently of the
AI answering a final request.

Show the last successful save and its age, plus unsaved, stale, refused or
failed capture states. A failed final save must leave the previous valid
save available. Concurrent edits can prevent an exact latest capture; never
claim those changing bytes were saved successfully.

## Recovery and acceptance

A continuation (planned) restores a save into a separate idle worker and
starts one separately authorized new task with exclusive ownership, followed
by fresh checks and independent reviews. It does not inherit earlier
readiness. Keep the original branch, files and failed run intact.

Saving never commits arbitrary dirty files or accepts code. A coherent
source commit is still subject to checks and reviews. A recovery save is
explicitly unverified. Restore and inspection make no provider calls.

Filename exclusions cannot guarantee arbitrary source or task text is
secret-free. Worktrees are trusted-host coordination, and a private local
save is not an off-device backup.

## Required checks

Slice 1 is covered by `tests/unio-work-saving.py`: actual restored HEAD,
full index and bytes/modes, source immutability, zero provider calls,
corruption, unsupported states, concurrent edits, interrupted publication,
retention, pinning, caps, destination refusals, rollback and Unknown.

Slice 2 still needs offline providers to prove abrupt quota failure,
timeout, termination, missing allowance telemetry and low reported
allowance, preserving the original failed exit, and that a continuation
neither authorizes a second paid attempt nor bypasses current verification.
