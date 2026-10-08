# Work saving — manual and automatic saves in source for v0.5.4

Owner requirement recorded 2026-10-06 after a worker reached its allowance
limit with useful edits but no final commit. See the
[version plan](VERSION-PLAN.md), the frozen
[implementation contract](development/WORK-SAVING-CONTRACT.md) and the
[roadmap](development/ROADMAP.md#approved-delivery-priorities).

## Status

| Part | State |
| --- | --- |
| Manual `unio save create`, `inspect` and `restore` | Implemented in source (slice 1); not in any public release yet |
| Automatic baseline, periodic and final saves during runs | Implemented in source (automatic part of slice 2); unreleased |
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

`create` acquires the source worker's native lock exactly once (a validated, regular, owned file in a safe parent directory, without following symlinks or blocking) and observes the worktree twice. It saves only when both observations match: committed history after the base (as a verified Git bundle carrying HEAD over the base), the full index and the working files, each with its own bytes and modes. Staged, unstaged, untracked, deleted, binary, empty, executable and retained deleted-from-index content is kept exactly. Ignored caches and the native ignored role cards are omitted before any of their bytes are read; however, required paths like HEAD-tracked files inside ignored directories are still saved. The base is the frozen task base that `unio run` recorded, otherwise the commit named by `coord/base`.

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
the worker is busy, its native lock or coordination parents are unsafe, or it
cannot be observed. Unsafe lock admission refuses before changing saved or
claim evidence. Existing owned, single-link 0644 native locks are supported;
new native locks are 0600, and save-store privacy remains 0700/0600.

`restore` writes into a different worker that is idle, clean and at the
saved base in the same repository. Everything is validated first: manifest,
content, task text, bundle (in a private quarantine), paths and collisions
with ignored destination files. It then records a claim, fast-forwards only
the destination branch, rebuilds the exact index and working files, and
compares the result with the saved fingerprint. On failure it restores the
destination's exact earlier state, or records the outcome as Unknown and
never restores into that destination again automatically. It never commits,
resets the source, cleans ignored files or moves another branch.

## Automatic saving (in source, unreleased)

Native `unio run` saves local file state before starting its provider, checks
for changed state every sixty seconds, and captures final state after success,
failure, timeout or graceful TERM/INT interruption. Unchanged periodic state
creates no duplicate save. Saving needs no AI request or final answer. Each
save records its worker, task, native attempt ID, revisions, file hashes and
observation time; final saves also record the actual process exit.

The same validated, bounded format and retention rules apply as for manual
saves. The native shell keeps its existing worker and shared-account ownership;
providers and capture children inherit neither lock nor account-control pipes.
Capture children have a thirty-second deadline and are stopped and reaped.
Provider execution continues if saving fails. Its real exit and native quality
receipts remain separate from saving; a refused or failed final capture keeps
the previous good save visible through `unio save inspect --worker WORKER`.
No allowance telemetry is required, and no worker is benched or restarted by a
save failure. Forced process termination (SIGKILL), host loss or disk failure
can prevent the final save; already published checkpoints remain available.
`unio kill TASK` requests orderly shutdown and allows up to sixty seconds for
provider cleanup, final capture and receipts before forcing owned processes to
stop. It retains process identity checks and makes no new provider call.

Workers receive guidance to commit coherent, scoped changes regularly. A
finish reserve leaves time to validate and commit before the run deadline
or a known allowance boundary. Use supported readings and timestamped manual
input where available; missing quota information remains Unknown. This
cannot predict every provider cutoff, so saving works independently of the
AI answering a final request.

Use `inspect` for the last successful save, observation time, latest attempt
and live saved/changed/Unknown state. Concurrent edits can prevent an exact
latest capture; those changing bytes are never reported as successfully saved.

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

`tests/unio-work-saving-auto.py` uses offline native providers to exercise failed
exits without a final answer, exact restore, timeout, termination, periodic
change capture and deduplication, capture failure, last-good retention and
released worker/account ownership without allowance telemetry. Authorized
continuation still needs its own implementation and acceptance; automatic
saving grants no additional provider invocation or inherited verification.
